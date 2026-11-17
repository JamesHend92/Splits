"""Splits: the screens. Run (post-run), Season, Goals, Graphs, Profile, Trophies."""
import random

import altair as alt
import pandas as pd
import streamlit as st

import splits_lines as L
from splits_data import PB_LABEL
from splits_engine import (DIVS, FORM_DAYS, GOAL_DISTS, GRADE_COLOURS, GRADES, ME, PERKS, RIVAL,
                           SEASON_WEEKS, TYPE_ICON, TYPES, WINDOW_DAYS, clock, cum_time, grade_for, parse_clock)

CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap');
html, body, [class*="st-"], .card, .sec {font-family:'Outfit',system-ui,sans-serif}
[data-testid="stAppViewContainer"]{background:radial-gradient(1200px 600px at 10% -10%,var(--g1) 0%,transparent 55%),
  radial-gradient(900px 500px at 110% 10%,var(--g2) 0%,transparent 50%),var(--base)}
[data-testid="stHeader"]{background:transparent}
.block-container{padding-top:1.6rem;padding-bottom:3rem;max-width:520px}
#MainMenu, footer, [data-testid="stToolbar"]{visibility:hidden}
div[data-baseweb="tab-list"]{position:sticky;top:0;z-index:20;background:var(--base);gap:2px}
div[data-baseweb="tab-list"] button{padding:6px 7px !important}
div[data-baseweb="tab-list"] button p{font-family:'Outfit',sans-serif;font-weight:700;font-size:.8rem}
[data-testid="stIconMaterial"], .material-symbols-rounded{font-family:'Material Symbols Rounded' !important}
.card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:14px 16px;margin:8px 0;color:#f1f5f9;
  box-shadow:0 6px 24px rgba(0,0,0,.25);backdrop-filter:blur(6px)}
