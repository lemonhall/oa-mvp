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
- 审批人（主管岗）：`approver / approver123`
- 财务（财务岗）：`finance / finance123`
- 员工：`employee / employee123`

数据库文件默认是仓库根目录的 `oa.db`（删掉后重启会重新初始化）。

## 功能（当前 MVP）

- 登录：账号密码 + JWT
- 公告：所有登录用户可看；admin 可发
- 申请：请假 / 报销（员工发起；自动分配一个审批人）
- 审批：支持多节点审批流；当前节点对应岗位的在职人员可审批
- 管理：admin 页面支持部门/用户/岗位管理、配置审批流、重置密码

## 升级提示（重要）

本项目目前没有迁移脚本；如果你拉取更新后出现列/表不一致，直接删除旧的 `oa.db` 再启动即可重建。

## 环境变量（可选）

- `OA_SECRET_KEY`：JWT 密钥（生产环境务必修改）
- `OA_DB_URL`：数据库地址（默认 `sqlite:///./oa.db`）
- `OA_CORS_ORIGINS`：CORS 白名单（逗号分隔）
