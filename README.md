# FastAPI 點數平台系統規劃書

## 1. 架構設計與技術棧

- **後端框架**：FastAPI（Python）
- **資料庫**：PostgreSQL（每個 merchant 一個 schema，主庫存 merchants 與 api keys）
- **API**：RESTful，統一前綴 `/api/v1/`，自動生成 Swagger 文件
- **多租戶**：根據 `x-api-key` 動態切換 schema
- **管理介面**：Gradio（Python UI library）
- **部署**：Docker（包含 app、db、Gradio）

## 2. 專案目錄結構建議

```plaintext
point-system/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── merchants.py
│   │   │   │   ├── points.py
│   │   │   │   └── ...
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── multi_tenancy.py
│   ├── models/
│   │   ├── merchant.py
│   │   ├── point_rule.py
│   │   ├── point_log.py
│   │   └── ...
│   ├── schemas/
│   ├── services/
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── ...
│   └── utils/
├── gradio_ui/
│   └── admin_panel.py
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── ...
├── tests/
├── requirements.txt
└── README.md
```

## 3. 資料庫設計

- **主庫（public schema）**
    - `merchants`：商戶基本資料
    - `merchant_api_keys`：API Key、有效期限、權限、狀態
- **每個 merchant schema**
    - `point_rules`：點數換算規則
    - `point_logs`：點數操作紀錄（含 uid、balance，需考慮併發）

## 4. API 驗證與安全

- 所有 API 需帶 `x-api-key`
- 每個 key 有效期限、權限範圍，支援輪替/撤銷
- 請求時根據 key 查詢 merchant 與 schema，切換資料庫操作
- 統一回傳格式：`{ code, message, data }`

## 5. 業務邏輯模組

- **Merchant 管理**：註冊、API Key 設定、查詢
- **點數換算規則**：自訂匯率、即時計算、歷史查詢、批次同步
- **帳務稽核/追蹤**：每筆 usage、換算、回傳皆有審計紀錄

## 6. Gradio UI

- 提供管理介面（如商戶註冊、API Key 管理、規則設定、查詢審計紀錄等）
- 以 Python Gradio 實作，與 FastAPI 共用部分 service 層

## 7. Docker 部署

- 使用 `docker-compose` 管理 FastAPI、PostgreSQL、Gradio
- 可單獨測試（unit test、integration test）

## 8. 開發與部署流程

1. 設計資料庫 schema 與多租戶切換邏輯
2. 開發 API 與驗證機制
3. 實作業務邏輯與審計紀錄
4. 開發 Gradio 管理介面
5. 撰寫 Dockerfile 與 docker-compose
6. 撰寫測試
7. 部署與驗證

---

# FastAPI 點數平台專案

本專案為 FastAPI + PostgreSQL 多租戶點數平台，詳細規劃請參考主目錄 README.md。

## 專案結構

- app/
  - main.py
  - api/
  - core/
  - models/
  - schemas/
  - services/
  - db/
  - utils/
- gradio_ui/
- docker/
- tests/
- requirements.txt
- docker-compose.yml

## 快速開始

1. 啟動服務：`docker-compose up`
2. 進入 http://localhost:8030/docs 查看 API 文件
