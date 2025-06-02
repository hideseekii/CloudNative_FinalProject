# 使用官方 Python 3.11 slim 版本作為基礎映像
FROM python:3.11-slim

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=CloudNative_final.settings

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        netcat-traditional \
        gettext \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案檔案
COPY . .

# 建立靜態檔案目錄並設定權限
RUN mkdir -p /app/staticfiles /app/mediafiles \
    && chmod -R 755 /app/staticfiles /app/mediafiles

# 收集靜態檔案
RUN python manage.py collectstatic --noinput --settings=CloudNative_final.settings

# 建立非 root 用戶來運行應用
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/', timeout=10)" || exit 1

# 啟動腳本 - 等待資料庫準備好再執行 migrate
CMD ["sh", "-c", "while ! nc -z postgres 5432; do sleep 1; done; python manage.py migrate && gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 60 CloudNative_final.wsgi:application"]