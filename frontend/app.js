import { api, clearToken, getToken, setToken } from "./api.js";

const appEl = document.getElementById("app");
const userBarEl = document.getElementById("userBar");
const meTextEl = document.getElementById("meText");
const logoutBtn = document.getElementById("logoutBtn");

let PROCESS_TYPES = [];
let PROCESS_BY_CODE = new Map();

const TYPE_LABEL = {
  leave: "请假",
  reimburse: "报销",
};

const STATUS_LABEL = {
  pending: "待审批",
  approved: "已同意",
  rejected: "已驳回",
};

const NODE_STATUS_LABEL = {
  not_started: "未开始",
  pending: "待审批",
  approved: "已同意",
  rejected: "已驳回",
};

function labelType(type) {
  return PROCESS_BY_CODE.get(type)?.name || TYPE_LABEL[type] || type || "";
}

function labelStatus(status) {
  return STATUS_LABEL[status] || status || "";
}

function labelNodeStatus(status) {
  return NODE_STATUS_LABEL[status] || status || "";
}

async function ensureProcessTypes() {
  if (PROCESS_TYPES.length) return;
  try {
    const items = await api.listProcessTypes();
    PROCESS_TYPES = Array.isArray(items) ? items : [];
    PROCESS_BY_CODE = new Map(PROCESS_TYPES.map((p) => [p.code, p]));
  } catch {
    PROCESS_TYPES = [
      { code: "leave", name: "请假", requires_amount: false, fields: [] },
      { code: "reimburse", name: "报销", requires_amount: true, fields: [] },
    ];
    PROCESS_BY_CODE = new Map(PROCESS_TYPES.map((p) => [p.code, p]));
  }
}

logoutBtn.addEventListener("click", () => {
  clearToken();
  location.hash = "#/login";
  render();
});

function el(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}

function setUserBar(me) {
  if (!me) {
    userBarEl.classList.add("hidden");
    meTextEl.textContent = "";
    return;
  }
  userBarEl.classList.remove("hidden");
  meTextEl.textContent = `${me.username}（${me.role}）`;
}

function showError(container, err) {
  const msg = err?.message || String(err);
  container.querySelector(".error")?.remove();
  const e = el(`<div class="error"></div>`);
  e.textContent = msg;
  container.appendChild(e);
}

function nav(me) {
  const items = [
    { hash: "#/dashboard", label: "首页" },
    { hash: "#/requests", label: "我的申请" },
    { hash: "#/new-request", label: "发起申请" },
    { hash: "#/approvals", label: "待我审批" },
  ];
  if (me?.role === "admin") {
    items.push({ hash: "#/admin", label: "管理" });
  }

  const bar = el(`<div class="toolbar"></div>`);
  for (const it of items) {
    const b = el(`<button class="btn btn-secondary"></button>`);
    b.textContent = it.label;
    b.addEventListener("click", () => {
      location.hash = it.hash;
      render();
    });
    bar.appendChild(b);
  }
  return bar;
}

async function renderLogin() {
  const root = el(`
    <div>
      <div class="section-title">登录（默认账号：admin / admin123）</div>
      <div class="row">
        <div>
          <input id="username" class="input" placeholder="用户名" />
        </div>
        <div>
          <input id="password" class="input" placeholder="密码" type="password" />
        </div>
      </div>
      <div style="margin-top: 12px; display: flex; gap: 10px;">
        <button id="loginBtn" class="btn btn-primary">登录</button>
      </div>
    </div>
  `);

  const usernameEl = root.querySelector("#username");
  const passwordEl = root.querySelector("#password");
  const btn = root.querySelector("#loginBtn");

  btn.addEventListener("click", async () => {
    try {
      const r = await api.login(usernameEl.value.trim(), passwordEl.value);
      setToken(r.access_token);
      location.hash = "#/dashboard";
      await render();
    } catch (err) {
      showError(root, err);
    }
  });

  appEl.replaceChildren(root);
  setUserBar(null);
}

async function renderDashboard(me) {
  const root = el(`<div></div>`);
  root.appendChild(nav(me));

  await ensureProcessTypes();

  const annWrap = el(`<div><div class="section-title">公告</div><div class="list" id="annList"></div></div>`);
  root.appendChild(annWrap);

  try {
    const anns = await api.listAnnouncements();
    const listEl = annWrap.querySelector("#annList");
    if (anns.length === 0) {
      listEl.appendChild(el(`<div class="muted">暂无公告</div>`));
    } else {
      for (const a of anns) {
        const item = el(`<div class="item"><div class="item-title"></div><div class="muted"></div></div>`);
        item.querySelector(".item-title").textContent = a.title;
        item.querySelector(".muted").textContent = a.content || "";
        listEl.appendChild(item);
      }
    }
  } catch (err) {
    showError(annWrap, err);
  }

  appEl.replaceChildren(root);
}

