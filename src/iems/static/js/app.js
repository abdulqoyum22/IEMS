"use strict";

const state = { user: null, page: "dashboard", transactions: { income: [], expense: [] }, report: null };
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const money = (value) => new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN", minimumFractionDigits: 2 }).format(Number(value || 0));
const isoToday = () => new Date().toISOString().slice(0, 10);
const safe = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[char]);

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("iems-theme", theme);
  const dark = theme === "dark";
  const button = $("#theme-toggle");
  button.querySelector(".theme-toggle-icon").textContent = dark ? "☀" : "◐";
  button.querySelector(".theme-toggle-label").textContent = dark ? "Light" : "Dark";
  button.setAttribute("aria-label", `Switch to ${dark ? "light" : "dark"} mode`);
  button.title = `Switch to ${dark ? "light" : "dark"} mode (Ctrl+Shift+D)`;
}

async function api(url, options = {}) {
  const response = await fetch(url, { headers: { "Content-Type": "application/json", ...(options.headers || {}) }, ...options });
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok) throw new Error(data?.error || "Something went wrong. Please try again.");
  return data;
}

function toast(message, error = false) {
  const item = document.createElement("div");
  item.className = `toast${error ? " error" : ""}`;
  item.textContent = message;
  $("#toast-region").append(item);
  setTimeout(() => item.remove(), 3800);
}

function setAuthMode(setup) {
  $("#auth-title").textContent = setup ? "Set up IEMS" : "Welcome back";
  $("#auth-copy").textContent = setup ? "Create the first administrator account for CESA." : "Sign in to manage the association's finances.";
  $("#auth-submit").textContent = setup ? "Create administrator account" : "Sign in";
  $("#auth-note").textContent = setup ? "Use a secure password of at least 8 characters." : "Your account is managed by the IEMS administrator.";
  $("#name-field").classList.toggle("hidden", !setup);
  $("#auth-form").dataset.mode = setup ? "setup" : "login";
}

function enterApp(user) {
  state.user = user;
  $("#auth-view").classList.add("hidden");
  $("#app-view").classList.remove("hidden");
  $("#sidebar-name").textContent = user.full_name;
  $("#sidebar-role").textContent = user.role === "admin" ? "Administrator" : "Treasurer";
  $("#sidebar-initial").textContent = user.full_name.slice(0, 1).toUpperCase();
  $$(".admin-only").forEach((item) => item.classList.toggle("hidden", user.role !== "admin"));
  $("#today-label").textContent = new Intl.DateTimeFormat("en-NG", { day: "numeric", month: "short", year: "numeric" }).format(new Date());
  switchPage("dashboard");
}

function switchPage(page) {
  if ((page === "users" || page === "audit") && state.user.role !== "admin") return;
  state.page = page;
  $$(".page").forEach((item) => item.classList.toggle("active", item.id === `page-${page}`));
  $$(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.page === page));
  const labels = { dashboard: ["OVERVIEW", "Financial dashboard"], income: ["RECEIPTS", "Income management"], expenses: ["PAYMENTS", "Expense management"], reports: ["ANALYSIS", "Financial reports"], users: ["ACCESS CONTROL", "User management"], audit: ["ACCOUNTABILITY", "Audit log"] };
  $("#page-kicker").textContent = labels[page][0];
  $("#page-title").textContent = labels[page][1];
  if (page === "dashboard") loadDashboard();
  if (page === "income") loadTransactions("income");
  if (page === "expenses") loadTransactions("expense");
  if (page === "users") loadUsers();
  if (page === "audit") loadAudit();
}

async function loadDashboard() {
  try {
    const data = await api("/api/dashboard");
    $("#balance-value").textContent = money(data.totals.balance);
    $("#total-income").textContent = money(data.totals.income_total);
    $("#total-expense").textContent = money(data.totals.expense_total);
    $("#month-income").textContent = `This month: ${money(data.current_month.income_total)}`;
    $("#month-expense").textContent = `This month: ${money(data.current_month.expense_total)}`;
    $("#month-count").textContent = data.current_month.income.length + data.current_month.expenses.length;
    renderExpenseBars(data.current_month.expense_by_category);
    renderRecent(data.recent, data.current_month.income);
  } catch (error) { toast(error.message, true); }
}

