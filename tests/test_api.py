"""Model stub is for unit tests only, never used by the delivered application."""
import unittest
from unittest.mock import MagicMock, patch
from tests.test_inputs import archive_bytes, image_bytes

try:
    from fastapi.testclient import TestClient
    from caption_app import backend
    from caption_app import metrics
except ImportError:
    backend = None


class StubEngine:
    def caption(self, image, mode):
        return 'unit-test stub caption', 0.01


@unittest.skipIf(backend is None, 'Install project dependencies to run API unit tests')
class APITests(unittest.TestCase):
    def setUp(self):
        self.p1 = patch.object(backend, 'CaptionEngine', StubEngine)
        self.p2 = patch.object(backend, 'start_http_server', return_value=(MagicMock(), MagicMock()))
        self.p1.start()
        self.p2.start()
        self.client = TestClient(backend.app).__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.p2.stop()
        self.p1.stop()

    def test_single_success_and_metrics(self):
        session = 'abc123def4567890'
        label = 'abc123def456'
        before_bytes = metrics.IMAGE_BYTES.labels('single', label)._sum.get()
        before_length = metrics.CAPTION_LENGTH.labels('single', label)._sum.get()
        before_jobs = metrics.JOB_TIME.labels('single', label)._count.get()
        response = self.client.post('/caption', data={'mode': 'single', 'session_id': session},
            files={'file': ('test.png', image_bytes(), 'image/png')})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['client_session'], label)
        self.assertEqual(metrics.IMAGE_BYTES.labels('single', label)._sum.get() - before_bytes, len(image_bytes()))
        self.assertEqual(metrics.CAPTION_LENGTH.labels('single', label)._sum.get() - before_length, len('unit-test stub caption'))
        self.assertEqual(metrics.JOB_TIME.labels('single', label)._count.get() - before_jobs, 1)
        self.assertEqual(metrics.ACTIVE.labels('single')._value.get(), 0)

    def test_bulk_partial_failure_keeps_valid_result(self):
        before_images = metrics.IMAGE_BYTES.labels('bulk', 'anonymous')._count.get()
        before_captions = metrics.CAPTION_LENGTH.labels('bulk', 'anonymous')._count.get()
        data = archive_bytes([('good.png', image_bytes()), ('bad.png', b'broken')])
        response = self.client.post('/caption', data={'mode': 'bulk'},
            files={'file': ('test.zip', data, 'application/zip')})
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result['status'], 'partial')
        self.assertEqual([r['status'] for r in result['results']], ['success', 'error'])
        self.assertEqual(metrics.ACTIVE.labels('bulk')._value.get(), 0)
        self.assertEqual(metrics.IMAGE_BYTES.labels('bulk', 'anonymous')._count.get() - before_images, 2)
        self.assertEqual(metrics.CAPTION_LENGTH.labels('bulk', 'anonymous')._count.get() - before_captions, 1)

    def test_bad_zip_returns_400(self):
        response = self.client.post('/caption', data={'mode': 'bulk'},
            files={'file': ('test.zip', b'bad zip', 'application/zip')})
        self.assertEqual(response.status_code, 400)

    def test_invalid_mode_returns_422(self):
        response = self.client.post('/caption', data={'mode': 'other'},
            files={'file': ('test.png', image_bytes(), 'image/png')})
        self.assertEqual(response.status_code, 422)

    def test_session_labels_are_readable_and_sanitized(self):
        self.assertEqual(metrics.client_session('abc123def4567890'), 'abc123def456')
        self.assertEqual(metrics.client_session('another-session'), 'another-sess')
        self.assertEqual(metrics.client_session('\n!!!'), 'anonymous')
        self.assertEqual(metrics.client_session('demo_user-01'), 'demo_user-01')