async function renderMyRequests(me) {
  const root = el(`<div></div>`);
  root.appendChild(nav(me));

  const wrap = el(`<div><div class="section-title">我的申请</div><div class="list" id="list"></div></div>`);
  root.appendChild(wrap);

  try {
    const items = await api.listMyRequests();
    const listEl = wrap.querySelector("#list");
    if (items.length === 0) {
      listEl.appendChild(el(`<div class="muted">暂无申请</div>`));
    } else {
      for (const r of items) {
        const item = el(`<div class="item"></div>`);
        const head = el(`<div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;"></div>`);
        const title = el(`<div class="item-title" style="flex:1;"></div>`);
        title.textContent = `【${labelType(r.type)}】${r.title} — ${labelStatus(r.status)}`;
        const btn = el(`<button class="btn btn-secondary">详情</button>`);
        btn.addEventListener("click", () => {
          location.hash = `#/request/${r.id}`;
          render();
        });
        head.appendChild(title);
        head.appendChild(btn);
        item.appendChild(head);
        const c = el(`<div class="muted"></div>`);
        c.textContent = r.content || "";
        item.appendChild(c);
        listEl.appendChild(item);
      }
    }
  } catch (err) {
    showError(wrap, err);
  }

  appEl.replaceChildren(root);
}

async function renderRequestDetail(me, requestId) {
  const root = el(`<div></div>`);
  root.appendChild(nav(me));

  await ensureProcessTypes();

  const wrap = el(`<div><div class="section-title">申请详情</div></div>`);
  root.appendChild(wrap);

  const box = el(`<div class="item"></div>`);
  wrap.appendChild(box);

  try {
    const detail = await api.requestDetail(requestId);
    const r = detail.request;

    const head = el(`<div></div>`);
    const title = el(`<div class="item-title"></div>`);
    title.textContent = `【${labelType(r.type)}】${r.title} — ${labelStatus(r.status)}`;
    const meta = el(`<div class="muted"></div>`);
    meta.textContent = `申请类型：${detail.process_name || labelType(r.type)} | 审批流程：${detail.workflow_name || "（未配置）"} | 单号：${r.id}`;
    head.appendChild(title);
    head.appendChild(meta);

    if (r.amount != null) {
      const amt = el(`<div class="pill">金额：<span class="mono"></span></div>`);
      amt.querySelector(".mono").textContent = String(r.amount);
      head.appendChild(amt);
    }
    if (r.content) {
      const c = el(`<div style="margin-top:10px;" class="muted"></div>`);
      c.textContent = r.content;
      head.appendChild(c);
    }
    box.appendChild(head);

    const formData = detail.form_data || {};
    const p = PROCESS_BY_CODE.get(r.type);
    const fields = Array.isArray(p?.fields) ? p.fields : [];
    const formBox = el(`<div style="margin-top:12px;"></div>`);
    formBox.appendChild(el(`<div class="section-title">表单信息</div>`));
    if (!fields.length) {
      formBox.appendChild(el(`<div class="muted">（无额外表单字段）</div>`));
    } else {
      const t = el(
        `<table class="table"><thead><tr><th>字段</th><th>值</th></tr></thead><tbody></tbody></table>`
      );
      const tbody = t.querySelector("tbody");
      for (const f of fields) {
        const tr = el(`<tr><td></td><td class="mono"></td></tr>`);
        tr.children[0].textContent = f.label;
        tr.children[1].textContent = formData?.[f.key] != null ? String(formData[f.key]) : "";
        tbody.appendChild(tr);
      }
      formBox.appendChild(t);
    }
    box.appendChild(formBox);

    const flow = el(`<div style="margin-top:12px;"></div>`);
    flow.appendChild(el(`<div class="section-title">需要哪些岗位审批 / 当前状态</div>`));
    if (!detail.nodes || detail.nodes.length === 0) {
      flow.appendChild(el(`<div class="muted">暂无节点</div>`));
    } else {
      const t = el(
        `<table class="table"><thead><tr><th>顺序</th><th>岗位</th><th>节点</th><th>状态</th><th>审批人</th><th>审批时间</th></tr></thead><tbody></tbody></table>`
      );
      const tbody = t.querySelector("tbody");
      for (const n of detail.nodes) {
        const tr = el(
          `<tr><td class="mono"></td><td></td><td></td><td></td><td class="mono"></td><td class="mono"></td></tr>`
        );
        tr.children[0].textContent = String(n.step_order);
        tr.children[1].textContent = `${n.position_name} (#${n.position_id})`;
        tr.children[2].textContent = n.node_name || "";
        tr.children[3].textContent = labelNodeStatus(n.status);
        tr.children[4].textContent = n.decided_by_username || "";
        tr.children[5].textContent = n.decided_at ? String(n.decided_at) : "";
        tbody.appendChild(tr);
      }
      flow.appendChild(t);
    }

    const canDecide =
      me?.role === "admin" ||
      (r.status === "pending" &&
        !!me?.position_id &&
        Array.isArray(detail.nodes) &&
        detail.nodes.some((n) => n.status === "pending" && n.position_id === me.position_id));

    if (r.status === "pending" && canDecide) {
      const actions = el(
        `<div style="margin-top: 10px; display: flex; gap: 10px; flex-wrap: wrap;">
          <input class="input" style="max-width: 420px;" placeholder="审批意见（可选）" />
          <button class="btn btn-primary">同意</button>
          <button class="btn btn-danger">驳回</button>
        </div>`
      );
      const commentEl = actions.querySelector("input");
      const okBtn = actions.querySelector(".btn-primary");
      const noBtn = actions.querySelector(".btn-danger");
      okBtn.addEventListener("click", async () => {
        try {
          await api.decide(r.id, "approved", commentEl.value.trim());
          await render();
        } catch (err) {
          showError(box, err);
        }
      });
      noBtn.addEventListener("click", async () => {
        try {
          await api.decide(r.id, "rejected", commentEl.value.trim());
          await render();
        } catch (err) {
          showError(box, err);
        }
      });
      flow.appendChild(actions);
    }

    box.appendChild(flow);

    const hist = el(`<div style="margin-top:12px;"></div>`);
    hist.appendChild(el(`<div class="section-title">审批记录（时间/意见）</div>`));
    if (!detail.history || detail.history.length === 0) {
      hist.appendChild(el(`<div class="muted">暂无记录</div>`));
    } else {
      const t = el(
        `<table class="table"><thead><tr><th>ID</th><th>节点</th><th>岗位</th><th>审批人</th><th>决策</th><th>时间</th><th>意见</th></tr></thead><tbody></tbody></table>`
      );
      const tbody = t.querySelector("tbody");
      for (const h of detail.history) {
        const tr = el(
          `<tr><td class="mono"></td><td></td><td></td><td class="mono"></td><td></td><td class="mono"></td><td></td></tr>`
        );
        tr.children[0].textContent = String(h.id);
        tr.children[1].textContent = h.step_order != null ? `${h.step_order}. ${h.node_name || ""}` : "";
        tr.children[2].textContent = h.position_name ? `${h.position_name} (#${h.position_id})` : "";
        tr.children[3].textContent = h.approver_username;
        tr.children[4].textContent = labelStatus(h.decision);
        tr.children[5].textContent = String(h.decided_at);
        tr.children[6].textContent = h.comment || "";
        tbody.appendChild(tr);
      }
      hist.appendChild(t);
    }
    box.appendChild(hist);
  } catch (err) {
    showError(box, err);
  }

  appEl.replaceChildren(root);
}