function renderExpenseBars(items) {
  const container = $("#expense-bars");
  if (!items.length) { container.className = "bar-list empty-state"; container.textContent = "No expenses recorded this month."; return; }
  const highest = Math.max(...items.map((item) => Number(item.amount)));
  container.className = "bar-list";
  container.innerHTML = items.map((item) => `<div class="bar-row"><span>${safe(item.category)}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(6, Number(item.amount) / highest * 100)}%"></div></div><b>${money(item.amount)}</b></div>`).join("");
}

function renderRecent(items, incomeItems) {
  const incomeIds = new Set(incomeItems.map((item) => item.id));
  const container = $("#recent-list");
  if (!items.length) { container.className = "activity-list empty-state"; container.textContent = "No recent transactions."; return; }
  container.className = "activity-list";
  container.innerHTML = items.map((item) => {
    const isIncome = incomeIds.has(item.id);
    return `<div class="activity-item"><span class="activity-type ${isIncome ? "" : "expense"}">${isIncome ? "↗" : "↘"}</span><div class="activity-main"><b>${safe(item.party)}</b><small>${safe(item.category)} · ${item.date}</small></div><span class="activity-amount ${isIncome ? "" : "expense-text"}">${isIncome ? "+" : "−"}${money(item.amount)}</span></div>`;
  }).join("");
}

async function loadTransactions(kind) {
  const plural = kind === "income" ? "income" : "expense";
  const params = new URLSearchParams();
  const search = $(`#${kind}-search`).value.trim();
  const start = $(`#${kind}-start`).value;
  const end = $(`#${kind}-end`).value;
  if (search) params.set("search", search); if (start) params.set("start", start); if (end) params.set("end", end);
  try {
    const data = await api(`/api/transactions/${kind}?${params}`);
    state.transactions[kind] = data.transactions;
    const body = $(`#${kind}-table`);
    if (!data.transactions.length) { body.innerHTML = `<tr><td colspan="6" class="empty-state">No ${plural} records found.</td></tr>`; return; }
    body.innerHTML = data.transactions.map((item) => `<tr><td>${item.date}</td><td><b>${safe(item.party)}</b><br><small>${safe(item.description)}</small></td><td><span class="badge ${kind}">${safe(item.category)}</span></td><td>${safe(item.reference || "—")}</td><td class="amount ${kind === "expense" ? "expense-text" : ""}">${money(item.amount)}</td><td><div class="row-actions"><button class="table-button" data-edit="${kind}" data-id="${item.id}">Edit</button><button class="table-button delete" data-delete="${kind}" data-id="${item.id}">Delete</button></div></td></tr>`).join("");
  } catch (error) { toast(error.message, true); }
}

async function openTransaction(kind, record = null) {
  const form = $("#transaction-form");
  form.reset();
  form.kind.value = kind;
  form.record_id.value = record?.id || "";
  form.date.value = record?.date || isoToday();
  form.party.value = record?.party || "";
  form.amount.value = record?.amount || "";
  form.reference.value = record?.reference || "";
  form.description.value = record?.description || "";
  $("#transaction-kicker").textContent = record ? "EDIT RECORD" : "NEW RECORD";
  $("#transaction-title").textContent = `${record ? "Edit" : "Add"} ${kind}`;
  $("#party-label").firstChild.textContent = kind === "income" ? "Source" : "Payee";
  try {
    const data = await api(`/api/categories?type=${kind}`);
    form.category_id.innerHTML = `<option value="">Choose category</option>${data.categories.map((item) => `<option value="${item.id}" ${Number(record?.category_id) === item.id ? "selected" : ""}>${safe(item.name)}</option>`).join("")}`;
    $("#transaction-modal").showModal();
  } catch (error) { toast(error.message, true); }
}

