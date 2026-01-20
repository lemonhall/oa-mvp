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
- 人事（人事岗）：`hr / hr123456`
- 总经理（总经理岗）：`ceo / ceo123456`
- 法务（法务岗）：`legal / legal123456`
- 采购（采购岗）：`procurement / procurement123456`
- 行政（行政岗）：`admin_affairs / adminaffairs123456`
- IT（IT岗）：`it / it123456`
- 员工：`employee / employee123`

数据库文件默认是仓库根目录的 `oa.db`（删掉后重启会重新初始化）。

## 功能（当前 MVP）

- 登录：账号密码 + JWT
- 公告：所有登录用户可看；admin 可发
- 申请：支持多种申请类型（动态表单）；每种类型绑定一个启用的审批流
- 审批：支持多节点审批流；当前节点对应岗位的在职人员可审批
- 管理：admin 页面支持部门/用户/岗位管理、配置审批流、重置密码

## 内置申请类型（可扩展）

内置了常见 OA 类型：请假、报销、出差、加班、采购、付款、用章、合同、预算、借款、招聘、人事异动、资产、项目、开票、权限开通。

## 升级提示（重要）

本项目目前没有迁移脚本；如果你拉取更新后出现列/表不一致，直接删除旧的 `oa.db` 再启动即可重建。

## 环境变量（可选）

- `OA_SECRET_KEY`：JWT 密钥（生产环境务必修改）
- `OA_DB_URL`：数据库地址（默认 `sqlite:///./oa.db`）
- `OA_CORS_ORIGINS`：CORS 白名单（逗号分隔）
