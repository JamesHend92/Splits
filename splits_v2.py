"""Splits v2 screens: Run · League · Objectives · Goals, plus the Profile page and status pop-up.

Fewer headings, more tapping. Builds on the helpers and cards in splits_ui.
"""
import random

import pandas as pd
import streamlit as st

import splits_lines as L
from splits_data import PB_LABEL
from splits_engine import DAFT_HINTS, PERKS, TITLES, TYPE_ICON, TYPES, WINDOW_DAYS, clock, cum_time
from splits_ui import (_former_glory, _league_card, _matchweek, _monthly_card, _rank_card, _rival, _trials,
                       _wrapped_cards, bar, better, md, page_graphs, page_goals, page_profile, refs, weather_text)

V2_CSS = """<style>
.st-key-hdr [data-testid="stHorizontalBlock"], .st-key-runnav [data-testid="stHorizontalBlock"]{flex-wrap:nowrap !important;gap:.4rem !important}
.st-key-hdr [data-testid="stColumn"], .st-key-runnav [data-testid="stColumn"]{min-width:0 !important}
.st-key-lvbtn button, .st-key-hdr [data-testid="stPopover"] button{border-radius:999px !important;padding:2px 10px !important;
  min-height:34px !important;border:1px solid var(--acc) !important;background:color-mix(in srgb,var(--acc) 18%,transparent) !important}
.st-key-lvbtn button p, .st-key-hdr [data-testid="stPopover"] button p{font-size:.78rem !important;font-weight:800 !important;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.st-key-runnav button{border-radius:12px !important;min-height:40px !important;font-size:1.2rem !important}
.navlbl{text-align:center;line-height:1.2}.navlbl b{display:block;font-size:.95rem}.navlbl span{font-size:.72rem;color:#94a3c4}
.rc{padding:12px 14px}.rtop{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}
.rtop .rname{font-size:1.15rem;margin-top:0}.mini{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}
.mini span{font-size:.7rem;padding:2px 8px;border-radius:999px;background:rgba(0,0,0,.28);border:1px solid #334155;color:#cbd5e1}
.rc .big3{margin-top:10px}.rc .stat .v{font-size:1.35rem}.rc .stat{padding:8px 7px}
.legend{font-size:.66rem;color:#94a3c4;margin-top:6px;text-align:right}
.vx{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-top:10px}
.strip{display:flex;flex-wrap:wrap;gap:6px;margin:4px 0 6px}
.strip span{font-size:.76rem;padding:4px 10px;border-radius:999px;background:var(--card);border:1px solid var(--line);color:#e2e8f0}
.wk-h{display:flex;justify-content:space-between;align-items:center;gap:8px}
.slot .sd{display:block;font-size:.7rem;color:#94a3c4;font-weight:400;margin-top:2px}
.lvl-row{display:flex;justify-content:space-between;padding:7px 2px;border-bottom:1px solid var(--line);font-size:.88rem}
.lvl-row.lr-cur{color:#fff;font-weight:800}.lvl-row.lr-far{opacity:.45}
.st-key-hdr .logo{font-size:1.35rem;letter-spacing:.06em;white-space:nowrap}
.st-key-typepick [data-testid="stButtonGroup"] button{padding:4px 7px !important;min-height:34px !important}
.st-key-typepick [data-testid="stButtonGroup"] button p{font-size:.74rem !important}
.st-key-typepick [data-testid="stButtonGroup"]>div{flex-wrap:nowrap !important}
.st-row{display:flex;gap:10px;align-items:flex-start;padding:7px 0;border-bottom:1px solid var(--line);font-size:.85rem}
.st-row.cur{font-weight:800}.st-row .d{color:#94a3c4;font-size:.75rem}
</style>"""

STATUSES = [("✅", "Fit", "0–3 days since your last run", "Available for selection."),
            ("🟡", "Doubtful", "4–6 days", "Minor knock. Sofa strain, mostly."),
            ("🟠", "Injured", "7–13 days", "Hamstring, allegedly."),
            ("🔴", "Long-term injury", "14–27 days", "The physio has stopped asking."),
            ("⚫", "Out of contract", "28+ days", "Pre-season block kicks in when you're back.")]
SHORT = {"Fit": "Fit", "Doubtful": "Doubtful", "Injured": "Injured", "Long-term injury": "Long-term",
         "Out of contract": "Released"}


