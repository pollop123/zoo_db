# 動物園管理系統 - 操作手冊 (Operation Manual)

本手冊旨在提供系統管理員與一般使用者詳細的操作指引，涵蓋環境建置、系統啟動、日常操作及故障排除。

---

## 1. 系統架構與環境 (System Architecture)

本系統採用 **混合式資料庫架構 (Hybrid Database Architecture)**，結合關聯式資料庫與 NoSQL 資料庫的優勢。

### 1.1 技術組件
*   **前端介面**: Python CLI (Command Line Interface)
*   **後端服務**: Python Socket Server
*   **核心資料庫 (RDBMS)**: PostgreSQL 17 (儲存員工、動物、庫存、班表)
*   **日誌資料庫 (NoSQL)**: MongoDB (儲存稽核日誌、登入紀錄、健康警報)

### 1.2 軟硬體需求
*   **作業系統**: macOS / Linux / Windows (建議使用 Unix-like 環境)
*   **Python 版本**: 3.8+
*   **記憶體**: 建議 4GB 以上

---

## 2. 環境建置與部署 (Deployment)

### 2.1 安裝資料庫
1.  **PostgreSQL**:
    *   下載並安裝 PostgreSQL 17。
    *   確保服務已啟動且監聽 `5432` 埠。
2.  **MongoDB**:
    *   **MacOS (Homebrew)**:
        ```bash
        brew tap mongodb/brew
        brew install mongodb-community@7.0
        brew services start mongodb/brew/mongodb-community
        ```
    *   確保服務已啟動且監聽 `27017` 埠。

### 2.2 初始化資料
1.  **建立 SQL 資料庫**:
    ```bash
    createdb -U postgres zoo_db
    ```
2.  **還原 SQL 資料**:
    ```bash
    pg_restore -U postgres -d zoo_db -F c zoo.backup
    ```
3.  **還原 NoSQL 資料**:
    ```bash
    mongoimport --db zoo_nosql --collection login_logs --file mongo_login_logs.json --jsonArray
    mongoimport --db zoo_nosql --collection audit_logs --file mongo_audit_logs.json --jsonArray
    mongoimport --db zoo_nosql --collection health_alerts --file mongo_health_alerts.json --jsonArray
    ```

### 2.3 安裝 Python 依賴
```bash
pip install psycopg2-binary pymongo rich
```

---

## 3. 系統啟動 (System Startup)

請依照順序啟動系統組件。

### 3.1 啟動後端伺服器
開啟終端機 (Terminal A)，執行：
```bash
python server.py
```
*   **成功訊號**: 看到 `[START] Server listening on 0.0.0.0:9999`。

### 3.2 啟動前端客戶端
開啟另一個終端機 (Terminal B)，執行：
```bash
python client.py
```
*   **成功訊號**: 看到歡迎畫面與登入提示。

---

## 4. 使用者操作指南 (User Guide)

### 4.1 登入系統
*   輸入員工 ID (例如 `E001`, `E003`)。
*   系統會驗證 ID 是否存在及其權限。

### 4.2 飼育員功能 (Employee)
*   **查詢班表**: 查看今日負責的動物與時段。
*   **動物餵食**:
    *   輸入動物 ID 與飼料 ID。
    *   輸入餵食量 (kg)。
    *   **注意**: 系統會檢查庫存、班表權限及專業證照。
*   **回報狀態**: 記錄動物體重與健康狀況。

### 4.3 管理員功能 (Admin)
*   **庫存管理**: 查看飼料庫存水位，執行補貨操作。
*   **工作指派**: 分派日常照護任務給員工。
*   **異常偵測**:
    *   **冒失鬼名單**: 查看頻繁操作錯誤的員工。
    *   **高風險動物**: 查看體重波動異常的動物。
*   **稽核日誌**: 查詢系統內的所有敏感操作紀錄 (存於 MongoDB)。

---

## 5. 故障排除 (Troubleshooting)

### 5.1 資料庫連線失敗
*   **錯誤訊息**: `Connection refused`
*   **解法**:
    1.  檢查 `config.py` 中的 `PG_PASSWORD` 是否正確。
    2.  確認 PostgreSQL (`5432`) 與 MongoDB (`27017`) 服務是否已啟動。

### 5.2 權限不足 (Permission Denied)
*   **情境**: 餵食時被拒絕。
*   **原因**:
    1.  **非值班時間**: 您不在該時段的班表上。
    2.  **非負責動物**: 您未被指派照顧該動物。
    3.  **缺乏證照**: 該動物屬於危險或特殊類別 (如食肉目)，您缺乏相應證照。

### 5.3 庫存扣減失敗
*   **原因**: 庫存不足或同時有多人操作導致鎖定衝突 (極少見，系統有 Retry 機制)。
*   **解法**: 請管理員先執行補貨。

---

## 6. 系統維護 (Maintenance)

### 6.1 資料備份
*   **SQL**: `pg_dump -U postgres -F c zoo_db > zoo_backup_$(date +%Y%m%d).dump`
*   **NoSQL**: `mongoexport --db zoo_nosql ...`

### 6.2 日誌清理
*   建議定期封存 MongoDB 中的舊日誌資料以釋放空間。
