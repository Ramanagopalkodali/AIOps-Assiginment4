"""Generate Grafana JSON and retain each query's AI prompt in panel descriptions.

Prompt: Build an accessible captioning observability dashboard with five-second
refresh. Order health, work, latency, then VM resources. Use linear labeled axes,
units, legends and explanatory stories. Distinguish series by dash/point shapes
as well as Okabe-Ito colors. Correlate bulk activity with VM CPU/RAM on shared time.
Use histogram_quantile for p95, rate(sum)/rate(count) for weighted mean latency,
and clearly label metric reset behavior and VM versus process measurements.
"""
import json
from pathlib import Path

PANELS = []
COLORS = ['#0072B2', '#E69F00', '#009E73', '#CC79A7', '#56B4E9', '#D55E00']


def panel(title, description, queries, unit='short', axis='', kind='timeseries', w=12, h=8, x=0, y=0):
    overrides = []
    for i, (_, legend) in enumerate(queries):
        overrides.append({'matcher': {'id': 'byName', 'options': legend}, 'properties': [
            {'id': 'color', 'value': {'mode': 'fixed', 'fixedColor': COLORS[i % len(COLORS)]}},
            {'id': 'custom.lineStyle', 'value': {'fill': 'solid' if i % 2 == 0 else 'dash', 'dash': [8, 5]}},
            {'id': 'custom.pointSize', 'value': 3 + i % 3},
        ]})
    p = {'id': len(PANELS) + 1, 'title': title, 'description': description,
         'type': kind, 'datasource': {'type': 'prometheus', 'uid': 'prometheus'},
         'gridPos': {'x': x, 'y': y, 'w': w, 'h': h},
         'targets': [{'refId': chr(65+i), 'expr': expr, 'legendFormat': legend, 'range': True}
                     for i, (expr, legend) in enumerate(queries)],
         'fieldConfig': {'defaults': {'unit': unit, 'min': 0, 'decimals': 2,
             'color': {'mode': 'palette-classic'},
             'custom': {'axisLabel': axis, 'axisCenteredZero': False, 'axisPlacement': 'auto',
                 'scaleDistribution': {'type': 'linear'}, 'drawStyle': 'line',
                 'lineWidth': 2, 'fillOpacity': 5, 'showPoints': 'always', 'pointSize': 3,
                 'spanNulls': False}}, 'overrides': overrides},
         'options': {'tooltip': {'mode': 'multi'},
             'legend': {'displayMode': 'table', 'placement': 'bottom', 'showLegend': True,
                        'calcs': ['lastNotNull', 'max']}}}
    if kind == 'stat':
        p['options'] = {'reduceOptions': {'calcs': ['lastNotNull'], 'fields': '', 'values': False},
                        'colorMode': 'none', 'graphMode': 'none', 'textMode': 'auto'}
        p['fieldConfig']['defaults']['custom'] = {}
        p['fieldConfig']['overrides'] = []
    PANELS.append(p)
    return p


def status(title, expr, x):
    p = panel(title, 'Current status: 1 = ready/reachable; 0 = unavailable. A reachable exporter alone does not prove inference works.',
              [(expr, title)], kind='stat', w=6, h=4, x=x, y=0)
    p['fieldConfig']['defaults']['mappings'] = [{'type': 'value', 'options': {
        '0': {'text': 'DOWN / NOT READY', 'color': '#D55E00'},
        '1': {'text': 'UP / READY', 'color': '#0072B2'}}}]


status('Application exporter', 'up{job="caption_app"}', 0)
status('Caption model ready', 'caption_model_ready{job="caption_app"}', 6)
status('Ubuntu node exporter', 'up{job="node"}', 12)
panel('Active bulk jobs', 'Current accepted bulk jobs, including work waiting for the CPU lock. Zero means no bulk job is in progress.',
      [('caption_active_jobs{mode="bulk"}', 'Bulk jobs')], kind='stat', w=6, h=4, x=18, y=0)

