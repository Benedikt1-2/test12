"""WG Organizer – a flat-share app with Fair Split, House Organizer and Cooking.

Run:  streamlit run app.py
"""
from __future__ import annotations

import html
import re
from datetime import date, datetime

import streamlit as st

import fx as fxmod
import logic as L
import ml
import recipe_db
import store
from recipes import ALLERGIES, BUILTIN, CUISINES, DIET_LABEL, DIETS

st.set_page_config(page_title="WG Organizer", layout="wide")

CATS = ["Groceries", "Household & cleaning", "Rent & utilities", "Going out", "Travel", "Other", "Settlement"]
COLORS = ["#6E95FF", "#F07BB5", "#5CC88C", "#F0A15A", "#A790FF", "#4EC6CE"]
TOGGLE_COLORS = ["blue", "violet", "green", "orange", "violet", "blue"]  # markdown colours for sidebar labels
NAV_ICONS = {"Today": ":material/wb_sunny:", "Fair Split": ":material/payments:",
             "House Organizer": ":material/calendar_month:", "Cooking": ":material/restaurant:",
             "Flat & People": ":material/group:"}
PAGE_TITLES = {"Today": "Today", "Fair Split": "Who owes what?", "House Organizer": "Life at home",
               "Cooking": "What's for dinner?", "Flat & People": "Flat & People"}
SECTIONS = ["Today", "Fair Split", "House Organizer", "Cooking", "Flat & People"]
ORG_TABS = ["Calendar", "Chores & tasks", "Shopping list"]
TIMEZONE = "Europe/Zurich"  # for "Good morning / afternoon / evening"
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WEEKDAYS_LONG = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
DATE_FMT = "DD/MM/YYYY"

# ---------- "Night Kitchen" design: dark ground, amber accent, Manrope + JetBrains Mono ----------
AMBER, POS, NEG, MUTED = "#F2B544", "#5CC88C", "#FF8A7A", "#A7B0BC"
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea, .stApp button, .stApp h1, .stApp h2, .stApp h3,
.stApp h4, .stApp small, .stApp div[data-testid="stMarkdownContainer"], .stApp span:not([data-testid="stIconMaterial"]) {
  font-family: 'Manrope', system-ui, sans-serif; }