# ============================================================== header + profile + status
@st.dialog("Profile", width="large")
def profile_dialog(G, store):
    upcoming = ""
    for lv in range(max(1, G.lvl - 1), G.lvl + 5):
        title = TITLES[lv - 1] if lv <= len(TITLES) else "Immortal"
        cls = "lr-cur" if lv == G.lvl else "" if lv <= G.lvl + 2 else "lr-far"
        need = sum(100 * k for k in range(1, lv))  # total XP to reach this level
        note = "you are here" if lv == G.lvl else ("done" if lv < G.lvl else f"{need:,} XP")
        gold = " 🥇" if lv == 10 else ""
        upcoming += f'<div class="lvl-row {cls}"><span>Lv {lv} · {title}{gold}</span><span>{note}</span></div>'
    md(f'<div class="card"><div class="lbl">Levels · you have {G.total_xp:,} XP</div>{upcoming}'
       f'<div class="sub" style="margin-top:8px;opacity:.75">XP only counts for {WINDOW_DAYS} days. Stop running and you slide back down.</div></div>')
    page_profile(G, store)
    with st.expander("How XP works"):
        st.markdown(
            "- **10 XP per km**, +30 longest run in 90 days, +25 fastest pace in 90 days\n"
            "- **+75** season best 5K, **+40** other season bests, **+150** 5K rank up, **+100** all-time PB\n"
            "- **+20** beating your ghost, weather bonus up to **+40**\n"
            "- Objectives: **+100** weekly, **+200** time trial, **+50** side quest, **+75** mystery, **+100** monthly\n"
            "- Your weekly XP is your goals in the league")


def header(G, store):
    md(V2_CSS)
    with st.container(key="hdr"):
        c1, c2, c3 = st.columns([1.35, 2.7, 1.5], vertical_alignment="center")
        c1.markdown('<span class="logo">SPLITS</span>', unsafe_allow_html=True)
        if c2.button(f"Lv {G.lvl} · {G.title} ›", key="lvbtn", width="stretch"):
            profile_dialog(G, store)
        ic, status, why = G.injury
        with c3.popover(f"{ic} {SHORT.get(status, status)}", width="stretch"):
            rows = "".join(f'<div class="st-row{" cur" if n == status else ""}"><span>{i}</span><div>{n}'
                           f'{" ← you" if n == status else ""}<div class="d">{d} · {t}</div></div></div>'
                           for i, n, d, t in STATUSES)
            md(f'<div class="lbl">Injury list</div>{rows}<div class="sub" style="margin-top:8px">{why}</div>')


