# Python 通用規範

## Type Hints
- 新增或修改的函式參數與回傳值要加 type hints
- 不需要替整個既有檔案補標注，只針對改動的部分


## Logging
- 使用 `logging.getLogger(__name__)` 取得 logger
- 不用 `print()` 做 debug 輸出
- log 格式遵循專案既有設定，不自行覆蓋 basicConfig

## HTTP 請求（requests 套件）
使用 `requests` 呼叫外部 API 時，必須：
1. 呼叫 `response.raise_for_status()` 捕捉 4xx / 5xx 錯誤
2. 設定 `timeout` 參數，並捕捉 `requests.exceptions.Timeout`

```python
import requests

try:
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
except requests.exceptions.Timeout:
    logger.error("Request timed out: %s", url)
    raise
except requests.exceptions.HTTPError as e:
    logger.error("HTTP error %s: %s", e.response.status_code, url)
    raise
```

## CLI 參數解析
- 腳本需要輸入參數時，一律使用 `argparse`，不用 `sys.argv` 直接存取
- 將解析邏輯封裝在獨立的 `parse_args()` 函式中
- 在 `if __name__ == "__main__":` 呼叫 `parse_args()`

```python
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="說明這個腳本的用途")
    parser.add_argument("--origin", type=str, required=True, help="參數說明")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
```