[data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; }
.stApp { background: #0F1318; }
.stApp h1, .stApp h2, .stApp h3 { font-weight: 800; letter-spacing: -0.02em; }
.mono, [data-testid="stMetricValue"] { font-family: 'JetBrains Mono', ui-monospace, monospace !important; }

/* sidebar: brand, navigation, who's home */
section[data-testid="stSidebar"] { background: #151A21; border-right: 1px solid #252C36; }
.nk-brand { display: flex; align-items: center; gap: 10px; font-size: 1.15rem; font-weight: 800; margin: 4px 0 18px; }
.nk-logo { width: 36px; height: 36px; border-radius: 10px; background: #F2B544; display: inline-flex; align-items: center; justify-content: center; }
.nk-label { font-size: .72rem; font-weight: 700; text-transform: uppercase; letter-spacing: .1em; color: #8592A3; margin: 22px 0 6px; }
section[data-testid="stSidebar"] .stButton button { justify-content: flex-start; border: 0; background: transparent; color: #AEB8C5;
  font-weight: 600; padding: 10px 12px; border-radius: 10px; }
section[data-testid="stSidebar"] .stButton button div { justify-content: flex-start; }
section[data-testid="stSidebar"] .stButton button:hover { background: #1D232C; color: #FFFFFF; }
section[data-testid="stSidebar"] .stButton button[kind="primary"],
section[data-testid="stSidebar"] .stButton button[data-testid="stBaseButton-primary"] { background: #222A35; color: #FFFFFF; font-weight: 700; }
section[data-testid="stSidebar"] .stButton button[kind="primary"] [data-testid="stIconMaterial"],
section[data-testid="stSidebar"] .stButton button[data-testid="stBaseButton-primary"] [data-testid="stIconMaterial"] { color: #F2B544; }

/* buttons */
.stApp button[kind="primary"], .stApp button[data-testid="stBaseButton-primary"],
.stApp button[kind="primaryFormSubmit"], .stApp button[data-testid="stBaseButton-primaryFormSubmit"] {
  background: #F2B544; border: 1px solid #F2B544; color: #1A1405; font-weight: 800; border-radius: 12px; }
.stApp button[kind="primary"]:hover, .stApp button[data-testid="stBaseButton-primary"]:hover,
.stApp button[kind="primaryFormSubmit"]:hover, .stApp button[data-testid="stBaseButton-primaryFormSubmit"]:hover {
  background: #FFD27A; border-color: #FFD27A; color: #1A1405; }
.stApp .main button[kind="secondary"], .stApp .main button[data-testid="stBaseButton-secondary"],
.stApp [data-testid="stMain"] button[data-testid="stBaseButton-secondary"] { background: transparent; border: 1px solid #3A4452; border-radius: 12px; }

/* page header */
.nk-head { margin: 0 0 10px; }
.nk-date { font-size: .85rem; font-weight: 600; color: #8592A3; }
.nk-head h1 { font-size: 2rem; margin: 2px 0 0; padding: 0; }

/* cards */
.st-key-hero { background: #1C1A14; border: 1px solid #3A3220; border-radius: 20px; padding: 22px 24px; }
.nk-kicker { font-size: .74rem; font-weight: 800; text-transform: uppercase; letter-spacing: .12em; color: #F2B544; }
.nk-hero-name { font-size: 2rem; font-weight: 800; letter-spacing: -0.02em; margin: 4px 0; line-height: 1.15; }
.nk-hero-text { color: #C3CBD6; font-size: .95rem; margin: 0 0 6px; }
.nk-tiles { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.nk-tile { background: #14120D; border-radius: 12px; padding: 12px; display: flex; flex-direction: column; gap: 2px; }
.nk-tile b { font-family: 'JetBrains Mono', monospace; font-size: 1.35rem; }
.nk-tile span { font-size: .75rem; color: #A7B0BC; }
div[class*="st-key-fit-row-"], div[class*="st-key-nofit-row-"] { background: #161B22; border: 1px solid #222934; border-radius: 12px; padding: 8px 14px; }
.nk-rank { font-family: 'JetBrains Mono', monospace; color: #8592A3; font-size: .85rem; }
.nk-name { font-weight: 700; font-size: 1rem; }
.nk-meta { color: #A7B0BC; font-size: .85rem; }
div[class*="st-key-aside-"] { background: #161B22; border: 1px solid #252C36; border-radius: 16px; padding: 14px 16px; }
.nk-line { display: flex; justify-content: space-between; gap: 8px; font-size: .92rem; padding: 3px 0; }
.nk-h { font-weight: 800; font-size: .95rem; margin-bottom: 4px; }

/* shared bits */
.who{display:inline-flex;align-items:center;gap:6px;font-weight:600}
.who i{width:9px;height:9px;border-radius:50%;display:inline-block}
.pill{font-size:.75rem;font-weight:700;border-radius:99px;padding:2px 9px;background:#222A35;color:#C3CBD6}
.pill.late{background:rgba(255,138,122,.14);color:#FF8A7A}
.pill.today{background:rgba(242,181,68,.16);color:#F2B544}
.pill.ok{background:rgba(92,200,140,.14);color:#5CC88C}
.bal{display:grid;grid-template-columns:minmax(70px,auto) 1fr auto;gap:8px 12px;align-items:center}
.bal .mono{font-weight:700}
.bar{position:relative;height:18px;background:#222A35;border-radius:5px}
.bar:after{content:"";position:absolute;left:50%;top:-3px;bottom:-3px;width:2px;background:#3A4452}
.bar b{position:absolute;top:3px;bottom:3px;border-radius:3px}
.cal{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:4px}
.cal .wd{font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:#8592A3;text-align:center;font-weight:700}
.day{border:1px solid #2A323E;background:#161B22;border-radius:9px;min-height:88px;padding:5px;display:flex;flex-direction:column;gap:2px;overflow:hidden;font-size:.72rem}
.day.other{opacity:.4}
.day.away{background:rgba(255,138,122,.09);border-color:rgba(255,138,122,.5)}
.day.sel{outline:2px solid #F2B544}
.day .dn{font-weight:700;font-family:'JetBrains Mono',monospace}
.day.today .dn{background:#F2B544;color:#1A1405;border-radius:99px;padding:0 6px;align-self:flex-start}
.ab{font-weight:700;color:#FF8A7A;background:rgba(255,138,122,.14);border-radius:4px;padding:0 4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ev{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ev i{width:7px;height:7px;border-radius:50%;display:inline-block;margin-right:4px}
.ev.late{color:#FF8A7A;font-weight:700}
.ab .s{display:none}
@media (max-width:640px){.day{min-height:56px}.ev span,.ab .l{display:none}.ab .s{display:inline}.nk-tiles{grid-template-columns:repeat(3,minmax(0,1fr))}}
.blockers{color:#FF8A7A;font-size:.85rem}
.lk{font-size:.75rem;font-weight:700;border-radius:99px;padding:1px 9px;border:1px solid;margin:3px 4px 0 0;display:inline-block}
.lk.ml{border-style:dashed}
.lk.rec{color:#F2B544;border-color:#F2B544}

/* Today: summary tiles and week strip */
div[class*="st-key-tile-"] { background: #161B22; border: 1px solid #252C36; border-radius: 16px; padding: 14px 16px; min-height: 150px; }
.nk-tl { font-size: .72rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: #8592A3; }
.nk-tv { font-family: 'JetBrains Mono', monospace; font-size: 1.45rem; font-weight: 700; margin: 4px 0 2px; line-height: 1.2;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.nk-tv.txt { font-family: 'Manrope', system-ui, sans-serif; font-weight: 800; }
.nk-ts { font-size: .84rem; color: #A7B0BC; }
.week { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 6px; }
.week .day { min-height: 92px; }
.week .wdn { font-size: .7rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: #8592A3; }

/* Cooking: recipe cards */
div[class*="st-key-card-"] { background: #161B22; border: 1px solid #222934; border-radius: 14px; padding: 14px 16px; min-height: 178px; }
div[class*="st-key-card-"] .nk-name { margin-top: 2px; }

/* Flat & People: person cards */
div[class*="st-key-person-"] { background: #161B22; border: 1px solid #252C36; border-radius: 16px; padding: 16px 18px; }
.nk-person { display: flex; align-items: center; gap: 12px; }
.nk-avatar { width: 42px; height: 42px; border-radius: 50%; color: #0F1318; font-weight: 800; font-size: 1.05rem;
  display: inline-flex; align-items: center; justify-content: center; flex: none; }
.nk-pname { font-weight: 800; font-size: 1.05rem; }
.nk-learn { background: #1C1A14; border: 1px solid #3A3220; border-radius: 12px; padding: 10px 12px; margin: 8px 0; font-size: .88rem; }
.nk-learn .nk-tl { color: #F2B544; }
.nk-small { font-size: .86rem; color: #C3CBD6; margin: 3px 0; }
.nk-small b { color: #8592A3; }
</style>
""", unsafe_allow_html=True)


# ====================== Load data ======================
def load():
    s = {c: store.list_docs(c) for c in ["members", "expenses", "tasks", "shopping", "recipes", "ratings", "meals"]}
    s["settings"] = store.get("config", "settings") or {"id": "settings", "base": "EUR"}
    for r in s["recipes"]:
        r["custom"] = True
    return s


@st.cache_data(ttl=3 * 3600, show_spinner=False)
def cached_rates(day: str):
    return fxmod.load_rates()


@st.cache_resource(show_spinner="Loading the recipe database …")
def recipe_index(signature: tuple):
    # `signature` changes when the database files change, so a fresh upload is picked up
    return recipe_db.load_index()


@st.cache_data(show_spinner=False, max_entries=500)
def db_recipe(rid: str):
    return recipe_db.get(rid)


S = load()
FX, FX_ERR = cached_rates(L.today())
try:
    DB_INDEX, DB_ERR = recipe_index(recipe_db.signature()), None
except Exception as exc:  # missing or damaged database files: keep the app usable, show why
    DB_INDEX, DB_ERR = [], str(exc)


# ---------- taste learning (see ml.py) ----------
@st.cache_resource(show_spinner="Preparing taste learning …")
def taste_features(signature: tuple, _db_index):
    """Feature rows for all built-in and database recipes, built once per database version."""
    pool = BUILTIN + _db_index
    return ml.Features(pool), {r["id"]: r for r in pool}


@st.cache_resource(max_entries=64, show_spinner=False)
def taste_model(member_id: str, ratings_key: tuple, favs_key: tuple, signature: tuple, custom_key: tuple,
                _by_id, _features, _background):
    # the plain arguments are the cache key: the model is retrained whenever ratings or favourites change
    return ml.train(member_id, dict(ratings_key), list(favs_key), _by_id, _features, _background)


try:
    FEATURES, DB_BY_ID = taste_features(recipe_db.signature(), DB_INDEX)
    ML_ERR = None
except Exception as exc:
    FEATURES, DB_BY_ID, ML_ERR = None, {}, str(exc)


def rating_score(d) -> float | None:
    """Overall 1–10 rating of a rating document: 50 % taste + 50 % price (older thumbs-up/down ratings map to 8 / 3)."""
    if d.get("taste") is not None and d.get("price") is not None:
        return ml.overall(d["taste"], d["price"])
    if d.get("value") in (1, -1):
        return 8.0 if d["value"] == 1 else 3.0
    return None


def ratings_of(mid) -> dict:
    return {d["recipe"]: sc for d in S["ratings"] if d.get("member") == mid and (sc := rating_score(d)) is not None}


def model_for(m):
    """The member's trained taste model, or None if there's nothing to learn from yet."""
    if FEATURES is None:
        return None
    try:
        by_id = {**DB_BY_ID, **{r["id"]: r for r in S["recipes"]}}
        background = [r["id"] for r in DB_INDEX] or [r["id"] for r in BUILTIN]
        return taste_model(m["id"], tuple(sorted(ratings_of(m["id"]).items())), tuple(m.get("favs") or []),
                           recipe_db.signature(), tuple(sorted(r["id"] for r in S["recipes"])),
                           by_id, FEATURES, background)
    except Exception:  # learning must never break the app
        return None


def save_rating(mid, r, taste: int, price: int):
    """Taste and price from 1 to 10; one rating per person and dish (a new one replaces the old one)."""
    store.put("ratings", {"id": f"{mid}--{r['id']}", "member": mid, "recipe": r["id"], "name": r["name"],
                          "taste": int(taste), "price": int(price), "date": L.today()})


def delete_rating(mid, r):
    store.delete("ratings", f"{mid}--{r['id']}")


TASTE_HELP = "1 = didn't like it at all, 10 = loved it"
PRICE_HELP = "Value for money: 1 = far too expensive, 10 = great value"


def rating_line(d) -> str:
    return f"taste {d['taste']} · price {d['price']} → **{ml.overall(d['taste'], d['price']):.1f}**"


BASE = S["settings"].get("base", "EUR")
MEMBERS = S["members"]
ss = st.session_state
ss.setdefault("pref_queue", [])
ss.setdefault("sel_day", date.today())
ss.setdefault("cal", (date.today().year, date.today().month))


def rate(cur: str) -> float:
    return fxmod.eur_per_unit(FX, cur)


def to_base(eur: float) -> float:
    return eur / rate(BASE)


def member(mid):
    return next((m for m in MEMBERS if m["id"] == mid), None)


def mname(mid) -> str:
    m = member(mid)
    return m["name"] if m else "Former flatmate"


def mcolor(mid) -> str:
    m = member(mid)
    return COLORS[(m.get("ci") or 0) % 6] if m else "#888"


def who(mid) -> str:
    return f'<span class="who"><i style="background:{mcolor(mid)}"></i>{html.escape(mname(mid))}</span>'


def own_recipes():
    """Built-in picks plus the flat's own recipes (the big database is searched separately)."""
    return BUILTIN + S["recipes"]


def recipe(rid):
    r = next((r for r in own_recipes() if r["id"] == rid), None)
    if r is None and str(rid).startswith("ar-"):
        r = db_recipe(rid)
    return r


def fmt_minutes(r) -> str:
    t = r.get("time")
    if not t:
        return ""
    est = "≈ " if r.get("source") == "db" else ""
    if t >= 120:
        return f"{est}{t / 60:.0f} h" if t % 60 == 0 or t >= 600 else f"{est}{t / 60:.1f} h"
    return f"{est}{t} min"


def fmt_date(d: str, long=False) -> str:
    x = date.fromisoformat(d)
    if long:
        return f"{WEEKDAYS_LONG[x.weekday()]}, {x.day} {MONTHS[x.month - 1]}"
    return f"{WEEKDAYS[x.weekday()]} {x.day} {MONTHS[x.month - 1][:3]}"


def short_date(x: date) -> str:
    return f"{x.day} {MONTHS[x.month - 1][:3]}"


def due_badge(d: str) -> str:
    n = L.days_until(d)
    if n < 0:
        return f'<span class="pill late">{-n} day{"s" if n < -1 else ""} overdue</span>'
    if n == 0:
        return '<span class="pill today">today</span>'
    if n == 1:
        return '<span class="pill ok">tomorrow</span>'
    return f'<span class="pill">in {n} days</span>'


def present():
    return L.present(MEMBERS)


def portions() -> int:
    n = max(1, len(present()))
    return ss.get(f"portions-{n}", n)


def prefs_known(m) -> bool:
    return bool((m.get("prefs") or {}).get("done"))


# ====================== Write actions ======================
def save_member(m):
    store.put("members", m)


def toggle_present(mid):
    m = member(mid)
    t = L.today()
    ab = L.away_on(m, t)
    if ab:  # an absence covering today ends yesterday (or is removed)
        away = []
        for a in m.get("away") or []:
            if a["id"] != ab["id"]:
                away.append(a)
            elif a["from"] < t:
                away.append({**a, "to": L.add_days(t, -1)})
        save_member({**m, "away": away, "present": True})
    else:
        save_member({**m, "present": m.get("present", True) is False})


def add_to_shopping(name, qty, unit, source=""):
    for s in S["shopping"]:
        if not s.get("done") and s["name"].lower() == name.lower() and (s.get("unit") or "") == (unit or ""):
            froms = list(dict.fromkeys(filter(None, (s.get("from") or "").split(", ") + [source])))
            store.put("shopping", {**s, "qty": round((s.get("qty") or 0) + (qty or 0), 2), "from": ", ".join(froms)})
            return
    store.put("shopping", {"id": store.new_id("s"), "name": name, "qty": qty or 0, "unit": unit or "", "done": False, "from": source})


def reassign_chores():
    """Don't leave a due chore with someone who is away that day."""
    members = store.list_docs("members")
    t = L.today()
    for task in store.list_docs("tasks"):
        if task.get("kind") != "chore":
            continue
        day = max(task["due"], t)
        m = next((x for x in members if x["id"] == task["assignee"]), None)
        if m and not L.is_home(m, day):
            nx = L.next_available(members, task["assignee"], day)
            if nx != task["assignee"]:
                store.put("tasks", {**task, "assignee": nx})


# ====================== Dialogs ======================
def expense_form(pre: dict, key: str):
    """Form for a new or existing expense. Returns True when saved."""
    ids = [m["id"] for m in MEMBERS]
    default_parts = pre.get("parts") or [m["id"] for m in (present() or MEMBERS)]
    with st.form(key, clear_on_submit=True):
        title = st.text_input("What for?", value=pre.get("title", ""), placeholder="e.g. weekly shop")
        c1, c2 = st.columns([2, 1])
        # empty field (not 0.00) so typing "10" gives 10, not 0.0010
        amount = c1.number_input("Amount", min_value=0.0, step=0.5, format="%.2f",
                                 value=float(pre["amount"]) if pre.get("amount") else None, placeholder="0.00")
        cur = c2.selectbox("Currency", fxmod.CURRENCIES, index=fxmod.CURRENCIES.index(pre.get("currency", BASE)),
                           help="Other currencies are converted with today's ECB exchange rate.")
        c4, c5 = st.columns(2)
        cat = c4.selectbox("Category", CATS, index=CATS.index(pre.get("cat", "Groceries")))
        day = c5.date_input("Date", value=date.fromisoformat(pre.get("date") or L.today()), format=DATE_FMT)
        payer = st.selectbox("Paid by", ids, format_func=mname,
                             index=ids.index(pre["payer"]) if pre.get("payer") in ids else (ids.index(present()[0]["id"]) if present() else 0))
        parts = st.multiselect("Split between", ids, default=[p for p in default_parts if p in ids], format_func=mname)
        ok = st.form_submit_button("Save", type="primary")
    if ok:
        if not amount or amount <= 0 or not parts:
            st.error("Please enter an amount and choose at least one person.")
            return False
        r = 1 if cur == BASE else rate(cur) / rate(BASE)
        if pre.get("id") and cur == pre.get("currency"):
            # keep the rate from the day the expense was first recorded
            eur = pre["eur"] if abs(amount - pre["amount"]) < 1e-9 else round(amount * pre["eur"] / pre["amount"], 2)
        else:
            eur = round(amount * r * rate(BASE), 2)
        store.put("expenses", {"id": pre.get("id") or store.new_id("e"), "title": title.strip() or "Expense",
                               "amount": round(amount, 2), "currency": cur, "eur": eur, "cat": cat, "payer": payer,
                               "parts": parts, "date": day.isoformat()})
        return True
    return False


@st.dialog("Edit expense")
def edit_expense_dialog(eid):
    e = next(x for x in S["expenses"] if x["id"] == eid)
    if expense_form(e, f"edit-{eid}"):
        st.rerun()
    if st.button("Delete expense", key=f"del-{eid}"):
        store.delete("expenses", eid)
        st.rerun()


@st.dialog("Split the cost")
def cost_dialog(pre, after_items=None):
    st.caption("Enter the amount from the receipt.")
    if expense_form(pre, "cost-form"):
        for sid in after_items or []:
            store.delete("shopping", sid)
        st.rerun()


@st.dialog("Recipe", width="large")
def recipe_dialog(rid):
    r = recipe(rid)
    n = portions()
    f = n / (r.get("servings") or 4)
    ev = L.evaluate(r, present())
    st.subheader(r["name"])
    meta = [x for x in [fmt_minutes(r), DIET_LABEL.get(r.get("diet"), ""), (r.get("cuisine") or "").capitalize(),
                        f"scaled to {n} serving{'s' if n != 1 else ''}"] if x]
    st.caption(" · ".join(meta))
    if r.get("allergens"):
        st.caption("Contains: " + ", ".join(r["allergens"]))
    if r.get("source") == "db":
        if r.get("description"):
            st.write(r["description"])
        st.caption("From the recipe database. Serving size isn't in the data, so amounts assume 4 servings. "
                   "Diet, allergens and time are estimated from the ingredients and steps, so always check labels.")
    if not ev["ok"]:
        st.markdown(f'<div class="blockers">Not suitable today: {html.escape("; ".join(ev["blockers"]))}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.4])
    with c1:
        st.markdown("**Ingredients**")
        st.markdown("\n".join("- " + " ".join(x for x in [L.fmt_qty(q * f), u, nm] if x) for q, u, nm in r["ingredients"]))
    with c2:
        st.markdown("**Method**")
        st.markdown("\n".join(f"{i}. {s}" for i, s in enumerate(r["steps"], 1)))
    st.markdown("**Rate this dish**")
    st.caption("Taste and price from 1 to 10. The overall rating (50 % taste, 50 % price) teaches the app what each of you likes.")
    current = {d["member"]: d for d in store.list_docs("ratings") if d.get("recipe") == r["id"] and d.get("taste") is not None}
    for m in MEMBERS:
        if m["id"] in current:
            st.markdown(f"{who(m['id'])} &nbsp; {rating_line(current[m['id']])}", unsafe_allow_html=True)
    rate_ids = [m["id"] for m in MEMBERS]
    first = (present() or MEMBERS)[0]["id"]
    with st.form(f"rate-{r['id']}"):
        rater = st.selectbox("Who is rating?", rate_ids, index=rate_ids.index(first), format_func=mname)
        x, y = st.columns(2)
        taste = x.slider("Taste", 1, 10, 7, help=TASTE_HELP)
        price = y.slider("Price", 1, 10, 7, help=PRICE_HELP)
        sa, sb = st.columns(2)
        save = sa.form_submit_button("Save rating", type="primary")
        remove = sb.form_submit_button("Remove this person's rating")
    if save:
        save_rating(rater, r, taste, price)
        st.rerun(scope="fragment")
    if remove:
        delete_rating(rater, r)
        st.rerun(scope="fragment")
    ids = [m["id"] for m in MEMBERS]
    fans = st.multiselect("Favourite of", ids, default=[m["id"] for m in MEMBERS if r["id"] in (m.get("favs") or [])],
                          format_func=mname, key=f"fans-{r['id']}")
    b1, b2, b3 = st.columns(3)
    if b1.button("Save favourites", key="fav-save"):
        for m in MEMBERS:
            favs = [x for x in (m.get("favs") or []) if x != r["id"]] + ([r["id"]] if m["id"] in fans else [])
            if favs != (m.get("favs") or []):
                save_member({**m, "favs": favs})
        st.rerun()
    if b2.button("Add ingredients to shopping list", key="to-shop"):
        added = 0
        for q, u, nm in r["ingredients"]:
            if not q and re.search(r"to taste|as needed|for (garnish|serving|drizzling|frying)|optional|cooking spray", nm.lower()):
                continue
            add_to_shopping(L.shopping_name(nm), round(q * f, 2) if q else 0, u, r["name"])
            added += 1
        st.toast(f"{added} ingredients added to the shopping list")
        st.rerun()
    if b3.button("Cooked it: split the cost", type="primary", key="cooked"):
        mark_cooked(r)
        st.rerun()
    if r.get("custom") and st.button("Delete recipe", key="del-recipe"):
        store.delete("recipes", r["id"])
        for m in MEMBERS:
            if r["id"] in (m.get("favs") or []):
                save_member({**m, "favs": [x for x in m["favs"] if x != r["id"]]})
        st.rerun()


def mark_cooked(r):
    """Log the meal (for 'How was it?') and open the expense form for the shopping."""
    store.put("meals", {"id": store.new_id("meal"), "recipe": r["id"], "name": r["name"], "date": L.today(),
                        "eaters": [m["id"] for m in present()]})
    ss.pending_cost = {"title": "Cooked: " + r["name"], "amount": None, "cat": "Groceries", "currency": BASE}


def go(section_name, tab=None):
    ss.nav = section_name
    if tab:
        ss.org_tab = tab


def page_header(section_name, title=None, sub=None):
    st.markdown(f'<div class="nk-head"><span class="nk-date">{html.escape(sub or fmt_date(L.today(), long=True))}</span>'
                f'<h1>{html.escape(title or PAGE_TITLES[section_name])}</h1></div>', unsafe_allow_html=True)


def header_with_button(section_name, label, key, title=None, sub=None, primary=True) -> bool:
    """Page title on the left, one action button on the right. Returns True when the button is clicked."""
    a, b = st.columns([4, 1.1], vertical_alignment="bottom")
    with a:
        page_header(section_name, title, sub)
    return b.button(label, key=key, type="primary" if primary else "secondary", use_container_width=True)


def me():
    """The flatmate picked under "I am" in the sidebar."""
    return member(ss.get("me")) or (MEMBERS[0] if MEMBERS else None)


def greeting() -> str:
    try:
        from zoneinfo import ZoneInfo
        h = datetime.now(ZoneInfo(TIMEZONE)).hour
    except Exception:
        h = datetime.now().hour
    return "Good morning" if 4 <= h < 11 else "Good afternoon" if 11 <= h < 18 else "Good evening"


def open_transfers():
    return L.settle(L.balances(MEMBERS, S["expenses"], BASE, rate))


def due_items(day=None):
    """Chores and dated tasks that are due today or overdue."""
    t = day or L.today()
    return [x for x in S["tasks"] if x.get("due") and x["due"] <= t
            and (x.get("kind") == "chore" or (x.get("kind") == "todo" and not x.get("done")))]


def upcoming_items(n=5):
    """Chores and open dated tasks, soonest first."""
    items = [x for x in S["tasks"] if x.get("due") and (x.get("kind") == "chore" or not x.get("done"))]
    return sorted(items, key=lambda x: x["due"])[:n]


def pending_ratings(only=None, exclude=None):
    """Recently cooked meals that someone who ate hasn't rated yet: [(meal, [member ids])]."""
    rated = {(d.get("member"), d.get("recipe")) for d in S["ratings"]}
    todo = []
    for meal in sorted(S["meals"], key=lambda x: x.get("date", ""), reverse=True):
        if meal.get("closed") or L.days_until(meal["date"]) < -14:
            continue
        pending = [mid for mid in meal.get("eaters") or [] if member(mid) and (mid, meal["recipe"]) not in rated
                   and (only is None or mid == only) and mid != exclude]
        if pending:
            todo.append((meal, pending))
    return todo


def open_shopping():
    return [x for x in S["shopping"] if not x.get("done")]


def prefs_banner():
    if not missing:
        return
    c1, c2 = st.columns([4, 1], vertical_alignment="center")
    c1.info(f"Food preferences are missing for {', '.join(m['name'] for m in missing)}. "
            "Answer a few quick questions so the suggestions fit.")
    if c2.button("Fill in now", type="primary", key="prefs-fill"):
        ss.pref_queue = [m["id"] for m in missing]
        ss.pref_total = len(missing)
        st.rerun()


@st.dialog("New expense")
def new_expense_dialog():
    m = me()
    if expense_form({"payer": m["id"] if m else None}, "dlg-expense"):
        st.toast("Expense saved")
        st.rerun()


@st.dialog("Add an absence")
def absence_dialog():
    ids = [m["id"] for m in MEMBERS]
    mine = me()
    with st.form("away", clear_on_submit=True):
        mid = st.selectbox("Who's away?", ids, format_func=mname, index=ids.index(mine["id"]) if mine else 0)
        start = max(ss.sel_day, date.today())
        rng = st.date_input("Period", value=(start, start), format=DATE_FMT)
        ok = st.form_submit_button("Add", type="primary")
    if ok:
        if isinstance(rng, (tuple, list)) and len(rng) == 2:
            a_, b_ = sorted(rng)
            m = member(mid)
            save_member({**m, "away": (m.get("away") or []) + [{"id": store.new_id("a"), "from": a_.isoformat(), "to": b_.isoformat()}]})
            reassign_chores()
            st.toast(f"{m['name']} is away from {short_date(a_)} to {short_date(b_)}")
            st.rerun()
        else:
            st.error("Please choose a start and an end date.")


@st.dialog("Add a flatmate")
def add_member_dialog():
    with st.form("add-member", clear_on_submit=True):
        n = st.text_input("Name")
        ok = st.form_submit_button("Add", type="primary")
    if ok and n.strip():
        used = {m.get("ci") for m in MEMBERS}
        ci = next((i for i in range(6) if i not in used), len(MEMBERS) % 6)
        mid = store.new_id("m")
        store.put("members", {"id": mid, "name": n.strip(), "ci": ci, "present": True, "favs": [], "prefs": None, "away": []})
        ss.pref_queue = [mid]
        st.rerun()


@st.dialog("Add your own recipe", width="large")
def own_recipe_dialog():
    with st.form("new-recipe", clear_on_submit=True):
        name = st.text_input("Name", placeholder="Grandma's lentil soup")
        a, b, c = st.columns(3)
        serv = a.number_input("Serves", min_value=1, value=4)
        time = b.number_input("Minutes", min_value=1, value=30)
        diet = c.selectbox("Type", list(DIET_LABEL), format_func=DIET_LABEL.get)
        e1, e2, e3 = st.columns(3)
        allergens = e1.multiselect("Contains", ALLERGIES)
        rc = e2.selectbox("Cuisine", [""] + CUISINES, format_func=lambda c: c.capitalize() if c else "—")
        rcourse = e3.selectbox("Course", list(recipe_db.COURSES), format_func=recipe_db.COURSES.get)
        ings = st.text_area("Ingredients, one per line", placeholder="200 g lentils\n1 onion\n2 tbsp vinegar")
        steps = st.text_area("Steps, one per line")
        ok = st.form_submit_button("Save", type="primary")
    if ok:
        if not name.strip():
            st.error("Please give the recipe a name.")
            return
        store.put("recipes", {"id": store.new_id("r"), "name": name.strip(), "servings": int(serv), "time": int(time),
                              "diet": diet, "allergens": allergens, "cuisine": rc, "course": rcourse, "tags": [],
                              "ingredients": [x for x in map(L.parse_ingredient, ings.splitlines()) if x],
                              "steps": [s.strip() for s in steps.splitlines() if s.strip()]})
        st.toast("Recipe saved")
        st.rerun()


def prefs_form(mid, step=1, total=1):
    m = member(mid)
    p = m.get("prefs") or {}
    st.markdown(f"#### What does {html.escape(m['name'])} like to eat?" + (f"  ·  Person {step} of {total}" if total > 1 else ""))
    with st.form(f"prefs-{mid}"):
        diet = st.radio("Diet", list(DIETS), format_func=DIETS.get, horizontal=True,
                        index=list(DIETS).index(p.get("diet") or "any") if (p.get("diet") or "any") in DIETS else 0)
        allergies = st.multiselect("Can't eat (allergies, intolerances)", ALLERGIES,
                                   default=[a for a in (p.get("allergies") or []) if a in ALLERGIES])
        likes = st.text_input("Really likes", value=p.get("likes", ""), placeholder="e.g. pumpkin, pasta, spicy",
                              help="Ingredients or dishes, separated by commas.")
        dislikes = st.text_input("Doesn't like at all", value=p.get("dislikes", ""), placeholder="e.g. mushrooms, coriander, olives",
                                 help="Recipes with these ingredients won't be suggested while this person is home.")
        cuisines = st.multiselect("Favourite cuisines", CUISINES, default=[c for c in (p.get("cuisines") or []) if c in CUISINES],
                                  format_func=str.capitalize)
        c1, c2 = st.columns(2)
        ok = c1.form_submit_button("Save" + (" and continue" if total > step else ""), type="primary")
        skip = c2.form_submit_button("Skip" if total > 1 else "Cancel")
    if ok:
        save_member({**m, "prefs": {"diet": diet, "allergies": allergies, "likes": likes.strip(), "dislikes": dislikes.strip(),
                                    "cuisines": cuisines, "done": True}})
    if ok or skip:
        ss.pref_queue = ss.pref_queue[1:]
        st.rerun()


# ====================== Sidebar: brand, "I am", navigation, who's home ======================
ss.setdefault("nav", "Today")
if ss.nav not in SECTIONS:
    ss.nav = "Today"
LOGO = ('<span class="nk-logo"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1A1405" stroke-width="2.2" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/></svg></span>')
st.sidebar.markdown(f'<div class="nk-brand">{LOGO}<span>WG Organizer</span></div>', unsafe_allow_html=True)

if not MEMBERS:
    st.markdown('<div class="nk-head"><span class="nk-date">Welcome</span><h1>Who lives in your flat?</h1></div>', unsafe_allow_html=True)
    st.write("Add all your flatmates, separated by commas. The app will then ask each person a few questions about what they like to eat.")
    with st.form("setup"):
        names = st.text_input("Names", placeholder="Lena, Jonas, Aylin, Tim")
        base = st.selectbox("Main currency", fxmod.CURRENCIES)
        go_setup = st.form_submit_button("Create flat", type="primary")
    if go_setup:
        lst = [n.strip() for n in names.split(",") if n.strip()]
        if not lst:
            st.error("Please enter at least one name.")
        else:
            store.put("config", {"id": "settings", "base": base})
            ids = []
            for i, n in enumerate(lst):
                mid = store.new_id("m")
                ids.append(mid)
                store.put("members", {"id": mid, "name": n, "ci": i % 6, "present": True, "favs": [], "prefs": None, "away": []})
            ss.pref_queue = ids
            ss.nav = "Today"
            st.rerun()
    st.stop()

MEMBER_IDS = [m["id"] for m in MEMBERS]
if ss.get("me") not in MEMBER_IDS:
    # remembered in the link (?me=…), so a bookmark opens the app as that person
    try:
        qp = st.query_params.get("me")
    except Exception:
        qp = None
    ss.me = qp if qp in MEMBER_IDS else MEMBER_IDS[0]


def remember_me():
    try:
        st.query_params["me"] = ss.me
    except Exception:
        pass


TRANSFERS = open_transfers()
BADGES = {"Fair Split": (sum(1 for t in TRANSFERS if ss.me in (t["from"], t["to"])), "orange"),
          "House Organizer": (len(due_items()), "red")}

with st.sidebar:
    st.markdown('<div class="nk-label" style="margin-top:0">I am</div>', unsafe_allow_html=True)
    st.selectbox("I am", MEMBER_IDS, key="me", format_func=mname, on_change=remember_me, label_visibility="collapsed",
                 help="Your balance, your chores and your ratings are shown for this person.")
    st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
    for sec in SECTIONS:
        n, col = BADGES.get(sec, (0, ""))
        label = sec + (f"   :{col}[**{n}**]" if n else "")
        st.button(label, key=f"nav-{sec}", icon=NAV_ICONS[sec], type="primary" if ss.nav == sec else "secondary",
                  on_click=go, args=(sec,), use_container_width=True)
    st.markdown('<div class="nk-label">Home today</div>', unsafe_allow_html=True)
    for m in MEMBERS:
        ab = L.away_on(m, L.today())
        label = f":{TOGGLE_COLORS[(m.get('ci') or 0) % 6]}[●] {m['name']}" + (
            f" · away until {short_date(date.fromisoformat(ab['to']))}" if ab else "")
        st.toggle(label, value=L.is_home(m), key=f"pres-{m['id']}-{L.is_home(m)}", on_change=toggle_present, args=(m["id"],))

missing = [m for m in MEMBERS if not prefs_known(m)]
section = ss.nav

# Dialog requested in the previous run
if ss.get("pending_cost"):
    cost_dialog(ss.pop("pending_cost"))

# Food preference questionnaire (after setup or on request)
ss.pref_queue = [mid for mid in ss.pref_queue if member(mid)]
if ss.pref_queue:
    with st.container(border=True):
        total = ss.get("pref_total") or len(ss.pref_queue)
        ss.pref_total = max(total, len(ss.pref_queue))
        prefs_form(ss.pref_queue[0], ss.pref_total - len(ss.pref_queue) + 1, ss.pref_total)
    st.stop()
ss.pref_total = 0


# ====================== Fair Split ======================
def page_fair_split():
    if header_with_button("Fair Split", "+ Add expense", "split-add-exp"):
        new_expense_dialog()
    b = L.balances(MEMBERS, S["expenses"], BASE, rate)
    tr = TRANSFERS
    total = sum(to_base(e["eur"]) for e in S["expenses"] if e.get("cat") != "Settlement")
    mine = b.get(ss.me, 0)
    c1, c2, c3 = st.columns(3)
    c1.metric("Spent together", L.money(total, BASE))
    c2.metric("Open payments", len(tr))
    c3.metric("You get back" if mine > 0.005 else "You owe" if mine < -0.005 else "Your balance",
              L.money(abs(mine) if abs(mine) >= .005 else 0, BASE))

    left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.subheader("Expenses")
        if not S["expenses"]:
            st.info("No expenses yet. Add the first one with “+ Add expense”.")
        for e in sorted(S["expenses"], key=lambda x: (x.get("date", ""), x["id"]), reverse=True):
            with st.container(border=True):
                a, bcol, c = st.columns([3, 1.3, 0.8])
                parts = e.get("parts") or []
                if e.get("cat") == "Settlement":
                    sub = f"{who(e['payer'])} paid {', '.join(html.escape(mname(p)) for p in parts)}"
                else:
                    target = "for everyone" if len(parts) == len(MEMBERS) else "for " + ", ".join(html.escape(mname(p)) for p in parts)
                    sub = f"{who(e['payer'])} paid · {target}"
                a.markdown(f"**{html.escape(e['title'])}**  \n<small>{html.escape(e.get('cat', ''))} · {sub} · {fmt_date(e['date'])}</small>",
                           unsafe_allow_html=True)
                amt = f'<span class="mono">{L.money(e["amount"], e["currency"])}</span>'
                if e["currency"] != BASE:
                    amt += f"  \n<small>≈ {L.money(to_base(e['eur']), BASE)}</small>"
                bcol.markdown(amt, unsafe_allow_html=True)
                if c.button("Edit", key=f"edit-{e['id']}"):
                    edit_expense_dialog(e["id"])
    with right:
        with st.container(border=True):
            st.subheader("Balances")
            mx = max([1] + [abs(v) for v in b.values()])
            rows = []
            for m in MEMBERS:
                v = b.get(m["id"], 0)
                w = abs(v) / mx * 50
                bar = (f'<b style="left:50%;width:{w}%;background:{POS}"></b>' if v >= 0
                       else f'<b style="right:50%;width:{w}%;background:{NEG}"></b>')
                col = POS if v > 0.005 else NEG if v < -0.005 else "inherit"
                rows.append(f'{who(m["id"])}<div class="bar">{bar}</div>'
                            f'<span class="mono" style="color:{col}">{"+" if v > 0.005 else ""}{L.money(0 if abs(v) < .005 else v, BASE)}</span>')
            st.markdown(f'<div class="bal">{"".join(rows)}</div>', unsafe_allow_html=True)
            st.caption("Plus means: gets money back.")
        with st.container(border=True):
            st.subheader("Who pays whom?")
            if not tr:
                st.caption("All settled up.")
            for i, t in enumerate(tr):
                a, bcol, c = st.columns([2.2, 1.2, 1])
                you = " · <b>you</b>" if ss.me in (t["from"], t["to"]) else ""
                a.markdown(f"{who(t['from'])} → {who(t['to'])}{you}", unsafe_allow_html=True)
                bcol.markdown(f'<span class="mono">{L.money(t["v"], BASE)}</span>', unsafe_allow_html=True)
                if c.button("Paid", key=f"settle-{i}-{t['from']}-{t['to']}"):
                    store.put("expenses", {"id": store.new_id("e"), "title": f"Settlement {mname(t['from'])} → {mname(t['to'])}",
                                           "cat": "Settlement", "amount": t["v"], "currency": BASE, "eur": round(t["v"] * rate(BASE), 2),
                                           "payer": t["from"], "parts": [t["to"]], "date": L.today()})
                    st.rerun()
        other = sorted({e["currency"] for e in S["expenses"]} - {BASE})
        st.caption(("Expenses in " + ", ".join(other) + " are converted" if other else "Other currencies are converted")
                   + f" with the ECB rate of the day they were entered (today's rates: {fmt_date(FX['date'])})."
                   " Main currency and all rates: Flat & People.")


# ====================== House Organizer ======================
def day_cell(d, ev, month=None, sel=None, head=None):
    """One calendar day: date, who's away (red), chores and tasks."""
    x = date.fromisoformat(d)
    away = [m for m in MEMBERS if L.away_on(m, d)]
    es = ev.get(d, [])
    cls = ["day"]
    if month and x.month != month:
        cls.append("other")
    if away:
        cls.append("away")
    if d == L.today():
        cls.append("today")
    if d == sel:
        cls.append("sel")
    inner = f'<span class="wdn">{head}</span>' if head else ""
    inner += f'<span class="dn">{x.day}</span>'
    inner += "".join(f'<span class="ab"><span class="l">{html.escape(m["name"])} away</span>'
                     f'<span class="s">{html.escape(m["name"][:1])}</span></span>' for m in away)
    inner += "".join(f'<span class="ev{" late" if e["late"] else ""}"><i style="background:{mcolor(e["who"])}"></i>'
                     f'<span>{html.escape(e["title"])}</span></span>' for e in es[:3])
    if len(es) > 3:
        inner += f'<span style="opacity:.6">+{len(es) - 3} more</span>'
    return f'<div class="{" ".join(cls)}">{inner}</div>'


def calendar_html(year, month, sel):
    days = L.month_grid(year, month)
    ev = L.events_between(S["tasks"], MEMBERS, days[0], days[-1])
    cells = "".join(f'<div class="wd">{w}</div>' for w in WEEKDAYS)
    cells += "".join(day_cell(d, ev, month, sel) for d in days)
    return f'<div class="cal">{cells}</div>'


def week_html(start=None):
    """The next seven days, starting today."""
    start = start or L.today()
    days = [L.add_days(start, i) for i in range(7)]
    ev = L.events_between(S["tasks"], MEMBERS, days[0], days[-1])
    heads = ["Today" if i == 0 else WEEKDAYS[date.fromisoformat(d).weekday()] for i, d in enumerate(days)]
    return '<div class="week">' + "".join(day_cell(d, ev, head=h) for d, h in zip(days, heads)) + "</div>"


def org_calendar():
    y, mo = ss.cal
    left, right = st.columns([2.2, 1], gap="large")
    with left:
        with st.container(border=True):
            a, b, c, d = st.columns([0.6, 3, 0.6, 1])
            if a.button("‹", key="cal-prev", help="Previous month"):
                ss.cal = (y - 1, 12) if mo == 1 else (y, mo - 1)
                st.rerun()
            b.markdown(f"### {MONTHS[mo - 1]} {y}")
            if c.button("›", key="cal-next", help="Next month"):
                ss.cal = (y + 1, 1) if mo == 12 else (y, mo + 1)
                st.rerun()
            if d.button("Today", key="cal-today"):
                ss.cal = (date.today().year, date.today().month)
                ss.sel_day = date.today()
                st.rerun()
            st.markdown(calendar_html(y, mo, ss.sel_day.isoformat()), unsafe_allow_html=True)
            legend = " &nbsp; ".join(who(m["id"]) for m in MEMBERS)
            st.markdown(f'<small><span class="ab">red</span> = someone is away &nbsp;·&nbsp; {legend}</small>', unsafe_allow_html=True)
    with right:
        with st.container(key="aside-day"):
            sel = st.date_input("View day", key="sel_day", format=DATE_FMT,
                                on_change=lambda: ss.update(cal=(ss.sel_day.year, ss.sel_day.month)))
            s = sel.isoformat()
            st.markdown(f'<div class="nk-h">{fmt_date(s, long=True)}</div>', unsafe_allow_html=True)
            for m in MEMBERS:
                ab = L.away_on(m, s)
                if ab:
                    st.markdown(f'<span class="pill late">{html.escape(m["name"])} away until {fmt_date(ab["to"])}</span>',
                                unsafe_allow_html=True)
            st.caption("Home: " + (", ".join(m["name"] for m in MEMBERS if not L.away_on(m, s)) or "nobody"))
            evs = L.events_between(S["tasks"], MEMBERS, s, s).get(s, [])
            if not evs:
                st.caption("Nothing planned.")
            for e in evs:
                st.markdown(f'<div class="nk-line"><span>{html.escape(e["title"])} · {html.escape(mname(e["who"]))}</span>'
                            + ('<span class="pill late">overdue</span>' if e["late"] else
                               f'<span class="nk-meta">{"Chore" if e["kind"] == "chore" else "Task"}</span>') + "</div>",
                            unsafe_allow_html=True)
        with st.container(key="aside-away"):
            st.markdown('<div class="nk-h">Planned absences</div>', unsafe_allow_html=True)
            upcoming = sorted(((m, a) for m in MEMBERS for a in (m.get("away") or []) if a["to"] >= L.today()),
                              key=lambda x: x[1]["from"])
            if not upcoming:
                st.caption("None. Everyone's around.")
            for m, a in upcoming:
                c1, c2 = st.columns([4, 1], vertical_alignment="center")
                c1.markdown(f"{who(m['id'])} {fmt_date(a['from'])} – {fmt_date(a['to'])}", unsafe_allow_html=True)
                if c2.button("✕", key=f"del-away-{a['id']}", help="Delete absence"):
                    save_member({**m, "away": [x for x in m["away"] if x["id"] != a["id"]]})
                    st.rerun()


def org_chores():
    ids = [m["id"] for m in MEMBERS]
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.subheader("Cleaning rota")
        st.caption("Ticking off a chore passes it to the next person who is home on its next date.")
        for t in sorted([t for t in S["tasks"] if t.get("kind") == "chore"], key=lambda x: x["due"]):
            with st.container(border=True):
                a, b, c = st.columns([4, 1, 1], vertical_alignment="center")
                you = " · you" if t["assignee"] == ss.me else ""
                a.markdown(f"**{html.escape(t['title'])}** {due_badge(t['due'])}  \n"
                           f"<small>{who(t['assignee'])}{you} · every {t['every']} days</small>", unsafe_allow_html=True)
                if b.button("Done", key=f"done-{t['id']}", type="primary" if L.days_until(t["due"]) <= 0 else "secondary"):
                    nt = L.chore_done(t, MEMBERS)
                    store.put("tasks", nt)
                    st.toast(f"Thanks! Next up: {mname(nt['assignee'])}, {fmt_date(nt['due'])}")
                    st.rerun()
                if c.button("✕", key=f"del-{t['id']}", help="Delete chore"):
                    store.delete("tasks", t["id"])
                    st.rerun()
        with st.expander("New chore"):
            with st.form("new-chore", clear_on_submit=True):
                title = st.text_input("What?", placeholder="Clean the fridge")
                every = st.number_input("Every … days", min_value=1, value=7)
                due = st.date_input("First due", value=date.today(), format=DATE_FMT)
                first = st.selectbox("Starts with", ids, format_func=mname)
                if st.form_submit_button("Save", type="primary") and title.strip():
                    store.put("tasks", {"id": store.new_id("t"), "kind": "chore", "title": title.strip(), "every": int(every),
                                        "due": due.isoformat(), "assignee": first})
                    st.rerun()
    with c2:
        st.subheader("Tasks")
        with st.form("new-todo", clear_on_submit=True):
            title = st.text_input("New task", placeholder="e.g. bleed the radiators")
            a, b = st.columns(2)
            owner = a.selectbox("Who?", [""] + ids, format_func=lambda x: mname(x) if x else "nobody")
            due = b.date_input("By when?", value=None, format=DATE_FMT)
            if st.form_submit_button("Add") and title.strip():
                store.put("tasks", {"id": store.new_id("t"), "kind": "todo", "title": title.strip(), "assignee": owner,
                                    "due": due.isoformat() if due else "", "done": False})
                st.rerun()
        todos = sorted([t for t in S["tasks"] if t.get("kind") == "todo"], key=lambda x: (x.get("done", False), x.get("due") or "9"))
        if not todos:
            st.caption("No open tasks.")
        for t in todos:
            a, b = st.columns([5, 1])
            label = t["title"] + (f" · {mname(t['assignee'])}" if t.get("assignee") else "") + (
                f" · by {fmt_date(t['due'])}" if t.get("due") and not t.get("done") else "")
            val = a.checkbox(label, value=t.get("done", False), key=f"todo-{t['id']}-{t.get('done', False)}")
            if val != t.get("done", False):
                store.put("tasks", {**t, "done": val})
                st.rerun()
            if b.button("✕", key=f"deltodo-{t['id']}"):
                store.delete("tasks", t["id"])
                st.rerun()


def org_shopping():
    left, right = st.columns([1.6, 1], gap="large")
    with left:
        with st.form("new-item", clear_on_submit=True):
            a, b = st.columns([4, 1], vertical_alignment="bottom")
            txt = a.text_input("Add an item", placeholder="e.g. 2 l oat milk")
            if b.form_submit_button("Add", type="primary", use_container_width=True) and txt.strip():
                q, u, n = L.parse_ingredient(txt)
                add_to_shopping(n, q, u)
                st.rerun()
        items = sorted(S["shopping"], key=lambda s: (s.get("done", False), s["name"].lower()))
        if not items:
            st.caption("The list is empty.")
        for s in items:
            a, b = st.columns([6, 1])
            label = (f"{L.fmt_qty(s['qty'])} {s.get('unit', '')} " if s.get("qty") else "") + s["name"] + (
                f"  ·  for {s['from']}" if s.get("from") else "")
            val = a.checkbox(label, value=s.get("done", False), key=f"shop-{s['id']}-{s.get('done', False)}")
            if val != s.get("done", False):
                store.put("shopping", {**s, "done": val})
                st.rerun()
            if b.button("✕", key=f"delshop-{s['id']}"):
                store.delete("shopping", s["id"])
                st.rerun()
    with right:
        with st.container(key="aside-checkout"):
            bought = [s for s in S["shopping"] if s.get("done")]
            st.markdown('<div class="nk-h">At the till</div>', unsafe_allow_html=True)
            st.caption("Tick what's in the trolley. “Check out” adds the receipt to Fair Split and clears those items.")
            if st.button(f"Check out {len(bought)} item{'s' if len(bought) != 1 else ''}", type="primary",
                         disabled=not bought, key="checkout", use_container_width=True):
                names = ", ".join(s["name"] for s in bought[:4]) + (" …" if len(bought) > 4 else "")
                cost_dialog({"title": "Shopping: " + names, "cat": "Groceries", "currency": BASE}, [s["id"] for s in bought])


def page_organizer():
    if header_with_button("House Organizer", "+ Add absence", "org-add-away"):
        absence_dialog()
    counts = {"Chores & tasks": len(due_items()), "Shopping list": len(open_shopping())}
    if ss.get("org_tab") not in ORG_TABS:
        ss.org_tab = "Calendar"
    st.segmented_control("View", ORG_TABS, key="org_tab", label_visibility="collapsed",
                         format_func=lambda t: f"{t} ({counts[t]})" if counts.get(t) else t)
    tab = ss.get("org_tab") or "Calendar"
    if tab == "Chores & tasks":
        org_chores()
    elif tab == "Shopping list":
        org_shopping()
    else:
        org_calendar()


# ====================== Cooking ======================
def recipe_meta(r) -> str:
    meta = [x for x in [fmt_minutes(r), DIET_LABEL.get(r.get("diet"), ""), (r.get("cuisine") or "").capitalize()] if x]
    if r.get("custom"):
        meta.append("your own")
    elif r.get("source") == "builtin":
        meta.append("our pick")
    return " · ".join(meta)


def recipe_chips(ev) -> str:
    """Why a dish fits (favourites, likes, cuisines) or, if it doesn't, why not."""
    if not ev["ok"]:
        return f'<div class="blockers">Not suitable: {html.escape("; ".join(ev["blockers"]))}</div>'
    by = {}
    for m, t in ev["reasons"]:
        by.setdefault(m["id"], (m, []))[1].append(t)
    chips = "".join(f'<span class="lk" style="color:{mcolor(mid)};border-color:{mcolor(mid)}">'
                    f'{html.escape(m["name"])}: {html.escape(", ".join(dict.fromkeys(ts)))}</span>' for mid, (m, ts) in by.items())
    if ev.get("daily"):  # one of today's top picks from the learned ratings
        names = " & ".join(m["name"] for m, _, _ in ev.get("learned", []))
        chips = (f'<span class="lk ml rec" title="Picked for {html.escape(names)} from your ratings '
                 f'(50 % taste, 50 % price)">★ Daily recommendation</span>') + chips
    return chips


def recipe_row(ev, idx, prefix, rank=None):
    """One line of the ranked list: number, name, details, reasons, View."""
    r = ev["r"]
    with st.container(key=f"{prefix}-row-{idx}"):
        a, b, c = st.columns([0.45, 6, 1.1], vertical_alignment="center")
        a.markdown(f'<span class="nk-rank">{rank:02d}</span>' if rank else "", unsafe_allow_html=True)
        pts = f' <span class="nk-meta">· {ev["score"]:.0f} pts</span>' if round(ev["score"]) else ""
        b.markdown(f'<div class="nk-name">{html.escape(r["name"])}{pts}</div><div class="nk-meta">{html.escape(recipe_meta(r))}</div>'
                   f'{recipe_chips(ev)}', unsafe_allow_html=True)
        if c.button("View", key=f"{prefix}-{idx}-{r['id']}", use_container_width=True):
            recipe_dialog(r["id"])


def one_tag(ev) -> str:
    """The single most useful label for a recipe card."""
    if ev.get("daily"):
        return '<span class="lk ml rec">★ Daily recommendation</span>'
    if ev.get("reasons"):
        m, t = ev["reasons"][0]
        return (f'<span class="lk" style="color:{mcolor(m["id"])};border-color:{mcolor(m["id"])}">'
                f'{html.escape(m["name"])}: {html.escape(t)}</span>')
    return ""


def recipe_card(ev, rank):
    """A card in the Cooking grid: rank, name, details, one label, View."""
    r = ev["r"]
    with st.container(key=f"card-{rank}"):
        st.markdown(f'<span class="nk-rank">{rank:02d}</span><div class="nk-name">{html.escape(r["name"])}</div>'
                    f'<div class="nk-meta">{html.escape(recipe_meta(r))}</div>{one_tag(ev)}', unsafe_allow_html=True)
        if st.button("View →", key=f"card-view-{rank}-{r['id']}", use_container_width=True):
            recipe_dialog(r["id"])


def recipe_hero(ev, learners, pr, kicker=None, more=False):
    """Today's best match as a large card (top of Cooking and Today)."""
    r = ev["r"]
    full = recipe(r["id"]) or r
    names = [m["name"] for m in pr]
    who_txt = ", ".join(names[:-1]) + (" and " if len(names) > 1 else "") + names[-1] if names else "you"
    with st.container(key="hero"):
        left, right = st.columns([1.7, 1], vertical_alignment="center", gap="large")
        with left:
            kicker = kicker or ("★ Daily recommendation" if ev.get("daily") else "★ Best match today")
            why = "Picked for " + who_txt + (" from your ratings" if learners else "")
            details = " · ".join(x for x in [DIET_LABEL.get(r.get("diet"), ""), fmt_minutes(r)] if x)
            st.markdown(f'<div class="nk-kicker">{html.escape(kicker)}</div><div class="nk-hero-name">{html.escape(r["name"])}</div>'
                        f'<p class="nk-hero-text">{html.escape(why)} · {html.escape(details)}</p>', unsafe_allow_html=True)
            x, y, z = st.columns([1, 1, 1.2])
            if x.button("View recipe", key="hero-view", type="primary", use_container_width=True):
                recipe_dialog(r["id"])
            if y.button("Cooked it", key="hero-cooked", use_container_width=True):
                mark_cooked(full)
                st.rerun()
            if more:
                z.button("More ideas →", key="hero-more", on_click=go, args=("Cooking",), use_container_width=True)
        with right:
            t = r.get("time")
            st.markdown('<div class="nk-tiles">'
                        f'<div class="nk-tile"><b>{t if t and t < 600 else "–"}</b><span>minutes</span></div>'
                        f'<div class="nk-tile"><b>{portions()}</b><span>servings</span></div>'
                        f'<div class="nk-tile"><b>{len(full.get("ingredients") or [])}</b><span>ingredients</span></div>'
                        '</div>', unsafe_allow_html=True)


def matches_filters(r, words, course, cuisine, max_time):
    if course != "all" and (r.get("course") or "main") != course:
        return False
    if cuisine != "all" and r.get("cuisine") != cuisine:
        return False
    if max_time and (not r.get("time") or r["time"] > max_time):
        return False
    if words:
        text = L.recipe_text(r)
        return all(w in text for w in words)
    return True


PAGE = 24
DAILY_PICKS = 3  # the best-ranked dishes of the day get the "Daily recommendation" label
DEFAULT_COURSE = list(recipe_db.COURSES)[0]


def ranked(pr, words=(), course=DEFAULT_COURSE, cuisine="all", max_time=0):
    """Rules first (diet, allergies, dislikes, favourites, likes), then each person's taste model re-ranks."""
    pool = own_recipes() + DB_INDEX
    evals = [L.evaluate(r, pr) for r in pool if matches_filters(r, words, course, cuisine, max_time)]
    fits = [e for e in evals if e["ok"]]
    learners = [(m, mod) for m in pr if (mod := model_for(m)) is not None]
    if learners and fits:
        X = FEATURES.matrix([e["r"] for e in fits])
        for m, mod in learners:
            for e, p in zip(fits, mod.predict(X)):
                p = float(p)
                e["score"] += mod.bonus(p)
                e.setdefault("learned", []).append((m, p, mod.percentile(p)))
    order = {"builtin": 0, "db": 1}
    fits.sort(key=lambda e: (-e["score"], order.get(e["r"].get("source"), 0), e["r"]["name"]))
    if learners:
        for e in fits[:DAILY_PICKS]:
            e["daily"] = True
    return fits, [e for e in evals if not e["ok"]], learners


def rating_prompts(only=None, exclude=None, limit=5):
    """'How was it?': taste and price from 1 to 10 for recently cooked dishes."""
    todo = pending_ratings(only, exclude)
    if not todo:
        return
    with st.container(border=True):
        st.subheader("How was it?")
        st.caption("Taste and price from 1 to 10. Both count 50 % towards the overall rating the app learns from.")
        for meal, pending in todo[:limit]:
            r = recipe(meal["recipe"]) or {"id": meal["recipe"], "name": meal["name"]}
            a, c = st.columns([6, 1])
            a.markdown(f"**{html.escape(meal['name'])}** &nbsp; <small>{fmt_date(meal['date'])}</small>", unsafe_allow_html=True)
            cols = st.columns(min(len(pending), 3))
            for i, mid in enumerate(pending):
                with cols[i % len(cols)]:
                    with st.form(f"mr-{meal['id']}-{mid}"):
                        st.markdown(who(mid), unsafe_allow_html=True)
                        taste = st.slider("Taste", 1, 10, 7, key=f"mt-{meal['id']}-{mid}", help=TASTE_HELP)
                        price = st.slider("Price", 1, 10, 7, key=f"mp-{meal['id']}-{mid}", help=PRICE_HELP)
                        if st.form_submit_button("Save rating", type="primary"):
                            save_rating(mid, r, taste, price)
                            st.rerun()
            if c.button("✕", key=f"mx-{meal['id']}", help="Don't ask about this meal"):
                store.put("meals", {**meal, "closed": True})
                st.rerun()


# ====================== Today ======================
def tile(col, key, label, value, sub, color=None, text=False, button=None, target=None):
    with col:
        with st.container(key=key):
            st.markdown(f'<div class="nk-tl">{html.escape(label)}</div>'
                        f'<div class="nk-tv{" txt" if text else ""}" style="color:{color or "inherit"}">{html.escape(value)}</div>'
                        f'<div class="nk-ts">{sub}</div>', unsafe_allow_html=True)
            if button:
                st.button(button, key=f"{key}-go", on_click=go, args=target)


def page_today():
    m = me()
    pr = present()
    if header_with_button("Today", "+ Add expense", "today-add-exp", title=f"{greeting()}, {m['name']}"):
        new_expense_dialog()
    prefs_banner()

    # four tiles: my money, my next chore, the shopping list, my ratings
    v = L.balances(MEMBERS, S["expenses"], BASE, rate).get(m["id"], 0)
    t1, t2, t3, t4 = st.columns(4)
    if v > 0.005:
        tile(t1, "tile-bal", "You get back", L.money(v, BASE), "from the others", POS, button="Fair Split →", target=("Fair Split",))
    elif v < -0.005:
        to = ", ".join(html.escape(mname(t["to"])) for t in TRANSFERS if t["from"] == m["id"])
        tile(t1, "tile-bal", "You owe", L.money(-v, BASE), f"to {to}" if to else "to the others", NEG,
             button="Settle up →", target=("Fair Split",))
    else:
        tile(t1, "tile-bal", "Your balance", L.money(0, BASE), "all square", MUTED, button="Fair Split →", target=("Fair Split",))
    mine = sorted([t for t in S["tasks"] if t.get("kind") == "chore" and t.get("assignee") == m["id"]], key=lambda t: t["due"])
    if mine:
        tile(t2, "tile-chore", "Your next chore", mine[0]["title"], due_badge(mine[0]["due"]), text=True,
             button="Chores →", target=("House Organizer", "Chores & tasks"))
    else:
        tile(t2, "tile-chore", "Your next chore", "Nothing", "no chore is yours right now", MUTED, text=True,
             button="Chores →", target=("House Organizer", "Chores & tasks"))
    items = open_shopping()
    names = ", ".join(html.escape(x["name"]) for x in items[:3]) + (" …" if len(items) > 3 else "")
    tile(t3, "tile-shop", "Shopping list", str(len(items)), names or "nothing to buy",
         button="Open list →", target=("House Organizer", "Shopping list"))
    todo = pending_ratings(only=m["id"])
    tile(t4, "tile-rate", "Rate a meal", str(len(todo)),
         "waiting for your rating below" if todo else "all your meals are rated", AMBER if todo else MUTED)

    left, right = st.columns([2.2, 1], gap="large")
    with left:
        fits, _, learners = ranked(pr)
        if fits:
            recipe_hero(fits[0], learners, pr, kicker="★ Tonight", more=True)
        elif not pr:
            st.info("Nobody is marked as home today. Switch people on under “Home today” in the sidebar.")
        rating_prompts(only=m["id"])
        others = pending_ratings(exclude=m["id"])
        if others:
            waiting = sorted({mname(mid) for _, p in others for mid in p})
            with st.expander(f"Others still to rate: {', '.join(waiting)}"):
                rating_prompts(exclude=m["id"])
        st.subheader("This week")
        st.markdown(week_html(), unsafe_allow_html=True)
    with right:
        with st.container(key="aside-due"):
            lines = "".join(
                f'<div class="nk-line"><span>{html.escape(t["title"])} · '
                f'{"<b>you</b>" if t.get("assignee") == m["id"] else html.escape(mname(t.get("assignee")) if t.get("assignee") else "anyone")}'
                f'</span>{due_badge(t["due"])}</div>' for t in upcoming_items()) or '<div class="nk-meta">Nothing planned.</div>'
            st.markdown(f'<div class="nk-h">Due in the flat</div>{lines}', unsafe_allow_html=True)
            st.button("Open organizer →", key="today-go-org", on_click=go, args=("House Organizer", "Chores & tasks"))
        with st.container(key="aside-home"):
            lines = "".join(
                f'<div class="nk-line">{who(x["id"])}'
                + (f'<span class="pill late">away until {fmt_date(ab["to"])}</span>' if (ab := L.away_on(x, L.today()))
                   else '<span class="pill ok">home</span>' if L.is_home(x) else '<span class="pill late">not home</span>')
                + "</div>" for x in MEMBERS)
            st.markdown(f'<div class="nk-h">Who\'s home</div>{lines}', unsafe_allow_html=True)
        with st.container(key="aside-shop"):
            st.markdown(f'<div class="nk-h">Shopping list</div><div class="nk-meta">{names or "The list is empty."}</div>',
                        unsafe_allow_html=True)
            st.button(f"Open list ({len(items)})", key="today-go-shop", on_click=go, args=("House Organizer", "Shopping list"))


# ====================== Cooking ======================
def page_cooking():
    pr = present()
    if header_with_button("Cooking", "+ Own recipe", "own-recipe", primary=False):
        own_recipe_dialog()
    prefs_banner()

    f1, f2, f3, f4, f5 = st.columns([2.2, 1.3, 1.3, 1, 0.9])
    query = f1.text_input("Search recipes", placeholder=f"Search {len(own_recipes()) + len(DB_INDEX):,} recipes", key="rq")
    course = f2.selectbox("Course", ["all"] + list(recipe_db.COURSES), index=1, key="rcourse",
                          format_func=lambda c: "All courses" if c == "all" else recipe_db.COURSES[c])
    cuisine = f3.selectbox("Cuisine", ["all"] + CUISINES, key="rcuisine",
                           format_func=lambda c: "All cuisines" if c == "all" else c.capitalize())
    max_time = f4.selectbox("Max. time", [0, 20, 30, 45, 60, 90], key="rtime",
                            format_func=lambda t: "Any" if not t else f"{t} min")
    f5.number_input("Servings", min_value=1, value=max(1, len(pr)), key=f"portions-{max(1, len(pr))}")

    words = [w for w in re.split(r"[\s,]+", query.lower()) if w]
    fits, nofit, learners = ranked(pr, words, course, cuisine, max_time)
    filt = (query, course, cuisine, max_time, tuple(m["id"] for m in pr))
    if ss.get("rfilt") != filt:
        ss.rfilt, ss.rlimit = filt, PAGE
    shown = fits[: ss.rlimit]

    if DB_ERR:
        st.warning(f"Only our {len(BUILTIN)} own recipes are available. {DB_ERR}")
    if not pr:
        st.info("Nobody is marked as home today. Switch people on under “Home today” in the sidebar.")
    if fits:
        recipe_hero(fits[0], learners, pr)

    st.subheader(f"Suits everyone today ({len(fits):,})")
    note = (f" Ranking also uses what the app learned about {', '.join(m['name'] for m, _ in learners)}."
            if learners else " Rate dishes (taste and price, 1–10) and the app will learn what you like.")
    st.caption("Best matches for the people at home come first." + note)
    if not fits:
        st.caption("No recipe matches everyone at the table with these filters. Try other filters or add your own recipe.")
    rest = shown[1:]
    for start in range(0, len(rest), 3):
        cols = st.columns(3)
        for j, e in enumerate(rest[start:start + 3]):
            with cols[j]:
                recipe_card(e, start + j + 2)
    if len(fits) > len(shown):
        if st.button(f"Show more ({len(fits) - len(shown):,} left)", key="more"):
            ss.rlimit += PAGE
            st.rerun()
    if nofit:
        with st.expander(f"Not suitable today ({len(nofit):,})"):
            st.caption("A few examples and why they don't work for everyone at the table:")
            for i, e in enumerate(nofit[:9]):
                recipe_row(e, i, "nofit")
    a, b = st.columns([3, 1.3], vertical_alignment="center")
    a.caption("Food preferences and what the app has learned about each of you are on Flat & People.")
    b.button("Flat & People →", key="cook-go-people", on_click=go, args=("Flat & People",), use_container_width=True)


# ====================== Flat & People ======================
def learned_summary(m):
    """(text, stats) of what the taste model knows about a person."""
    mod = model_for(m)
    if mod is None:
        return "Nothing learned yet. Rate a dish after cooking or mark a favourite to start.", ""
    mine = [d for d in S["ratings"] if d.get("member") == m["id"] and d.get("taste") is not None]
    avg = (f" · avg. taste {sum(d['taste'] for d in mine) / len(mine):.1f}, price {sum(d['price'] for d in mine) / len(mine):.1f}"
           if mine else "")
    stats = (f"{mod.n_rated} rating{'s' if mod.n_rated != 1 else ''} · {mod.n_favs} favourite{'s' if mod.n_favs != 1 else ''}"
             f"{avg} · counts {mod.confidence:.0%}")
    if mod.confidence < 3 / ml.FULL_CONFIDENCE_AT:
        return f"A few more ratings and it can say what {m['name']} likes.", stats
    bits = []
    if mod.likes:
        bits.append("Leans towards " + ", ".join(mod.likes))
    if mod.dislikes:
        bits.append("less keen on " + ", ".join(mod.dislikes))
    return " · ".join(bits) or "No clear pattern yet.", stats


def person_card(m, bal):
    p = m.get("prefs") or {}
    ab = L.away_on(m, L.today())
    if ab:
        status, scol = f"Away until {fmt_date(ab['to'])}", NEG
    elif L.is_home(m):
        status, scol = "Home today", POS
    else:
        status, scol = "Not home today", NEG
    with st.container(key=f"person-{m['id']}"):
        you = ' <span class="pill today">you</span>' if m["id"] == ss.me else ""
        st.markdown(f'<div class="nk-person"><span class="nk-avatar" style="background:{mcolor(m["id"])}">'
                    f'{html.escape(m["name"][:1].upper())}</span><div><div class="nk-pname">{html.escape(m["name"])}{you}</div>'
                    f'<div style="font-size:.8rem;font-weight:700;color:{scol}">{html.escape(status)}</div></div></div>',
                    unsafe_allow_html=True)
        if prefs_known(m):
            allergy = ", ".join(p.get("allergies") or [])
            pills = (f'<span class="pill ok">{html.escape(DIETS.get(p.get("diet"), "Eats everything"))}</span> '
                     + (f'<span class="pill late">{html.escape(allergy)}</span>' if allergy else '<span class="pill">No allergies</span>'))
            lines = [("Likes", p.get("likes")), ("Won't eat", p.get("dislikes")),
                     ("Cuisines", ", ".join(c.capitalize() for c in p.get("cuisines") or []))]
            body = "".join(f'<div class="nk-small"><b>{k}</b> {html.escape(val)}</div>' for k, val in lines if val)
            st.markdown(f'<div style="margin:10px 0 4px">{pills}</div>{body}', unsafe_allow_html=True)
        else:
            st.markdown('<div class="nk-small" style="margin-top:10px">No food preferences yet.</div>', unsafe_allow_html=True)
        text, stats = learned_summary(m)
        st.markdown(f'<div class="nk-learn"><div class="nk-tl">The app has learned</div><div>{html.escape(text)}</div>'
                    + (f'<div class="nk-meta mono" style="font-size:.75rem;margin-top:3px">{html.escape(stats)}</div>' if stats else "")
                    + "</div>", unsafe_allow_html=True)
        col = POS if bal > 0.005 else NEG if bal < -0.005 else MUTED
        st.markdown(f'<div class="nk-line"><span class="nk-meta">Balance</span><span class="mono" style="color:{col};font-weight:700">'
                    f'{"+" if bal > 0.005 else ""}{L.money(0 if abs(bal) < .005 else bal, BASE)}</span></div>', unsafe_allow_html=True)
        a, b = st.columns(2)
        if a.button("Food preferences" if prefs_known(m) else "Fill in", key=f"pref-{m['id']}", use_container_width=True,
                    type="secondary" if prefs_known(m) else "primary"):
            ss.pref_queue = [m["id"]]
            ss.pref_total = 1
            st.rerun()
        with b.popover("Manage", use_container_width=True):
            new = st.text_input("Name", value=m["name"], key=f"name-{m['id']}")
            if st.button("Rename", key=f"rename-{m['id']}") and new.strip() and new.strip() != m["name"]:
                save_member({**m, "name": new.strip()})
                st.rerun()
            st.caption("Moving out hands their chores to the next person.")
            if st.button("Move out", key=f"out-{m['id']}"):
                for t in S["tasks"]:
                    if t.get("assignee") == m["id"]:
                        store.put("tasks", {**t, "assignee": L.next_available(MEMBERS, m["id"], t.get("due") or L.today())
                                            if t.get("kind") == "chore" else ""})
                store.delete("members", m["id"])
                if ss.get("me") == m["id"]:
                    ss.pop("me", None)
                st.rerun()


def page_people():
    if header_with_button("Flat & People", "+ Add flatmate", "people-add", primary=False,
                          sub=f"{len(MEMBERS)} flatmate{'s' if len(MEMBERS) != 1 else ''} · everything about people in one place"):
        add_member_dialog()
    b = L.balances(MEMBERS, S["expenses"], BASE, rate)
    for start in range(0, len(MEMBERS), 3):
        cols = st.columns(3)
        for j, m in enumerate(MEMBERS[start:start + 3]):
            with cols[j]:
                person_card(m, b.get(m["id"], 0))

    with st.container(key="aside-settings"):
        st.markdown('<div class="nk-h">Flat settings</div>', unsafe_allow_html=True)
        a, bcol, c = st.columns(3, gap="large")
        with a:
            nb = st.selectbox("Main currency", fxmod.CURRENCIES, index=fxmod.CURRENCIES.index(BASE))
            if nb != BASE:
                store.put("config", {"id": "settings", "base": nb})
                st.rerun()
        with bcol:
            src = "ECB reference rate" if FX.get("source") == "ECB" else "Fallback rate"
            st.markdown("**Exchange rates**")
            st.caption(f"{src} from {fmt_date(FX['date'], long=True)}, loaded automatically from the European Central Bank "
                       "(working days at around 16:00 CET).")
            if FX_ERR:
                st.warning(FX_ERR + " The last saved rates are used.")
            if st.button("Reload rates now", key="fx-reload"):
                cached_rates.clear()
                st.rerun()
        with c:
            st.markdown("**Recipe database**")
            if DB_ERR:
                st.warning(DB_ERR)
            st.caption(f"{len(DB_INDEX) + len(own_recipes()):,} recipes: {len(DB_INDEX):,} from the database, "
                       f"{len(BUILTIN)} of our picks, {len(S['recipes'])} of your own.")
        with st.expander("All exchange rates"):
            st.dataframe([{"Currency": cu, f"1 unit in {BASE}": round(rate(cu) / rate(BASE), 5)}
                          for cu in fxmod.CURRENCIES if cu != BASE], hide_index=True)
        with st.expander("How the app learns what you like"):
            st.caption("For each person, a small machine-learning model (ridge regression) learns from their ratings and favourites "
                       "which ingredients, cuisines, courses and cooking times they rate highly. Each rating counts 50 % taste and "
                       "50 % price. The model predicts a rating from 1 to 10 for every recipe, which re-ranks the suggestions; diet, "
                       "allergies and dislikes always stay fixed rules. The more you rate, the more it counts.")
            if ML_ERR:
                st.warning("Taste learning is switched off: " + ML_ERR)


PAGES = {"Today": page_today, "Fair Split": page_fair_split, "House Organizer": page_organizer,
         "Cooking": page_cooking, "Flat & People": page_people}
PAGES.get(section, page_today)()
