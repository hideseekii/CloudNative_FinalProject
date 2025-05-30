# 台積電內部餐廳系統
## 國立陽明交通大學 x 台積電雲原生課程期末專案

本專案為國立陽明交通大學與台灣積體電路製造股份有限公司（台積電）合作開設的雲原生課程期末作業。系統設計為台積電內部員工專用的餐廳點餐平台，提供便利的用餐服務管理。

## 專案概述

台積電內部餐廳系統是基於 Django 的雲原生後端服務，讓員工能夠瀏覽菜單、下訂單並管理用餐體驗。本系統展現了現代雲原生架構原則，包含容器化、Kubernetes 部署和微服務設計。

## 核心功能

* **員工身分驗證**：台積電內部使用者安全登入系統
* **菜單管理**：瀏覽餐廳菜品，包含圖片、描述和價格
* **訂單處理**：下訂單並即時追蹤訂單狀態
* **評論系統**：對餐點評分和評論，協助其他員工選擇餐點
* **管理後台**：餐廳人員可管理菜單、訂單和客戶回饋
* **雲原生架構**：完全容器化並支援 Kubernetes 部署

## 系統架構

系統遵循雲原生原則：
- **容器化**：使用 Docker 容器確保一致性部署
- **編排管理**：Kubernetes (K3d) 進行容器管理
- **資料庫**：PostgreSQL 提供可靠的資料持久化
- **API 優先設計**：RESTful API 支援前後端通訊
- **可擴展性**：設計支援台積電內部使用者規模

## 快速部署

### 系統需求

部署前請確認已安裝以下工具：

- **Docker**：容器執行環境
- **K3d**：輕量級 Kubernetes 發行版
- **kubectl**：Kubernetes 命令列工具

### 一鍵部署

系統提供自動化部署腳本，快速建置環境：

```bash
# 克隆專案
git clone https://github.com/AlHIO/Cloud-Native-NYCU-FinalProject.git
cd Cloud-Native-NYCU-FinalProject

# 執行部署腳本
./deploy.sh
```

### 存取應用程式

部署完成後，透過以下方式存取餐廳系統：

```bash
# 設定端口轉發以存取應用程式
kubectl port-forward svc/django 8080:80 -n cloudnative-final

# 在瀏覽器開啟 http://localhost:8080
```

## 專案結構

```
Cloud-Native-NYCU-FinalProject/
├── CloudNative_final/    # Django 專案設定
├── menu/                 # 菜單管理應用程式
├── orders/               # 訂單處理應用程式  
├── reviews/              # 評論評分系統
├── users/                # 員工身分驗證
├── static/               # 靜態資源 (CSS, JS, 圖片)
├── templates/            # HTML 樣板
├── k8s/                  # Kubernetes 部署檔案
├── deploy.sh             # 自動化部署腳本
├── Dockerfile            # 容器設定檔
├── docker-compose.yml    # 本地開發環境設定
├── requirements.txt      # Python 相依套件
└── README.md
```

## 開發環境設定

本地開發環境（不使用 Kubernetes）：

### 1. 環境設定
```bash
# 建立虛擬環境
python -m venv .venv

# 啟動虛擬環境
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows CMD:
.venv\Scripts\activate.bat  
# Linux/macOS:
source .venv/bin/activate
```

### 2. 安裝相依套件
```bash
pip install -r requirements.txt
```

### 3. 資料庫設定
```bash
# 執行資料庫遷移
python manage.py migrate

# 建立管理員帳號
python manage.py createsuperuser
```

### 4. 啟動開發伺服器
```bash
python manage.py runserver
```

在瀏覽器開啟 `http://127.0.0.1:8000/` 存取應用程式

## 測試

執行測試套件確保系統可靠性：

```bash
python manage.py test
```

## 雲原生特色

本專案展現關鍵雲原生概念：

- **容器化**：應用程式打包於 Docker 容器中
- **編排管理**：Kubernetes 部署與服務發現
- **可擴展性**：水平擴展機制
- **韌性**：健康檢查和自我修復機制
- **設定管理**：基於環境的設定管理
- **監控**：內建日誌記錄和指標收集

## 課程背景

本專案滿足國立陽明交通大學與台積電雲原生課程要求，ImplementVoiceNote了以下概念：
- 現代容器化實務
- Kubernetes 編排技術
- 雲原生設計模式
- 可擴展微服務架構
- 透過部署腳本實現 DevOps 自動化
