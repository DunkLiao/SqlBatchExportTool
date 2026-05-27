# SQL 批次查詢 Excel 匯出工具

## Software Design Document（SDD）

### 適用於 VIBE CODING / AI 協作開發

---

# 1. 專案名稱

SQL Batch Export Tool（Oracle → Excel）

中文名稱：

> Oracle SQL 批次查詢 Excel 匯出工具

---

# 2. 專案目標

建立一套：

* Windows 免安裝
* 可攜式（Portable）
* 桌面 GUI 工具

讓使用者可以：

* 批次讀取多個 `.sql`
* 查詢 Oracle Database
* 將每個 SQL 查詢結果
* 自動輸出到指定 Excel 檔案
* 每個 SQL 對應一個工作表（Sheet）

---

# 3. 使用情境（Use Case）

## 銀行報表情境

風管、授信、稽核、法遵、資訊單位：

每月需：

* 執行大量 SQL
* 匯出 Excel
* 分頁整理報表
* 提供主管檢閱

目前流程：

```text
手動開 SQL Developer
→ 貼 SQL
→ 執行
→ 匯出 Excel
→ 建工作表
→ 重複數十次
```

本工具目標：

```text
一次完成全部
```

---

# 4. 核心功能

## 4.1 SQL 批次執行

系統需：

* 讀取指定資料夾內所有 `.sql`
* 依檔名排序執行
* 每個 SQL 獨立執行

---

## 4.2 Oracle 連線

支援：

* Host
* Port
* Service Name
* Username
* Password

使用：

* python-oracledb thin mode

不需安裝 Oracle Client。

---

## 4.3 Excel 匯出

系統需：

* 建立 `.xlsx`
* 每個 SQL 結果輸出至獨立工作表
* Sheet Name = SQL 檔名

---

## 4.4 GUI 桌面介面

需提供：

| 元件             | 功能             |
| -------------- | -------------- |
| Oracle Host    | DB 主機          |
| Port           | DB Port        |
| Service Name   | Oracle Service |
| Username       | 帳號             |
| Password       | 密碼             |
| SQL Folder     | SQL 資料夾        |
| Output Excel   | 輸出檔            |
| Execute Button | 執行             |
| Log Area       | 顯示執行紀錄         |

---

## 4.5 執行紀錄

需顯示：

* SQL 名稱
* 執行成功/失敗
* 查詢筆數
* 執行秒數
* 錯誤訊息

---

# 5. 系統架構

```text
GUI Layer
    ↓
Controller Layer
    ↓
SQL Executor
    ↓
Oracle Database

Result Handler
    ↓
Excel Writer
```

---

# 6. 技術架構

| 項目        | 技術                |
| --------- | ----------------- |
| Language  | Python 3.12+      |
| GUI       | PySide6           |
| DB Driver | python-oracledb   |
| Excel     | pandas + openpyxl |
| Packaging | PyInstaller       |
| Logging   | logging           |
| Config    | JSON              |

---

# 7. 專案資料夾結構

```text
SqlBatchExportTool/
│
├─ app/
│   ├─ main.py
│   ├─ ui/
│   │   └─ main_window.py
│   ├─ services/
│   │   ├─ db_service.py
│   │   ├─ sql_service.py
│   │   ├─ excel_service.py
│   │   └─ log_service.py
│   ├─ models/
│   │   └─ config_model.py
│   └─ utils/
│       └─ file_utils.py
│
├─ sql/
│   ├─ 01_放款.sql
│   ├─ 02_逾期.sql
│   └─ 03_ECL.sql
│
├─ output/
│
├─ logs/
│
├─ config/
│   └─ config.json
│
├─ requirements.txt
│
└─ README.md
```

---

# 8. SQL 執行規格

## 8.1 SQL 檔案規格

支援：

```sql
SELECT *
FROM CUSTOMER
WHERE DATA_DATE = SYSDATE
```

---

## 8.2 執行順序

依：

```text
檔名排序
```

例如：

```text
01_xxx.sql
02_xxx.sql
03_xxx.sql
```

---

## 8.3 SQL 編碼

需支援所有常見的繁體中文編碼

---

## 8.4 失敗不中斷

若某 SQL 發生錯誤：

* 紀錄錯誤
* 繼續執行下一支 SQL

---

# 9. Excel 匯出規格

---

## 9.1 工作表名稱

規則：

```text
Sheet Name = SQL 檔名
```

例如：

```text
01_放款.sql
→
01_放款
```

---

## 9.2 Excel 限制處理

需處理：