panel('Successful images • per mode', 'Images completed per second over one minute. AI prompt: sum the rate of successful image counters separately for Single and Bulk; preserve mode comparison.',
      [(f'sum(rate(caption_images_total{{status="success",mode="{mode}"}}[1m]))', label)
       for mode, label in [('single', 'Single'), ('bulk', 'Bulk')]], 'suffix: images/s', 'Images/s (linear)', y=4)
panel('Accepted jobs in progress', 'Concurrent jobs may wait for one shared CPU model. Compare bulk activity with the resource panels on the same time axis.',
      [('caption_active_jobs{mode="single"}', 'Single'), ('caption_active_jobs{mode="bulk"}', 'Bulk')],
      'short', 'Jobs (linear)', x=12, y=4)
panel('Model inference • mean and p95', 'Wall time in model.generate only. AI prompt: weighted mean = sum(rate(duration_sum))/sum(rate(duration_count)); approximate p95 = histogram_quantile over summed buckets. No observations gives a gap, not zero latency.',
      [('sum(rate(caption_inference_seconds_sum[2m])) / sum(rate(caption_inference_seconds_count[2m]))', 'Mean'),
       ('histogram_quantile(0.95, sum by (le) (rate(caption_inference_seconds_bucket[2m])))', 'p95 estimate')],
      's', 'Inference seconds (linear)', y=12)
panel('Per-image latency • decode + queue + inference', 'AI prompt: calculate weighted per-mode mean image latency from histogram sums and counts. Queue delay is included here, unlike model inference.',
      [(f'sum(rate(caption_image_duration_seconds_sum{{mode="{mode}"}}[2m])) / sum(rate(caption_image_duration_seconds_count{{mode="{mode}"}}[2m]))', label)
       for mode, label in [('single', 'Single'), ('bulk', 'Bulk')]], 's', 'Seconds/image (linear)', x=12, y=12)
panel('Whole-job duration • Summary', 'AI prompt: mean full-job duration = Summary sum rate divided by Summary observation count rate, per mode. Bulk includes all images, so it should usually exceed Single. Python Summary has _sum and _count, not built-in quantiles.',
      [(f'sum(rate(caption_job_duration_seconds_sum{{mode="{mode}"}}[5m])) / sum(rate(caption_job_duration_seconds_count{{mode="{mode}"}}[5m]))', label)
       for mode, label in [('single', 'Single'), ('bulk', 'Bulk')]], 's', 'Seconds/job (linear)', y=20)
panel('Images attempted since backend start', 'AI prompt: sum image counters by mode and success/error outcome. These totals reset when the backend restarts; status is also written in the result CSV.',
      [(f'sum(caption_images_total{{mode="{mode}",status="{state}"}})', f'{label} {state}')
       for mode,label in [('single','Single'),('bulk','Bulk')] for state in ('success','error')],
      'short', 'Images (linear)', x=12, y=20)
panel('Ubuntu VM CPU • correlate with bulk', 'AI prompt: VM CPU percent = 100*(1-mean(rate(idle CPU seconds[1m]))) over VM cores. Bulk line uses the right axis. These are Ubuntu guest metrics, not Mac host metrics.',
      [('100 * (1 - avg(rate(node_cpu_seconds_total{job="node",mode="idle"}[1m])))', 'VM CPU'),
       ('caption_active_jobs{mode="bulk"}', 'Bulk jobs')], 'percent', 'VM CPU % (linear)', y=28)
panel('Ubuntu VM memory • correlate with bulk', 'AI prompt: used-memory percent = 100*(1-MemAvailable/MemTotal). Bulk jobs use the right axis. MemAvailable includes reclaimable memory; do not substitute MemFree.',
      [('100 * (1 - node_memory_MemAvailable_bytes{job="node"} / node_memory_MemTotal_bytes{job="node"})', 'VM memory'),
       ('caption_active_jobs{mode="bulk"}', 'Bulk jobs')], 'percent', 'VM memory % (linear)', x=12, y=28)
for p in PANELS[-2:]:
    p['fieldConfig']['overrides'].append({'matcher': {'id':'byName', 'options':'Bulk jobs'}, 'properties':[
        {'id':'custom.axisPlacement','value':'right'}, {'id':'custom.axisLabel','value':'Bulk jobs (linear)'},
        {'id':'unit','value':'short'}, {'id':'custom.drawStyle','value':'bars'},
        {'id':'custom.fillOpacity','value':12}]})

