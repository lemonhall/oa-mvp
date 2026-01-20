import { api, clearToken, getToken, setToken } from "./api.js";

const appEl = document.getElementById("app");
const userBarEl = document.getElementById("userBar");
const meTextEl = document.getElementById("meText");
const logoutBtn = document.getElementById("logoutBtn");

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
  ];
  if (me?.role === "admin" || me?.role === "approver") {
    items.push({ hash: "#/approvals", label: "待我审批" });
  }
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
        const item = el(`
          <div class="item">
            <div class="item-title"></div>
            <div class="muted"></div>
          </div>
        `);
        item.querySelector(".item-title").textContent = `[${r.type}] ${r.title} — ${r.status}`;
        item.querySelector(".muted").textContent = r.content || "";
        listEl.appendChild(item);
      }
    }
  } catch (err) {
    showError(wrap, err);
  }

  appEl.replaceChildren(root);
}

async function renderNewRequest(me) {
  const root = el(`<div></div>`);
  root.appendChild(nav(me));

  const form = el(`
    <div>
      <div class="section-title">发起申请</div>
      <div class="row">
        <div>
          <select id="type" class="input">
            <option value="leave">请假</option>
            <option value="reimburse">报销</option>
          </select>
        </div>
        <div>
          <input id="title" class="input" placeholder="标题" />
        </div>
      </div>
      <div style="margin-top: 12px;">
        <input id="amount" class="input" placeholder="金额（报销必填）" />
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
  const contentEl = form.querySelector("#content");
  const submitBtn = form.querySelector("#submitBtn");

  typeEl.addEventListener("change", () => {
    amountEl.disabled = typeEl.value !== "reimburse";
    amountEl.value = "";
  });
  typeEl.dispatchEvent(new Event("change"));

  submitBtn.addEventListener("click", async () => {
    try {
      const payload = {
        type: typeEl.value,
        title: titleEl.value.trim(),
        content: contentEl.value.trim(),
        amount: typeEl.value === "reimburse" ? Number(amountEl.value || "0") : null,
      };
      if (payload.type === "reimburse" && (!amountEl.value || Number.isNaN(payload.amount))) {
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
            <div class="item-title"></div>
            <div class="muted"></div>
            <div style="margin-top: 10px; display: flex; gap: 10px; flex-wrap: wrap;">
              <input class="input" style="max-width: 420px;" placeholder="审批意见（可选）" />
              <button class="btn btn-primary">同意</button>
              <button class="btn btn-danger">驳回</button>
            </div>
          </div>
        `);
        item.querySelector(".item-title").textContent = `[${r.type}] ${r.title}`;
        item.querySelector(".muted").textContent = r.content || "";

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

  const wrap = el(`
    <div>
      <div class="section-title">管理（仅 admin）</div>
      <div class="pill">提示：目前仅提供“发公告”，用户/部门管理可通过 API 扩展</div>
      <div style="margin-top: 12px;" class="row">
        <div><input id="title" class="input" placeholder="公告标题" /></div>
        <div><input id="content" class="input" placeholder="公告内容（简短）" /></div>
      </div>
      <div style="margin-top: 12px;">
        <button id="publish" class="btn btn-primary">发布公告</button>
      </div>
    </div>
  `);

  const titleEl = wrap.querySelector("#title");
  const contentEl = wrap.querySelector("#content");
  wrap.querySelector("#publish").addEventListener("click", async () => {
    try {
      await api.createAnnouncement(titleEl.value.trim(), contentEl.value.trim());
      location.hash = "#/dashboard";
      await render();
    } catch (err) {
      showError(wrap, err);
    }
  });

  root.appendChild(wrap);
  appEl.replaceChildren(root);
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

  location.hash = "#/dashboard";
  return renderDashboard(me);
}

window.addEventListener("hashchange", () => void render());

render();