# ============================================================== RUN
def page_run(G, store):
    df = G.alltime
    if not len(df):
        md('<div class="card"><div class="mid">No runs yet</div><div class="sub">Record one on Strava and it lands here.</div></div>')
        return
    if st.session_state.pop("saved_msg", None):
        st.toast("Saved ✓", icon="✅")
    recent = df.iloc[::-1].head(40).reset_index(drop=True)
    i = min(st.session_state.get("run_i", 0), len(recent) - 1)
    r = recent.iloc[i]
    with st.container(key="runnav"):
        a, b, c = st.columns([1, 4, 1], vertical_alignment="center")
        if a.button("‹", key="prev", disabled=i >= len(recent) - 1, width="stretch"):
            st.session_state.run_i = i + 1
            st.rerun()
        when = "Latest run" if i == 0 else f"{i} run{'s' if i > 1 else ''} back"
        b.markdown(f'<div class="navlbl"><b>{r["date"]:%a %d %b · %H:%M}</b><span>{when}</span></div>',
                   unsafe_allow_html=True)
        if c.button("›", key="next", disabled=i == 0, width="stretch"):
            st.session_state.run_i = i - 1
            st.rerun()

    short, long_, lab = refs(df, r)

    def cmp_block(val, ref_s, ref_l, fmt, lower_better=False, eps=0.5):
        out = ""
        for ref, tag in ((ref_s, f"last {len(short)}"), (ref_l, "90d")):
            if ref is None or pd.isna(ref):
                continue
            diff = (ref - val) if lower_better else (val - ref)
            out += f'<div>{better(diff, fmt, eps)} <i>{tag}</i></div>'
        return f'<div class="cmp">{out or "<i>first one</i>"}</div>'

    km_s, km_l = (short["km"].mean(), long_["km"].mean()) if len(short) else (None, None)
    pc_s, pc_l = (short["pace"].mean(), long_["pace"].mean()) if len(short) else (None, None)
    tm_s, tm_l = (short["secs"].mean(), long_["secs"].mean()) if len(short) else (None, None)
    chips = [f'{TYPE_ICON[r["type"]]} {r["type"]}{" ✓" if r["confirmed"] else ""}']
    wt = weather_text(r.get("weather"))
    if wt:
        chips.append(wt)
    if pd.notna(r["hr"]):
        chips.append(f"❤️ {r['hr']:.0f}")
    if r["elev"]:
        chips.append(f"⛰️ {r['elev']:.0f} m")
    md(f'<div class="card rc"><div class="rtop"><div class="rname">{r["name"]}</div><span class="xp">+{r["xp"]} XP</span></div>'
       f'<div class="mini">{"".join(f"<span>{x}</span>" for x in chips)}</div>'
       f'<div class="big3">'
       f'<div class="stat"><div class="lbl">Distance</div><div class="v">{r["km"]:.2f}<span class="u"> km</span></div>'
       f'{cmp_block(r["km"], km_s, km_l, lambda x: f"{x:.1f} km", eps=0.05)}</div>'
       f'<div class="stat"><div class="lbl">Pace</div><div class="v">{clock(r["pace"])}<span class="u">/km</span></div>'
       f'{cmp_block(r["pace"], pc_s, pc_l, lambda x: f"{x:.0f}s", lower_better=True)}</div>'
       f'<div class="stat"><div class="lbl">Time</div><div class="v">{clock(r["secs"])}</div>'
       f'{cmp_block(r["secs"], tm_s, tm_l, clock, eps=5)}</div></div>'
       f'<div class="legend">▲ better ▼ worse · vs {lab}</div></div>')

    # ---- run type: pick, then confirm
    rid = str(r["id"])
    with st.container(key="typepick"):
        sel = st.segmented_control("Run type", TYPES, default=r["type"], key=f"type_{rid}",
                                   format_func=lambda t: f"{TYPE_ICON[t]} {'Int.' if t == 'Intervals' else t}",
                                   label_visibility="collapsed")
    sel = sel or r["type"]
    if r["confirmed"] and sel == r["type"]:
        st.caption(f"✓ Confirmed as {r['type']}")
    else:
        hint = "" if r["confirmed"] else f"I guessed {r['detected']} from your splits. "
        if st.button(f"Confirm ✓  {TYPE_ICON[sel]} {sel}", key=f"conf_{rid}", type="primary", width="stretch",
                     help=hint + "Tap to save the run type."):
            ov = dict(store.get("types", {}))
            ov[rid] = sel
            store.set("types", ov)
            st.session_state.saved_msg = True
            st.rerun()
        if hint:
            st.caption(hint + "Wrong? Pick another, then confirm.")

    # ---- PB flags (only when there are any)
    pbs = [t for t in r["tags"] if t.startswith("PB ")]
    sbs = [t for t in r["tags"] if t.startswith("SB ") or t.startswith("Rank up")]
    if pbs or sbs:
        name_of = {v: k for k, v in PB_LABEL.items()}
        rows = ""
        for t in pbs + sbs:
            lab_ = t.split(" ", 1)[1] if not t.startswith("Rank") else t
            eff = name_of.get(lab_)
            tm = clock(r["efforts"].get(eff) or (r["best5k"] if lab_ == "5K" else None)) if eff or lab_ == "5K" else ""
            kind = "pb" if t.startswith("PB") else "sb"
            word = "All-time PB" if kind == "pb" else ("Rank up" if t.startswith("Rank") else "Season best")
            rows += (f'<div class="pbrow"><span><b>{lab_}</b> <span class="pill {kind}">{word}</span></span>'
                     f'<span class="t">{tm}</span></div>')
        dig = random.Random(f"dig-{rid}").choice(L.PB_DIG) if pbs else "Measured against current you, the only one that counts."
        md(f'<div class="card">{rows}<div class="roast">{dig}</div></div>')

    # ---- manager's verdict
    line = L.verdict(rid, r["res"], r["sev"], pb=bool(pbs), short=r["km"] < 2.5)
    md(f'<div class="card"><div class="lbl">🗣️ Manager\'s verdict</div><div class="verdict">"{line}"</div>'
       f'<div class="resline"><span class="res {r["res"]}">{"•" if r["res"] == "N" else r["res"]}</span><span>{r["note"]}</span></div></div>')

    if i == 0:
        head, body = G.suggest
        md(f'<div class="card next"><div class="lbl">Next up</div><div class="mid">{head}</div><div class="sub">{body}</div></div>')

    # ---- everything else behind one tap
    with st.expander("More: XP breakdown, ghost race, form guide"):
        xp_rows = "".join(f'<div class="xprow"><span>{lab_}</span><b>+{x}</b></div>' for lab_, x in r["parts"])
        md(f'<div class="card"><div class="lbl">XP earned · +{r["xp"]}</div>{xp_rows}</div>')
        g = r["ghost"]
        if isinstance(g, dict):
            gr = df[df["id"] == g["id"]].iloc[0]
            d, gap = g["km"], g["gap"]
            cps = []
            for k in list(range(1, int(d) + 1)) + ([d] if d - int(d) > 0.05 else []):
                gk = cum_time(r, k) - cum_time(gr, k)
                cls = "good" if gk < -0.5 else "bad" if gk > 0.5 else "flat"
                lab_ = f"{k:g}K" if isinstance(k, int) else f"{k:.1f}"
                cps.append(f'<span class="cp">{lab_} <span class="{cls}">{"+" if gk > 0 else "−" if gk < 0 else ""}{clock(abs(gk))}</span></span>')
            metres = abs(gap) / (gr["pace"] if gap > 0 else r["pace"]) * 1000
            behind = 100 - min(85, metres / (d * 10) * 3)
            you, gh = (100, behind) if gap <= 0 else (behind, 100)
            verdict = (f"You beat your ghost by <b>{metres:.0f} m</b>" if gap < -0.5 else
                       f"Your ghost beat you by <b>{metres:.0f} m</b>" if gap > 0.5 else "Dead heat with your ghost.")
            md(f'<div class="card"><div class="lbl">👻 Ghost · last {r["type"].lower()} run, {gr["date"]:%a %d %b}</div>'
               f'<div class="lane"><span>You</span><div class="track"><div style="width:{you:.0f}%">🏃</div></div></div>'
               f'<div class="lane"><span>Ghost</span><div class="track ghost"><div style="width:{gh:.0f}%">👻</div></div></div>'
               f'<div class="sub" style="margin-top:6px">{verdict} over {d:.2f} km</div><div class="cps">{"".join(cps)}</div></div>')
        upto = df[df["date"] <= r["date"]].tail(5)
        cells = "".join(f'<div><div class="res {x.res}">{"•" if x.res == "N" else x.res}</div>{TYPE_ICON[x.type]} {x.date:%d/%m}</div>'
                        for x in upto.itertuples())
        w_, d_, l_ = (upto["res"] == "W").sum(), (upto["res"] == "D").sum(), (upto["res"] == "L").sum()
        md(f'<div class="card"><div class="lbl">Form guide · {w_}W {d_}D {l_}L</div><div class="form5">{cells}</div>'
           f'<div class="sub" style="margin-top:8px;opacity:.75">Each run against your last 5 of the same type.</div></div>')

    st.write("")
    if st.button("↻ Refresh from Strava", width="stretch"):
        st.cache_data.clear()
        st.rerun()