async function renderNewRequest(me) {
  const root = el(`<div></div>`);
  root.appendChild(nav(me));

  await ensureProcessTypes();

  const form = el(`
    <div>
      <div class="section-title">发起申请</div>
      <div class="row">
        <div>
          <select id="type" class="input"></select>
        </div>
        <div>
          <input id="title" class="input" placeholder="标题" />
        </div>
      </div>
      <div style="margin-top: 12px;" id="dynamicFields"></div>
      <div style="margin-top: 12px;" id="amountWrap" class="hidden">
        <input id="amount" class="input" placeholder="金额（必填）" />
      </div>
      <div style="margin-top: 12px;">
        <textarea id="content" placeholder="内容说明（可选）"></textarea>
      </div>
      <div style="margin-top: 12px; display: flex; gap: 10px;">
        <button id="submitBtn" class="btn btn-primary">提交</button>
      </div>
    </div>
  `);

  const typeEl = form.querySelector("#type");
  const titleEl = form.querySelector("#title");
  const amountEl = form.querySelector("#amount");
  const amountWrapEl = form.querySelector("#amountWrap");
  const contentEl = form.querySelector("#content");
  const submitBtn = form.querySelector("#submitBtn");
  const fieldsWrap = form.querySelector("#dynamicFields");

  function renderFields() {
    fieldsWrap.replaceChildren();
    const p = PROCESS_BY_CODE.get(typeEl.value);
    if (!p) return;

    amountWrapEl.classList.toggle("hidden", !p.requires_amount);
    if (!p.requires_amount) amountEl.value = "";

    const fields = Array.isArray(p.fields) ? p.fields : [];
    if (!fields.length) return;

    const grid = el(`<div class="row"></div>`);
    for (const f of fields) {
      const cell = el(`<div></div>`);
      const label = el(`<div class="section-title"></div>`);
      label.textContent = `${f.label}${f.required ? "（必填）" : ""}`;
      cell.appendChild(label);

      let input;
      if (f.type === "textarea") {
        input = el(`<textarea data-field-key="${f.key}" placeholder="${f.label}"></textarea>`);
      } else if (f.type === "number") {
        input = el(`<input class="input" data-field-key="${f.key}" type="number" placeholder="${f.label}" />`);
      } else if (f.type === "date") {
        input = el(`<input class="input" data-field-key="${f.key}" type="date" />`);
      } else if (f.type === "datetime") {
        input = el(`<input class="input" data-field-key="${f.key}" type="datetime-local" />`);
      } else if (f.type === "select") {
        input = el(`<select class="input" data-field-key="${f.key}"></select>`);
        input.appendChild(el(`<option value="">请选择</option>`));
        for (const opt of f.options || []) {
          const o = el(`<option></option>`);
          o.value = opt;
          o.textContent = opt;
          input.appendChild(o);
        }
      } else {
        input = el(`<input class="input" data-field-key="${f.key}" placeholder="${f.label}" />`);
      }

      cell.appendChild(input);
      grid.appendChild(cell);
    }
    fieldsWrap.appendChild(grid);
  }

  typeEl.replaceChildren();
  if (PROCESS_TYPES.length === 0) {
    typeEl.appendChild(el(`<option value="leave">请假</option>`));
    typeEl.appendChild(el(`<option value="reimburse">报销</option>`));
  } else {
    for (const p of PROCESS_TYPES) {
      const o = el(`<option></option>`);
      o.value = p.code;
      o.textContent = p.name;
      typeEl.appendChild(o);
    }
  }
  typeEl.addEventListener("change", renderFields);
  renderFields();

  submitBtn.addEventListener("click", async () => {
    try {
      const p = PROCESS_BY_CODE.get(typeEl.value) || {};
      const data = {};
      for (const elx of fieldsWrap.querySelectorAll("[data-field-key]")) {
        const key = elx.getAttribute("data-field-key");
        if (!key) continue;
        data[key] = elx.value;
      }

      const payload = {
        type: typeEl.value,
        title: titleEl.value.trim(),
        content: contentEl.value.trim(),
        amount: p.requires_amount ? Number(amountEl.value || "") : null,
        data,
      };
      if (p.requires_amount && (!amountEl.value || Number.isNaN(payload.amount))) {
        throw new Error("请输入有效金额");
      }
      await api.createRequest(payload);
      location.hash = "#/requests";
      await render();
    } catch (err) {
      showError(form, err);
    }
  });

  root.appendChild(form);
  appEl.replaceChildren(root);
}

