# 個人全域設定

## 回覆語言
永遠使用**繁體中文**回覆，包含說明、提問、錯誤訊息解釋等。
程式碼內的變數名、註解可依專案慣例決定（不強制中文）。

## Python 環境
本機使用 venv 管理 Python 環境。執行任何 Python 相關指令時：
- 使用 `venv/bin/python`，不用系統 `python` 或 `python3`
- 使用 `venv/bin/pip`，不用系統 `pip`
- 啟動 FastAPI：`venv/bin/uvicorn main:app --reload`
- 執行腳本：`venv/bin/python script.py`

## Git Commit 風格
- 語言：英文
- 格式：動詞開頭，首字大寫，不加句號
- 長度：標題不超過 72 字
- 動詞範例：Add / Fix / Update / Remove / Refactor / Move / Rename

```
Add user authentication endpoint
Fix async CPU blocking in event loop
Update requirements to pin dependency versions
```

## 程式碼風格
- **變數命名**：一律使用小駝峰（camelCase），例如 `userName`、`totalCount`（包含 Python，優先於 PEP 8 的 snake_case）
- **簡潔優先**：不過度工程化，不為一次性操作建立抽象層
- **不加多餘 comment**：只在邏輯不直觀時才加說明
- **不加多餘 docstring**：除非使用者明確要求
- **不加型別標注**：只在修改的程式碼中才加，不幫整個檔案補
- **不加 error handling**：只在系統邊界（使用者輸入、外部 API）才加

## 檔案修改確認
在執行 Edit 或 Write 之前，必須先向使用者說明：
- 要改哪個檔案的哪個部分
- 改什麼、為什麼改
等使用者明確同意後才執行，不可自動直接修改。
