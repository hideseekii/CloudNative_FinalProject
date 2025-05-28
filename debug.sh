#!/bin/bash

echo "🔍 CloudNative Final - 故障排除"

# 檢查 namespace 中的所有資源
echo "📋 查看所有資源狀態..."
kubectl get all -n cloudnative-final

echo ""
echo "🐍 Django Pod 詳細狀態..."
kubectl get pods -l app=django -n cloudnative-final -o wide

echo ""
echo "📜 Django Pod 日誌 (最近 50 行)..."
kubectl logs --tail=50 deployment/django -n cloudnative-final

echo ""
echo "🔍 Django Pod 詳細描述..."
kubectl describe pods -l app=django -n cloudnative-final

echo ""
echo "🐘 PostgreSQL 狀態..."
kubectl get pods -l app=postgres -n cloudnative-final

echo ""
echo "📊 Service 狀態..."
kubectl get svc -n cloudnative-final

echo ""
echo "💾 PVC 狀態..."
kubectl get pvc -n cloudnative-final

echo ""
echo "⚙️  ConfigMap 內容..."
kubectl get configmap app-config -n cloudnative-final -o yaml

echo ""
echo "🔐 Secret 狀態 (不顯示內容)..."
kubectl get secret app-secrets -n cloudnative-final

echo ""
echo "🩺 測試資料庫連線..."
if kubectl get pod -l app=postgres -n cloudnative-final >/dev/null 2>&1; then
    echo "嘗試從 Django Pod 連接到 PostgreSQL..."
    kubectl exec deployment/django -n cloudnative-final -- python -c "
import os
import psycopg2
try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'postgres'),
        port=os.getenv('DB_PORT', '5432'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME', 'cloudnative_final')
    )
    print('✅ 資料庫連線成功')
    conn.close()
except Exception as e:
    print(f'❌ 資料庫連線失敗: {e}')
" 2>/dev/null || echo "❌ 無法執行資料庫連線測試"
else
    echo "❌ PostgreSQL Pod 不存在"
fi

echo ""
echo "🌐 測試 Django 健康檢查..."
kubectl exec deployment/django -n cloudnative-final -- curl -f http://localhost:8000/health/ 2>/dev/null || echo "❌ 健康檢查失敗"

echo ""
echo "📡 Port Forward 測試指令："
echo "kubectl port-forward svc/django 8080:80 -n cloudnative-final"
echo "然後在另一個終端執行: curl http://localhost:8080/health/"