async function renderApprovals(me) {
  const root = el(`<div></div>`);
  root.appendChild(nav(me));

  await ensureProcessTypes();

  const wrap = el(`<div><div class="section-title">待我审批</div><div class="list" id="list"></div></div>`);
  root.appendChild(wrap);

  try {
    const items = await api.listPendingApprovals();
    const listEl = wrap.querySelector("#list");
    if (items.length === 0) {
      listEl.appendChild(el(`<div class="muted">暂无待审批</div>`));
    } else {
      for (const r of items) {
        const item = el(`
          <div class="item">
            <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
              <div class="item-title" style="flex:1;"></div>
              <button class="btn btn-secondary">详情</button>
            </div>
            <div class="muted"></div>
            <div style="margin-top: 10px; display: flex; gap: 10px; flex-wrap: wrap;">
              <input class="input" style="max-width: 420px;" placeholder="审批意见（可选）" />
              <button class="btn btn-primary">同意</button>
              <button class="btn btn-danger">驳回</button>
            </div>
          </div>
        `);
        item.querySelector(".item-title").textContent = `【${labelType(r.type)}】${r.title}`;
        item.querySelector(".muted").textContent = r.content || "";
        item.querySelector(".btn.btn-secondary").addEventListener("click", () => {
          location.hash = `#/request/${r.id}`;
          render();
        });

        const commentEl = item.querySelector("input");
        const okBtn = item.querySelector(".btn-primary");
        const noBtn = item.querySelector(".btn-danger");

        okBtn.addEventListener("click", async () => {
          try {
            await api.decide(r.id, "approved", commentEl.value.trim());
            await render();
          } catch (err) {
            showError(item, err);
          }
        });
        noBtn.addEventListener("click", async () => {
          try {
            await api.decide(r.id, "rejected", commentEl.value.trim());
            await render();
          } catch (err) {
            showError(item, err);
          }
        });

        listEl.appendChild(item);
      }
    }
  } catch (err) {
    showError(wrap, err);
  }

  appEl.replaceChildren(root);
}

