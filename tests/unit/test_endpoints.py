import glob
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

    def test_handle_system_exists(self):
        test_uuid = UUID("12345678-1234-5678-1234-567812345678")
        response = self.client.get(f"/api/inventory/v1/host_exists?insights_id={test_uuid}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"id": str(test_uuid)})

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
        files = glob.glob("uploads/*.gz")
        for file in files:
            os.remove(file)

    def test_handle_test_insights_archive(self):
        response = self.client.post(
            "/api/ingress/v1/upload/",
            data={'test': 'test'}
        )
        self.assertEqual(response.status_code, 200)
