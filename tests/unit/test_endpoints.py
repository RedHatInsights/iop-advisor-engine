import os
import tempfile
import unittest
from fastapi.testclient import TestClient
from unittest.mock import patch
from uuid import UUID
from advisor_engine.endpoints import app


class TestEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_handle_module_update_router(self):
        response = self.client.get("/api/module-update-router/v1/channel")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"url": "/release"})

    def test_handle_system_get_legacy(self):
        response = self.client.get("/r/insights/v1/systems/some_path")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"unregistered_at": None})

    def test_handle_system_get(self):
        test_uuid = UUID("12345678-1234-5678-1234-567812345678")
        response = self.client.get(f"/api/inventory/v1/hosts?insights_id={test_uuid}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"total": 1, "results": [{"id": str(test_uuid)}]})

    def test_handle_egg(self):
        response = self.client.get("/r/insights/v1/static/release/insights-core.egg")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'application/octet-stream')

    def test_handle_egg_asc(self):
        response = self.client.get("/r/insights/v1/static/release/insights-core.egg.asc")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'text/plain; charset=utf-8')

    @patch('advisor_engine.endpoints.process_background')
    def test_handle_insights_archive(self, mock_process_background):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"Test content")
            temp_file_path = temp_file.name

        with open(temp_file_path, 'rb') as f:
            response = self.client.post(
                "/api/ingress/v1/upload/test_path",
                files={"file": ("test_archive.tar.gz", f, "application/gzip")}
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'message': 'File uploaded successfully'})

        os.unlink(temp_file_path)
        os.unlink('uploads/test_archive.tar.gz')