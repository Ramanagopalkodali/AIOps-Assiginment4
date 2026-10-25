"""User interface. All inference runs in backend.py, locally in the same Ubuntu VM."""
import csv
import io
import os
import uuid
import requests
import streamlit as st

API = os.getenv('CAPTION_API', 'http://127.0.0.1:8000')
st.set_page_config(page_title='Caption Lab', page_icon='📷', layout='wide')
st.title('Caption Lab')
st.caption('Describe one image or a collection. Captions are generated locally on the CPU and may contain mistakes.')
if 'session_id' not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex

with st.sidebar:
    st.header('Service status')
    try:
        response = requests.get(API + '/healthz', timeout=3)
        ready = response.ok
    except requests.RequestException:
        ready = False
    st.success('Captioning service ready') if ready else st.error('Start the captioning service in Terminal 1.')
    st.markdown('[Monitoring dashboard](http://127.0.0.1:3000/d/caption-lab)')
    st.write('Single: up to 20 MiB. ZIP: up to 100 MiB, 60 images and 200 MiB expanded.')
    st.write('Supported images: JPG, PNG and WebP. Bulk jobs run sequentially to keep memory use predictable.')

choice = st.radio('Choose upload mode', ['Single image', 'Bulk ZIP'], horizontal=True)
mode = 'single' if choice == 'Single image' else 'bulk'
upload = st.file_uploader('Choose an image' if mode == 'single' else 'Choose a ZIP of images',
                          type=['jpg', 'jpeg', 'png', 'webp'] if mode == 'single' else ['zip'], key=mode)
if upload and mode == 'single':
    try:
        st.image(upload.getvalue(), width=320)
    except Exception:
        st.warning('Preview unavailable. The captioning service will validate the uploaded image.')

if st.button('Generate captions', type='primary', disabled=not (ready and upload)):
    with st.spinner('Generating captions on the CPU. Keep this page open; a bulk job can take several minutes.'):
        try:
            response = requests.post(API + '/caption',
                data={'mode': mode, 'session_id': st.session_state.session_id},
                files={'file': (upload.name, upload.getvalue(), upload.type)}, timeout=(5, 3600))
            if not response.ok:
                try:
                    detail = response.json().get('detail', response.text)
                except ValueError:
                    detail = response.text
                st.error(f'Upload could not be processed: {detail}')
            else:
                st.session_state.last_result = response.json()
        except requests.RequestException as exc:
            st.error(f'Connection interrupted: {exc}. A timed-out job can continue in the backend; check the dashboard before retrying.')

if 'last_result' in st.session_state:
    result = st.session_state.last_result
    good = sum(r['status'] == 'success' for r in result['results'])
    st.subheader('Most recent result')
    st.write(f"{good}/{len(result['results'])} images captioned in {result['elapsed_seconds']:.1f} seconds.")
    st.dataframe(result['results'], hide_index=True, use_container_width=True)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['file', 'caption', 'status', 'inference_seconds', 'error'])
    writer.writeheader()
    writer.writerows(result['results'])
    st.download_button('Download captions as CSV', output.getvalue(), 'captions.csv', 'text/csv')
