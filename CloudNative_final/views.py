# CloudNative_final/views.py
from django.http import JsonResponse
from django.db import connection
import logging

logger = logging.getLogger(__name__)

def health_check(request):
    """
    系統健康檢查端點
    檢查資料庫連線狀態
    """
    try:
        # 檢查 PostgreSQL 資料庫連線
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'message': 'All systems operational'
        })
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JsonResponse({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }, status=503)