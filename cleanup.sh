#!/bin/bash
set -e

echo "🗑️  CloudNative Final - 清理資源"

# 刪除 Kubernetes 資源
echo "🧹 刪除 Kubernetes 資源..."
kubectl delete namespace cloudnative-final --ignore-not-found=true

# 清理 Docker 映像
echo "🐳 清理 Docker 映像..."
docker rmi cloudnative-final:latest || true

# 停止 docker-compose（如果有使用）
echo "📦 停止 docker-compose..."
docker-compose down || true

echo "✅ 清理完成！"