# ============================================================== LEAGUE
def page_league(G):
    _league_card(G)
    done = [s for s in G.seasons if s["done"]]
    if done and (G.today - done[-1]["end"]).days <= 21:
        _wrapped_cards(done[-1])
    _rival(G)
    _matchweek(G)


# ============================================================== OBJECTIVES
def page_objectives(G, store):
    today = G.today
    mk = today.strftime("%Y-%m")
    chosen = store.get(f"perk:{mk}")
    wk = G.alltime[G.alltime["date"] >= G.week_start]
    wx = int(sum(x for parts in wk["parts"] for lab_, x in parts if lab_.startswith("Weather")))
    if chosen in PERKS or today.day > 7:
        key = chosen if chosen in PERKS else G.perk_for(mk)
        ic, nm, ds = PERKS[key]
        perk_earned = sum(x for parts, d in zip(G.alltime["parts"], G.alltime["date"]) if d.strftime("%Y-%m") == mk
                          for lab_, x in parts if lab_.startswith("Perk") or ("doubled" in lab_ and key == "weather"))
        md(f'<div class="strip"><span title="{ds}">{ic} {nm} · +{perk_earned} XP</span>'
           f'<span>☔ Weather bonus this week +{wx} XP</span></div>')
    else:
        md(f'<div class="strip"><span>☔ Weather bonus this week +{wx} XP</span></div>')
        with st.expander(f"💼 Transfer window open till {today.replace(day=7):%a %d %b}: sign a perk"):
            for key in G.offered(mk):
                ic, nm, ds = PERKS[key]
                if st.button(f"{ic} {nm}: {ds}", key=f"perk_{key}", width="stretch"):
                    store.set(f"perk:{mk}", key)
                    st.session_state.saved_msg = True
                    st.rerun()

    if G.preseason:
        ps = G.preseason
        msg = ("Out of contract. Pre-season starts with your next run: 3 × 20 min easy." if ps["state"] == "out"
               else f"Pre-season week {ps['week']} of 2: {ps['runs']}/3 easy runs. Rebuild before chasing numbers.")
        md(f'<div class="card nag" style="padding:10px 14px"><div class="sub">🏋️ {msg}</div></div>')

    t1, t2, t3, t4 = st.tabs(["Weekly", "Side quests", "Monthly", "Trophies"])
    with t1:
        _weekly_simple(G)
    with t2:
        _side_quests(G)
    with t3:
        _monthly_card(G)
    with t4:
        _trophies(G)


