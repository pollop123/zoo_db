# 資料庫變更日誌 (Database Changelog)

本文件記錄了動物園管理系統的所有重要變更。

---

## [v1.3.0] - 2025-12-04

### 資料庫變更
- 新增 `a_name` 欄位至 `animal` 表，提供動物友善名稱顯示
- 移除 `Bird`、`Reptile` 證照
- 新增 `Penguin` 證照 (5 名員工)
- 新增 `Endangered` 證照 (10 名員工)
- 更新 `zoo.backup` 備份檔

### 程式修正
- 修正 `batch_check_anomalies`: 使用 `a_name` 取代不存在的 `a_name` 欄位
- 修正 `add_inventory_stock`: 將 `restock` 改為 `purchase` (符合 check constraint)
- 修正 `add_animal_state`: 新增 `record_id` 自動產生
- 修正 `action/schedule.py`: 新增 `a_id` 參數傳遞
- 修正 `test/test_agent.py`: 新增缺失的 `get_backend()` 方法與測試案例

### 文件更新
- 新增 `DEMO_GUIDE.md` 展示指南
- 更新 `README.md` 結構與安裝說明

---

## [v1.2.0] - 2025-12-02

### 資料優化
- 重新分類動物證照需求 (獅子/老虎=Carnivore，無尾熊/熊貓=Endangered)
- 重置展示用員工技能 (E005 無任何證照)
- 生成 E003, E004, E005 的專屬班表

### 程式優化
- 引入 `Decimal` 進行精確數值運算，防止浮點誤差
- 重構 API：移除舊版 `add_feeding` 方法，全面改用 `add_feeding_record`
- 優化登入回饋：區分「查無帳號」與「帳號狀態異常」
- 新增 `add_employee_skill` API
- `add_animal_state` 支援選擇動物狀態 (`status_type`)
- 將所有資料表名稱移至 `config.py` 統一管理
- 引入 `psycopg2.pool.ThreadedConnectionPool` 提升併發效能

### 文件更新
- README.md 全面中文化
- 新增 MongoDB 資料還原指南
- 新增 `OPERATION_MANUAL.md`

---

## [v1.1.0] - 2025-12-01

### 資料整併與重編號
- 合併重複的工作類型
- 工作項目重新編號：
  - `T001`: 籠舍清潔
  - `T002`: 用藥紀錄
  - `T003`: 環境消毒
  - `T004`: 特殊訓練
  - `T005`: 健康檢查
  - `T006`: 日常照護

### 展示用資料
- 為 E003, E004, E005 指派今日全天班表
- 為歷史班表隨機指派負責動物
- 授予 E001, E003, E004 初始證照

---

## [v1.0.0] - 初始版本

### 新增資料表
- `employee_skills`: 員工專業證照表
- `task`: 工作項目表

### 修改資料表
- `employee`: 新增 `role` 欄位 (Admin/User)
- `animal`: 新增 `required_skill` 欄位
- `employee_shift`: 新增 `a_id` 欄位

### 移除資料表
- `animal_schedule`: 改用新的證照/班表雙重驗證邏輯

### 錯誤修復
- 修復負庫存問題：注入初始進貨紀錄
- 修復管理員登入：更新 E001 狀態為 active