async function saveTransaction(event) {
  event.preventDefault();
  const form = event.currentTarget; const kind = form.kind.value; const recordId = form.record_id.value;
  const payload = Object.fromEntries(new FormData(form)); delete payload.kind; delete payload.record_id;
  try {
    await api(`/api/transactions/${kind}${recordId ? `/${recordId}` : ""}`, { method: recordId ? "PUT" : "POST", body: JSON.stringify(payload) });
    $("#transaction-modal").close(); toast(`${kind[0].toUpperCase() + kind.slice(1)} record saved.`);
    loadTransactions(kind); loadDashboard();
  } catch (error) { toast(error.message, true); }
}

async function deleteTransaction(kind, id) {
  if (!confirm("Delete this record? It will be retained in the audit trail.")) return;
  try { await api(`/api/transactions/${kind}/${id}`, { method: "DELETE" }); toast("Transaction deleted."); loadTransactions(kind); loadDashboard(); } catch (error) { toast(error.message, true); }
}

function setReportPreset(preset) {
  const today = new Date(); let start = new Date(today); let end = new Date(today);
  if (preset === "week") { const day = (today.getDay() + 6) % 7; start.setDate(today.getDate() - day); }
  if (preset === "month") start = new Date(today.getFullYear(), today.getMonth(), 1);
  $("#report-start").value = start.toISOString().slice(0, 10); $("#report-end").value = end.toISOString().slice(0, 10);
}

async function generateReport() {
  const start = $("#report-start").value, end = $("#report-end").value;
  if (!start || !end) return toast("Choose both report dates.", true);
  try {
    const data = await api(`/api/reports?start=${start}&end=${end}`); state.report = data.report;
    $("#report-output").classList.remove("hidden"); $("#report-income").textContent = money(data.report.income_total); $("#report-expense").textContent = money(data.report.expense_total); $("#report-balance").textContent = money(data.report.balance); $("#report-period").textContent = `${start} to ${end}`;
    const rows = [...data.report.income.map((item) => ({ ...item, kind: "Income" })), ...data.report.expenses.map((item) => ({ ...item, kind: "Expense" }))].sort((a, b) => b.date.localeCompare(a.date));
    $("#report-table").innerHTML = rows.length ? rows.map((item) => `<tr><td><span class="badge ${item.kind === "Income" ? "income" : "expense"}">${item.kind}</span></td><td>${item.date}</td><td>${safe(item.category)}</td><td>${safe(item.party)}</td><td class="amount ${item.kind === "Expense" ? "expense-text" : ""}">${money(item.amount)}</td></tr>`).join("") : `<tr><td colspan="5" class="empty-state">No transactions for this period.</td></tr>`;
  } catch (error) { toast(error.message, true); }
}

function exportReport(format) {
  const start = $("#report-start").value, end = $("#report-end").value;
  if (!start || !end) return toast("Generate a report first.", true);
  window.location.href = `/api/reports/export/${format}?start=${start}&end=${end}`;
}

async function loadUsers() {
  try { const data = await api("/api/users"); $("#users-table").innerHTML = data.users.map((item) => `<tr><td><b>${safe(item.full_name)}</b></td><td>${safe(item.username)}</td><td><span class="badge">${safe(item.role)}</span></td><td><span class="badge ${item.is_active ? "active" : "inactive"}">${item.is_active ? "Active" : "Inactive"}</span></td><td>${item.created_at.slice(0, 10)}</td><td>${item.id === state.user.id ? "" : `<button class="table-button" data-user-status="${item.id}" data-active="${item.is_active}">${item.is_active ? "Deactivate" : "Activate"}</button>`}</td></tr>`).join(""); } catch (error) { toast(error.message, true); }
}

async function saveUser(event) {
  event.preventDefault(); const form = event.currentTarget; const payload = Object.fromEntries(new FormData(form));
  try { await api("/api/users", { method: "POST", body: JSON.stringify(payload) }); form.reset(); $("#user-modal").close(); toast("User created."); loadUsers(); } catch (error) { toast(error.message, true); }
}

async function toggleUser(id, isActive) {
  try { await api(`/api/users/${id}/status`, { method: "PATCH", body: JSON.stringify({ is_active: !isActive }) }); toast("User status updated."); loadUsers(); } catch (error) { toast(error.message, true); }
}

