from django.test import TestCase, Client
from unittest.mock import patch
from django.db.utils import OperationalError

class HealthCheckTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_check_success(self):
        """測試當資料庫正常連線時，health endpoint 回傳 200 且內容正確"""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'status': 'healthy',
            'database': 'connected',
            'message': 'All systems operational'
        })

    @patch('CloudNative_final.views.connection')
    def test_health_check_failure(self, mock_connection):
        """模擬資料庫連線失敗，檢查是否正確回傳 503 及錯誤資訊"""
        mock_connection.cursor.side_effect = OperationalError("Database is down")

        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['status'], 'unhealthy')
        self.assertEqual(response.json()['database'], 'disconnected')
        self.assertIn('error', response.json())
