# 動物園管理系統 - 快速操作備忘

本文件只保留日常操作與故障排除。環境建置、資料庫初始化與備份還原指令以 `README.md` 為準。

---

## 啟動順序

### 1. 確認資料庫服務

```bash
brew services list
```

需要確認 PostgreSQL 與 MongoDB 都在執行中。

### 2. 啟動 Server

展示前建議先刷新班表並做 smoke check：

```bash
source venv/bin/activate
python scripts/refresh_demo_data.py
python scripts/verify_system.py
```

```bash
source venv/bin/activate
python server.py
```

成功時會看到：

```text
[LISTENING] Server is listening on 127.0.0.1:60000
```

### 3. 啟動 Client

另開一個終端機：

```bash
source venv/bin/activate
python client.py
```

---

## 常用帳號

| 角色 | 員工 ID | 預設密碼 | 用途 |
|------|---------|----------|------|
| Admin | E001 | zoo123 | 管理功能、健康監控、庫存、排班 |
| User | E003 | zoo123 | 一般員工流程展示 |

登入畫面輸入 `f` 可查詢展示用密碼；任一輸入框輸入 `b` 可返回上一層。

---

## 功能入口

### User

| 功能 | 用途 |
|------|------|
| 新增餵食紀錄 | 新增餵食並扣庫存 |
| 新增身體資訊 | 回報體重與狀態 |
| 查詢班表 | 查看自己的排班與負責動物 |
| 修正自己紀錄 | 修正個人輸入錯誤 |
| 修改密碼 | 修改登入密碼 |
| 我的修正紀錄 | 查看自己的錯誤與修正紀錄 |

User 操作會檢查是否在值班時間、是否負責該動物，以及是否具備所需證照。

### Admin

| 功能 | 用途 |
|------|------|
| 稽核日誌 | 查看 MongoDB 修正紀錄 |
| 健康監控 | 異常掃描、高風險動物、趨勢、待處理警示 |
| 庫存管理 | 查看庫存與進貨 |
| 指派工作 | 排班與指派負責動物 |
| 修正紀錄 | 管理員修正資料 |
| 冒失鬼名單 | 查看被修正次數較高的員工 |
| 員工管理 | 新增、停用、變更角色與管理證照 |
| 飲食管理 | 設定物種可食用飼料 |

---

## 故障排除

### Client 顯示無法連線 Server

1. 確認 `server.py` 已啟動。
2. 確認 Server 顯示 `[LISTENING] Server is listening on 127.0.0.1:60000`。
3. 若 port 被占用，先關閉舊的 server 程序後重啟。

### Server 顯示資料庫連線失敗

1. 確認 PostgreSQL 與 MongoDB 服務已啟動。
2. 確認 `config.py` 的 `PG_USER`、`PG_PASSWORD`、`PG_DB` 與本機一致。
3. 資料庫初始化與還原請依 `README.md` 操作。

### User 沒有可選動物

這通常表示目前時間沒有符合條件的班表，或員工沒有被指派負責動物。展示前可先執行：

```bash
python scripts/refresh_demo_data.py
python scripts/verify_system.py
```

若仍失敗，再由 Admin 重新指派工作與動物。

### 權限不足

可能原因：

- 不在值班時間
- 未負責該動物
- 缺少該物種需要的證照

### 庫存不足

請使用 Admin 帳號進入「庫存管理」進貨後再操作餵食。
