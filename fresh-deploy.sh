#!/bin/bash
set -e

echo "🚀 CloudNative Final - 全新部署"

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

# 4. 創建 Kubernetes 資源
echo "📋 創建 Kubernetes 資源..."

# 創建命名空間
kubectl create namespace cloudnative-final

# 部署 PostgreSQL
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: cloudnative-final
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: cloudnative_final
        - name: POSTGRES_USER
          value: postgres
        - name: POSTGRES_PASSWORD
          value: password
        ports:
        - containerPort: 5432
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: cloudnative-final
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
EOF

# 等待 PostgreSQL 啟動
echo "⏳ 等待 PostgreSQL 啟動..."
sleep 10
kubectl wait --for=condition=ready pod -l app=postgres -n cloudnative-final --timeout=120s

# 部署 Django
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: django
  namespace: cloudnative-final
spec:
  replicas: 2
  selector:
    matchLabels:
      app: django
  template:
    metadata:
      labels:
        app: django
    spec:
      containers:
      - name: django
        image: cloudnative-final:latest
        imagePullPolicy: Never
        env:
        - name: DEBUG
          value: "true"
        - name: SECRET_KEY
          value: "dev-secret-key-12345"
        - name: ALLOWED_HOSTS
          value: "*"
        - name: DB_NAME
          value: cloudnative_final
        - name: DB_USER
          value: postgres
        - name: DB_PASSWORD
          value: password
        - name: DB_HOST
          value: postgres
        - name: DB_PORT
          value: "5432"
        ports:
        - containerPort: 8000
        readinessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: django
  namespace: cloudnative-final
spec:
  selector:
    app: django
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
EOF

# 等待 Django 啟動
echo "⏳ 等待 Django 啟動..."
sleep 10
kubectl wait --for=condition=ready pod -l app=django -n cloudnative-final --timeout=120s

# 執行資料庫遷移
echo "🔄 執行資料庫遷移..."
kubectl exec deployment/django -n cloudnative-final -- python manage.py migrate

# 創建 HPA
kubectl apply -f - <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: django-hpa
  namespace: cloudnative-final
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: django
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
EOF

echo "✅ 部署完成！"
kubectl get all -n cloudnative-final

echo ""
echo "🌐 測試應用："
echo "kubectl port-forward svc/django 8080:80 -n cloudnative-final"
echo "然後訪問 http://localhost:8080/health/"