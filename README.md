# 動物園管理系統 (Zoo Management System)

## 專案概述 (Project Overview)
本動物園管理系統是一套全方位的軟體解決方案，旨在簡化現代動物園的日常營運流程。透過安全且基於角色的操作介面，本系統協助管理動物照護、庫存控制、員工排班以及異常偵測等關鍵任務。

本系統採用主從式架構 (Client-Server Architecture)，使用 Python 處理應用邏輯，並結合 PostgreSQL 處理交易型資料 (如餵食紀錄、庫存、班表)，以及 MongoDB 處理稽核日誌與非結構化資料 (如健康警報)。

## 核心功能 (Key Features)

### 1. 角色權限控管 (RBAC)
*   **管理員 (Administrator)**: 擁有系統設定、庫存管理、工作指派及查閱稽核日誌的完整權限。
*   **飼育員 (Employee/Keeper)**: 權限僅限於日常操作任務，如餵食與回報動物狀態。

### 2. 嚴格權限驗證系統 (Strict Permission System)
*   **班表驗證 (Shift Verification)**: 員工僅能在其排定的值班時間內執行操作。
*   **責任歸屬檢查 (Responsibility Check)**: 員工僅能操作其被指派負責的特定動物。
*   **專業證照認證 (Skill Certification)**: 執行特定任務需具備相應的專業證照 (例如: 食肉動物照護證照、爬蟲類照護證照)。

### 3. 庫存管理 (Inventory Management)
*   **即時追蹤**: 精確追蹤飼料庫存水位。
*   **併發控制 (Concurrency Control)**: 實作「列級鎖定 (Row-Level Locking)」與「表級鎖定 (Table Locking)」機制，防止多用戶同時操作時發生競態條件 (Race Conditions)。
*   **自動化補貨**: 提供管理員專用的庫存補給工具。

### 4. 異常偵測與分析 (Anomaly Detection & Analytics)
*   **體重監測**: 自動偵測顯著的體重波動 (閾值: 5%) 並標記潛在健康問題。
*   **人為疏失偵測**: 識別頻繁輸入錯誤數據的員工 (冒失鬼名單)。
*   **趨勢分析**: 提供動物健康指標的歷史數據視覺化圖表。

### 5. 混合式資料庫架構 (Hybrid Database Architecture)
本系統特別採用 **PostgreSQL + MongoDB** 的雙資料庫設計，以發揮各自的優勢：

*   **PostgreSQL (關聯式資料庫)**:
    *   **用途**: 儲存核心業務資料 (員工、動物、庫存、班表)。
    *   **原因**: 這些資料之間有嚴謹的關聯性 (Foreign Keys)，且交易過程 (如扣庫存) 需要 ACID 強一致性保證。

*   **MongoDB (NoSQL 非關聯式資料庫)**:
    *   **用途**: 專門用於儲存 **稽核日誌 (Audit Logs)** 與 **健康警報 (Health Alerts)**。
    *   **使用策略**:
        *   **稽核日誌**: 由於不同操作 (如「修改體重」與「修改班表」) 所需記錄的欄位差異巨大，我們利用 MongoDB 的文件模型 (Document Model) 直接儲存異質性的 JSON 資料，避免在關聯式資料庫中建立過多稀疏欄位 (Sparse Columns)。
        *   **健康警報**: 系統偵測到異常時會生成非結構化的警報物件，直接寫入 MongoDB 供管理員後續查詢，不需預先定義嚴格的資料表結構。

## 展示與測試指南 (Demo Guide)
為了方便期末展示，系統已預設以下測試帳號與情境：

### 角色權限展示 (Role & Permission)
| 員工 ID | 角色 (Role) | 專長 (Skill) | 負責動物 (Shift) | 預期行為 |
| :--- | :--- | :--- | :--- | :--- |
| **E003** | 資深員工 | **Carnivore (肉食)** | **獅子 (A002)** | 可餵食獅子 (有證照+有班表)<br>不可餵食老虎 (非負責動物) |
| **E004** | 中階員工 | **Carnivore (肉食)** | **老虎 (A005)** | 可餵食老虎 (有證照+有班表)<br>不可餵食獅子 (非負責動物) |
| **E005** | 菜鳥員工 | **無 (None)** | **無尾熊 (A004)** |可餵食無尾熊 (無門檻動物)<br>**不可餵食獅子** (系統擋：缺乏證照) |