panel('Ubuntu root filesystem • used space', 'AI prompt: root filesystem used percent = 100*(1-avail/size), select mountpoint=/ and exclude tmpfs/overlay. This measures the guest filesystem, not the Mac disk.',
      [('100 * (1 - node_filesystem_avail_bytes{job="node",mountpoint="/",fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes{job="node",mountpoint="/",fstype!~"tmpfs|overlay"})', 'Root disk')],
      'percent', 'Disk used % (linear)', y=36)
panel('Inference-process RAM and model weights', 'Model weights are parameter/buffer storage only; RSS also includes Python, temporary tensors and decoded inputs. These are bytes, not VM-wide RAM.',
      [('caption_process_memory_bytes', 'Process RSS'), ('caption_model_weight_bytes', 'Model weights')],
      'bytes', 'Memory bytes (linear)', x=12, y=36)
panel('Jobs completed by outcome', 'AI prompt: sum completed job counters for success/partial/error separately. Partial means some ZIP members failed. Counters reset on backend restart.',
      [(f'sum(caption_jobs_total{{status="{s}"}})', s.title()) for s in ('success','partial','error')],
      'short', 'Jobs (linear)', y=44)
panel('Client sessions • image activity', 'AI prompt: show successful image counts by the first 12 safe characters of the actual browser session ID. Session prefixes are not unique people and can collide. For a small demo only; avoid unbounded labels in production.',
      [('sum by (client) (caption_images_total{status="success"})', '{{client}}')],
      'short', 'Images (linear)', x=12, y=44)
panel('Inference-process CPU', '100% equals one fully used CPU core; this can exceed 100% on multiple cores. VM CPU above is normalized across all VM cores.',
      [('caption_process_cpu_percent', 'Process CPU')], 'percent', 'Process CPU % (linear)', y=52)
panel('Rejected uploads', 'Rejected oversized or malformed uploads. Corrupt images inside accepted jobs are counted in image errors instead. Rejections do not become accepted jobs.',
      [('caption_rejected_uploads_total', 'Rejected requests')], 'short', 'Rejections (linear)', x=12, y=52)
panel('Uploaded input bytes • rate', 'AI prompt: show rate of accepted uploaded-byte counters separately by mode. This is application input volume, not operating-system network traffic.',
      [('sum(rate(caption_upload_bytes_total{mode="single"}[1m]))', 'Single'),
       ('sum(rate(caption_upload_bytes_total{mode="bulk"}[1m]))', 'Bulk')], 'Bps', 'Bytes/second (linear)', y=60)
panel('Prometheus firing alerts', 'Number of firing alert series. Check Prometheus Alerts, Alertmanager and the local receiver for details; pending conditions are excluded.',
      [('sum(ALERTS{alertstate="firing"}) or vector(0)', 'Firing alerts')], 'short', 'Alerts (linear)', x=12, y=60)

panel('Encoded image size • Summary mean', 'AI prompt: weighted mean bytes per attempted image = sum(rate(caption_image_upload_bytes_sum[5m])) / sum(rate(caption_image_upload_bytes_count[5m])), separately by mode. Includes corrupt image entries; excludes ZIP compression overhead.',
      [(f'sum(rate(caption_image_upload_bytes_sum{{mode="{mode}"}}[5m])) / sum(rate(caption_image_upload_bytes_count{{mode="{mode}"}}[5m]))', label)
       for mode,label in [('single','Single'),('bulk','Bulk')]], 'bytes', 'Encoded bytes/image (linear)', y=68)
panel('Generated caption length • Summary mean', 'AI prompt: weighted mean Unicode characters per successful caption = sum(rate(caption_length_characters_sum[5m])) / sum(rate(caption_length_characters_count[5m])), separately by mode. Includes spaces, excludes failed captions; length is not a quality score.',
      [(f'sum(rate(caption_length_characters_sum{{mode="{mode}"}}[5m])) / sum(rate(caption_length_characters_count{{mode="{mode}"}}[5m]))', label)
       for mode,label in [('single','Single'),('bulk','Bulk')]], 'suffix: characters', 'Characters/caption (linear)', x=12, y=68)

