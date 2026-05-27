# Python 虛擬環境與 Anaconda 注意事項

## 背景

本專案使用 `PySide6` 建立 Windows 桌面 GUI。開發時曾直接使用系統預設的 `python` 執行：

```powershell
python -m app.main
```

當時 `python` 指向 Anaconda：

```text
D:\ProgramData\anaconda3\python.exe
```

並發生以下錯誤：

```text
ImportError: DLL load failed while importing QtWidgets: 找不到指定的程序。
```

測試 `PySide6.QtCore`、`PySide6.QtGui`、`PySide6.QtWidgets` 都會失敗，代表問題在 Qt/PySide6 DLL 載入層，不是本專案的 GUI 程式碼。

## 原因

Anaconda 會自帶許多 DLL 與套件搜尋路徑。若再透過 `pip --user` 或混合環境安裝 `PySide6`，容易造成 Qt DLL 或 runtime 版本衝突。

本次環境中也曾安裝到：

```text
C:\Users\user\AppData\Roaming\Python\Python313\site-packages
```

這代表套件不完全位於 Anaconda 的環境內，進一步增加 DLL 載入風險。

## 解法

本專案改用專案本機虛擬環境：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

並將 `PySide6` 固定為已驗證可正常載入的版本：

```text
PySide6==6.8.3
```

驗證指令：

```powershell
.\.venv\Scripts\python.exe -c "from PySide6.QtWidgets import QApplication; print('PySide6 QtWidgets ok')"
```

成功時會看到：

```text
PySide6 QtWidgets ok
```

## 專案執行方式

不要直接使用：

```powershell
python -m app.main
```

請使用專案提供的批次檔：

```powershell
.\run_app.bat
```

此批次檔會固定使用：

```text
.venv\Scripts\python.exe
```

## 打包方式

請使用：

```powershell
.\build_exe.bat
```

此批次檔也會固定使用 `.venv` 內的 Python 與 PyInstaller：

```text
.venv\Scripts\python.exe -m PyInstaller
```

## 若重新建立環境

若 `.venv` 損壞或需要重建：

```powershell
rmdir /s /q .venv
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

重建後再次驗證：

```powershell
.\.venv\Scripts\python.exe -c "from PySide6.QtWidgets import QApplication; print('PySide6 QtWidgets ok')"
```

## 維護建議

- 不要把 `.venv/` commit 到 Git。
- 不要混用 Anaconda base environment 與使用者層級 `pip --user` 套件。
- 若要升級 `PySide6`，先在 `.venv` 中驗證 `QtWidgets` import 成功，再更新 `requirements.txt`。
- 若出現 DLL load failed，優先檢查目前使用的 Python：

```powershell
python -c "import sys; print(sys.executable)"
```
