# 動物園管理系統 - 操作手冊

本手冊提供系統管理員與一般使用者詳細的操作指引。

---

## 1. 系統架構

### 技術組件
| 組件 | 技術 | 用途 |
|------|------|------|
| 前端介面 | Python CLI (Rich) | 使用者操作介面 |
| 後端服務 | Python Socket Server | 處理請求與商業邏輯 |
| 核心資料庫 | PostgreSQL 17 | 員工、動物、庫存、班表 |
| 日誌資料庫 | MongoDB 7.0 | 稽核日誌、登入紀錄、健康警報 |

### 環境需求
- 作業系統: macOS / Linux / Windows
- Python: 3.8+
- 記憶體: 建議 4GB 以上

---

## 2. 環境建置

### 2.1 安裝資料庫

**PostgreSQL (MacOS)**
```bash
brew install postgresql@17
brew services start postgresql@17
```

**MongoDB (MacOS)**
```bash
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb/brew/mongodb-community
```

### 2.2 初始化資料

```bash
# 建立 PostgreSQL 資料庫
createdb -U postgres zoo_db

# 還原 SQL 資料
psql -U postgres -d zoo_db < zoo.backup

# 還原 MongoDB 資料
mongoimport --db zoo_nosql --collection login_logs --file mongo_login_logs.json --jsonArray
mongoimport --db zoo_nosql --collection audit_logs --file mongo_audit_logs.json --jsonArray
mongoimport --db zoo_nosql --collection health_alerts --file mongo_health_alerts.json --jsonArray
```

### 2.3 安裝 Python 依賴

```bash
python3 -m venv venv
source venv/bin/activate
pip install psycopg2-binary pymongo rich
```

### 2.4 設定連線參數

編輯 `config.py`：
```python
PG_HOST = "localhost"
PG_PORT = "5432"
PG_DB = "zoo_db"
PG_USER = "postgres"
PG_PASSWORD = "your_password"

MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "zoo_nosql"
```

---

## 3. 系統啟動

### 3.1 啟動後端伺服器

```bash
python server.py
```
成功訊號: `Server listening on 127.0.0.1:60000`

### 3.2 啟動前端客戶端

開啟另一個終端機：
```bash
python client.py
```

---

## 4. 使用者操作指南

### 4.1 登入系統

輸入員工 ID (如 `E001`, `E003`)，系統會驗證：
- ID 是否存在
- 帳號是否為 active 狀態
- 角色權限 (Admin / User)

### 4.2 User 功能

| 功能 | 說明 | 注意事項 |
|------|------|---------|
| 新增餵食紀錄 | 記錄餵食內容 | 需在值班時間、負責的動物、有對應證照 |
| 新增身體資訊 | 回報體重與狀態 | 同上 |
| 查詢班表 | 查看自己的排班 | - |
| 修正自己紀錄 | 修正錯誤輸入 | 會記錄稽核日誌 |
| 修改密碼 | 修改自己的登入密碼 | - |
| 我的修正紀錄 | 查看自己被標記的冒失紀錄 | - |

### 4.3 Admin 功能

| 功能 | 說明 |
|------|------|
| 稽核日誌 | 查看所有修正紀錄 (MongoDB) |
| 健康監控 | 子選單：批量異常掃描、高風險動物、動物趨勢、待處理健康警示 |
| 庫存管理 | 子選單：查看庫存報表、進貨補充 |
| 指派工作 | 為員工安排班表 (含證照驗證) |
| 修正紀錄 | 可修正任何人的紀錄 |
| 冒失鬼名單 | 查看資料被修正的員工統計 |
| 員工管理 | 子選單：查看員工、新增、停用/啟用、變更角色、管理證照 |
| 飲食管理 | 設定各物種可食用的飼料 |

---

## 5. 故障排除

### 5.1 資料庫連線失敗

**錯誤訊息**: `Connection refused`

**解決方法**:
1. 檢查 `config.py` 中的密碼是否正確
2. 確認 PostgreSQL 服務已啟動: `brew services list`
3. 確認 MongoDB 服務已啟動: `brew services list`

### 5.2 權限不足

**錯誤訊息**: `無操作權限: 非值班時間或非負責動物`

**原因**:
1. 不在值班時間
2. 未被指派該動物
3. 缺乏對應證照

**解決方法**: 請管理員確認班表與證照設定

### 5.3 庫存不足

**錯誤訊息**: `庫存不足`

**解決方法**: 請管理員執行庫存進貨

---

## 6. 系統維護

### 6.1 資料備份

**PostgreSQL**:
```bash
pg_dump -U postgres zoo_db > zoo_backup_$(date +%Y%m%d).sql
```

**MongoDB**:
```bash
mongoexport --db zoo_nosql --collection audit_logs --out audit_logs_backup.json --jsonArray
```

### 6.2 還原資料

```bash
# PostgreSQL
psql -U postgres -d zoo_db < zoo.backup

# MongoDB
mongoimport --db zoo_nosql --collection audit_logs --file audit_logs_backup.json --jsonArray --drop
```

### 6.3 重置測試資料

若需將資料庫恢復至初始狀態：
```bash
dropdb -U postgres zoo_db
createdb -U postgres zoo_db
psql -U postgres -d zoo_db < zoo.backup
```