| 問題      | 處理     |
| ------- | ------ |
| 超過 31 字 | 自動截斷   |
| 特殊字元    | 替換 `_` |
| 重複名稱    | 自動加序號  |

---

## 9.3 欄位格式

需：

* 自動寫入欄位名稱
* 凍結第一列
* 自動調整欄寬

---

## 9.4 空資料

若 SQL 無結果：

* 仍建立工作表
* 顯示：

```text
No Data
```

---

# 10. Config 規格

## config.json

```json
{
  "db": {
    "host": "127.0.0.1",
    "port": 1521,
    "service_name": "ORCL",
    "username": "system",
    "password": ""
  },
  "last_sql_folder": "",
  "last_output_excel": ""
}
```

---

# 11. Logging 規格

Log 位置：

```text
/logs/
```

格式：

```text
2026-05-27 10:00:01 [INFO]
01_放款.sql Success Rows=1523 Time=3.25s

2026-05-27 10:00:05 [ERROR]
02_ECL.sql ORA-00942 table or view does not exist
```

---

# 12. UI/UX 規格

---

## 主視窗

```text
+------------------------------------------------+
| Oracle SQL Batch Export Tool                   |
+------------------------------------------------+
| Host:        [_______________]                 |
| Port:        [1521__________]                  |
| Service:     [ORCL__________]                  |
| Username:    [_______________]                 |
| Password:    [*************]                   |
+------------------------------------------------+
| SQL Folder:  [_______________][Browse]         |
| Output XLSX: [_______________][Browse]         |
+------------------------------------------------+
| [ Execute ]                                    |
+------------------------------------------------+
| Log Area                                       |
|                                                |
| 01_放款.sql Success Rows=1523                  |
| 02_ECL.sql Failed ORA-00942                    |
|                                                |
+------------------------------------------------+
```

---

# 13. 非功能需求（NFR）

| 項目        | 規格              |
| --------- | --------------- |
| 啟動時間      | < 3 秒           |
| 支援 SQL 數量 | 至少 500 支        |
| 支援資料量     | 單 Sheet 100 萬筆內 |
| 記憶體使用     | < 1.5GB         |
| 作業系統      | Windows 10/11   |
| 安裝需求      | 無               |
| 離線執行      | 可               |

---

# 14. 打包規格

使用：

```bash
PyInstaller
```

指令：

```bash
pyinstaller --onefile --windowed main.py
```

輸出：

```text
dist/
└─ SqlBatchExportTool.exe
```

---

# 15. 錯誤處理規格

| 錯誤         | 處理    |
| ---------- | ----- |
| DB 連線失敗    | Popup |
| SQL 語法錯誤   | Log   |
| Excel 被占用  | Popup |
| Sheet 名稱錯誤 | 自動修正  |
| 欄位過長       | 自動截斷  |

---

# 16. 後續擴充功能（Roadmap）

---

## Phase 2

### SQL 參數化

例如：

```sql
WHERE DATA_DATE = :DATA_DATE
```

GUI：

```text
DATA_DATE = 20260527
```

---

## Phase 3

### 多資料庫支援

* Oracle
* SQL Server
* PostgreSQL
* MySQL

---

## Phase 4

### 排程執行

例如：

```text
每天 06:00 自動產出報表
```

---

## Phase 5

### Email 自動寄送

```text
查詢完成
→ 自動寄 Excel
```

---

# 17. AI Coding 指示（VIBE CODING Prompt）

## 系統角色

你是資深 Python Desktop Application Engineer。

請協助開發：

「Oracle SQL 批次查詢 Excel 匯出工具」

---

## 技術限制

必須使用：

* Python 3.12+
* PySide6
* python-oracledb
* pandas
* openpyxl

禁止：

* Electron
* Web Framework
* 需安裝 Oracle Client 的方案

---

## 開發原則

必須：

* 模組化
* 可維護
* 可擴充
* GUI 與 Business Logic 分離
* 使用 MVC/MVVM 概念

---

## UI 需求

建立：

* Windows 桌面 GUI
* 深色模式
* 支援拖曳調整大小

---

## 程式品質要求

需：

* 完整型別註記
* logging
* try-except
* 錯誤訊息友善
* 避免 UI 卡死
* 長時間查詢需使用 QThread

---

## Excel 規格

每個 SQL：

* 對應一個 Sheet
* Sheet Name 使用 SQL 檔名
* 自動調整欄寬
* Freeze Header
* UTF-8 支援

---

## 最終輸出

需產生：

* 完整專案結構
* requirements.txt
* README.md
* 可直接執行程式碼
* PyInstaller 打包指令
* 範例 config.json
* 範例 SQL