# Visible row subtitles/stories are rendered Text panels, not hidden tooltips.
# Grafana supplies native time ticks; a supported Text panel explicitly names the
# shared x-axis instead of inventing an unsupported x-axis configuration field.
# AI prompt: Add concise visible stories above every pair of plots and label Time
# as the shared x-axis, with browser-local timezone and linear y-axis units.
stories = [
    ('Workload and throughput', 'Left: successful images per second by mode. Right: accepted jobs in progress, including CPU wait. Bulk activity should align with throughput and resource changes.'),
    ('Inference time versus user-visible image time', 'Left: mean and estimated p95 for model.generate only. Right: per-image mean including decode and queue delay. Missing observations produce gaps, not zero-second inference.'),
    ('Job duration and processing outcomes', 'Left: Summary mean for an entire job; a ZIP is one job. Right: image success/error totals since backend start. Counters reset on restart.'),
    ('Correlate bulk uploads with Ubuntu VM resources', 'Left: VM CPU averaged over cores. Right: VM memory using MemAvailable. Orange bars on each right axis show bulk jobs. These measure Ubuntu, not the Mac host.'),
    ('Storage and model memory', 'Left: Ubuntu root disk used percent. Right: backend RSS versus model weights; RSS includes runtime overhead. Streamlit memory is included only in VM-wide measurements.'),
    ('Outcomes and client sessions', 'Left: successful, partial and failed completed jobs. Right: image totals by short actual session ID. Use the table labels to distinguish sessions; prefixes can collide and are not user counts.'),
    ('Process load and rejected uploads', 'Left: 100% CPU means one full core, so this can exceed 100%. Right: rejected request count; corrupt images inside accepted ZIPs appear in image errors instead.'),
    ('Incoming bytes and alerts', 'Left: accepted uploaded bytes per second, including compressed ZIP size. Right: firing alert count. Check the local receiver for actual alert delivery.'),
    ('Two additional Summaries', 'Left: encoded bytes per attempted image, including corrupt entries. Right: Unicode characters per successful caption, including spaces. Caption length is not an accuracy metric.'),
]

metric_panels = list(PANELS)
headers = []
next_id = max(p['id'] for p in PANELS) + 1

def visible_text(title, content, y):
    global next_id
    headers.append({'id': next_id, 'type': 'text', 'title': title,
                    'gridPos': {'x': 0, 'y': y, 'w': 24, 'h': 4},
                    'options': {'mode': 'markdown', 'content': content}})
    next_id += 1

visible_text('Caption Lab — live CPU captioning and observability',
             '**Refresh: 5 seconds.** Read from health to workload, latency and Ubuntu VM resources. '
             'Exporter UP means metrics are reachable; model READY means weights are loaded. '
             'The plots below use **Time (browser-local timezone) on the x-axis** and explicitly labeled **linear y-axes**. '
             'All values come from actual application/exporter observations.', 0)
for p in metric_panels[:4]:
    p['gridPos']['y'] = 4
for index, (heading, story) in enumerate(stories):
    base_y = 8 + index * 12
    visible_text(heading, story + '\n\n**X-axis: Time (browser-local timezone). Y-axes: linear; units on each plot.**', base_y)
    for p in metric_panels[4 + index * 2:6 + index * 2]:
        p['gridPos']['y'] = base_y + 4
PANELS = sorted(metric_panels + headers, key=lambda p: (p['gridPos']['y'], p['gridPos']['x']))

dashboard = {'uid': 'caption-lab', 'title': 'Caption Lab | CPU image captioning',
             'tags': ['DA3408', 'A4', 'CPU'], 'timezone': 'browser', 'schemaVersion': 39,
             'version': 2, 'refresh': '5s', 'time': {'from': 'now-15m', 'to': 'now'},
             'editable': True, 'panels': PANELS, 'annotations': {'list': []},
             'templating': {'list': []}}
Path(__file__).resolve().parents[1].joinpath('grafana', 'dashboard.json').write_text(json.dumps(dashboard, indent=2))
print(f'Generated {len(PANELS)} panels; refresh 5s.')
