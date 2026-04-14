---
paths:
  - "requirements*.txt"
  - "pyproject.toml"
---

# Python 套件依賴規範

建立或修改 requirements 檔案時，必須遵守以下規則：

## 版本釘定
- 所有套件必須釘死完整版本號，格式：`package==x.y.z`
- 禁止使用 `>=`、`~=`、`>`、留空等不確定版本
- 正確範例：`fastapi==0.115.0`
- 錯誤範例：`fastapi>=0.100.0`、`fastapi`

## 版本確認流程
1. 用 `venv/bin/pip index versions <package>` 確認版本存在
2. 選擇最新的穩定版本（非 alpha/beta/rc）

## Vulnerability 檢查
1. 寫完 requirements.txt 後，執行 `venv/bin/pip audit` 檢查
2. 如有 known vulnerability：
   - 找出最近的無漏洞版本
   - 改用該版本並在旁邊加上 comment 說明原因
   - 範例：`package==x.y.z  # x.y.(z+1) has CVE-XXXX-XXXX`
3. 如果 `pip audit` 不存在，改用 `venv/bin/pip install pip-audit && venv/bin/pip-audit`
