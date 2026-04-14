# Learn Repo

分析一個 repo 或 codebase 的開發規範與風格，並更新個人設定檔（CLAUDE.md / rules）讓開發風格融入團隊。

## 執行步驟

### Phase 1：探索 codebase
並行蒐集以下資訊：
1. 讀取 repo 根目錄的設定檔：`pyproject.toml`、`setup.cfg`、`.flake8`、`ruff.toml`、`.eslintrc*`、`.prettierrc*`、`tsconfig.json`、`package.json`（scripts、dependencies）
2. 讀取 `README.md`、`CONTRIBUTING.md`、`DEVELOPMENT.md`（若存在）
3. 讀取既有的 `CLAUDE.md`、`.claude/rules/`（若存在）
4. 抽樣 5～10 個核心程式碼檔案，觀察：
   - 命名風格（snake_case / camelCase / PascalCase）
   - import 順序與分組方式
   - 函式長度與拆分習慣
   - 型別標注使用程度
   - error handling 方式
   - logging / print 使用習慣
   - 測試檔案結構與命名（`test_*.py`、`*.spec.ts` 等）

### Phase 2：歸納規律
整理發現的規範，分類為：
- **命名慣例**：變數、函式、class、檔案
- **程式碼風格**：縮排、行長、import 排序
- **架構習慣**：目錄結構、模組拆分方式
- **工具鏈**：linter、formatter、test runner、套件管理工具
- **Git 習慣**：branch 命名、commit message 格式（若 .git/COMMIT_EDITMSG 或 PR 範本存在）

### Phase 3：與現有設定比較
讀取 `~/.claude/CLAUDE.md` 與 `~/.claude/rules/` 現有內容，找出：
- 衝突點：新 repo 的規範與個人設定不同的地方
- 空缺：個人設定沒有涵蓋、但這個 repo 有明確規範的地方

### Phase 4：提出更新方案
列出建議的設定更新，並詢問使用者：
- 哪些要加入**全域**設定（~/.claude/）
- 哪些只加入**專案層級**設定（<repo>/.claude/）
- 哪些衝突要以新 repo 規範為優先

### Phase 5：寫入設定
依照使用者確認的範圍，更新對應檔案：
- 全域規範 → `~/.claude/CLAUDE.md` 或 `~/.claude/rules/<topic>.md`
- 專案規範 → `<repo>/.claude/CLAUDE.md` 或 `<repo>/.claude/rules/<topic>.md`

告知使用者每一個更動的位置與內容。

## 注意事項
- 不要主動覆蓋現有設定，衝突一律先詢問
- 如果 repo 沒有明確規範（只能從程式碼猜測），說明這是推測而非明文規定
- 優先讀取機器可讀的設定檔（linter config），其次才是從程式碼推斷