### 動物分類設定 (Animal Classification)
*   **危險區 (需證照)**: 獅子、老虎、棕熊、河馬。
*   **一般區 (免證照)**: 無尾熊、熊貓、大象、長頸鹿、斑馬。
*   **海洋區 (需證照)**: 企鵝。

## 技術棧 (Technology Stack)
*   **前端 (Frontend)**: Python (CLI 介面，使用 Rich 函式庫)
*   **後端 (Backend)**: Python (Socket Server)
*   **關聯式資料庫 (RDBMS)**: PostgreSQL 17
*   **非關聯式資料庫 (NoSQL)**: MongoDB
*   **測試 (Testing)**: 客製化自動化測試代理人 (多執行緒)

## 安裝與設定 (Installation & Setup)

### 1. 環境需求 (Prerequisites)
*   Python 3.8 或更高版本
*   PostgreSQL 17
*   MongoDB Community Edition

### 2. 資料庫初始化 (Database Initialization)
請依照以下步驟設定您的本地資料庫：

1.  **建立資料庫**:
    在終端機執行以下指令以建立名為 `zoo_db` 的資料庫：
    ```bash
    createdb -U postgres zoo_db
    ```

2.  **還原資料**:
    將提供的備份檔還原至剛建立的資料庫：
    ```bash
    pg_restore -U postgres -d zoo_db -F c zoo_final.backup
    ```

3.  **MongoDB 設定**:
    請確保 MongoDB 正在本地預設連接埠 (27017) 運行，且無需帳號密碼驗證 (預設設定)。

### 3. 系統設定 (Configuration)
本系統的資料庫連線設定位於 `config.py` 檔案中。請務必確認該檔案內的設定與您的本地環境一致：

1.  打開專案根目錄下的 `config.py` 檔案。
2.  修改以下變數以符合您的 PostgreSQL 設定：
    ```python
    PG_HOST = "localhost"       # 資料庫主機 (通常為 localhost)
    PG_PORT = "5432"            # PostgreSQL 連接埠 (預設 5432)
    PG_DB = "zoo_db"            # 資料庫名稱 (需與步驟 2 建立的名稱一致)
    PG_USER = "postgres"        # 您的 PostgreSQL 使用者名稱
    PG_PASSWORD = "your_password" # 您的 PostgreSQL 密碼 (請修改此處！)
    ```

### 4. 安裝依賴套件 (Dependencies)
安裝所需的 Python 套件：
```bash
pip install psycopg2-binary pymongo rich
```

## 使用指南 (Usage Guide)

### 啟動伺服器 (Starting the Server)
後端伺服器必須先啟動以處理客戶端請求。
```bash
python server.py
```

### 啟動客戶端 (Starting the Client)
在另一個終端機視窗啟動使用者介面。
```bash
python client.py
```

### 執行自動化測試 (Running Automated Tests)
若要驗證系統完整性與效能，請執行測試代理人：
```bash
python test/test_agent.py
```
**注意**: 測試程式會對資料庫進行真實的寫入操作 (如扣除庫存、新增班表)。若您希望在測試後將資料庫恢復至初始狀態，請執行以下指令：
```bash
pg_restore --clean --if-exists -U postgres -d zoo_db -F c zoo_final.backup
```

## 檔案結構 (File Structure)
*   `server.py`: 後端伺服器主程式。
*   `client.py`: 前端 CLI 主程式。
*   `DB_utils.py`: 核心資料庫互動邏輯與商業規則。
*   `config.py`: 系統設定與資料庫連線參數。
*   `action/`: **[模組化邏輯]** 包含各項業務功能的實作 (如 `feeding.py`, `inventory.py`)，採用 Command Pattern 設計。
*   `role/`: **[角色定義]** 定義不同角色的權限與選單介面 (如 `employee.py`)。
*   `test/`: 包含自動化測試套件的目錄 (`test_agent.py` 等)。
*   `scripts/`: 包含設定與工具腳本的目錄 (`setup_shifts.py`, `setup_skills.py`)。
*   `CHANGELOG.md`: 系統變更與更新的詳細紀錄。
*   `zoo_final.backup`: 資料庫備份檔。
