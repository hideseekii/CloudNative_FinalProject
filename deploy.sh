#!/bin/bash
set -e

echo "🚀 CloudNative Final - 模組化部署（含 Redis）"

# 檢查 k8s 資料夾是否存在
if [ ! -d "k8s" ]; then
    echo "❌ k8s 資料夾不存在，請先創建 k8s 配置檔案"
    exit 1
fi

# 詢問是否要清除資料庫資料
echo ""
echo "⚠️  部署選項："

echo "1. 完全重新部署（清除所有資料，包括資料庫和 Redis）"
echo "2. 保留資料庫重新部署（僅重新部署應用）"
echo "3. 僅更新應用程式（不重啟資料庫和 Redis）"

echo ""
read -p "請選擇部署模式 [1-3]: " DEPLOY_MODE

case $DEPLOY_MODE in
    1)
        echo "🗑️  選擇：完全重新部署"
        CLEAN_ALL=true
        REDEPLOY_DB=true

        REDEPLOY_REDIS=true

        REDEPLOY_APP=true
        ;;
    2)
        echo "🔄 選擇：保留資料庫重新部署"
        CLEAN_ALL=false
        REDEPLOY_DB=false

        REDEPLOY_REDIS=false

        REDEPLOY_APP=true
        ;;
    3)
        echo "🚀 選擇：僅更新應用程式"
        CLEAN_ALL=false
        REDEPLOY_DB=false

        REDEPLOY_REDIS=false

        REDEPLOY_APP=true
        ;;
    *)
        echo "❌ 無效選擇，使用預設模式：保留資料庫重新部署"
        CLEAN_ALL=false
        REDEPLOY_DB=false

        REDEPLOY_REDIS=false

        REDEPLOY_APP=true
        ;;
esac

# 1. 清理資源（根據選擇的模式）
if [ "$CLEAN_ALL" = true ]; then
    echo "🧹 完全清理舊資源..."
    kubectl delete namespace cloudnative-final --ignore-not-found=true || true
    docker-compose down || true
    docker rmi cloudnative-final:latest || true
else

    echo "🧹 清理應用程式資源（保留資料庫和 PVC）..."

    echo "🧹 清理應用程式資源（保留資料庫和 Redis）..."

    # 只刪除應用程式相關資源
    kubectl delete deployment django -n cloudnative-final --ignore-not-found=true || true
    kubectl delete hpa django-hpa -n cloudnative-final --ignore-not-found=true || true
    
    if [ "$REDEPLOY_DB" = true ]; then
        echo "🧹 重新部署資料庫..."
        kubectl delete deployment postgres -n cloudnative-final --ignore-not-found=true || true
        kubectl delete service postgres -n cloudnative-final --ignore-not-found=true || true
    fi
    

    if [ "$REDEPLOY_REDIS" = true ]; then
        echo "🧹 重新部署 Redis..."
        kubectl delete deployment redis -n cloudnative-final --ignore-not-found=true || true
        kubectl delete service redis -n cloudnative-final --ignore-not-found=true || true
    fi
    

    docker rmi cloudnative-final:latest || true
fi

# 2. 建置新的 Docker 映像
echo "🔨 建置 Docker 映像..."
docker build -t cloudnative-final:latest .

# 3. 載入映像到 k3d
echo "📦 載入映像到 k3d..."
k3d image import cloudnative-final:latest -c mycluster

# 4. 確保命名空間存在
echo "📋 確保命名空間存在..."
kubectl apply -f k8s/namespace.yaml

# 5. 部署配置和機密
echo "🔐 部署配置和機密..."
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# 6. 創建持久化存儲（如果不存在）
echo "💾 確保持久化存儲存在..."
kubectl apply -f k8s/pvc.yaml


# 7. 部署 PostgreSQL（如果需要）
if [ "$REDEPLOY_DB" = true ] || [ "$CLEAN_ALL" = true ]; then
    echo "🐘 部署 PostgreSQL..."
    kubectl apply -f k8s/postgres-deployment.yaml
    kubectl apply -f k8s/postgres-service.yaml
    
    # 等待 PostgreSQL 啟動
    echo "⏳ 等待 PostgreSQL 啟動..."
    kubectl wait --for=condition=ready pod -l app=postgres -n cloudnative-final --timeout=120s
