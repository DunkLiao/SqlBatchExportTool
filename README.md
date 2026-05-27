# 📊 Oracle SQL 批次查詢 Excel 匯出工具

這是一個 Windows 桌面小工具，可以一次執行多個 Oracle SQL 檔案，並把查詢結果整理成一份 Excel。

適合每月固定產報表、稽核資料、風控清單、法遵檢核或任何需要重複匯出 SQL 查詢結果的工作。

## ✨ 這個工具可以做什麼？

- 📁 讀取一整個資料夾裡的 `.sql` 檔案
- 🔢 依照檔名順序執行，例如 `01_xxx.sql`、`02_xxx.sql`
- 🗄️ 連線 Oracle Database
- 📘 輸出一份 `.xlsx` Excel 檔
- 📄 每個 SQL 檔案會變成 Excel 裡的一個工作表
- ✅ 單一 SQL 失敗時不會中斷，會繼續執行下一個
- 🧩 支援 Oracle 命名參數，例如 `:DATA_DATE`
- 🧪 可先按 `Test Connect` 測試 Oracle 連線
- 💾 關閉視窗後會記住上次輸入的連線資訊與路徑

## 🖥️ 使用前準備

請確認電腦已安裝：

- Windows 10 或 Windows 11
- Python 3.12 以上

第一次使用請在專案資料夾執行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

> ⚠️ 若你的電腦使用 Anaconda，請務必使用本專案的 `.venv`。相關說明請看 `doc/venv.md`。

## 🚀 如何啟動程式

直接執行：

```powershell
.\run_app.bat
```

開啟後依序填入：

1. Oracle Host
2. Port
3. Service Name
4. Username
5. Password
6. SQL Folder
7. Output XLSX
8. SQL Parameters

建議先按 `Test Connect`，確認資料庫連線成功後，再按 `Execute` 開始匯出。

## 📁 SQL 檔案怎麼放？

可以把 SQL 檔案放在 `sql/` 資料夾，也可以在畫面上選擇其他資料夾。

範例：

```text
sql/
├─ 01_customer.sql
├─ 02_account.sql
└─ 03_report.sql
```

程式會依檔名排序執行，所以建議用數字開頭控制順序。

每個 `.sql` 建議只放一段查詢：

```sql
SELECT *
FROM CUSTOMER
WHERE ROWNUM <= 100
```

支援常見中文編碼：

- `utf-8-sig`
- `utf-8`
- `cp950`
- `big5`

## 🧩 SQL 參數怎麼用？

SQL 可以使用 Oracle 命名參數：

```sql
SELECT *
FROM CUSTOMER
WHERE DATA_DATE = :DATA_DATE
```

在畫面的 `SQL Parameters` 輸入：

```text
DATA_DATE=20260527
```

多個參數請一行一個：

```text
DATA_DATE=20260527
BRANCH_ID=001
```

參數值會全部以字串傳給 Oracle。若需要日期或數字型別，建議在 SQL 中明確轉換：

```sql
WHERE DATA_DATE = TO_DATE(:DATA_DATE, 'YYYYMMDD')
  AND AMOUNT >= TO_NUMBER(:MIN_AMOUNT)
```

空白行會被忽略；參數名稱不可重複，也不可省略 `=`。

## 📘 Excel 輸出結果

每個 SQL 會建立一個工作表：

```text
01_customer.sql → 01_customer
02_account.sql  → 02_account
```

程式會自動處理：

- 工作表名稱超過 31 字會截短
- 不允許的特殊字元會改成 `_`
- 重複工作表名稱會自動加上編號
- 查無資料時仍會建立工作表，內容顯示 `No Data`
- 有資料時會凍結第一列並自動調整欄寬

## 📝 執行紀錄

畫面下方的 Log 區域會顯示每支 SQL 的狀態，例如成功、失敗、筆數與秒數。

系統也會把紀錄寫到：

```text
logs/app_YYYYMMDD.log
```

## 🧱 打包成 EXE

若要產生可執行檔，請執行：

```powershell
.\build_exe.bat
```

完成後會產生：

```text
dist/SqlBatchExportTool.exe
```

## ❓ 常見問題

### 找不到 PyInstaller？

請先安裝套件：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 出現 PySide6 DLL load failed？

通常是 Anaconda 或 Python 套件環境混用造成。請使用 `.venv`，並確認 `requirements.txt` 中的版本：

```text
PySide6==6.8.3
```

更多說明請看：

```text
doc/venv.md
```

### Oracle 連不上？

請先確認：

- Host 是否正確
- Port 通常是 `1521`
- Service Name 是否正確
- Username / Password 是否正確
- 公司網路或 VPN 是否已連線

可以先按 `Test Connect` 測試，不需要直接執行全部 SQL。

## 🔐 設定與密碼提醒

程式會把上次輸入的連線資訊記錄在：

```text
config/config.json
```

請不要把正式環境密碼提交到 Git 或分享給其他人。
