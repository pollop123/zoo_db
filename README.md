# 動物園管理系統 (Zoo Management System)

## 專案概述

本動物園管理系統是一套全方位的軟體解決方案，旨在簡化現代動物園的日常營運流程。透過安全且基於角色的操作介面，本系統協助管理動物照護、庫存控制、員工排班以及異常偵測等關鍵任務。

本系統採用主從式架構 (Client-Server Architecture)，使用 Python 處理應用邏輯，並結合 PostgreSQL 處理交易型資料 (如餵食紀錄、庫存、班表)，以及 MongoDB 處理稽核日誌與非結構化資料 (如健康警報)。

---

## 專案特色

### 1. 混合式資料庫架構 (Polyglot Persistence)
本系統採用 **PostgreSQL + MongoDB** 雙資料庫設計：

| 資料庫 | 用途 | 原因 |
|--------|------|------|
| PostgreSQL | 核心業務資料 (員工、動物、庫存、班表) | 資料關聯性強，需要 ACID 強一致性保證 |
| MongoDB | 稽核日誌、健康警報、冒失鬼紀錄、登入紀錄 | 異質性 JSON 資料，避免稀疏欄位問題 |

### 2. 三層權限驗證系統
- **班表驗證**: 員工僅能在排定的值班時間內執行操作
- **責任歸屬檢查**: 員工僅能操作其被指派負責的特定動物
- **專業證照認證**: 執行特定任務需具備相應證照

### 3. 併發控制機制
實作「列級鎖定」與「表級鎖定」機制，防止多用戶同時操作時發生競態條件。

### 4. 智慧異常偵測
- **體重監測**: 比對近 7 天平均體重，偏差超過 5% 自動標記異常
- **食量監測**: 比對近 7 天平均餵食量，偏差超過 30% 自動標記異常
- **人為疏失偵測**: 識別頻繁修正紀錄的員工 (冒失鬼名單)
- **趨勢分析**: 提供動物健康指標的歷史數據
- 詳細演算法說明請參考 [ANOMALY_DETECTION.md](ANOMALY_DETECTION.md)

---

## 安裝與設定

### 環境需求
- Python 3.8+
- PostgreSQL 17
- MongoDB Community Edition 7.0+

### 步驟 1: 安裝依賴套件

```bash
# 建立虛擬環境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝套件
pip install psycopg2-binary pymongo rich
```

### 步驟 2: 安裝資料庫

**PostgreSQL (MacOS)**:
```bash
brew install postgresql@17
brew services start postgresql@17
```

**MongoDB (MacOS)**:
```bash
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb/brew/mongodb-community
```

### 步驟 3: 初始化資料庫

```bash
# 建立 PostgreSQL 資料庫
createdb -U postgres zoo_db

# 還原資料
psql -U postgres -d zoo_db < zoo.backup

# 匯入 MongoDB 資料 (使用整合備份檔)
python3 -c "
import json
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client['zoo_nosql']
with open('mongo_backup.json', 'r') as f:
    data = json.load(f)
for collection, docs in data.items():
    if docs:
        db[collection].drop()
        db[collection].insert_many(docs)
        print(f'{collection}: {len(docs)} 筆')
"
```

### 步驟 4: 設定連線參數

編輯 `config.py`，確認資料庫連線設定：

```python
PG_HOST = "localhost"
PG_PORT = "5432"
PG_DB = "zoo_db"
PG_USER = "postgres"
PG_PASSWORD = "your_password"  # 修改為您的密碼

MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "zoo_nosql"
```

---

## 執行系統

### 啟動伺服器
```bash
python server.py
# 顯示: Server listening on 127.0.0.1:60000
```

### 啟動客戶端 (另開終端機)
```bash
python client.py
```

### 登入資訊
- **預設密碼**: `zoo123` (所有帳號)
- **忘記密碼**: 在登入畫面輸入 `f` 可查詢

### 執行自動化測試
```bash
python test/test_agent.py
```

---

## 功能說明

### User 功能 (6 項)
| 功能 | 說明 |
|------|------|
| 新增餵食紀錄 | 記錄餵食內容，自動依物種顯示可用飼料，顯示最近紀錄供參考 |
| 新增身體資訊 | 回報動物體重與健康狀態，顯示最近體重供參考 |
| 查詢班表 | 查看自己的排班資訊與負責動物 |
| 修正自己紀錄 | 修正自己輸入的錯誤資料 (會記錄稽核日誌) |
| 修改密碼 | 修改自己的登入密碼 |
| 我的修正紀錄 | 查看自己被標記的冒失紀錄與修正歷史 |

### Admin 功能 (9 項)
| 功能 | 說明 |
|------|------|
| 稽核日誌 | 查看所有修正紀錄的 MongoDB 稽核日誌 |
| 健康監控 | 子選單：批量異常掃描、高風險動物、動物趨勢 |
| 庫存管理 | 子選單：查看庫存報表、進貨補充 |
| 指派工作 | 為員工安排班表與負責動物 (含證照驗證) |
| 修正紀錄 | 管理員可修正任何人的紀錄 |
| 冒失鬼名單 | 查看頻繁輸入錯誤的員工 (修正次數 >= 5) |
| 員工管理 | 子選單：查看員工、新增、停用/啟用、變更角色、管理證照 |
| 飲食管理 | 設定各物種可食用的飼料 |
| 查詢動物趨勢 | 查看特定動物的體重與餵食趨勢，自動偵測異常 |

---

## 證照系統

| 證照名稱 | 可照顧的動物 | 動物數量 |
|---------|-------------|---------|
| Carnivore | 獅子、老虎、棕熊 (猛獸) | 61 隻 |
| Penguin | 企鵝 | 22 隻 |
| Endangered | 熊貓、無尾熊 (珍稀動物) | 47 隻 |
| (無需證照) | 斑馬、長頸鹿、大象等一般動物 | 70 隻 |

---

## 檔案結構

```
zoo_db/
├── server.py          # 後端伺服器主程式
├── client.py          # 前端 CLI 主程式
├── DB_utils.py        # 核心資料庫邏輯與商業規則
├── config.py          # 系統設定與連線參數
├── action/            # 業務功能模組 (Command Pattern)
├── role/              # 角色定義與權限
├── test/              # 自動化測試套件
├── zoo.backup         # PostgreSQL 資料庫備份
├── mongo_*.json       # MongoDB 資料備份
├── DEMO_GUIDE.md      # 展示指南
├── CHANGELOG.md       # 變更紀錄
└── README.md          # 本文件
```

---

## 技術棧

- **前端**: Python CLI (Rich 函式庫)
- **後端**: Python Socket Server
- **關聯式資料庫**: PostgreSQL 17
- **非關聯式資料庫**: MongoDB 7.0
- **測試**: 客製化自動化測試代理人

---

## 相關文件

- [DEMO_GUIDE.md](DEMO_GUIDE.md) - 功能展示指南與測試帳號
- [CHANGELOG.md](CHANGELOG.md) - 版本變更紀錄
- [OPERATION_MANUAL.md](OPERATION_MANUAL.md) - 操作手冊