else
    echo "🐘 PostgreSQL 已存在，跳過部署"
    # 檢查 PostgreSQL 是否正在運行
    if kubectl get pod -l app=postgres -n cloudnative-final --no-headers 2>/dev/null | grep -q Running; then
        echo "✅ PostgreSQL 正在運行"
    else
        echo "⚠️  PostgreSQL 似乎沒有運行，嘗試重新啟動..."
        kubectl apply -f k8s/postgres-deployment.yaml
        kubectl apply -f k8s/postgres-service.yaml
        kubectl wait --for=condition=ready pod -l app=postgres -n cloudnative-final --timeout=120s
    fi
fi

# 8. 部署 Django 應用

# 7. 部署 Redis（如果需要）
if [ "$REDEPLOY_REDIS" = true ] || [ "$CLEAN_ALL" = true ]; then
    echo "🔴 部署 Redis..."
    kubectl apply -f k8s/redis-deployment.yaml
    
    # 等待 Redis 啟動
    echo "⏳ 等待 Redis 啟動..."
    kubectl wait --for=condition=ready pod -l app=redis -n cloudnative-final --timeout=120s
else
    echo "🔴 Redis 已存在，跳過部署"
    # 檢查 Redis 是否正在運行
    if kubectl get pod -l app=redis -n cloudnative-final --no-headers 2>/dev/null | grep -q Running; then
        echo "✅ Redis 正在運行"
    else
        echo "⚠️  Redis 似乎沒有運行，嘗試重新啟動..."
        kubectl apply -f k8s/redis-deployment.yaml
        kubectl wait --for=condition=ready pod -l app=redis -n cloudnative-final --timeout=120s
    fi
fi

# 8. 部署 PostgreSQL（如果需要）
if [ "$REDEPLOY_DB" = true ] || [ "$CLEAN_ALL" = true ]; then
    echo "🐘 部署 PostgreSQL..."
    kubectl apply -f k8s/postgres-deployment.yaml
    kubectl apply -f k8s/postgres-service.yaml
    
    # 等待 PostgreSQL 啟動
    echo "⏳ 等待 PostgreSQL 啟動..."
    kubectl wait --for=condition=ready pod -l app=postgres -n cloudnative-final --timeout=120s
else
    echo "🐘 PostgreSQL 已存在，跳過部署"
    # 檢查 PostgreSQL 是否正在運行
    if kubectl get pod -l app=postgres -n cloudnative-final --no-headers 2>/dev/null | grep -q Running; then
        echo "✅ PostgreSQL 正在運行"
    else
        echo "⚠️  PostgreSQL 似乎沒有運行，嘗試重新啟動..."
        kubectl apply -f k8s/postgres-deployment.yaml
        kubectl apply -f k8s/postgres-service.yaml
        kubectl wait --for=condition=ready pod -l app=postgres -n cloudnative-final --timeout=120s
    fi
fi

# 9. 部署 Django 應用

if [ "$REDEPLOY_APP" = true ]; then
    echo "🐍 部署 Django 應用..."
    kubectl apply -f k8s/django-deployment.yaml
    kubectl apply -f k8s/django-service.yaml
    
    # 等待 Django 啟動 - 使用更穩定的方法
    echo "⏳ 等待 Django 啟動..."
    
    # 先等待 deployment 準備就緒
    kubectl rollout status deployment/django -n cloudnative-final --timeout=120s
    
    # 再檢查 Pod 狀態
    echo "🔍 檢查 Pod 狀態..."
    kubectl get pods -l app=django -n cloudnative-final
    
    # 等待至少一個 Pod 準備就緒
    for i in {1..24}; do
        READY_PODS=$(kubectl get pods -l app=django -n cloudnative-final --no-headers 2>/dev/null | grep -c "Running" || echo "0")
        if [ "$READY_PODS" -gt 0 ]; then
            echo "✅ Django Pod(s) 已準備就緒 ($READY_PODS 個)"
            break
        fi
        echo "⏳ 等待 Django Pod 啟動... ($i/24)"
        sleep 5
    done
    
    if [ "$READY_PODS" -eq 0 ]; then
        echo "⚠️  Django Pod 啟動超時，但繼續執行..."
        kubectl describe pods -l app=django -n cloudnative-final
    fi
