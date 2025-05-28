#!/bin/bash
set -e

echo "🚀 CloudNative Final - 模組化部署"

# 檢查 k8s 資料夾是否存在
if [ ! -d "k8s" ]; then
    echo "❌ k8s 資料夾不存在，請先創建 k8s 配置檔案"
    exit 1
fi

# 1. 清理舊資源
echo "🧹 清理舊資源..."
kubectl delete namespace cloudnative-final --ignore-not-found=true || true
docker-compose down || true
docker rmi cloudnative-final:latest || true

# 2. 建置新的 Docker 映像
echo "🔨 建置 Docker 映像..."
docker build -t cloudnative-final:latest .

# 3. 載入映像到 k3d
echo "📦 載入映像到 k3d..."
k3d image import cloudnative-final:latest -c mycluster

# 4. 創建命名空間
echo "📋 創建命名空間..."
kubectl apply -f k8s/namespace.yaml

# 5. 部署配置和機密
echo "🔐 部署配置和機密..."
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# 6. 創建持久化存儲
echo "💾 創建持久化存儲..."
kubectl apply -f k8s/pvc.yaml

# 7. 部署 PostgreSQL
echo "🐘 部署 PostgreSQL..."
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml

# 等待 PostgreSQL 啟動
echo "⏳ 等待 PostgreSQL 啟動..."
kubectl wait --for=condition=ready pod -l app=postgres -n cloudnative-final --timeout=120s

# 8. 部署 Django 應用
echo "🐍 部署 Django 應用..."
kubectl apply -f k8s/django-deployment.yaml
kubectl apply -f k8s/django-service.yaml

# 等待 Django 啟動
echo "⏳ 等待 Django 啟動..."
kubectl wait --for=condition=ready pod -l app=django -n cloudnative-final --timeout=120s

# 9. 執行資料庫遷移
echo "🔄 執行資料庫遷移..."
kubectl exec deployment/django -n cloudnative-final -- python manage.py migrate

# 10. 可選：創建超級用戶
echo "👤 創建管理員用戶（可選）"
echo "執行以下命令創建管理員："
echo "kubectl exec -it deployment/django -n cloudnative-final -- python manage.py createsuperuser"

# 11. 創建 HPA（需要確保 metrics-server 已安裝）
echo "📊 檢查 metrics-server..."
if kubectl get deployment metrics-server -n kube-system >/dev/null 2>&1; then
    echo "✅ Metrics-server 已安裝，創建 HPA..."
    kubectl apply -f k8s/hpa.yaml
else
    echo "⚠️  Metrics-server 未安裝，跳過 HPA 創建"
    echo "如需安裝 metrics-server，執行："
    echo "kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml"
fi

echo "✅ 部署完成！"
kubectl get all -n cloudnative-final

echo ""
echo "🌐 測試應用："
echo "kubectl port-forward svc/django 8080:80 -n cloudnative-final"
echo "然後訪問 http://localhost:8080/health/"
echo ""
echo "🔍 查看日誌："
echo "kubectl logs -f deployment/django -n cloudnative-final"
echo ""
echo "🗑️  清理資源："
echo "kubectl delete namespace cloudnative-final"