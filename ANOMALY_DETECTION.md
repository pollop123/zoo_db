# 異常檢測演算法說明

本文件說明動物園管理系統中用於偵測動物健康異常的演算法邏輯。

---

## 體重異常檢測

### 演算法：短期變化率檢測

**原理**：比較動物最近一次體重與前 7 天平均體重，若偏差超過閾值則視為異常。

**計算方式**：
```
偏差率 = |當前體重 - 近7天平均體重| / 近7天平均體重 × 100%
```

**判定標準**：
- 偏差率 > 5%：標記為異常
- 若近 7 天紀錄不足 3 筆，則放寬為近 30 天平均

**SQL 實作**：
```sql
WITH recent_avg AS (
    SELECT 
        a_id,
        AVG(weight) as avg_weight
    FROM animal_state_record
    WHERE recorded_at > NOW() - INTERVAL '7 days'
    GROUP BY a_id
    HAVING COUNT(*) >= 3
),
latest_weight AS (
    SELECT DISTINCT ON (a_id)
        a_id,
        weight,
        recorded_at
    FROM animal_state_record
    ORDER BY a_id, recorded_at DESC
)
SELECT 
    l.a_id,
    l.weight as current_weight,
    r.avg_weight,
    ABS(l.weight - r.avg_weight) / r.avg_weight * 100 as deviation_pct
FROM latest_weight l
JOIN recent_avg r ON l.a_id = r.a_id
WHERE ABS(l.weight - r.avg_weight) / r.avg_weight > 0.05;
```

**設計考量**：
- 使用短期平均而非歷史全平均，避免成長中動物被誤判
- 要求最少 3 筆資料才計算，避免資料不足造成誤判
- 5% 閾值可依物種調整（大型動物可放寬至 8%）

---

## 食量異常檢測

### 演算法：近期趨勢比對

**原理**：比較動物最近一次餵食量與前 7 天平均餵食量，偏差過大則視為異常。

**計算方式**：
```
偏差率 = |當次餵食量 - 近7天平均餵食量| / 近7天平均餵食量 × 100%
```

**判定標準**：
- 偏差率 > 30%：標記為異常
- 連續 3 天偏差率 > 20%：標記為趨勢異常

**SQL 實作**：
```sql
WITH recent_avg AS (
    SELECT 
        a_id,
        AVG(amount) as avg_amount
    FROM feeding_record
    WHERE fed_at > NOW() - INTERVAL '7 days'
    GROUP BY a_id
    HAVING COUNT(*) >= 3
),
latest_feeding AS (
    SELECT DISTINCT ON (a_id)
        a_id,
        amount,
        fed_at
    FROM feeding_record
    ORDER BY a_id, fed_at DESC
)
SELECT 
    l.a_id,
    l.amount as current_amount,
    r.avg_amount,
    ABS(l.amount - r.avg_amount) / r.avg_amount * 100 as deviation_pct
FROM latest_feeding l
JOIN recent_avg r ON l.a_id = r.a_id
WHERE ABS(l.amount - r.avg_amount) / r.avg_amount > 0.30;
```

**設計考量**：
- 食量波動比體重大，因此閾值設為 30%
- 需考慮季節因素（冬眠期動物食量自然下降）
- 異常紀錄會觸發 MongoDB health_alerts 寫入

---

## 高風險動物判定

### 綜合評分機制

當動物符合以下任一條件，將被列入高風險名單：

| 條件 | 權重 | 說明 |
|------|------|------|
| 體重異常 (>5%) | 高 | 最近體重與短期平均偏差過大 |
| 食量異常 (>30%) | 中 | 最近餵食量與短期平均偏差過大 |
| 健康狀態非 Normal | 高 | 員工回報的健康狀態異常 |
| 連續異常天數 >= 3 | 最高 | 持續性異常需立即關注 |

**輸出格式**：
```
高風險動物清單
┏━━━━━━┳━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┓
┃ 動物ID ┃ 名稱  ┃ 異常類型  ┃ 偏差率      ┃
┡━━━━━━╇━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━┩
│ A001   │ 辛巴  │ 體重下降  │ -7.2%      │
│ A015   │ 雪球  │ 食量異常  │ +45.3%     │
└────────┴───────┴──────────┴─────────────┘
```

---

## 冒失鬼員工檢測

### 演算法：修正頻率統計

**原理**：統計員工修正自己紀錄的次數，頻繁修正可能代表作業不夠謹慎。

**判定標準**：
- 修正次數 >= 5 次：列入冒失鬼名單
- 修正率 > 10%（修正次數/總紀錄數）：額外標註

**資料來源**：MongoDB audit_logs collection

```javascript
db.audit_logs.aggregate([
    { $match: { action: "correction" } },
    { $group: { 
        _id: "$employee_id", 
        correction_count: { $sum: 1 } 
    }},
    { $match: { correction_count: { $gte: 5 } } },
    { $sort: { correction_count: -1 } }
])
```

---

## 參數調整建議

| 參數 | 預設值 | 建議範圍 | 說明 |
|------|--------|----------|------|
| 體重偏差閾值 | 5% | 3-10% | 大型動物可放寬 |
| 食量偏差閾值 | 30% | 20-40% | 依物種習性調整 |
| 短期平均天數 | 7 天 | 5-14 天 | 越短越敏感 |
| 最少資料筆數 | 3 筆 | 3-5 筆 | 避免誤判 |
| 冒失鬼門檻 | 5 次 | 3-10 次 | 依團隊規模調整 |