else
    echo "🐍 Django 應用保持不變"
fi


# 9. 執行資料庫遷移（總是執行，確保資料庫結構是最新的）

# 10. 執行資料庫遷移（總是執行，確保資料庫結構是最新的）

echo "🔄 執行資料庫遷移..."

# 等待至少一個 Django Pod 可用
echo "⏳ 等待 Django Pod 準備執行遷移..."
for i in {1..12}; do
    # 獲取一個運行中的 Django Pod
    DJANGO_POD=$(kubectl get pods -l app=django -n cloudnative-final --no-headers 2>/dev/null | grep "Running" | head -1 | awk '{print $1}')
    
    if [ -n "$DJANGO_POD" ]; then
        echo "✅ 使用 Pod: $DJANGO_POD 執行遷移"
        
        # 執行遷移

        if kubectl exec "$DJANGO_POD" -n cloudnative-final -- python manage.py makemigrations && \
                kubectl exec "$DJANGO_POD" -n cloudnative-final -- python manage.py migrate; then

        if kubectl exec "$DJANGO_POD" -n cloudnative-final -- python manage.py migrate; then

            echo "✅ 資料庫遷移完成"
            break
        else
            echo "❌ 遷移失敗，重試中..."
        fi
    else
        echo "⏳ 等待 Django Pod 可用... ($i/12)"
        sleep 5
    fi
done

# 如果沒有找到可用的 Pod，使用 deployment 方式
if [ -z "$DJANGO_POD" ]; then
    echo "⚠️  嘗試使用 deployment 執行遷移..."
    kubectl exec deployment/django -n cloudnative-final -- python manage.py migrate || {
        echo "❌ 遷移失敗，請手動執行:"
        echo "kubectl exec -it deployment/django -n cloudnative-final -- python manage.py migrate"
    }
fi

# 10. 提示創建超級用戶

# 11. 提示創建超級用戶

if [ "$CLEAN_ALL" = true ]; then
    echo "👤 資料庫已重置，需要重新創建管理員用戶"
    echo "執行以下命令創建管理員：" 
    echo "kubectl exec -it deployment/django -n cloudnative-final -- python manage.py createsuperuser"
else
    echo "👤 現有管理員用戶應該仍然存在"
    echo "如需創建新管理員，執行："
    echo "kubectl exec -it deployment/django -n cloudnative-final -- python manage.py createsuperuser"
fi

# 12. 創建 HPA（需要確保 metrics-server 已安裝）
echo "📊 檢查 metrics-server..."
if kubectl get deployment metrics-server -n kube-system >/dev/null 2>&1; then
    echo "✅ Metrics-server 已安裝，創建 HPA..."
    kubectl apply -f k8s/hpa.yaml
else
    echo "⚠️  Metrics-server 未安裝，跳過 HPA 創建"
    echo "如需安裝 metrics-server，執行："
    echo "kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml"
fi

echo ""
echo "✅ 部署完成！"
kubectl get all -n cloudnative-final

echo ""
echo "📊 資源狀態："
echo "PVC 狀態："
kubectl get pvc -n cloudnative-final
echo ""
echo "Pod 狀態："
kubectl get pods -n cloudnative-final

echo ""


echo "🔴 Redis 連線測試："
echo "kubectl exec -it deployment/redis -n cloudnative-final -- redis-cli ping"

echo ""

echo "🌐 測試應用：" 
echo "kubectl port-forward svc/django 8080:80 -n cloudnative-final"
echo "然後訪問 http://localhost:8080/health/"
echo ""
echo "🔍 查看日誌："
echo "kubectl logs -f deployment/django -n cloudnative-final"
echo "kubectl logs -f deployment/redis -n cloudnative-final"
echo ""
echo "🗑️  完全清理資源："
echo "kubectl delete namespace cloudnative-final"