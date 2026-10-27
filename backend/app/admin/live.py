"""Live activity screen for the admin: every API call as it happens (for demos and debugging).

GET /admin/live       -> the page (log in with the admin account inside it)
GET /admin/live/feed  -> new activity since ?after=<id>, admin token only
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import activity
from app.auth.security import require_role, utcnow
from app.database.database import get_db
from app.database.models import ACCOUNT_PENDING, ADMIN, Order, User, UserSession

router = APIRouter(prefix="/admin/live", tags=["Admin"])


@router.get("/feed")
def live_feed(
    after: int = Query(0, description="Only entries newer than this id"),
    admin: User = Depends(require_role(ADMIN)),
    db: Session = Depends(get_db),
):
    """Recent API calls (newest last) plus a few live counters."""
    now = utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    active = UserSession.logged_out_at.is_(None) & (UserSession.expires_at > now)
    return {
        "entries": activity.recent(after),
        "stats": {
            "logged_in_users": db.scalar(select(func.count(func.distinct(UserSession.user_id))).where(active)),
            "registered_users": db.scalar(select(func.count(User.id))),
            "orders_today": db.scalar(select(func.count(Order.id)).where(Order.created_at >= today)),
            "pending_staff": db.scalar(
                select(func.count(User.id)).where(User.account_status == ACCOUNT_PENDING)
            ),
        },
    }


@router.get("", response_class=HTMLResponse, include_in_schema=False)
def live_page():
    return _PAGE


_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Canteen Backend Live</title>
<style>
  :root { --bg:#0f1115; --panel:#171a21; --line:#262b36; --text:#e6e8ee; --muted:#8b93a7;
          --ok:#3fb950; --warn:#d29922; --err:#f85149; --accent:#58a6ff; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text);
         font:14px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
  header { display:flex; flex-wrap:wrap; gap:12px; align-items:center; justify-content:space-between;
           padding:14px 20px; border-bottom:1px solid var(--line); background:var(--panel);
           position:sticky; top:0; }
  h1 { font-size:16px; margin:0; }
  .dot { display:inline-block; width:9px; height:9px; border-radius:50%; background:var(--ok);
         margin-right:8px; animation:pulse 1.6s infinite; }
  .dot.off { background:var(--err); animation:none; }
  @keyframes pulse { 50% { opacity:.3; } }
  .stats { display:flex; gap:18px; flex-wrap:wrap; color:var(--muted); }
  .stats b { color:var(--text); font-size:16px; margin-left:4px; }
  main { padding:8px 20px 40px; }
  table { width:100%; border-collapse:collapse; }
  th { text-align:left; color:var(--muted); font-weight:normal; padding:8px 8px; border-bottom:1px solid var(--line); }
  td { padding:7px 8px; border-bottom:1px solid var(--line); vertical-align:top; }
  tr.new { animation:flash 1.5s ease-out; }
  @keyframes flash { from { background:#1f3a5f; } to { background:transparent; } }
  .GET { color:var(--accent); } .POST { color:var(--ok); } .PUT, .PATCH { color:var(--warn); } .DELETE { color:var(--err); }
  .s2 { color:var(--ok); } .s4 { color:var(--warn); } .s5 { color:var(--err); }
  .muted { color:var(--muted); }
  .role { font-size:12px; padding:1px 6px; border-radius:4px; background:#262b36; color:var(--muted); margin-left:4px; }
  .detail { color:#c9d1d9; }
  form { max-width:340px; margin:12vh auto; background:var(--panel); padding:24px; border:1px solid var(--line); border-radius:8px; }
  form h1 { margin-bottom:6px; } form p { color:var(--muted); margin:0 0 16px; }
  input, button { width:100%; padding:10px; margin:6px 0; border-radius:6px; border:1px solid var(--line);
                  background:var(--bg); color:var(--text); font:inherit; }
  button { background:var(--accent); color:#0b1220; border:0; cursor:pointer; font-weight:bold; }
  .err { color:var(--err); min-height:1.4em; }
  .link { background:none; border:0; color:var(--muted); width:auto; padding:0; margin:0; cursor:pointer; text-decoration:underline; }
  @media (max-width:700px) { .hide-sm { display:none; } header { padding:12px 16px; } main { padding:8px 16px 40px; } }
</style>
</head>
<body>
<form id="login" hidden>
  <h1>Canteen Backend Live</h1>
  <p>Log in with the admin account to watch every API call live.</p>
  <input id="iid" placeholder="Institute ID" value="ADMIN001" autocomplete="username">
  <input id="pw" type="password" placeholder="Password" autocomplete="current-password">
  <button>Log in</button>
  <div class="err" id="err"></div>
</form>

<div id="app" hidden>
  <header>
    <h1><span class="dot" id="dot"></span>Canteen Backend Live</h1>
    <div class="stats">
      <span>Logged in <b id="st-in">-</b></span>
      <span>Users <b id="st-users">-</b></span>
      <span>Orders today <b id="st-orders">-</b></span>
      <span>Pending staff <b id="st-pending">-</b></span>
      <span>API calls <b id="st-calls">0</b></span>
      <button class="link" id="logout">log out</button>
    </div>
  </header>
  <main>
    <table>
      <thead><tr><th>Time</th><th>API</th><th>Status</th><th class="hide-sm">Took</th><th>Who</th><th>What happened</th></tr></thead>
      <tbody id="rows"><tr id="empty"><td colspan="6" class="muted">Waiting for API calls... use the app and they appear here.</td></tr></tbody>
    </table>
  </main>
</div>

<script>
const KEY = "canteen_live_token";
let token = null, after = 0, calls = 0, timer = null;
try { token = sessionStorage.getItem(KEY); } catch (e) {}

const $ = id => document.getElementById(id);
function td(text, cls) { const c = document.createElement("td"); c.textContent = text; if (cls) c.className = cls; return c; }

function show(loggedIn) {
  $("login").hidden = loggedIn; $("app").hidden = !loggedIn;
  if (loggedIn) poll(); else clearTimeout(timer);
}

$("login").addEventListener("submit", async ev => {
  ev.preventDefault(); $("err").textContent = "";
  try {
    const r = await fetch("/auth/admin/login", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ institute_id: $("iid").value.trim(), password: $("pw").value }) });
    const j = await r.json();
    if (!r.ok) { $("err").textContent = j.detail || "Login failed"; return; }
    token = j.access_token; try { sessionStorage.setItem(KEY, token); } catch (e) {}
    show(true);
  } catch (e) { $("err").textContent = "Cannot reach the backend"; }
});

$("logout").addEventListener("click", () => {
  fetch("/auth/logout", { method: "POST", headers: { Authorization: "Bearer " + token } }).catch(() => {});
  token = null; try { sessionStorage.removeItem(KEY); } catch (e) {}
  show(false);
});

function addRow(e) {
  const empty = $("empty"); if (empty) empty.remove();
  const tr = document.createElement("tr"); tr.className = "new";
  tr.append(td(e.time, "muted"));
  const api = td(""); const m = document.createElement("span"); m.className = e.method; m.textContent = e.method.padEnd(7);
  api.append(m, document.createTextNode(e.path)); tr.append(api);
  tr.append(td(String(e.status), "s" + String(e.status)[0]));
  tr.append(td(e.ms + " ms", "muted hide-sm"));
  const who = td(e.user || "guest", e.user ? "" : "muted");
  if (e.role) { const r = document.createElement("span"); r.className = "role"; r.textContent = e.role; who.append(r); }
  tr.append(who);
  tr.append(td(e.detail || "", "detail"));
  $("rows").prepend(tr);
  while ($("rows").children.length > 300) $("rows").lastChild.remove();
}

async function poll() {
  clearTimeout(timer);
  try {
    const r = await fetch("/admin/live/feed?after=" + after, { headers: { Authorization: "Bearer " + token } });
    if (r.status === 401 || r.status === 403) { token = null; try { sessionStorage.removeItem(KEY); } catch (e) {} show(false); return; }
    const j = await r.json();
    for (const e of j.entries) { addRow(e); after = e.id; calls++; }
    $("st-in").textContent = j.stats.logged_in_users; $("st-users").textContent = j.stats.registered_users;
    $("st-orders").textContent = j.stats.orders_today; $("st-pending").textContent = j.stats.pending_staff;
    $("st-calls").textContent = calls; $("dot").classList.remove("off");
  } catch (e) { $("dot").classList.add("off"); }
  timer = setTimeout(poll, 1500);
}

show(!!token);
</script>
</body>
</html>
"""