async function loadAudit() {
  try { const data = await api("/api/audit-logs"); $("#audit-table").innerHTML = data.logs.length ? data.logs.map((item) => `<tr><td>${new Date(item.created_at).toLocaleString()}</td><td><span class="badge">${safe(item.action)}</span></td><td>${safe(item.entity_type)}</td><td>${safe(item.description)}</td></tr>`).join("") : `<tr><td colspan="4" class="empty-state">No audit activity yet.</td></tr>`; } catch (error) { toast(error.message, true); }
}

$("#auth-form").addEventListener("submit", async (event) => {
  event.preventDefault(); const form = event.currentTarget; const payload = Object.fromEntries(new FormData(form)); const setup = form.dataset.mode === "setup";
  try { const data = await api(setup ? "/api/auth/setup" : "/api/auth/login", { method: "POST", body: JSON.stringify(payload) }); enterApp(data.user); } catch (error) { toast(error.message, true); }
});
$$('.password-toggle').forEach((button) => button.addEventListener("click", () => { const input = button.parentElement.querySelector("input"); const reveal = input.type === "password"; input.type = reveal ? "text" : "password"; button.textContent = reveal ? "Hide" : "Show"; button.setAttribute("aria-label", reveal ? "Hide password" : "Show password"); }));
$("#forgot-password").addEventListener("click", () => $("#recovery-modal").showModal());
$("#recovery-form").addEventListener("submit", async (event) => { event.preventDefault(); try { const payload = Object.fromEntries(new FormData(event.currentTarget)); const data = await api("/api/auth/forgot-password", { method: "POST", body: JSON.stringify(payload) }); $("#recovery-modal").close(); event.currentTarget.reset(); toast(data.message); } catch (error) { toast(error.message, true); } });
$$('.nav-item').forEach((button) => button.addEventListener("click", () => switchPage(button.dataset.page)));
$$('[data-go]').forEach((button) => button.addEventListener("click", () => switchPage(button.dataset.go)));
$("#quick-income").addEventListener("click", () => openTransaction("income"));
$$('[data-add]').forEach((button) => button.addEventListener("click", () => openTransaction(button.dataset.add)));
$$('[data-filter]').forEach((button) => button.addEventListener("click", () => loadTransactions(button.dataset.filter)));
$("#transaction-form").addEventListener("submit", saveTransaction); $("#user-form").addEventListener("submit", saveUser); $("#add-user").addEventListener("click", () => $("#user-modal").showModal());
$$('[data-close]').forEach((button) => button.addEventListener("click", () => $(`#${button.dataset.close}`).close()));
$("#generate-report").addEventListener("click", generateReport); $("#export-pdf").addEventListener("click", () => exportReport("pdf")); $("#export-excel").addEventListener("click", () => exportReport("excel"));
$$('[data-preset]').forEach((button) => button.addEventListener("click", () => setReportPreset(button.dataset.preset)));
document.addEventListener("click", (event) => { const edit = event.target.closest("[data-edit]"), remove = event.target.closest("[data-delete]"), status = event.target.closest("[data-user-status]"); if (edit) openTransaction(edit.dataset.edit, state.transactions[edit.dataset.edit].find((item) => item.id === Number(edit.dataset.id))); if (remove) deleteTransaction(remove.dataset.delete, remove.dataset.id); if (status) toggleUser(status.dataset.userStatus, status.dataset.active === "true"); });
$("#logout-button").addEventListener("click", async () => { try { await api("/api/auth/logout", { method: "POST" }); location.reload(); } catch (error) { toast(error.message, true); } });
$("#theme-toggle").addEventListener("click", () => applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));
document.addEventListener("keydown", (event) => { if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === "d") { event.preventDefault(); $("#theme-toggle").click(); } });

(async function boot() { applyTheme(localStorage.getItem("iems-theme") || "light"); setReportPreset("month"); try { const account = await fetch("/api/auth/me"); if (account.ok) return enterApp((await account.json()).user); const data = await api("/api/bootstrap"); setAuthMode(data.needs_setup); } catch (error) { toast("Could not start IEMS. Check the local server.", true); } })();