async function renderAdmin(me) {
  const root = el(`<div></div>`);
  root.appendChild(nav(me));

  const container = el(`<div></div>`);
  container.appendChild(el(`<div class="section-title">管理（仅 admin）</div>`));

  const announce = el(`
    <div class="item">
      <div class="item-title">发布公告</div>
      <div class="row" style="margin-top: 10px;">
        <div><input id="annTitle" class="input" placeholder="公告标题" /></div>
        <div><input id="annContent" class="input" placeholder="公告内容（简短）" /></div>
      </div>
      <div style="margin-top: 10px;">
        <button id="publish" class="btn btn-primary">发布</button>
      </div>
    </div>
  `);
  announce.querySelector("#publish").addEventListener("click", async () => {
    try {
      const title = announce.querySelector("#annTitle").value.trim();
      const content = announce.querySelector("#annContent").value.trim();
      await api.createAnnouncement(title, content);
      location.hash = "#/dashboard";
      await render();
    } catch (err) {
      showError(announce, err);
    }
  });
  container.appendChild(announce);

  const posBox = el(`
    <div class="item">
      <div class="item-title">岗位（用于审批流节点）</div>
      <div style="margin-top: 10px; display: flex; gap: 10px; flex-wrap: wrap;">
        <input id="posName" class="input" style="max-width: 240px;" placeholder="岗位名称" />
        <input id="posDesc" class="input" style="max-width: 380px;" placeholder="描述（可选）" />
        <button id="posCreate" class="btn btn-primary">新增岗位</button>
      </div>
      <div style="margin-top: 10px;" id="posList"></div>
    </div>
  `);
  async function refreshPositions() {
    const listEl = posBox.querySelector("#posList");
    listEl.replaceChildren();
    try {
      const items = await api.listPositions();
      if (items.length === 0) {
        listEl.appendChild(el(`<div class="muted">暂无岗位</div>`));
        return;
      }
      const t = el(
        `<table class="table"><thead><tr><th>ID</th><th>名称</th><th>描述</th></tr></thead><tbody></tbody></table>`
      );
      const tbody = t.querySelector("tbody");
      for (const p of items) {
        const tr = el(`<tr><td class="mono"></td><td></td><td class="muted"></td></tr>`);
        tr.children[0].textContent = String(p.id);
        tr.children[1].textContent = p.name;
        tr.children[2].textContent = p.description || "";
        tbody.appendChild(tr);
      }
      listEl.appendChild(t);
    } catch (err) {
      showError(posBox, err);
    }
  }
  posBox.querySelector("#posCreate").addEventListener("click", async () => {
    try {
      const name = posBox.querySelector("#posName").value.trim();
      const description = posBox.querySelector("#posDesc").value.trim();
      await api.createPosition({ name, description });
      posBox.querySelector("#posName").value = "";
      posBox.querySelector("#posDesc").value = "";
      await refreshPositions();
    } catch (err) {
      showError(posBox, err);
    }
  });
  container.appendChild(posBox);

  const flowBox = el(`
    <div class="item">
      <div class="item-title">审批流</div>
      <div class="pill">每个节点绑定一个岗位；同一类型只启用一个审批流（切换启用会自动关闭其他）</div>
      <div class="row" style="margin-top: 10px;">
        <div><input id="wfName" class="input" placeholder="审批流名称（唯一）" /></div>
        <div>
          <select id="wfType" class="input"></select>
        </div>
      </div>
      <div style="margin-top: 10px; display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
        <label class="pill" style="cursor:pointer;">
          <input id="wfActive" type="checkbox" checked />
          <span>启用</span>
        </label>
        <button id="wfCreate" class="btn btn-primary">新建审批流</button>
      </div>
      <div style="margin-top: 12px;" id="wfList"></div>
    </div>
  `);

  async function refreshWorkflows() {
    const listEl = flowBox.querySelector("#wfList");
    listEl.replaceChildren();
    try {
      await ensureProcessTypes();
      const [workflows, positions] = await Promise.all([api.listWorkflows(), api.listPositions()]);
      const posNameById = new Map(positions.map((p) => [p.id, p.name]));

      const wfTypeSel = flowBox.querySelector("#wfType");
      if (wfTypeSel && wfTypeSel.options.length === 0) {
        wfTypeSel.appendChild(el(`<option value="">选择申请类型</option>`));
        for (const p of PROCESS_TYPES) {
          const o = el(`<option></option>`);
          o.value = p.code;
          o.textContent = p.name;
          wfTypeSel.appendChild(o);
        }
      }

      if (workflows.length === 0) {
        listEl.appendChild(el(`<div class="muted">暂无审批流</div>`));
        return;
      }

      for (const wf of workflows) {
        const item = el(`<div class="item"></div>`);
        const header = el(`
          <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
            <div class="pill"><span class="mono">#${wf.id}</span></div>
            <div style="font-weight:600;"></div>
            <div class="pill">类型：<span class="mono" data-wf-type></span></div>
            <div class="spacer"></div>
            <label class="pill" style="cursor:pointer;">
              <input type="checkbox" />
              <span>启用</span>
            </label>
          </div>
        `);
        header.children[1].textContent = wf.name;
        header.querySelector("[data-wf-type]").textContent = labelType(wf.request_type);
        const activeCb = header.querySelector('input[type="checkbox"]');
        activeCb.checked = !!wf.is_active;
        activeCb.addEventListener("change", async () => {
          try {
            await api.updateWorkflow(wf.id, { is_active: activeCb.checked });
            await refreshWorkflows();
          } catch (err) {
            showError(flowBox, err);
          }
        });
        item.appendChild(header);

        const nodesWrap = el(`<div style="margin-top: 10px;"></div>`);
        if (!wf.nodes || wf.nodes.length === 0) {
          nodesWrap.appendChild(el(`<div class="muted">该审批流暂无节点（请求将无法发起）</div>`));
        } else {
          const t = el(
            `<table class="table"><thead><tr><th>顺序</th><th>岗位</th><th>节点名</th><th>操作</th></tr></thead><tbody></tbody></table>`
          );
          const tbody = t.querySelector("tbody");
          for (const n of wf.nodes) {
            const tr = el(`<tr><td class="mono"></td><td></td><td></td><td></td></tr>`);
            tr.children[0].textContent = String(n.step_order);
            tr.children[1].textContent = `${posNameById.get(n.position_id) || "未知"} (#${n.position_id})`;
            tr.children[2].textContent = n.name || "";
            const delBtn = el(`<button class="btn btn-danger">删除</button>`);
            delBtn.addEventListener("click", async () => {
              if (!confirm("确认删除该节点？")) return;
              try {
                await api.deleteWorkflowNode(wf.id, n.id);
                await refreshWorkflows();
              } catch (err) {
                showError(flowBox, err);
              }
            });
            tr.children[3].appendChild(delBtn);
            tbody.appendChild(tr);
          }
          nodesWrap.appendChild(t);
        }
        item.appendChild(nodesWrap);

        const addForm = el(`
          <div style="margin-top: 10px; display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
            <input class="input" style="max-width:120px;" placeholder="顺序(1..)" />
            <select class="input" style="min-width:180px;"></select>
            <input class="input" style="min-width:220px;" placeholder="节点名（可选）" />
            <button class="btn btn-secondary">新增节点</button>
          </div>
        `);
        const orderEl = addForm.querySelector("input");
        const posSel = addForm.querySelector("select");
        const nameEl = addForm.querySelectorAll("input")[1];
        posSel.appendChild(el(`<option value="">选择岗位</option>`));
        for (const p of positions) {
          const o = el(`<option></option>`);
          o.value = String(p.id);
          o.textContent = `${p.name} (#${p.id})`;
          posSel.appendChild(o);
        }
        addForm.querySelector("button").addEventListener("click", async () => {
          try {
            const step_order = Number(orderEl.value || "0");
            const position_id = Number(posSel.value || "0");
            const name = nameEl.value.trim();
            await api.addWorkflowNode(wf.id, { step_order, position_id, name });
            orderEl.value = "";
            posSel.value = "";
            nameEl.value = "";
            await refreshWorkflows();
          } catch (err) {
            showError(flowBox, err);
          }
        });
        item.appendChild(addForm);

        listEl.appendChild(item);
      }
    } catch (err) {
      showError(flowBox, err);
    }
  }

  flowBox.querySelector("#wfCreate").addEventListener("click", async () => {
    try {
      const name = flowBox.querySelector("#wfName").value.trim();
      const request_type = flowBox.querySelector("#wfType").value;
      const is_active = !!flowBox.querySelector("#wfActive").checked;
      if (!request_type) throw new Error("请选择申请类型");
      await api.createWorkflow({ name, request_type, is_active });
      flowBox.querySelector("#wfName").value = "";
      await refreshWorkflows();
    } catch (err) {
      showError(flowBox, err);
    }
  });
  container.appendChild(flowBox);

  const deptBox = el(`
    <div class="item">
      <div class="item-title">部门</div>
      <div style="margin-top: 10px; display: flex; gap: 10px; flex-wrap: wrap;">
        <input id="deptName" class="input" style="max-width: 320px;" placeholder="部门名称" />
        <button id="deptCreate" class="btn btn-primary">新增部门</button>
      </div>
      <div style="margin-top: 10px;" id="deptList"></div>
    </div>
  `);
  async function refreshDepts() {
    const listEl = deptBox.querySelector("#deptList");
    listEl.replaceChildren();
    try {
      const depts = await api.listDepts();
      if (depts.length === 0) {
        listEl.appendChild(el(`<div class="muted">暂无部门</div>`));
        return;
      }
      const t = el(`<table class="table"><thead><tr><th>ID</th><th>名称</th></tr></thead><tbody></tbody></table>`);
      const tbody = t.querySelector("tbody");
      for (const d of depts) {
        const tr = el(`<tr><td class="mono"></td><td></td></tr>`);
        tr.children[0].textContent = String(d.id);
        tr.children[1].textContent = d.name;
        tbody.appendChild(tr);
      }
      listEl.appendChild(t);
    } catch (err) {
      showError(deptBox, err);
    }
  }
  deptBox.querySelector("#deptCreate").addEventListener("click", async () => {
    try {
      const name = deptBox.querySelector("#deptName").value.trim();
      await api.createDept(name);
      deptBox.querySelector("#deptName").value = "";
      await refreshDepts();
    } catch (err) {
      showError(deptBox, err);
    }
  });
  container.appendChild(deptBox);

  const userBox = el(`
    <div class="item">
      <div class="item-title">用户</div>
      <div class="pill">提示：可创建用户、设置角色/部门、重置密码</div>
      <div class="row" style="margin-top: 10px;">
        <div><input id="uUsername" class="input" placeholder="用户名" /></div>
        <div><input id="uFullName" class="input" placeholder="姓名（可选）" /></div>
      </div>
      <div class="row" style="margin-top: 10px;">
        <div>
          <select id="uRole" class="input">
            <option value="employee">employee</option>
            <option value="approver">approver</option>
            <option value="admin">admin</option>
          </select>
        </div>
        <div><select id="uDept" class="input"></select></div>
      </div>
      <div style="margin-top: 10px;">
        <select id="uPos" class="input"></select>
      </div>
      <div style="margin-top: 10px;">
        <input id="uPassword" class="input" placeholder="初始密码（>=6位）" type="password" />
      </div>
      <div style="margin-top: 10px;">
        <button id="uCreate" class="btn btn-primary">创建用户</button>
      </div>
      <div style="margin-top: 12px;" id="userList"></div>
    </div>
  `);

  async function refreshUserAuxIntoSelects() {
    const deptSel = userBox.querySelector("#uDept");
    deptSel.replaceChildren();
    deptSel.appendChild(el(`<option value="">（无部门）</option>`));
    const posSel = userBox.querySelector("#uPos");
    posSel.replaceChildren();
    posSel.appendChild(el(`<option value="">（无岗位）</option>`));

    const [depts, positions] = await Promise.all([api.listDepts(), api.listPositions()]);
    for (const d of depts) {
      const o = el(`<option></option>`);
      o.value = String(d.id);
      o.textContent = `${d.name} (#${d.id})`;
      deptSel.appendChild(o);
    }
    for (const p of positions) {
      const o = el(`<option></option>`);
      o.value = String(p.id);
      o.textContent = `${p.name} (#${p.id})`;
      posSel.appendChild(o);
    }
  }

  async function refreshUsers() {
    const listEl = userBox.querySelector("#userList");
    listEl.replaceChildren();
    try {
      const [users, depts, positions] = await Promise.all([
        api.listUsers(),
        api.listDepts(),
        api.listPositions(),
      ]);
      const deptNameById = new Map(depts.map((d) => [d.id, d.name]));
      const posNameById = new Map(positions.map((p) => [p.id, p.name]));

      if (users.length === 0) {
        listEl.appendChild(el(`<div class="muted">暂无用户</div>`));
        return;
      }

      const t = el(`
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>用户名</th>
              <th>姓名</th>
              <th>角色</th>
              <th>部门</th>
              <th>岗位</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      `);
      const tbody = t.querySelector("tbody");

      for (const u of users) {
        const tr = el(`<tr></tr>`);
        tr.appendChild(el(`<td class="mono">${u.id}</td>`));
        tr.appendChild(el(`<td class="mono"></td>`));
        tr.children[1].textContent = u.username;
        tr.appendChild(el(`<td></td>`));
        tr.children[2].textContent = u.full_name || "";

        const roleTd = el(`<td></td>`);
        const roleSel = el(`
          <select class="input" style="min-width: 120px;">
            <option value="employee">employee</option>
            <option value="approver">approver</option>
            <option value="admin">admin</option>
          </select>
        `);
        roleSel.value = u.role;
        roleTd.appendChild(roleSel);
        tr.appendChild(roleTd);

        const deptTd = el(`<td></td>`);
        const deptSel = el(`<select class="input" style="min-width: 160px;"></select>`);
        deptSel.appendChild(el(`<option value="">（无）</option>`));
        for (const d of depts) {
          const o = el(`<option></option>`);
          o.value = String(d.id);
          o.textContent = d.name;
          deptSel.appendChild(o);
        }
        deptSel.value = u.department_id ? String(u.department_id) : "";
        deptTd.appendChild(deptSel);
        tr.appendChild(deptTd);

        const posTd = el(`<td></td>`);
        const posSel = el(`<select class="input" style="min-width: 160px;"></select>`);
        posSel.appendChild(el(`<option value="">（无）</option>`));
        for (const p of positions) {
          const o = el(`<option></option>`);
          o.value = String(p.id);
          o.textContent = p.name;
          posSel.appendChild(o);
        }
        posSel.value = u.position_id ? String(u.position_id) : "";
        posTd.appendChild(posSel);
        tr.appendChild(posTd);

        const activeTd = el(`<td></td>`);
        const activeSel = el(`
          <select class="input" style="min-width: 110px;">
            <option value="true">active</option>
            <option value="false">disabled</option>
          </select>
        `);
        activeSel.value = u.is_active ? "true" : "false";
        activeTd.appendChild(activeSel);
        tr.appendChild(activeTd);

        const opsTd = el(`<td></td>`);
        const saveBtn = el(`<button class="btn btn-secondary">保存</button>`);
        const pwdBtn = el(`<button class="btn btn-secondary">重置密码</button>`);
        opsTd.appendChild(el(`<div style="display:flex; gap:8px; flex-wrap:wrap;"></div>`));
        opsTd.firstElementChild.appendChild(saveBtn);
        opsTd.firstElementChild.appendChild(pwdBtn);
        tr.appendChild(opsTd);

        saveBtn.addEventListener("click", async () => {
          try {
            await api.updateUser(u.id, {
              role: roleSel.value,
              department_id: deptSel.value ? Number(deptSel.value) : null,
              position_id: posSel.value ? Number(posSel.value) : null,
              is_active: activeSel.value === "true",
            });
            await refreshUsers();
          } catch (err) {
            showError(userBox, err);
          }
        });

        pwdBtn.addEventListener("click", async () => {
          const pwd = prompt(`为用户 ${u.username} 设置新密码（>=6位）：`);
          if (!pwd) return;
          try {
            await api.setUserPassword(u.id, pwd);
            alert("密码已更新");
          } catch (err) {
            showError(userBox, err);
          }
        });

        tbody.appendChild(tr);
      }

      listEl.appendChild(t);
      userBox.querySelector(".pill").textContent = `共 ${users.length} 个用户（岗位数：${posNameById.size}）`;
    } catch (err) {
      showError(userBox, err);
    }
  }

  userBox.querySelector("#uCreate").addEventListener("click", async () => {
    try {
      const username = userBox.querySelector("#uUsername").value.trim();
      const fullName = userBox.querySelector("#uFullName").value.trim();
      const role = userBox.querySelector("#uRole").value;
      const dept = userBox.querySelector("#uDept").value;
      const pos = userBox.querySelector("#uPos").value;
      const password = userBox.querySelector("#uPassword").value;

      await api.createUser({
        username,
        password,
        full_name: fullName,
        role,
        department_id: dept ? Number(dept) : null,
        position_id: pos ? Number(pos) : null,
      });

      userBox.querySelector("#uUsername").value = "";
      userBox.querySelector("#uFullName").value = "";
      userBox.querySelector("#uPassword").value = "";
      await refreshUsers();
    } catch (err) {
      showError(userBox, err);
    }
  });

  container.appendChild(userBox);
  root.appendChild(container);
  appEl.replaceChildren(root);

  try {
    await refreshDepts();
    await refreshPositions();
    await refreshWorkflows();
    await refreshUserAuxIntoSelects();
    await refreshUsers();
  } catch (err) {
    showError(container, err);
  }
}

async function ensureMe() {
  if (!getToken()) return null;
  try {
    return await api.me();
  } catch {
    clearToken();
    return null;
  }
}

export async function render() {
  const me = await ensureMe();
  setUserBar(me);

  const hash = location.hash || "";
  const route = hash.replace(/^#/, "");

  if (!me) {
    if (route !== "/login") location.hash = "#/login";
    await renderLogin();
    return;
  }

  if (!route || route === "/dashboard") return renderDashboard(me);
  if (route === "/requests") return renderMyRequests(me);
  if (route === "/new-request") return renderNewRequest(me);
  if (route === "/approvals") return renderApprovals(me);
  if (route === "/admin") return renderAdmin(me);
  if (route.startsWith("/request/")) {
    const id = Number(route.replace("/request/", ""));
    if (!Number.isFinite(id) || id <= 0) {
      location.hash = "#/dashboard";
      return renderDashboard(me);
    }
    return renderRequestDetail(me, id);
  }

  location.hash = "#/dashboard";
  return renderDashboard(me);
}

window.addEventListener("hashchange", () => void render());

render();