def _week_now(G):
    if G.cur_block < 0 or not (0 <= G.weeks_in < len(G.chapters)):
        return None, None
    bl = G.blocks[G.cur_block]
    return bl, bl["weeks"][G.weeks_in % 4]


def _weekly_simple(G):
    today, df = G.today, G.alltime
    bl, ch = _week_now(G)
    if ch is None:
        md(f'<div class="card"><div class="lbl">Weekly objectives</div><div class="chap">Start {G.camp_start:%a %d %b}</div>'
           f'<div class="sub">Your first week gets built from your form on day one.</div></div>')
        return
    wk = df[(df["date"] >= ch["start"]) & (df["date"] < ch["start"] + pd.Timedelta(weeks=1))].sort_values("date")
    used = set()

    def take(mask):
        hit = wk[mask & ~wk.index.isin(used)]
        if len(hit):
            used.add(hit.index[0])
            return hit.iloc[0]
        return None

    nruns = next(q[3] for q in ch["quests"] if q[0] == "🏃")
    trial = ch["name"] == "Trial"
    if trial:
        bt = bl["target"]
        tr = take(wk["best5k"].notna() & ((wk["best5k"] < bt) if bt else True))
        slots = [("🟢", "Easy run", "", "Mon–Wed", 2, take(wk["km"] > 0)),
                 ("⏱️", f"5K time trial under {clock(bt)}" if bt else "5K time trial", "Warm up 10 min, then flat out.",
                  "Thu–Sun", 6, tr)]
    else:
        long_run = take(wk["km"] >= ch["long"])
        sess_run = take(wk["speed"])
        slots = [("⚡", ch["session"][0], ch["session"][1], "Wed–Thu", 3, sess_run),
                 ("📏", f"Long run {ch['long']:g} km+", "Chatting pace.", "Sat–Sun", 6, long_run)]
        for lab_, dl in [("Mon–Tue", 1), ("Thu–Fri", 4)][:max(0, nruns - 2)]:
            slots.insert(0 if dl == 1 else 2, ("🟢", "Easy run", "", lab_, dl, take(wk["km"] > 0)))
    behind = sum(1 for *_, dl, rr in slots if rr is None and dl < today.weekday())
    pill = '<span class="pill ok">On track ✅</span>' if not behind else f'<span class="pill bad">Behind · {behind} overdue</span>'
    days_left = 7 - today.weekday()
    name = "Time trial week" if trial else f"{ch['name']} week"
    html = (f'<div class="card"><div class="wk-h"><div><div class="chap" style="margin-top:0">{name}</div>'
            f'<div class="sub">{days_left} day{"s" if days_left != 1 else ""} left · +{ch["reward"]} XP</div></div>{pill}</div>')
    for icon, nm, desc, when, dl, rr in slots:
        sd = f'<span class="sd">{desc}</span>' if desc and rr is None else ""
        if rr is not None:
            html += (f'<div class="slot done"><span class="tick">✓</span><span class="sn">{nm}</span>'
                     f'<span class="sw">{rr["date"]:%a} · {rr["km"]:.1f} km</span></div>')
        else:
            late = dl < today.weekday()
            html += (f'<div class="slot{" late" if late else ""}"><span class="tick">{icon}</span><span class="sn">{nm}{sd}</span>'
                     f'<span class="sw">{"overdue" if late else when}</span></div>')
    kmq = next((q for q in ch["quests"] if q[0] == "📈"), None)
    if kmq:
        html += (f'<div class="quest"><span>📈 {kmq[1]}</span><span class="sub">{kmq[2]}/{kmq[3]:g} km</span></div>'
                 f'{bar(kmq[2] / kmq[3] * 100, "#22c55e" if kmq[2] >= kmq[3] else "#06b6d4")}')
    if not trial:
        wks = 3 - ch["w"]
        tgt = f", target {clock(bl['target'])}" if bl["target"] else ""
        html += (f'<div class="sub" style="margin-top:12px;opacity:.8">⏱️ 5K time trial in {wks} week'
                 f'{"s" if wks != 1 else ""}{tgt}</div>')
    md(html + "</div>")
    with st.expander("Time trial history"):
        _trials(G)