.sec{font-size:.78rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#cbd5e1;margin:20px 4px 2px}
.lbl{font-size:.7rem;color:#94a3c4;text-transform:uppercase;letter-spacing:.08em;font-weight:600}
.big{font-size:2.2rem;font-weight:800;line-height:1.12}
.mid{font-size:1.45rem;font-weight:800;line-height:1.2}
.sub{font-size:.86rem;color:#cbd5e1}
.small{font-size:.9rem;vertical-align:middle}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:8px 0}.grid .card{margin:0}
.good{color:#4ade80;font-weight:700}.bad{color:#fb7185;font-weight:700}.flat{color:#94a3b8;font-weight:700}
.up{color:#4ade80;font-weight:700}.down{color:#fb7185;font-weight:700}
.bar{height:10px;background:#1e293b;border-radius:6px;overflow:hidden;margin-top:8px}.bar>div{height:100%;border-radius:6px}
.row{display:flex;justify-content:space-between;gap:10px;padding:9px 2px;border-bottom:1px solid var(--line);font-size:.92rem}
.row b{color:#fff}.row:last-child{border-bottom:none}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.chips span{background:rgba(0,0,0,.28);border:1px solid #334155;border-radius:999px;padding:3px 10px;font-size:.78rem}
.brand{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
.logo{font-size:1.7rem;font-weight:800;letter-spacing:.14em;background:linear-gradient(90deg,var(--acc),var(--acc2));
  -webkit-background-clip:text;background-clip:text;color:transparent}
.tagline{display:block;font-size:.72rem;letter-spacing:.2em;text-transform:uppercase;color:#94a3c4;margin-top:-4px}
.lvchip{font-weight:800;font-size:.85rem;padding:4px 12px;border-radius:999px;border:1px solid var(--acc);color:#fff;
  background:color-mix(in srgb, var(--acc) 22%, transparent)}
.status{margin:0 0 6px}
.xp{float:right;background:linear-gradient(90deg,var(--acc),#ec4899);color:#fff;font-weight:800;border-radius:999px;padding:3px 11px;font-size:.85rem}
.rname{font-size:1.3rem;font-weight:800;margin-top:2px;clear:both}
.big3{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:12px}
.stat{background:rgba(0,0,0,.22);border:1px solid var(--line);border-radius:14px;padding:9px 8px}
.stat .v{font-size:1.55rem;font-weight:800;line-height:1.1;white-space:nowrap}
.stat .u{font-size:.75rem;color:#94a3c4;font-weight:600}
.cmp{font-size:.7rem;margin-top:5px;line-height:1.35;white-space:nowrap}.cmp i{color:#94a3c4;font-style:normal}
.cmpkey{font-size:.72rem;color:#94a3c4;margin-top:8px}
.tag{display:inline-block;background:#3b2506;color:#fbbf24;border:1px solid #92400e;border-radius:8px;padding:2px 8px;margin:6px 6px 0 0;font-size:.78rem;font-weight:700}
.pbrow{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--line)}
.pbrow:last-of-type{border-bottom:none}.pbrow .t{font-size:1.25rem;font-weight:800}
.pill{font-size:.72rem;font-weight:800;padding:3px 10px;border-radius:999px}
.pill.pb{background:#facc15;color:#1c1400}.pill.sb{background:#1e3a8a;color:#bfdbfe}
.pill.ok{background:#0f3d24;color:#86efac}.pill.bad{background:#4a1020;color:#fda4af}
.roast{margin-top:10px;font-style:italic;color:#fda4af;font-size:.9rem}
.sp{display:grid;grid-template-columns:30px 46px 1fr 58px 58px;align-items:center;gap:6px;padding:6px 0;
  border-bottom:1px solid var(--line);font-size:.82rem}
.sp.h{font-size:.64rem;color:#94a3c4;text-transform:uppercase;letter-spacing:.06em;font-weight:700}
.sp .n{color:#94a3c4;font-weight:700}.sp .p{font-weight:800}.sp .c{text-align:right;font-size:.74rem}
.spb{height:9px;border-radius:5px;background:linear-gradient(90deg,var(--acc2),var(--acc))}
.verdict{font-size:1.02rem;font-style:italic;color:#fde68a;margin-top:6px;line-height:1.4}
.res{display:inline-flex;align-items:center;justify-content:center;font-weight:800;font-size:.8rem;width:26px;height:26px;border-radius:7px}
.res.W,.res.win{background:#16a34a;color:#fff}.res.D,.res.draw{background:#a16207;color:#fff}
.res.L,.res.loss{background:#be123c;color:#fff}.res.N{background:#334155;color:#cbd5e1}
.resline{display:flex;gap:10px;align-items:center;margin-top:10px;font-size:.86rem;color:#cbd5e1}
.xprow{display:flex;justify-content:space-between;font-size:.82rem;padding:4px 0;color:#cbd5e1}
.xprow b{color:#e879f9}
.lane{display:flex;align-items:center;gap:8px;margin-top:6px;font-size:.78rem;color:#94a3c4}
.lane span{width:42px}.track{flex:1;height:22px;background:rgba(0,0,0,.35);border-radius:11px;overflow:hidden}
.track>div{height:100%;background:linear-gradient(90deg,transparent,#22c55e77);text-align:right;line-height:22px;
  border-radius:11px;font-size:.72rem;font-weight:800;padding-right:8px;color:#fff}
.track.ghost>div{background:linear-gradient(90deg,transparent,#94a3b877)}
.track.gavt>div{background:linear-gradient(90deg,transparent,#e5e7eb88)}
.cps{display:flex;flex-wrap:wrap;gap:5px;margin-top:10px}
.cp{font-size:.72rem;padding:3px 7px;border-radius:7px;background:rgba(0,0,0,.3);border:1px solid var(--line)}
.form5{display:flex;gap:8px;margin-top:10px}.form5 div{text-align:center;font-size:.65rem;color:#94a3c4}
.form5 .res{display:flex;width:34px;height:34px;font-size:.95rem;margin:0 auto 3px}.form5>div{flex:1}
.next{background:linear-gradient(135deg,color-mix(in srgb,var(--acc) 20%,transparent),color-mix(in srgb,var(--acc2) 12%,transparent));
  border:1px solid var(--acc)}
.next .mid{margin-top:2px}
.quest{display:flex;justify-content:space-between;margin-top:12px;font-size:.9rem}
.map{display:flex;gap:5px;margin:10px 0 6px}
.node{flex:1;border:2px solid;border-radius:12px;text-align:center;padding:5px 0;font-size:.85rem;line-height:1.2;background:rgba(0,0,0,.25)}
.node div{font-size:.7rem;color:#94a3c4}
.chap{font-size:1.2rem;font-weight:800;margin-top:10px}
.plan-h{display:flex;justify-content:space-between;align-items:center;margin-top:14px}
.slot{display:flex;align-items:center;gap:10px;margin-top:8px;padding:9px 10px;border-radius:12px;background:rgba(0,0,0,.25);border:1px solid var(--line)}
.slot .tick{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#1e293b;font-size:.9rem;flex:none}
.slot .sn{flex:1;font-weight:600;font-size:.9rem}.slot .sw{font-size:.75rem;color:#94a3c4}
.slot.done{border-color:#166534;background:rgba(22,101,52,.18)}.slot.done .tick{background:#22c55e;color:#06210f;font-weight:800}
.slot.done .sw{color:#86efac}.slot.late{border-color:#9f1239}.slot.late .sw{color:#fda4af;font-weight:700}
.tip{margin-top:14px;background:rgba(0,0,0,.25);border:1px dashed var(--acc);border-radius:14px;padding:10px 12px;font-size:.9rem}
.daft{margin-top:12px;background:linear-gradient(135deg,rgba(236,72,153,.16),rgba(139,92,246,.12));border:1px dashed #f472b6;border-radius:14px;padding:9px 12px}
.daft.open{border-style:solid;border-color:#22c55e}.dname{font-size:1.05rem;font-weight:800;margin:4px 0 2px;letter-spacing:.04em}
.perk{display:flex;gap:12px;align-items:center;margin-top:10px}.perk .ic{font-size:2rem}
.league .divname{font-size:1.5rem;font-weight:800;margin-top:2px}
.banner{margin-top:8px;padding:8px 10px;border-radius:10px;background:rgba(250,204,21,.12);border:1px solid #a16207;font-size:.88rem}
.derby{margin-top:10px;text-align:center;font-weight:800;letter-spacing:.06em;padding:6px;border-radius:10px;
  background:linear-gradient(90deg,#b91c1c,#111 50%,#e5e7eb);color:#fff;text-shadow:0 1px 2px #000}
.match{margin-top:10px;padding:10px 12px;border-radius:14px;background:rgba(0,0,0,.3);border:1px solid var(--line)}
.mhead{display:flex;justify-content:space-between;align-items:center}
.livepill{font-size:.72rem;font-weight:800;color:#fff;background:#dc2626;border-radius:6px;padding:2px 7px}
.mscore{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:8px 0 6px}
.mscore .tm{flex:1;font-weight:700;font-size:.9rem}.mscore .tm.r{text-align:right}
.mscore .gl{font-size:1.9rem;font-weight:800;white-space:nowrap}
.formrow{display:flex;align-items:center;gap:5px;margin-top:10px}
.fchip{width:22px;height:22px;border-radius:6px;display:inline-flex;align-items:center;justify-content:center;font-size:.72rem;font-weight:800}
.fchip.w{background:#16a34a;color:#fff}.fchip.d{background:#a16207;color:#fff}.fchip.l{background:#be123c;color:#fff}
.ltable{width:100%;border-collapse:collapse;margin-top:10px;font-size:.8rem}
.ltable th{color:#94a3c4;font-weight:600;font-size:.68rem;text-transform:uppercase;padding:4px 3px;text-align:center}
.ltable td{padding:5px 3px;text-align:center;border-top:1px solid var(--line)}
.ltable td.tn2{text-align:left;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:170px}
.ltable tr.up td:first-child{box-shadow:inset 3px 0 #22c55e}.ltable tr.dn td:first-child{box-shadow:inset 3px 0 #f43f5e}
.ltable tr.me td{background:color-mix(in srgb,var(--acc) 28%,transparent);font-weight:800}
.ltable tr.gav td{background:repeating-linear-gradient(90deg,rgba(255,255,255,.07) 0 8px,rgba(0,0,0,.15) 8px 16px)}
.zkey{display:inline-block;width:10px;height:10px;background:#22c55e;border-radius:2px;margin-right:5px}
.zkey2{display:inline-block;width:10px;height:10px;background:#f43f5e;border-radius:2px;margin:0 5px 0 2px}
.rival{background:linear-gradient(160deg,#1c1c1c,#0f1424 70%);border-color:#e5e7eb55}
.rhead{display:flex;align-items:center;gap:12px}.ava{font-size:2.2rem;width:52px;height:52px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;background:repeating-linear-gradient(90deg,#111 0 7px,#f8fafc 7px 14px)}
.gname{font-size:1.25rem;font-weight:800}
.bubble{margin-top:10px;padding:10px 12px;border-radius:14px 14px 14px 4px;background:#f8fafc;color:#111;font-weight:600;font-size:.9rem}
.report{background:linear-gradient(160deg,#10243a,#121a30)}.report .score{font-size:1.5rem;font-weight:800;margin-top:6px}
.wrapx{display:flex;gap:10px;overflow-x:auto;scroll-snap-type:x mandatory;padding:4px 2px 10px;margin:8px -2px}
.wcard{flex:0 0 78%;scroll-snap-align:start;min-height:200px;border-radius:22px;padding:18px;color:#fff;
  display:flex;flex-direction:column;justify-content:space-between;box-shadow:0 8px 24px rgba(0,0,0,.35)}
.wcard .wk{font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;opacity:.85;font-weight:700}
.wcard .wn{font-size:2.6rem;font-weight:800;line-height:1.05}.wcard .wt{font-size:.95rem;opacity:.92}
.scout .att{display:grid;grid-template-columns:96px 1fr 34px 58px;align-items:center;gap:8px;margin-top:12px;font-size:.9rem}
.scout .att .meter{height:10px;border-radius:6px;background:#1e293b;overflow:hidden}
.scout .att .meter div{height:100%;border-radius:6px;background:linear-gradient(90deg,var(--acc2),var(--acc))}
.scout .att b{font-size:1.05rem;text-align:right}
.ovr{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:1px dashed var(--line);padding-bottom:10px}
.ovr .n{font-size:2.6rem;font-weight:800;line-height:1}
.notes{margin-top:12px;font-size:.88rem;line-height:1.5;color:#e2e8f0}.notes b{color:#fff}
.inj{display:flex;gap:12px;align-items:center}.inj .ic{font-size:1.8rem}
.kits{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-top:10px}
.kit{border-radius:14px;padding:10px;border:1px solid var(--line);font-size:.8rem}
.kit .sw2{height:26px;border-radius:8px;margin-bottom:6px}
.kit.off{opacity:.4}.kit.on{border:2px solid #fff}
.badges{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px}
.bdg{border-radius:14px;padding:10px 6px;text-align:center;border:1px solid var(--line)}
.bdg.on{background:rgba(255,255,255,.04);border-width:2px}.bdg.off{opacity:.35}
.bdg .ic{font-size:1.6rem}.bdg .bn{font-size:.78rem;font-weight:800;margin-top:2px}.bdg .bh{font-size:.66rem;color:#94a3c4}
.glory{background:linear-gradient(160deg,#2a2118,#16130f);border-color:#78614a}
.gl{display:flex;justify-content:space-between;align-items:baseline;margin-top:8px;font-size:.95rem}
.old{font-size:1.3rem;font-weight:800;color:#a8a29e;text-decoration:line-through;text-decoration-color:#ef4444}
.ladder{display:flex;gap:4px;margin-top:8px}.rung{flex:1;height:6px;border-radius:3px}
.badge{display:inline-block;padding:3px 10px;border-radius:999px;font-weight:800;font-size:.8rem;color:#0b1220}
.goalbig{font-size:1.9rem;font-weight:800;line-height:1.1;margin-top:2px}
.gstats{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px}
.gstats div{background:rgba(0,0,0,.22);border:1px solid var(--line);border-radius:12px;padding:8px 10px}
.gstats b{display:block;font-size:1.3rem}
.xpc{color:#e879f9;font-weight:700}
.nag{background:linear-gradient(160deg,#3a1218,#1d0b10);border-color:#9f1239}
</style>"""


def md(html):
    st.markdown(html, unsafe_allow_html=True)


def section(text):
    md(f'<div class="sec">{text}</div>')


def bar(pct, colour="#22c55e"):
    return f'<div class="bar"><div style="width:{max(2, min(100, pct)):.0f}%;background:{colour}"></div></div>'


def better(diff, fmt, eps=0.5):
    """▲ green = better, ▼ red = worse, with the actual difference. diff > 0 means better."""
    if diff is None or pd.isna(diff):
        return '<span class="flat">–</span>'
    if abs(diff) < eps:
        return '<span class="flat">● same</span>'
    return f'<span class="{"good" if diff > 0 else "bad"}">{"▲" if diff > 0 else "▼"} {fmt(abs(diff))}</span>'


def ordinal(n):
    return f"{n}{'st' if n % 10 == 1 and n != 11 else 'nd' if n % 10 == 2 and n != 12 else 'rd' if n % 10 == 3 and n != 13 else 'th'}"


def weather_text(w):
    if not isinstance(w, dict):
        return None
    ic = "🌧️" if (w.get("rain") or 0) >= 0.3 else "💨" if (w.get("wind") or 0) >= 25 else \
        "🥶" if (w.get("temp") or 10) <= 3 else "☀️" if (w.get("temp") or 0) >= 18 else "⛅"
    bits = [f"{w['temp']:.0f}°C"] if w.get("temp") is not None else []
    if (w.get("rain") or 0) >= 0.1:
        bits.append(f"{w['rain']:.1f} mm")
    bits.append(f"{w.get('wind') or 0:.0f} km/h wind")
    return f"{ic} " + " · ".join(bits)


PACE_AXIS = "floor(datum.value/60) + ':' + (datum.value % 60 < 10 ? '0' : '') + floor(datum.value % 60)"


def chart(c, h=230):
    c = c.properties(height=h).configure(background="transparent").configure_view(strokeWidth=0)
    st.altair_chart(c, width="stretch", theme="streamlit")


# ============================================================== header
def header(G):
    md(f'<div class="brand"><div><span class="logo">SPLITS</span><span class="tagline">No former glory</span></div>'
       f'<span class="lvchip">Lv {G.lvl} · {G.title}</span></div>'
       f'<div class="chips status"><span>{G.injury[0]} {G.injury[1]}</span><span>🔥 {G.streak} wk streak</span>'
       f'<span>⭐ {G.total_xp:,} XP</span></div>')


# ============================================================== RUN (post-run screen)
def refs(df, r):
    prior = df[(df["date"] < r["date"]) & (df["date"] >= r["date"] - pd.Timedelta(days=WINDOW_DAYS))]
    same = prior[prior["type"] == r["type"]]
    label = f"{r['type'].lower()} runs"
    if not len(same):
        same, label = prior, "runs"
    return same.tail(5), same, label


def split_ref(runs, n):
    vals = [s["secs"] / s["km"] for sp in runs["splits"] for s in sp if s["n"] == n and s["km"] >= 0.99]
    if vals:
        return sum(vals) / len(vals)
    return runs["pace"].mean() if len(runs) else None


def page_run(G, store):
    df = G.alltime
    if not len(df):
        md('<div class="card"><div class="mid">No runs yet</div><div class="sub">Record one on Strava and it lands here.</div></div>')
        return
    recent = df.iloc[::-1].head(40)
    labels = {rid: f"{d:%a %d %b} · {k:.1f} km · {TYPE_ICON[t]} {t}"
              for rid, d, k, t in zip(recent["id"], recent["date"], recent["km"], recent["type"])}
    pick = st.selectbox("Run", list(labels), format_func=lambda i: labels[i], label_visibility="collapsed", key="pick")
    r = df[df["id"] == pick].iloc[0]
    is_latest = pick == df.iloc[-1]["id"]
    short, long_, lab = refs(df, r)

    # ---- hero: distance, pace, duration with arrows vs last 5 and 90-day average
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
        chips.append(f"❤️ {r['hr']:.0f} bpm")
    if r["elev"]:
        chips.append(f"⛰️ {r['elev']:.0f} m")
    md(f'<div class="card"><span class="xp">+{r["xp"]} XP</span>'
       f'<div class="lbl">{"Latest run · " if is_latest else ""}{r["date"]:%A %d %b · %H:%M}</div>'
       f'<div class="rname">{r["name"]}</div>'
       f'<div class="chips">{"".join(f"<span>{c}</span>" for c in chips)}</div>'
       f'<div class="big3">'
       f'<div class="stat"><div class="lbl">Distance</div><div class="v">{r["km"]:.2f}<span class="u"> km</span></div>'
       f'{cmp_block(r["km"], km_s, km_l, lambda x: f"{x:.1f} km", eps=0.05)}</div>'
       f'<div class="stat"><div class="lbl">Pace</div><div class="v">{clock(r["pace"])}<span class="u">/km</span></div>'
       f'{cmp_block(r["pace"], pc_s, pc_l, lambda x: f"{x:.0f}s", lower_better=True)}</div>'
       f'<div class="stat"><div class="lbl">Time</div><div class="v">{clock(r["secs"])}</div>'
       f'{cmp_block(r["secs"], tm_s, tm_l, clock, eps=5)}</div></div>'
       f'<div class="cmpkey">▲ better · ▼ worse · vs your last {len(short)} {lab} and your 90-day {lab[:-1] if lab.endswith("s") else lab} average</div></div>')

    # ---- run type: detected, tap to correct
    sel = st.segmented_control("Run type", TYPES, default=r["type"], format_func=lambda t: f"{TYPE_ICON[t]} {t}",
                               key=f"type_{pick}", label_visibility="collapsed")
    st.caption(("Confirmed ✓ " if r["confirmed"] else f"Guessed **{r['detected']}** from your splits. ")
               + "Tap to change it.")
    if sel and sel != r["type"]:
        ov = dict(store.get("types", {}))
        ov[str(pick)] = sel
        store.set("types", ov)
        st.rerun()

    # ---- PB flags
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
        dig = random.Random(f"dig-{pick}").choice(L.PB_DIG) if pbs else \
            "Season best. Measured against current you, the only one that counts."
        md(f'<div class="card"><div class="lbl">🏅 Flags</div>{rows}<div class="roast">{dig}</div></div>')

    # ---- splits
    if r["splits"]:
        sp = r["splits"]
        paces = [s["secs"] / s["km"] for s in sp]
        fast, slow = min(paces), max(paces)
        rows = (f'<div class="sp h"><span>KM</span><span>Pace</span><span></span><span class="c">Last {len(short)}</span>'
                f'<span class="c">90d</span></div>')
        for s, p in zip(sp, paces):
            w = 100 if slow == fast else 45 + 55 * (slow - p) / (slow - fast)
            rs, rl = split_ref(short, s["n"]), split_ref(long_, s["n"])
            ds = better((rs - p) if rs else None, lambda x: f"{x:.0f}s", 1)
            dl = better((rl - p) if rl else None, lambda x: f"{x:.0f}s", 1)
            n = s["n"] if s["km"] >= 0.99 else f"{s['km']:.2f}"
            rows += (f'<div class="sp"><span class="n">{n}</span><span class="p">{clock(p)}</span>'
                     f'<div class="spb" style="width:{w:.0f}%"></div><span class="c">{ds}</span><span class="c">{dl}</span></div>')
        md(f'<div class="card"><div class="lbl">Splits · ▲ faster than your usual for that km</div>{rows}</div>')
        cd = pd.DataFrame([{"km": s["n"], "pace": p, "hr": s["hr"], "usual": split_ref(short, s["n"])}
                           for s, p in zip(sp, paces) if s["km"] >= 0.5])
        if len(cd) >= 2:
            cd["vs"] = (cd["usual"] - cd["pace"]).round(0)
            base = alt.Chart(cd).encode(x=alt.X("km:O", title="km", axis=alt.Axis(labelAngle=0)))
            bars = base.mark_bar(opacity=.55, cornerRadius=3).encode(
                y=alt.Y("vs:Q", title="s/km vs usual"),
                color=alt.condition("datum.vs >= 0", alt.value("#22c55e"), alt.value("#f43f5e")))
            pace_line = base.mark_line(point=True, color="#22d3ee", strokeWidth=3).encode(
                y=alt.Y("pace:Q", title=None, scale=alt.Scale(zero=False, reverse=True),
                        axis=alt.Axis(labelExpr=PACE_AXIS, orient="right", labelPadding=2)),
                tooltip=[alt.Tooltip("km:O"), alt.Tooltip("vs:Q", title="s/km vs usual")])
            chart(alt.layer(bars, pace_line).resolve_scale(y="independent")
                  .properties(padding={"left": 4, "right": 14, "top": 6, "bottom": 4}), 210)
            st.caption("Blue line: pace per km (up = faster, right axis). Bars: seconds per km faster (green) or slower (red) than your usual for that km.")

    # ---- manager's verdict + XP breakdown
    line = L.verdict(pick, r["res"], r["sev"], pb=bool(pbs), short=r["km"] < 2.5)
    xp_rows = "".join(f'<div class="xprow"><span>{lab_}</span><b>+{x}</b></div>' for lab_, x in r["parts"])
    md(f'<div class="card"><div class="lbl">🗣️ Manager\'s verdict</div><div class="verdict">"{line}"</div>'
       f'<div class="resline"><span class="res {r["res"]}">{"•" if r["res"] == "N" else r["res"]}</span><span>{r["note"]}</span></div>'
       f'<div class="lbl" style="margin-top:14px">XP earned</div>{xp_rows}</div>')

    # ---- ghost runner (like for like)
    g = r["ghost"]
    if isinstance(g, dict):
        gr = df[df["id"] == g["id"]].iloc[0]
        d = g["km"]
        gap = g["gap"]
        cps = []
        for k in list(range(1, int(d) + 1)) + ([d] if d - int(d) > 0.05 else []):
            gk = cum_time(r, k) - cum_time(gr, k)
            cls = "good" if gk < -0.5 else "bad" if gk > 0.5 else "flat"
            lab_ = f"{k:g}K" if isinstance(k, int) else f"{k:.1f}"
            cps.append(f'<span class="cp">{lab_} <span class="{cls}">{"+" if gk > 0 else "−" if gk < 0 else ""}{clock(abs(gk))}</span></span>')
        metres = abs(gap) / (gr["pace"] if gap > 0 else r["pace"]) * 1000
        behind = 100 - min(85, metres / (d * 10) * 3)
        you, gh = (100, behind) if gap <= 0 else (behind, 100)
        verdict = (f"You beat your ghost by <b>{metres:.0f} m</b> ({clock(abs(gap))})" if gap < -0.5 else
                   f"Your ghost beat you by <b>{metres:.0f} m</b> ({clock(gap)})" if gap > 0.5 else "Dead heat with your ghost.")
        md(f'<div class="card"><div class="lbl">👻 Ghost · your last {r["type"].lower()} run, {gr["date"]:%a %d %b}</div>'
           f'<div class="lane"><span>You</span><div class="track"><div style="width:{you:.0f}%">🏃</div></div></div>'
           f'<div class="lane"><span>Ghost</span><div class="track ghost"><div style="width:{gh:.0f}%">👻</div></div></div>'
           f'<div class="sub" style="margin-top:6px">{verdict} over {d:.2f} km</div>'
           f'<div class="cps">{"".join(cps)}</div>'
           f'<div class="sub" style="margin-top:6px;opacity:.7">Gap at each km: − you were ahead, + the ghost was.</div></div>')

    # ---- form guide: last five runs up to this one
    upto = df[df["date"] <= r["date"]].tail(5)
    cells = "".join(f'<div><div class="res {x.res}">{"•" if x.res == "N" else x.res}</div>{TYPE_ICON[x.type]} {x.date:%d/%m}</div>'
                    for x in upto.itertuples())
    w_, d_, l_ = (upto["res"] == "W").sum(), (upto["res"] == "D").sum(), (upto["res"] == "L").sum()
    md(f'<div class="card"><div class="lbl">Form guide · last 5 runs · {w_}W {d_}D {l_}L</div><div class="form5">{cells}</div>'
       f'<div class="sub" style="margin-top:8px;opacity:.75">Each run against your last 5 of the same type. '
       f'Easy runs are judged on fitness score, long runs on distance, the rest on pace.</div></div>')

    if is_latest:
        head, body = G.suggest
        md(f'<div class="card next"><div class="lbl">Next up</div><div class="mid">{head}</div><div class="sub">{body}</div></div>')
    st.write("")
    if st.button("↻ Refresh from Strava", width="stretch"):
        st.cache_data.clear()
        st.rerun()


# ============================================================== SEASON
def page_season(G, store):
    today = G.today
    if G.preseason:
        ps = G.preseason
        if ps["state"] == "out":
            md(f'<div class="card nag"><div class="lbl">⚫ Out of contract</div><div class="mid">Pre-season starts with your next run</div>'
               f'<div class="sub">{G.days_off} days off. Week 1: three easy runs of 20 minutes. No pace targets, no heroics.</div></div>')
        else:
            goal = 3
            md(f'<div class="card"><div class="lbl">🏋️ Pre-season · week {ps["week"]} of 2</div>'
               f'<div class="mid">{"3 × 20 min easy" if ps["week"] == 1 else "3 × 30 min easy, add 4 strides to one"}</div>'
               f'<div class="quest"><span>🏃 Easy runs this week</span><span class="sub">{min(ps["runs"], goal)}/{goal}</span></div>'
               f'{bar(ps["runs"] / goal * 100)}<div class="sub" style="margin-top:8px">Back from a break. '
               f'Rebuild the legs before chasing numbers.</div></div>')

    # ---- transfer window
    mk = today.strftime("%Y-%m")
    chosen = store.get(f"perk:{mk}")
    section("💼 Transfer window")
    if chosen in PERKS:
        ic, nm, ds = PERKS[chosen]
        earned = sum(x for parts, d in zip(G.alltime["parts"], G.alltime["date"]) if d.strftime("%Y-%m") == mk
                     for lab_, x in parts if lab_.startswith("Perk") or ("doubled" in lab_ and chosen == "weather"))
        md(f'<div class="card"><div class="lbl">Signed for {today:%B}</div><div class="perk"><span class="ic">{ic}</span>'
           f'<div><div class="mid">{nm}</div><div class="sub">{ds}</div></div></div>'
           f'<div class="sub" style="margin-top:10px">Earned so far: <b>+{earned} XP</b>. New window opens 1 {(today + pd.offsets.MonthBegin(1)):%B}.</div></div>')
    elif today.day <= 7:
        md(f'<div class="card"><div class="lbl">Window open · closes {today.replace(day=7):%a %d %b}</div>'
           f'<div class="mid">Sign one perk for {today:%B}</div><div class="sub">Miss the deadline and you get a panic buy.</div></div>')
        for key in G.offered(mk):
            ic, nm, ds = PERKS[key]
            if st.button(f"{ic} {nm}: {ds}", key=f"perk_{key}", width="stretch"):
                store.set(f"perk:{mk}", key)
                st.rerun()
    else:
        key = G.perk_for(mk)
        ic, nm, ds = PERKS[key]
        md(f'<div class="card"><div class="lbl">Deadline day panic buy · {today:%B}</div><div class="perk"><span class="ic">{ic}</span>'
           f'<div><div class="mid">{nm}</div><div class="sub">{ds}</div></div></div>'
           f'<div class="sub" style="margin-top:10px">You missed the window, so the board signed this. '
           f'Pick yourself next month (1st to 7th).</div></div>')

    # ---- weekly objectives
    section("🗓️ Objectives")
    _weekly(G)
    _monthly_card(G)

    # ---- league
    section("🏟️ League")
    _league_card(G)
    done = [s for s in G.seasons if s["done"]]
    if done and (today - done[-1]["end"]).days <= 21:
        _wrapped_cards(done[-1])
    section("😏 Rival")
    _rival(G)
    _matchweek(G)
    with st.expander("Time trials and the campaign map"):
        _trials(G)


def _weekly(G):
    today, df = G.today, G.alltime
    if G.cur_block < 0:
        md(f'<div class="card"><div class="lbl">Weekly objectives</div><div class="chap">Start {G.camp_start:%a %d %b}</div>'
           f'<div class="sub">The first block is built from your form on day one.</div></div>')
        return
    NODE = {"done": ("✅", "#22c55e"), "now": ("▶️", "var(--acc)"), "failed": ("❌", "#ef4444"), "locked": ("🔒", "#334155")}
    bl = G.blocks[G.cur_block]
    ch = bl["weeks"][G.weeks_in % 4]
    nodes = "".join(f'<div class="node" style="border-color:{NODE[c["state"]][1]}">'
                    f'{"⏱️" if c["name"] == "Trial" and c["state"] in ("now", "locked") else NODE[c["state"]][0]}'
                    f'<div>{"Time trial" if c["name"] == "Trial" else c["name"]}</div></div>' for c in bl["weeks"])
    tgt = clock(bl["target"]) if bl["target"] else "set baseline"
    days_left = 7 - today.weekday()
    html = (f'<div class="card"><div class="lbl">Block {G.cur_block + 1} · week {ch["w"] + 1} of 4 · {days_left} '
            f'day{"s" if days_left != 1 else ""} left · +{ch["reward"]} XP</div><div class="map">{nodes}</div>'
            f'<div class="sub">Form going in: <b>{clock(bl["best"]) if bl["best"] else "–"}</b> 5K · '
            f'time trial target: <b>{tgt}</b>{" · easier block after 2 misses" if bl["easy"] else ""}</div>')
    wk = df[(df["date"] >= ch["start"]) & (df["date"] < ch["start"] + pd.Timedelta(weeks=1))].sort_values("date")
    used = set()

    def take(mask):
        hit = wk[mask & ~wk.index.isin(used)]
        if len(hit):
            used.add(hit.index[0])
            return hit.iloc[0]
        return None

    nruns = next(q[3] for q in ch["quests"] if q[0] == "🏃")
    if ch["name"] == "Trial":
        bt = bl["target"]
        trial_run = take(wk["best5k"].notna() & ((wk["best5k"] < bt) if bt else True))
        slots = [("🟢", "Easy run", "Mon–Wed", 2, take(wk["km"] > 0)),
                 ("⏱️", f"5K time trial under {clock(bt)}" if bt else "5K time trial (baseline)", "Thu–Sun", 6, trial_run)]
    else:
        long_run = take(wk["km"] >= ch["long"])
        sess_run = take(wk["speed"])
        slots = [("⚡", ch["session"][0], "Wed–Thu", 3, sess_run), ("📏", f"Long run {ch['long']:g} km+", "Sat–Sun", 6, long_run)]
        for lab_, dl in [("Mon–Tue", 1), ("Thu–Fri", 4)][:max(0, nruns - 2)]:
            slots.insert(0 if dl == 1 else 2, ("🟢", "Easy run", lab_, dl, take(wk["km"] > 0)))
    behind = sum(1 for *_, dl, rr in slots if rr is None and dl < today.weekday())
    pill = '<span class="pill ok">On track ✅</span>' if not behind else f'<span class="pill bad">Behind ⚠️ {behind} overdue</span>'
    html += f'<div class="plan-h"><span class="lbl">This week</span>{pill}</div>'
    for icon, name, when, dl, rr in slots:
        if rr is not None:
            html += (f'<div class="slot done"><span class="tick">✓</span><span class="sn">{name}</span>'
                     f'<span class="sw">{rr["date"]:%a} · {rr["km"]:.1f} km</span></div>')
        else:
            late = dl < today.weekday()
            html += (f'<div class="slot{" late" if late else ""}"><span class="tick">{icon}</span><span class="sn">{name}</span>'
                     f'<span class="sw">{"overdue" if late else when}</span></div>')
    kmq = next((q for q in ch["quests"] if q[0] == "📈"), None)
    if kmq:
        html += (f'<div class="quest"><span>📈 {kmq[1]}</span><span class="sub">{kmq[2]}/{kmq[3]:g} km</span></div>'
                 f'{bar(kmq[2] / kmq[3] * 100, "#22c55e" if kmq[2] >= kmq[3] else "#06b6d4")}')
    html += '<div class="lbl" style="margin-top:14px">Side quests · +50 XP each</div>'
    for icon, name, ok in ch["side"]:
        html += (f'<div class="quest"><span>{"✅" if ok else icon} {name}</span>'
                 f'<span class="{"good" if ok else "sub"}">{"done" if ok else "+50"}</span></div>')
    from splits_engine import DAFT_HINTS
    d_icon, d_name, d_ok = ch["daft"]
    if d_ok:
        html += (f'<div class="daft open"><div class="lbl">🃏 Mystery quest · unlocked · +75 XP</div>'
                 f'<div class="dname">{d_icon} {d_name}</div></div>')
    else:
        html += (f'<div class="daft"><div class="lbl">🃏 Mystery quest · +75 XP</div><div class="dname">❓❓❓</div>'
                 f'<div class="sub">Clue: <i>{DAFT_HINTS.get(d_name.split(":")[0], "Figure it out.")}</i></div></div>')
    if ch["session"] and ch["name"] != "Trial":
        ref = bl["target"] or bl["best"]
        hard = f" Hard bits at about <b>{clock(ref / 5 - 5)}/km</b>." if ref else ""
        html += f'<div class="tip"><div class="lbl">This week\'s session</div><b>{ch["session"][0]}</b>: {ch["session"][1]}{hard}</div>'
    md(html + "</div>")


def _monthly_card(G):
    days_left = (G.month_end - G.today).days
    html = f'<div class="card"><div class="lbl">{G.today:%B} objectives · {days_left} days left · +100 XP each</div>'
    for icon, name, have, goal, unit in G.month_objs:
        ok = have >= goal
        html += (f'<div class="quest"><span>{"✅" if ok else icon} {name}</span>'
                 f'<span class="{"good" if ok else "sub"}">{have:g}/{goal:g} {unit}</span></div>'
                 f'{bar(have / goal * 100, "#22c55e" if ok else "var(--acc2)")}')
    md(html + "</div>")


def _league_card(G):
    if not G.seasons:
        md(f'<div class="card"><div class="lbl">Pre-season</div><div class="chap">Season 1 kicks off {G.camp_start:%a %d %b}</div>'
           f'<div class="sub">You start in the <b>Sunday League</b>. Weekly XP is your goals. Top 3 up, bottom 3 down.</div></div>')
        return
    se = G.seasons[-1]
    dname, _, dcol = DIVS[se["div"]]
    names, tb = se["names"], se["tb"]
    md_no = (se["live"]["md"] + 1) if se["live"] else len(se["results"])
    html = (f'<div class="card league" style="border-color:{dcol}66"><div class="lbl">Season {se["sn"] + 1} · '
            f'Matchday {md_no}/{SEASON_WEEKS}</div><div class="divname" style="color:{dcol}">{dname}</div>')
    prev = G.seasons[-2] if len(G.seasons) > 1 else None
    if prev and se["live"] and se["live"]["md"] <= 1:
        moved = "⬆️ PROMOTED" if se["div"] > prev["div"] else "⬇️ RELEGATED" if se["div"] < prev["div"] else "Stayed up"
        html += (f'<div class="banner">Last season: finished <b>{ordinal(prev["pos"])}</b> in {DIVS[prev["div"]][0]} · '
                 f'<b>{moved}</b></div>')
    lv = se["live"]
    if lv:
        if lv["derby"]:
            html += '<div class="derby">⚔️ TYNE–WEAR DERBY ⚔️</div>'
        html += (f'<div class="match"><div class="mhead"><span class="livepill">● LIVE {lv["minute"]}\'</span>'
                 f'<span class="sub">ends Sunday night</span></div><div class="mscore"><span class="tm">{ME}</span>'
                 f'<span class="gl">{lv["yg"]} – {lv["og"]}</span><span class="tm r">{lv["opp_name"]}</span></div>'
                 f'<div class="sub">Your XP this week: <b>{lv["xp"]}</b> · next goal at <b>{lv["next_at"]} XP</b> '
                 f'(+{max(0, lv["next_at"] - lv["xp"])})</div></div>')
    form = tb[0]["form"][-5:]
    if form:
        html += ('<div class="formrow"><span class="lbl">Form</span>'
                 + "".join(f'<span class="fchip {f.lower()}">{f}</span>' for f in form) + '</div>')
    html += '<table class="ltable"><tr><th>#</th><th style="text-align:left">Team</th><th>P</th><th>GD</th><th>Pts</th></tr>'
    for p, i in enumerate(se["order"], 1):
        row = tb[i]
        zone = "up" if p <= 3 and se["div"] < len(DIVS) - 1 else "dn" if p >= 18 and se["div"] > 0 else ""
        cls = " me" if i == 0 else " gav" if i == 1 else ""
        html += (f'<tr class="{zone}{cls}"><td>{p}</td><td class="tn2">{names[i]}{" 😏" if i == 1 else ""}</td>'
                 f'<td>{row["P"]}</td><td>{row["GF"] - row["GA"]:+d}</td><td><b>{row["Pts"]}</b></td></tr>')
    up_to = DIVS[se["div"] + 1][0] if se["div"] < len(DIVS) - 1 else None
    html += (f'</table><div class="sub" style="margin-top:8px"><span class="zkey"></span>'
             f'{"Top 3 promoted to " + up_to if up_to else "Top of the pyramid. Win the title."}'
             f'{" · <span class=zkey2></span>bottom 3 relegated" if se["div"] > 0 else ""}</div></div>')
    md(html)
    with st.expander("Results, past seasons and Wrapped"):
        rows = "".join(f'<div class="row"><span>MD{x["md"] + 1} {"⚔️ " if x["derby"] else ""}v {x["opp_name"]}</span>'
                       f'<span><b>{x["gf"]}–{x["ga"]}</b> <span class="res {x["res"].lower()}" style="width:22px;height:22px">'
                       f'{x["res"][0]}</span></span></div>' for x in reversed(se["results"]))
        md(rows or '<div class="sub">No results yet this season.</div>')
        done = [s for s in G.seasons if s["done"]]
        if done:
            md('<div class="lbl" style="margin-top:12px">Past seasons</div>' + "".join(
                f'<div class="row"><span>Season {x["sn"] + 1} · {DIVS[x["div"]][0]}</span><b>{ordinal(x["pos"])} '
                f'{x["wrapped"].outcome}</b></div>' for x in done))
            pick = st.selectbox("Season review", [s["sn"] for s in done], format_func=lambda n: f"Season {n + 1} Wrapped",
                                index=len(done) - 1)
            _wrapped_cards(next(s for s in done if s["sn"] == pick))
        st.caption("Your weekly XP becomes goals. Opponents score from their own weekly XP. 12 matchdays a season.")


def _wrapped_cards(se):
    W = se["wrapped"]
    grads = ["linear-gradient(150deg,#7c3aed,#db2777)", "linear-gradient(150deg,#0891b2,#2563eb)",
             "linear-gradient(150deg,#16a34a,#0d9488)", "linear-gradient(150deg,#ea580c,#dc2626)",
             "linear-gradient(150deg,#ca8a04,#a16207)", "linear-gradient(150deg,#4f46e5,#0f172a)"]
    cards = [("Season " + str(se["sn"] + 1) + " Wrapped", W.outcome, f"{ordinal(W.pos)} in {W.div} · {W.pts} pts"),
             ("You ran", f"{W.km:.0f} km", f"{W.runs} runs · {W.hours:.1f} hours on your feet"),
             ("Goals", f"{W.gf}–{W.ga}", "scored v conceded across 12 matchdays"),
             ("Geordie Gav", f"{W.gav[0]}–{W.gav[1]}", "weekly duels won. " + ("He's sulking." if W.gav[0] > W.gav[1] else "He'll never let you forget it."))]
    cards += [(nm, ic, txt) for ic, nm, txt in W.awards]
    html = '<div class="wrapx">'
    for i, (k, n, t) in enumerate(cards):
        html += (f'<div class="wcard" style="background:{grads[i % len(grads)]}"><div class="wk">{k}</div>'
                 f'<div class="wn">{n}</div><div class="wt">{t}</div></div>')
    md(html + '</div><div class="sub" style="opacity:.7;text-align:center">Swipe for the awards →</div>')


def _rival(G):
    week_start, df = G.week_start, G.df
    gav_wx = G.rival_xp(week_start)
    frac = min(1.0, max(0.0, (G.now - week_start).total_seconds() / (7 * 86400)))
    gav_now, you_now = int(gav_wx * frac), G.week_xp(week_start)
    pre = df[(df["date"] >= G.today - pd.Timedelta(days=FORM_DAYS)) & (df["date"] < week_start)]
    pre5 = pre["best5k"].min() if pre["best5k"].notna().any() else None
    gav5 = pre5 - 20 if pre5 else None
    tw = df[df["date"] >= week_start]
    tw5 = tw["best5k"].min() if tw["best5k"].notna().any() else None
    beat5 = bool(gav5 and tw5 and tw5 < gav5)
    h2h = [0, 0]
    if G.seasons:
        for x in G.seasons[-1]["results"]:
            h2h[0 if G.week_xp(x["ws"]) > G.rival_xp(x["ws"]) else 1] += 1
    live = G.seasons[-1]["live"] if G.seasons else None
    mood = ("beat5k" if beat5 else "injured" if G.days_off >= 7 else "derby" if live and live["derby"]
            else "idle" if G.days_off >= 4 else "behind" if you_now > gav_now else "ahead")
    line = L.GAV[mood][(week_start.dayofyear + G.today.weekday()) % len(L.GAV[mood])]
    top = max(gav_wx, you_now, 1)
    km4 = G.alltime[(G.alltime["date"] >= week_start - pd.Timedelta(weeks=4)) & (G.alltime["date"] < week_start)]["km"].sum() / 4
    md(f'<div class="card rival"><div class="rhead"><div class="ava">😏</div><div><div class="gname">Geordie Gav</div>'
       f'<div class="sub">{RIVAL} · always just ahead</div></div></div><div class="bubble">"{line}"</div>'
       f'<div class="lbl" style="margin-top:12px">This week so far (XP)</div>'
       f'<div class="lane"><span>You</span><div class="track"><div style="width:{max(6, you_now / top * 100):.0f}%">{you_now}</div></div></div>'
       f'<div class="lane"><span>Gav</span><div class="track gavt"><div style="width:{max(6, gav_now / top * 100):.0f}%">{gav_now}</div></div></div>'
       f'<div class="sub">{"You are ahead. Keep it that way." if you_now > gav_now else f"Gav is {gav_now - you_now} XP ahead. He will finish around {gav_wx}."}</div>'
       f'<div class="row" style="margin-top:8px"><span>5K</span><span>You <b>{clock(pre5)}</b> · Gav <b>{clock(gav5)}</b></span></div>'
       f'<div class="row"><span>Weekly km (4 wk avg)</span><span>You <b>{km4:.1f}</b> · Gav <b>{km4 * 1.08:.1f}</b></span></div>'
       f'<div class="row"><span>Weekly duels this season</span><span>You <b>{h2h[0]}</b> – <b>{h2h[1]}</b> Gav</span></div></div>')


def _matchweek(G):
    ll = G.league_last
    if not ll:
        return
    lw_start = G.week_start - pd.Timedelta(weeks=1)
    lw = G.alltime[(G.alltime["date"] >= lw_start) & (G.alltime["date"] < G.week_start)]
    rows = f'<div class="row"><span>Distance</span><b>{lw["km"].sum():.1f} km</b></div><div class="row"><span>XP</span><b>+{ll["xp"]}</b></div>'
    if len(lw):
        star = lw.loc[lw["xp"].idxmax()]
        rows += f'<div class="row"><span>⭐ Best moment</span><span>{star["date"]:%a}: {star["km"]:.1f} km (+{star["xp"]} XP)</span></div>'
        if len(lw) > 1:
            flop = lw.drop(index=star.name)
            flop = flop.loc[flop["pace"].idxmax()]
            rows += f'<div class="row"><span>🥴 Worst moment</span><span>{flop["date"]:%a}: {clock(flop["pace"])}/km</span></div>'
    motm = "Your legs" if ll["res"] == "WIN" else f"The sofa (on loan to {ll['opp_name']})" if ll["res"] == "LOSS" else "Nobody, really"
    rows += f'<div class="row"><span>🏅 Man of the match</span><b>{motm}</b></div>'
    md(f'<div class="card report"><div class="lbl">📰 Matchweek report · w/c {lw_start:%d %b}</div>'
       f'<div class="score">{ME} {ll["gf"]} – {ll["ga"]} {ll["opp_name"]}</div>'
       f'<span class="res {ll["res"].lower()}" style="width:auto;padding:0 8px;margin:4px 0 6px">{ll["res"]}</span>{rows}</div>')


def _trials(G):
    hist = pd.DataFrame([{"Block": f"B{b['k'] + 1}", "Target": clock(b["target"]) if b["target"] else "baseline",
                          "You ran": clock(b["trial_best"]), "Result": "✅" if b["beaten"] else ("⏳" if b["k"] == G.cur_block else "❌")}
                         for b in G.blocks if b["k"] <= G.cur_block])
    if len(hist):
        st.dataframe(hist, hide_index=True, width="stretch")
    st.caption("Every 4 weeks: Base, Build, Peak, then a 5K time trial. Each target comes from your form going into the "
               "block. Beat it and the next one gets tougher; miss two and it eases off.")


# ============================================================== GOALS
def page_goals(G, store, show_rank=True):
    goal = G.goal
    with st.expander("🎯 Change goal", expanded=False):
        with st.form("goalform"):
            dists = list(GOAL_DISTS)
            dist = st.selectbox("Distance", dists, index=dists.index(goal["dist"]) if goal["dist"] in dists else 3)
            tgt = st.text_input("Target time (mm:ss or h:mm:ss)", value=clock(goal["target"]))
            has_race = st.checkbox("I've got a race date", value=bool(goal.get("race")))
            race_default = pd.Timestamp(goal["race"]).date() if goal.get("race") else (G.today + pd.Timedelta(weeks=12)).date()
            race = st.date_input("Race date", value=race_default, format="DD/MM/YYYY")
            if st.form_submit_button("Save goal", width="stretch"):
                t = parse_clock(tgt)
                if not t:
                    st.error("Use mm:ss, like 53:00, or h:mm:ss for longer ones.")
                else:
                    changed = dist != goal["dist"] or t != goal["target"]
                    store.set("goal", {"dist": dist, "target": t, "race": race.isoformat() if has_race else None,
                                       "set": G.today.date().isoformat() if changed or not goal.get("set") else goal["set"]})
                    st.rerun()
    D, target, pred = G.goal_km, goal["target"], G.goal_pred
    if pred is None:
        md(f'<div class="card"><div class="lbl">Goal · {goal["dist"]}</div><div class="goalbig">{goal["dist"]} in {clock(target)}</div>'
           f'<div class="sub">Run 3 km or more and I can predict where you are.</div></div>')
        return
    gap = pred - target
    trend = better((G.goal_4wk - pred) if G.goal_4wk else None, clock, 1)
    base = G.goal_base or pred
    pct = 100 if gap <= 0 else max(0, (base - pred) / (base - target) * 100) if base > target else 0
    eta = ("✅ You're already there. Time to set a tougher one." if gap <= 0 else
           f"At this rate: around <b>{G.goal_eta:%B %Y}</b>" if G.goal_eta is not None else
           "Not trending down yet. More sessions, more consistency.")
    race = ""
    if goal.get("race"):
        rd = pd.Timestamp(goal["race"])
        wks = (rd - G.today).days / 7
        on = G.goal_eta is not None and G.goal_eta <= rd or gap <= 0
        race = (f'<div class="row"><span>🏁 Race day {rd:%d %b %Y}</span><b>{wks:.0f} weeks · '
                f'{"on course ✅" if on else "behind ⚠️"}</b></div>')
    actual = f'<div class="row"><span>Best actual {goal["dist"]}, last 6 weeks</span><b>{clock(G.goal_eff)}</b></div>' if G.goal_eff else ""
    md(f'<div class="card"><div class="lbl">Goal</div><div class="goalbig">{goal["dist"]} in {clock(target)}</div>'
       f'<div class="gstats"><div><span class="lbl">Predicted today</span><b>{clock(pred)}</b>{trend} <span class="sub">vs 4 wks ago</span></div>'
       f'<div><span class="lbl">{"Ahead by" if gap <= 0 else "Still to find"}</span><b>{clock(abs(gap))}</b>'
       f'<span class="sub">{abs(gap) / D:.0f} s/km</span></div>'
       f'<div><span class="lbl">Goal pace</span><b>{clock(target / D)}/km</b></div>'
       f'<div><span class="lbl">Current pace</span><b>{clock(pred / D)}/km</b></div></div>'
       f'<div class="lbl" style="margin-top:14px">Progress since you set it · {pct:.0f}%</div>{bar(pct, "var(--acc)")}'
       f'<div class="sub" style="margin-top:8px">{eta}</div>{race}{actual}</div>')
    h = G.goal_hist.dropna(subset=["pred"])
    if len(h) >= 2:
        line = alt.Chart(h).mark_line(point=True, color="#f59e0b", strokeWidth=3).encode(
            x=alt.X("week:T", title=None, axis=alt.Axis(format="%d %b")),
            y=alt.Y("pred:Q", title=None, scale=alt.Scale(zero=False, reverse=True), axis=alt.Axis(labelExpr=PACE_AXIS)),
            tooltip=[alt.Tooltip("week:T", format="w/c %d %b"), alt.Tooltip("pred:Q", format=".0f")])
        rule = alt.Chart(pd.DataFrame({"t": [target]})).mark_rule(strokeDash=[6, 4], color="#22c55e").encode(y="t:Q")
        txt = alt.Chart(pd.DataFrame({"t": [target], "l": ["goal"]})).mark_text(align="left", dx=4, dy=-7, color="#22c55e").encode(
            y="t:Q", text="l:N", x=alt.value(0))
        chart(alt.layer(rule, txt, line), 230)
        st.caption(f"Predicted {goal['dist']} each week (up = faster), from your best runs in the 6 weeks before. Green: the goal.")
    if show_rank:
        _rank_card(G)


def _rank_card(G):
    best5k = G.best5k
    df = G.df
    prev_form = df[(df["date"] < G.today - pd.Timedelta(days=FORM_DAYS)) & (df["date"] >= G.today - pd.Timedelta(days=2 * FORM_DAYS))]
    prev5k = prev_form["best5k"].min() if prev_form["best5k"].notna().any() else None
    section("🏅 5K rank")
    if best5k is None:
        md('<div class="card"><div class="lbl">5K rank</div><div class="mid">Unranked</div>'
           '<div class="sub">No 5K in the last 6 weeks. Old ones don\'t count.</div></div>')
        return
    rank = grade_for(best5k)
    colour = GRADE_COLOURS[rank]
    if rank + 1 < len(GRADES):
        nxt_limit, nxt_name = GRADES[rank + 1]
        prev_limit = GRADES[rank][0] or 2100
        pct = (prev_limit - best5k) / (prev_limit - nxt_limit) * 100
        to_go = f"{clock(best5k - nxt_limit + 1)} to <b>{nxt_name}</b> · +150 XP"
    else:
        pct, to_go = 100, "Top rank. Legend."
    ladder = "".join(f'<span class="rung" style="background:{GRADE_COLOURS[i] if i <= rank else "#2b3a4a"}"></span>'
                     for i in range(1, len(GRADES)))
    arrow = better((prev5k - best5k) if prev5k else None, clock, 1)
    md(f'<div class="card"><div class="lbl">5K rank · last 6 weeks</div>'
       f'<span class="badge" style="background:{colour}">R{rank} · {GRADES[rank][1]}</span>'
       f'<div class="big" style="margin-top:6px">{clock(best5k)} <span class="small">{arrow}</span></div>'
       f'<div class="sub">{to_go}</div>{bar(pct, colour)}<div class="ladder">{ladder}</div></div>')


# ============================================================== GRAPHS
def page_graphs(G):
    df = G.df
    if len(df) < 2:
        st.info("Need a couple of runs first.")
        return
    section("📏 Weekly distance")
    wk = df.set_index("date")["km"].resample("W-MON", label="left", closed="left").sum().reset_index()
    wk = wk.tail(14)
    wk["avg"] = wk["km"].rolling(4, min_periods=1).mean()
    wk["w"] = wk["date"].dt.strftime("%d %b")
    b = alt.Chart(wk).encode(x=alt.X("w:O", title=None, sort=None, axis=alt.Axis(labelAngle=-45)))
    chart(alt.layer(
        b.mark_bar(color="#3b82f6", opacity=.75, cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            y=alt.Y("km:Q", title="km"), tooltip=[alt.Tooltip("date:T", format="w/c %d %b"), alt.Tooltip("km:Q", format=".1f")]),
        b.mark_line(color="#facc15", strokeWidth=3, point=True).encode(y="avg:Q")))
    st.caption("Bars: km each week. Yellow line: 4-week average. You want the line climbing gently.")

    section("⏱️ Pace by run type")
    d = df[["date", "pace", "type", "km"]].copy()
    d["avg"] = d.groupby("type")["pace"].transform(lambda s: s.rolling(4, min_periods=1).mean())
    pts = alt.Chart(d).mark_circle(size=55, opacity=.55).encode(
        x=alt.X("date:T", title=None, axis=alt.Axis(format="%d %b")),
        y=alt.Y("pace:Q", title=None, scale=alt.Scale(zero=False, reverse=True), axis=alt.Axis(labelExpr=PACE_AXIS)),
        color=alt.Color("type:N", legend=alt.Legend(orient="bottom", title=None, columns=3)),
        tooltip=[alt.Tooltip("date:T", format="%d %b"), "type:N", alt.Tooltip("km:Q", format=".1f")])
    lines = alt.Chart(d).mark_line(strokeWidth=2.5).encode(x="date:T", y="avg:Q", color="type:N")
    chart(alt.layer(pts, lines), 260)
    st.caption("Up = faster. Dots are runs, lines are the rolling average for each type. Compare easy with easy.")

    section("💓 Fitness score")
    f = df.dropna(subset=["score"])[["date", "score"]].copy()
    if len(f) >= 2:
        f["avg"] = f["score"].rolling(5, min_periods=1).mean()
        b = alt.Chart(f).encode(x=alt.X("date:T", title=None, axis=alt.Axis(format="%d %b")))
        chart(alt.layer(b.mark_circle(color="#a855f7", opacity=.45, size=45).encode(y=alt.Y("score:Q", title=None, scale=alt.Scale(zero=False))),
                        b.mark_line(color="#a855f7", strokeWidth=3).encode(y="avg:Q")))
        st.caption("Metres per minute per heartbeat. Goes up as you get fitter: same pace, lower heart rate.")
    else:
        st.info("Needs heart rate. Wear the Watch on your runs.")

    section("🏃 Runs per week")
    rc = df.set_index("date")["km"].resample("W-MON", label="left", closed="left").count().reset_index().tail(14)
    rc.columns = ["date", "runs"]
    rc["target"] = 3
    rc["w"] = rc["date"].dt.strftime("%d %b")
    b = alt.Chart(rc).encode(x=alt.X("w:O", title=None, sort=None, axis=alt.Axis(labelAngle=-45)))
    chart(alt.layer(b.mark_bar(color="#22c55e", opacity=.75, cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        y=alt.Y("runs:Q", title=None, axis=alt.Axis(tickMinStep=1))),
        b.mark_line(color="#94a3b8", strokeDash=[5, 4]).encode(y="target:Q")), 180)
    st.caption("Dashed line: 3 a week.")


# ============================================================== PROFILE
def page_profile(G, store):
    r, rp = G.ratings, G.ratings_prev
    atts = ""
    for k in ("Speed", "Stamina", "Consistency"):
        atts += (f'<div class="att"><span>{k}</span><div class="meter"><div style="width:{r[k]}%"></div></div>'
                 f'<b>{r[k]}</b><span style="font-size:.75rem">{better(r[k] - rp[k], lambda x: f"{x:.0f}", 0.5)}</span></div>')
    md(f'<div class="card scout"><div class="lbl">Scouting report · {G.today:%d %b %Y}</div>'
       f'<div class="ovr"><div><div class="mid">James</div><div class="sub">{G.position}</div></div>'
       f'<div style="text-align:right"><div class="n">{r["Overall"]}</div><div class="sub">overall '
       f'{better(r["Overall"] - rp["Overall"], lambda x: f"{x:.0f}", 0.5)}</div></div></div>{atts}'
       f'<div class="notes"><b>Strengths:</b> {G.strength.lower()}. <b>Work on:</b> {G.weakness.lower()}.<br>'
       f'<b>Recommendation:</b> {G.recommend}</div>'
       f'<div class="row" style="margin-top:8px"><span>Predicted 5K</span><b>{clock(G.p5)}</b></div>'
       f'<div class="row"><span>Longest run, 6 weeks</span><b>{G.longest42:.1f} km</b></div>'
       f'<div class="row"><span>Weekly km, 4-week average</span><b>{G.wk_km:.1f}</b></div>'
       f'<div class="sub" style="opacity:.7;margin-top:6px">Ratings 1–99 from the last 6 weeks. Arrows vs 6 weeks ago.</div></div>')

    ic, status, why = G.injury
    md(f'<div class="card"><div class="lbl">Injury list</div><div class="inj"><span class="ic">{ic}</span>'
       f'<div><div class="mid">{status}</div><div class="sub">{why}</div></div></div></div>')

    xp_arrow = better(G.xp_week - G.xp_last_same, lambda x: f"{x:.0f}", 0.5)
    md(f'<div class="card" style="border:2px solid var(--acc)"><div class="lbl">Level · last {WINDOW_DAYS} days</div>'
       f'<div class="big">Lv {G.lvl} <span style="font-size:1.1rem;color:var(--acc2)">{G.title}</span></div>'
       f'<div class="sub">{G.into} / {G.need} XP to Lv {G.lvl + 1}{"" if G.lvl >= 10 else " · Gold Kit at Lv 10"}</div>'
       f'{bar(G.into / G.need * 100, "var(--acc)")}'
       f'<div class="chips"><span>🔥 {G.streak} wk streak</span><span>🏃 {len(G.df)} runs</span>'
       f'<span>📏 {G.df["km"].sum():.0f} km</span></div>'
       f'<div class="sub" style="margin-top:10px">This week <b>+{G.xp_week} XP</b> {xp_arrow} vs this point last week</div>'
       + (f'<div class="sub" style="margin-top:6px">⏳ <b>{G.expiring} XP</b> expires this week. Run to replace it.</div>' if G.expiring else "")
       + '</div>')

    section("👕 Kit room")
    cells = ""
    for key, name, how, ok, v in G.kits:
        cells += (f'<div class="kit {"on" if key == G.kit else "" if ok else "off"}">'
                  f'<div class="sw2" style="background:linear-gradient(90deg,{v["acc"]},{v["acc2"]})"></div>'
                  f'<b>{name}</b><div class="sub" style="font-size:.72rem">{"Wearing" if key == G.kit else "Unlocked" if ok else "🔒 " + how}</div></div>')
    md(f'<div class="card"><div class="lbl">Milestones unlock new colours</div><div class="kits">{cells}</div></div>')
    unlocked = [k for k, n, h, ok, v in G.kits if ok]
    names = {k: n for k, n, h, ok, v in G.kits}
    if len(unlocked) > 1:
        pick = st.selectbox("👕 Wear", unlocked, index=unlocked.index(G.kit), format_func=lambda k: names[k],
                            key="kitpick")
        if pick and pick != G.kit:
            store.set("kit", pick)
            st.rerun()


# ============================================================== TROPHIES
def page_trophies(G):
    section("🏆 Trophy cabinet")
    rare = {"common": "#94a3b8", "rare": "#3b82f6", "epic": "#a855f7", "legendary": "#eab308"}
    got = sum(b[4] for b in G.badges)
    cells = "".join(f'<div class="bdg {"on" if ok else "off"}" style="border-color:{rare[rr]}"><div class="ic">{ic if ok else "🔒"}</div>'
                    f'<div class="bn">{nm}</div><div class="bh">{how}</div></div>' for ic, nm, how, rr, ok in G.badges)
    md(f'<div class="card"><div class="lbl">Badges · {got}/{len(G.badges)} · last {WINDOW_DAYS} days</div>'
       f'<div class="sub">Stop earning them and they lock again. '
       + " ".join(f'<span style="color:{c}">●</span> {k}' for k, c in rare.items())
       + f'</div><div class="badges">{cells}</div></div>')

    done = [s for s in G.seasons if s["done"]]
    if done:
        rows = ""
        for s in done:
            W = s["wrapped"]
            rows += f'<div class="lbl" style="margin-top:10px">Season {s["sn"] + 1} · {W.div} · {ordinal(W.pos)}</div>'
            rows += "".join(f'<div class="row"><span>{ic} {nm}</span><span>{txt}</span></div>' for ic, nm, txt in W.awards)
        md(f'<div class="card"><div class="lbl">🎖️ Season awards</div>{rows}</div>')
    _former_glory(G)

    section("📒 Run log")
    rows = ""
    for x in G.alltime.iloc[::-1].head(15).itertuples():
        star = " 🏅" if any(t.startswith("PB") for t in x.tags) else ""
        rows += (f'<div class="row"><span>{x.date:%d %b} {TYPE_ICON[x.type]}{star}</span>'
                 f'<span><b>{x.km:.1f} km</b> · {clock(x.pace)}/km · <span class="xpc">+{x.xp}</span> '
                 f'<span class="res {x.res}" style="width:20px;height:20px;font-size:.7rem">{"•" if x.res == "N" else x.res}</span></span></div>')
    md(f'<div class="card">{rows}</div>')
    with st.expander("How XP works"):
        st.markdown(
            "- **10 XP per km**, plus: **+30** longest run in 90 days, **+25** fastest pace in 90 days\n"
            "- **+75** season best 5K, **+40** season best 1K / 10K / half, **+150** for a 5K rank up\n"
            "- **+100** for an all-time PB (from Strava)\n"
            "- **+20** for beating your ghost, **weather bonus** up to +40 for rain, wind, cold or heat\n"
            "- **+100** per weekly objective block week, **+200** per time trial won, **+50** side quests, **+75** mystery quests\n"
            "- **+100** per monthly objective, plus your **transfer window perk**\n"
            "- League: your weekly XP is your goals\n"
            f"- **Only the last {WINDOW_DAYS} days count.** Stop running and your level drops. No former glory.")


def _former_glory(G):
    alltime, df, cutoff = G.alltime, G.df, G.cutoff
    items = []
    cur5 = df["best5k"].min() if len(df) and df["best5k"].notna().any() else None
    if alltime["best5k"].notna().any():
        i = alltime["best5k"].idxmin()
        t5, d5 = alltime.loc[i, "best5k"], alltime.loc[i, "date"]
        if d5 < cutoff and (cur5 is None or t5 < cur5):
            items.append(("Fastest 5K ever", clock(t5), (G.today - d5).days,
                          f"Current you is {clock(cur5 - t5)} slower" if cur5 else "You haven't run a 5K since"))
    j = alltime["km"].idxmax()
    if alltime.loc[j, "date"] < cutoff and alltime.loc[j, "km"] > (df["km"].max() if len(df) else 0):
        items.append(("Longest run ever", f"{alltime.loc[j, 'km']:.1f} km", (G.today - alltime.loc[j, "date"]).days, "Not lately though"))

    def ago(days):
        if days >= 365:
            y = days / 365
            return f"{y:.0f} years" if y >= 1.5 else "over a year"
        return f"{days // 30} months" if days >= 60 else f"{days} days"

    if not items:
        md('<div class="card"><div class="lbl">Former glory</div><div class="mid">👑 You are your PB</div>'
           '<div class="sub">Current you beats every old you. Keep it that way.</div></div>')
        return
    roast = L.FORMER_GLORY[G.today.dayofyear % len(L.FORMER_GLORY)].format(ago=ago(items[0][2]))
    html = '<div class="card glory"><div class="lbl">🏛️ Former glory · worth 0 XP</div>'
    for name, val, days, gap in items:
        html += f'<div class="gl"><span>{name}</span><span class="old">{val}</span></div><div class="sub">{ago(days)} ago · {gap}</div>'
    md(html + f'<div class="roast">"{roast}"</div></div>')

