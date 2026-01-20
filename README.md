# OA (MVP)

前端：原生 HTML + JS（AJAX / fetch）

后端：Python FastAPI + SQLite + JWT（用 `uv` 管理依赖）

## 本地运行

前置：Python 3.10+，已安装 `uv`

```bash
uv venv
uv pip install -e .
uv run uvicorn backend.app.main:app --reload
```

打开：`http://127.0.0.1:8000/`

## 默认账号（首次启动会自动初始化到 SQLite）

- 管理员：`admin / admin123`
- 审批人：`approver / approver123`
- 员工：`employee / employee123`

数据库文件默认是仓库根目录的 `oa.db`（删掉后重启会重新初始化）。

## 环境变量（可选）

- `OA_SECRET_KEY`：JWT 密钥（生产环境务必修改）
- `OA_DB_URL`：数据库地址（默认 `sqlite:///./oa.db`）
- `OA_CORS_ORIGINS`：CORS 白名单（逗号分隔）