def _side_quests(G):
    bl, ch = _week_now(G)
    if ch is None:
        md('<div class="card"><div class="sub">Side quests start with your first week.</div></div>')
        return
    html = '<div class="card"><div class="lbl">This week · +50 XP each</div>'
    for icon, name, ok in ch["side"]:
        html += (f'<div class="quest"><span>{"✅" if ok else icon} {name}</span>'
                 f'<span class="{"good" if ok else "sub"}">{"done" if ok else "+50"}</span></div>')
    d_icon, d_name, d_ok = ch["daft"]
    if d_ok:
        html += (f'<div class="daft open"><div class="lbl">🃏 Mystery quest · unlocked · +75 XP</div>'
                 f'<div class="dname">{d_icon} {d_name}</div></div>')
    else:
        html += (f'<div class="daft"><div class="lbl">🃏 Mystery quest · +75 XP</div><div class="dname">❓❓❓</div>'
                 f'<div class="sub">Clue: <i>{DAFT_HINTS.get(d_name.split(":")[0], "Figure it out.")}</i></div></div>')
    md(html + '<div class="sub" style="margin-top:10px;opacity:.7">New ones every Monday.</div></div>')


def _trophies(G):
    rare = {"common": "#94a3b8", "rare": "#3b82f6", "epic": "#a855f7", "legendary": "#eab308"}
    got = sum(b[4] for b in G.badges)
    cells = "".join(f'<div class="bdg {"on" if ok else "off"}" style="border-color:{rare[rr]}"><div class="ic">{ic if ok else "🔒"}</div>'
                    f'<div class="bn">{nm}</div><div class="bh">{how}</div></div>' for ic, nm, how, rr, ok in G.badges)
    md(f'<div class="card"><div class="lbl">Badges · {got}/{len(G.badges)} · last {WINDOW_DAYS} days</div>'
       f'<div class="badges">{cells}</div></div>')
    done = [s for s in G.seasons if s["done"]]
    if done:
        rows = ""
        for s in done:
            W = s["wrapped"]
            rows += f'<div class="lbl" style="margin-top:10px">Season {s["sn"] + 1} · {W.div}</div>'
            rows += "".join(f'<div class="row"><span>{ic} {nm}</span><span>{txt}</span></div>' for ic, nm, txt in W.awards)
        md(f'<div class="card"><div class="lbl">🎖️ Season awards</div>{rows}</div>')
    _former_glory(G)


# ============================================================== GOALS (lighter)
def page_goals2(G, store):
    page_goals(G, store, show_rank=False)
    with st.expander("📈 Charts and 5K rank"):
        page_graphs(G)
        _rank_card(G)

