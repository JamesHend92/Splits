"""Splits: the engine. Turns a table of runs into XP, form, objectives, the league, ratings and the rest.

Everything is worked out fresh from Strava each time, so nothing can drift out of sync.
The only things saved are your own choices (run types you confirm, goal, transfer signings, kit).
"""
import random
import re
import statistics as stats
from types import SimpleNamespace

import pandas as pd

from splits_data import EFFORT_KM, PB_LABEL, PB_NAMES

WINDOW_DAYS = 90    # XP, badges, season bests: only the last 90 days count. No former glory.
FORM_DAYS = 42      # rank, predictions, ratings: the last 6 weeks = how fit you are NOW

TYPES = ["Easy", "Long", "Intervals", "Tempo", "Race"]
TYPE_ICON = {"Easy": "🟢", "Long": "📏", "Intervals": "⚡", "Tempo": "🔥", "Race": "🏁"}
SPEED_WORDS = ("4x4", "interval", "reps", "fartlek", "speed", "hills", "pyramid", "track", "x400", "x800", "x1k")

# Endless campaign: 4-week blocks built from your current form. Week 4 is a 5K time trial.
BLOCK = [("Base", 1.00, 0.0), ("Build", 1.10, 0.5), ("Peak", 1.20, 1.0), ("Trial", 0.80, None)]
MAX_LONG_KM = 16
SESSIONS = [
    ("Norwegian 4x4", "10 min easy, 4 × (4 min hard, 3 min jog), 5 min cool-down."),
    ("Kilometre Repeats", "10 min easy, 5 × 1 km hard with 2 min jog between, 5 min cool-down."),
    ("Hill Sprints", "10 min easy, 8 × 30 s hard uphill, walk back down, 10 min easy."),
    ("Tempo Run", "10 min easy, 20 min comfortably hard, 10 min easy."),
    ("Fartlek", "30 min: every few minutes sprint to a lamp post or tree, then jog till you recover."),
    ("Pyramid", "10 min easy, then 1-2-3-2-1 min hard with equal jogs, 5 min cool-down."),
    ("Progression Run", "30 min, starting slow and finishing the last 5 min at 5K effort."),
]

GRADES = [(None, "Starter"), (1800, "Sub-30"), (1680, "Sub-28"), (1620, "Sub-27"), (1500, "Sub-25"),
          (1380, "Sub-23"), (1260, "Sub-21"), (1200, "Sub-20"), (1140, "Sub-19"), (1080, "Sub-18"), (1020, "Sub-17")]
GRADE_COLOURS = ["#64748b", "#22c55e", "#14b8a6", "#3b82f6", "#8b5cf6", "#ec4899", "#f97316", "#eab308",
                 "#ef4444", "#e11d48", "#fde047"]
TITLES = ["Couch Potato", "Sofa Escapee", "Puddle Dodger", "Park Plodder", "Pavement Pounder",
          "Hill Botherer", "Jogging Menace", "Road Runner", "Tempo Terror", "N'Golo Kanté",
          "Pace Pirate", "Mile Muncher", "Lung Machine", "Speed Demon", "Fell Beast",
          "Asphalt Assassin", "Wind Chaser", "Human Diesel", "Ultra Unit", "Legend of the Wear"]

GOAL_DISTS = {"1K": 1.0, "1 mile": 1.6093, "5K": 5.0, "10K": 10.0, "Half marathon": 21.0975, "Marathon": 42.195}
GOAL_EFFORT = {"1K": "1k", "1 mile": "1 mile", "5K": "5k", "10K": "10k", "Half marathon": "half-marathon",
               "Marathon": "marathon"}
DEFAULT_GOAL = {"dist": "10K", "target": 3180, "race": None, "set": None}

# Monthly transfer window: sign one perk for the month.
PERKS = {
    "early": ("🐓", "Early Bird Contract", "+20 XP for every run started before 8am"),
    "weather": ("⛈️", "Storm Chaser", "Weather bonus XP doubled"),
    "distance": ("🛣️", "Distance Merchant", "+5 XP per km on runs of 8 km or more"),
    "speed": ("⚡", "Speed Clause", "+30 XP for every intervals or tempo run"),
    "weekend": ("🍺", "Weekend Warrior", "+25 XP for every Saturday or Sunday run"),
    "ghost": ("👻", "Ghost Buster", "+30 XP every time you beat your ghost"),
    "hattrick": ("🎩", "Hat-trick Bonus", "+60 XP for your third run of any week"),
    "form": ("📈", "Form Player", "+25 XP for every W on the form guide"),
}

# Kits: app colour themes, unlocked by milestones.
KITS = [
    ("home", "Home Kit", "Always yours",
     dict(g1="#2a1b5c", g2="#0e3a4a", base="#090d1a", card="rgba(20,27,48,.82)", line="#26314f",
          acc="#8b5cf6", acc2="#06b6d4")),
    ("away", "Away Kit", "Reach Lv 3",
     dict(g1="#0b2a4a", g2="#13384f", base="#071321", card="rgba(14,30,52,.85)", line="#1f3b5c",
          acc="#38bdf8", acc2="#e2e8f0")),
    ("stripes", "Red & White Stripes", "10 runs in 90 days",
     dict(g1="#5c0f16", g2="#3b0a0f", base="#14080a", card="rgba(40,16,20,.85)", line="#5b2027",
          acc="#ef4444", acc2="#f8fafc")),
    ("neon", "Neon Third Kit", "Set a season best 5K",
     dict(g1="#063b2a", g2="#3b0640", base="#06090f", card="rgba(12,22,24,.86)", line="#164e3b",
          acc="#22c55e", acc2="#f472b6")),
    ("retro", "Retro '96", "Finish a season",
     dict(g1="#0f4c5c", g2="#5c2a0f", base="#0b1216", card="rgba(18,36,42,.86)", line="#2b5560",
          acc="#14b8a6", acc2="#fb923c")),
    ("gold", "Gold Kit", "Reach Lv 10",
     dict(g1="#4a3a07", g2="#1f1a08", base="#0b0a06", card="rgba(30,26,12,.86)", line="#5c4b12",
          acc="#facc15", acc2="#fde68a")),
    ("blackout", "Blackout", "8-week streak",
     dict(g1="#1f1f1f", g2="#111111", base="#050505", card="rgba(22,22,22,.9)", line="#333333",
          acc="#e5e7eb", acc2="#9ca3af")),
]

SEASON_WEEKS = 12
DIVS = [("Sunday League", 330, "#94a3b8"), ("Non-League", 420, "#22c55e"), ("League Two", 520, "#06b6d4"),
        ("League One", 630, "#3b82f6"), ("Championship", 750, "#a855f7"), ("Premier League", 900, "#facc15")]
TEAM_POOL = ["Real Ale Madrid", "Inter Hamstring", "Achilles Athletic", "Sporting Shin Splints", "FC Chafing",
             "Dynamo Dad Bod", "Lactic Acid Albion", "Couch-to-5K City", "Parkrun Pirates",
             "Borussia Mönchengladjogging", "Bovril Rovers", "Stottie Cake Strollers", "Hobnob Harriers",
             "Ankle Rollers FC", "Tyne Tunnel Trotters", "Wearside Wobblers", "Pie & Pace AFC", "Expected Toast",
             "Prawn Cocktail Rovers", "Bleep Test Bandits", "Gel Pack United", "Shin Pad Shufflers",
             "Seaburn Sprinters", "Durham Dashers", "Mint Cake XI", "Sweatbox Sporting", "Blister Wanderers",
             "Deep Heat Dynamos", "Kit Bag Casuals", "Half-Time Orange FC", "Bus Lane Ballers", "Puddle Splash Town"]
ME, RIVAL = "James FC", "Gateshead Gazelles"


# ---------------------------------------------------------------- small helpers
def clock(seconds):
    if seconds is None or pd.isna(seconds):
        return "–"
    s = int(round(seconds))
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def parse_clock(txt):
    try:
        parts = [int(p) for p in str(txt).strip().split(":")]
    except ValueError:
        return None
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return None


def level_from_xp(xp):
    """Each level needs 100 XP more than the last: 100, 200, 300..."""
    lvl, need, floor = 1, 100, 0
    while xp >= floor + need:
        floor += need
        lvl += 1
        need = 100 * lvl
    return lvl, xp - floor, need


def grade_for(seconds):
    level = 0
    for i, (limit, _) in enumerate(GRADES[1:], start=1):
        if seconds is not None and not pd.isna(seconds) and seconds < limit:
            level = i
    return level


def interp(x, pts):
    if x is None or pd.isna(x):
        return None
    if x <= pts[0][0]:
        return pts[0][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[-1][1]


def cum_time(r, d):
    """Your time at distance d km into a run, from its splits (or average pace if no splits)."""
    t = done = 0.0
    for s in r["splits"] or []:
        if done + s["km"] >= d - 1e-9:
            return t + s["secs"] * (d - done) / s["km"]
        t += s["secs"]
        done += s["km"]
    return r["pace"] * d


def split_paces(r):
    return [s["secs"] / s["km"] for s in (r["splits"] or []) if s["km"] >= 0.5]


def detect_type(r, med_km, recent_pace):
    name = (r["name"] or "").lower()
    if r.get("wtype") == 1 or re.search(r"\brace\b|parkrun|time trial", name):
        return "Race"
    if "tempo" in name or "progression" in name or "threshold" in name:
        return "Tempo"
    if any(w in name for w in SPEED_WORDS) or r.get("wtype") == 3:
        return "Intervals"
    sp = split_paces(r)
    cv = None
    if len(sp) >= 4:
        speeds = [1 / p for p in sp]
        cv = stats.pstdev(speeds) / stats.mean(speeds)
        if cv > 0.07:
            return "Intervals"
    if r.get("wtype") == 2 or r["km"] >= max(8.0, 1.35 * med_km):
        return "Long"
    if cv is not None and cv < 0.05 and r["pace"] < recent_pace - 15:
        return "Tempo"
    return "Easy"


def weather_bonus(w):
    """Extra XP for running in grim weather. Returns (xp, [reasons])."""
    if not isinstance(w, dict):
        return 0, []
    xp, why = 0, []
    rain, wind, temp = w.get("rain") or 0, w.get("wind") or 0, w.get("temp")
    if rain >= 2:
        xp, why = xp + 25, why + ["biblical rain"]
    elif rain >= 0.3:
        xp, why = xp + 15, why + ["rain"]
    if wind >= 40:
        xp, why = xp + 20, why + ["gale"]
    elif wind >= 25:
        xp, why = xp + 10, why + ["wind"]
    if temp is not None and temp <= 0:
        xp, why = xp + 20, why + ["freezing"]
    elif temp is not None and temp <= 3:
        xp, why = xp + 10, why + ["cold"]
    elif temp is not None and temp >= 24:
        xp, why = xp + 10, why + ["heat"]
    return min(40, xp), why


def predict(runs, dist_km, upto, days=FORM_DAYS):
    """Best predicted time for a distance from the last `days` of runs (Riegel), or None."""
    w = runs[(runs["date"] <= upto) & (runs["date"] > upto - pd.Timedelta(days=days))]
    cands = []
    for _, r in w.iterrows():
        if r["km"] >= 3:
            cands.append(r["secs"] * (dist_km / r["km"]) ** 1.06)
        for name, t in (r["efforts"] or {}).items():
            k = EFFORT_KM.get(name)
            if k and t and k >= 1.5:
                cands.append(t * (dist_km / k) ** 1.06)
            elif k and t and abs(k - dist_km) < 0.01:
                cands.append(t)
    return min(cands) if cands else None


# ---------------------------------------------------------------- side quests and mystery quests
def side_quests(prev_long, wr, recent_pace):
    """Pool of optional side quests. Returns list of (icon, name, done)."""
    dow, hr_ = wr["date"].dt.dayofweek, wr.dropna(subset=["hr"])
    daysrun = sorted(wr["date"].dt.normalize().unique())
    back2back = any((b - a).days == 1 for a, b in zip(daysrun[:-1], daysrun[1:]))
    return [
        ("🌅", "Run before 8am", bool((wr["date"].dt.hour < 8).any())),
        ("🧘", "Easy run with avg HR under 150", bool((hr_["hr"] < 150).any())),
        ("🔁", "Run on back-to-back days", back2back),
        ("🏞️", "Weekend long run (6 km+ on Sat or Sun)", bool(((dow >= 5) & (wr["km"] >= 6)).any())),
        ("⛰️", "Find a hill: 40 m+ climb in a run", bool((wr["elev"] >= 40).any()) if "elev" in wr else False),
        ("⏳", "Run for 40 minutes non-stop", bool((wr["secs"] >= 2400).any())),
        ("📐", "Beat last week's longest run", bool(len(wr) and wr["km"].max() > prev_long > 0)),
        ("😩", "Monday run", bool((dow == 0).any())),
        ("🎲", "Three different distances", bool(wr["km"].round().nunique() >= 3)),
        ("🌙", "Run after 7pm", bool((wr["date"].dt.hour >= 19).any())),
        ("🐌", "Ultra easy: one run 90s/km slower than usual", bool((wr["pace"] > recent_pace + 90).any())),
        ("🔬", "Precision: finish within 50 m of a whole km", bool(((wr["km"] - wr["km"].round()).abs() < 0.05).any())),
    ]


def daft_quests(wr, recent_pace):
    """Whimsical quests. One a week, +75 XP. Returns (icon, name, done)."""
    d, km, mins = wr["date"], wr["km"], wr["secs"] / 60
    names = wr["name"].fillna("").str.lower()
    paces = wr["pace"].round()
    tidy = (km - km.round(1)).abs() < 0.005
    runs = wr.sort_values("date")
    escalator = len(runs) >= 3 and all(b > a for a, b in zip(runs["km"], runs["km"].iloc[1:]))
    return [
        ("🥧", "Pi Run: run 3.14 km (3.10 to 3.20)", bool(km.between(3.10, 3.20).any())),
        ("🪞", "Mirror Mirror: a run like 4.4, 5.5 or 6.6 km", bool(any(abs(k - r) < 0.05 for k in km for r in (3.3, 4.4, 5.5, 6.6, 7.7, 8.8)))),
        ("🐓", "Beat the Cockerel: start before 6am", bool((d.dt.hour < 6).any())),
        ("🧛", "Witching Hour: start after 10pm", bool((d.dt.hour >= 22).any())),
        ("🥪", "Lunch Break Legend: start between 12 and 2pm", bool(d.dt.hour.between(12, 13).any())),
        ("🎰", "Lucky Sevens: start at 7-something (am or pm)", bool(d.dt.hour.isin([7, 19]).any())),
        ("🕛", "On the Dot: start within 5 min of the hour", bool((d.dt.minute <= 5).any())),
        ("⏱️", "Thirty Minute Meal: a run of 29:30 to 30:30", bool(((wr["secs"] - 1800).abs() <= 30).any())),
        ("💿", "One Album: run 40 to 45 minutes", bool(mins.between(40, 45).any())),
        ("🎯", "Bullseye: average pace exactly on the minute (6:00/km)", bool((paces % 60 == 0).any())),
        ("🦥", "Sloth Mode: a run slower than 8:00/km. No shame.", bool((wr["pace"] > 480).any())),
        ("🐢", "Tortoise and Hare: two runs at least 60s/km apart", bool(len(wr) >= 2 and wr["pace"].max() - wr["pace"].min() >= 60)),
        ("🛗", "Escalator: 3 runs in a row, each longer than the last", bool(escalator)),
        ("🍟", "Chippy Dash: a run under 15 minutes", bool((wr["secs"] < 900).any())),
        ("🥐", "Before the Bakery Opens: Sat or Sun run before 9am", bool(((d.dt.dayofweek >= 5) & (d.dt.hour < 9)).any())),
        ("🫡", "Tribute Act: rename a run in Strava to include 'Kante'", bool(names.str.contains("kante|kanté").any())),
        ("😀", "Emoji Name: put an emoji in a Strava run name", bool(wr["name"].fillna("").map(lambda n: any(ord(c) > 10000 for c in n)).any())),
        ("📏", "Tidy Finish: stop on an exact tenth (like 5.00 or 4.30 km)", bool(tidy.any())),
        ("🔢", "Prime Time: run a prime number of km (2, 3, 5, 7 or 11)", bool(any(abs(k - p) < 0.05 for k in km for p in (2, 3, 5, 7, 11)))),
        ("🥪", "Sandwich: 3 runs where the middle one is the fastest", bool(len(runs) >= 3 and any(
            runs["pace"].iloc[i] < min(runs["pace"].iloc[i - 1], runs["pace"].iloc[i + 1]) for i in range(1, len(runs) - 1)))),
        ("⏬", "Countdown: 3 runs in a row, each shorter than the last", bool(len(runs) >= 3 and any(
            runs["km"].iloc[i] > runs["km"].iloc[i + 1] > runs["km"].iloc[i + 2] for i in range(len(runs) - 2)))),
        ("🔄", "Déjà Vu: two runs within 100 m of each other", bool(len(wr) >= 2 and (km.sort_values().diff().dropna() <= 0.1).any())),
        ("📺", "Sitcom Episode: a run of 22 to 25 minutes", bool(mins.between(22, 25).any())),
        ("🎳", "Strike!: run 10 km (9.95 to 10.1)", bool(km.between(9.95, 10.1).any())),
        ("🕺", "Friday Night Fever: Friday run after 6pm", bool(((d.dt.dayofweek == 4) & (d.dt.hour >= 18)).any())),
        ("🍗", "Sunday Roast Earned: Sunday run before 1pm", bool(((d.dt.dayofweek == 6) & (d.dt.hour < 13)).any())),
        ("🍳", "Breakfast Club: weekday run before 8am", bool(((d.dt.dayofweek < 5) & (d.dt.hour < 8)).any())),
        ("🧘", "Zen Master: a run with avg HR under 140", bool((wr["hr"] < 140).any())),
        ("🚀", "Rocket Boots: a run 30 s/km quicker than usual", bool((wr["pace"] < recent_pace - 30).any())),
        ("🛋️", "Sofa Revenge: name a run with the word 'sofa' in Strava", bool(names.str.contains("sofa").any())),
        ("🕰️", "Groundhog Day: two runs on different days starting within 15 min of the same time", bool(len(wr) >= 2 and any(
            a.date() != b.date() and abs((a.hour * 60 + a.minute) - (b.hour * 60 + b.minute)) <= 15
            for i, a in enumerate(d) for b in list(d)[i + 1:]))),
        ("🦘", "Leapfrog: 3 runs each exactly 2 days apart", bool(len(runs) >= 3 and any(
            (runs["date"].dt.normalize().iloc[i + 1] - runs["date"].dt.normalize().iloc[i]).days == 2 ==
            (runs["date"].dt.normalize().iloc[i + 2] - runs["date"].dt.normalize().iloc[i + 1]).days for i in range(len(runs) - 2)))),
    ]


DAFT_HINTS = {
    "Pi Run": "Mathematicians and bakers love this one.", "Mirror Mirror": "Two of the same, side by side.",
    "Beat the Cockerel": "Earlier than the farmyard.", "Witching Hour": "Vampire hours.",
    "Lunch Break Legend": "Sandwich o'clock.", "Lucky Sevens": "The clock likes a 7.",
    "On the Dot": "Watch the minute hand.", "Thirty Minute Meal": "Quick dinner, perfectly timed.",
    "One Album": "Press play and don't skip.", "Bullseye": "Round numbers on the pace.",
    "Sloth Mode": "Slower than you'd ever admit.", "Tortoise and Hare": "Fable time. Two speeds.",
    "Escalator": "Going up, up, up.", "Chippy Dash": "Short enough to beat the queue.",
    "Before the Bakery Opens": "Weekend. Very early.", "Tribute Act": "Honour the three-lunged one.",
    "Emoji Name": "Words aren't enough.", "Tidy Finish": "Stop your watch very carefully.",
    "Prime Time": "Only divisible by itself and one.", "Sandwich": "Best bit in the middle.",
    "Countdown": "Going down, down, down.", "Déjà Vu": "Haven't I run this before?",
    "Sitcom Episode": "Long enough for one episode.", "Strike!": "Knock all the pins down.",
    "Friday Night Fever": "End of the week, after dark.", "Sunday Roast Earned": "Earn the gravy.",
    "Breakfast Club": "Before cornflakes, on a work day.", "Zen Master": "Calm heart, calm mind.",
    "Rocket Boots": "Faster than normal you.", "Sofa Revenge": "Name your enemy.",
    "Groundhog Day": "Same time, different day.", "Leapfrog": "Skip a day, skip a day.",
}



# ---------------------------------------------------------------- the big build
def build(raw, store, demo=False, now=None):
    G = SimpleNamespace()
    now = now or pd.Timestamp.now()
    today = now.normalize()
    week_start = today - pd.Timedelta(days=today.weekday())
    cutoff = today - pd.Timedelta(days=WINDOW_DAYS)
    G.now, G.today, G.week_start, G.cutoff, G.demo = now, today, week_start, cutoff, demo

    df = raw.sort_values("date").reset_index(drop=True).copy()
    df["pace"] = df["secs"] / df["km"]
    df["score"] = (df["km"] * 1000 / (df["secs"] / 60)) / df["hr"] * 100
    for col in ("splits", "efforts", "prs"):
        df[col] = [v if isinstance(v, (list, dict)) else ([] if col != "efforts" else {}) for v in df[col]]

    # ---- run types: detected, then your confirmed overrides win
    overrides = store.get("types", {})
    win = df[df["date"] >= cutoff]
    med_km = (win["km"].median() if len(win) else df["km"].median()) or 5
    recent_pace = df["pace"].tail(10).mean()
    df["detected"] = [detect_type(r, med_km, recent_pace) for _, r in df.iterrows()]
    df["type"] = [overrides.get(str(i), d) for i, d in zip(df["id"], df["detected"])]
    df["confirmed"] = [str(i) in overrides for i in df["id"]]
    df["speed"] = df["type"].isin(["Intervals", "Tempo"])

    # ---- transfer window: which perk was signed each month (unsigned after day 7 = panic buy)
    def offered(month_key):
        keys = list(PERKS)
        random.Random(f"tw-{month_key}").shuffle(keys)
        return keys[:3]

    def perk_for(month_key):
        chosen = store.get(f"perk:{month_key}")
        if chosen in PERKS:
            return chosen
        y, m = map(int, month_key.split("-"))
        if (y, m) < (today.year, today.month) or today.day > 7:
            return offered(month_key)[0]
        return None
    G.offered, G.perk_for = offered, perk_for

    # ---- walk through every run in order: XP, tags, ghost, form result
    rows = df.to_dict("records")
    for i, r in enumerate(rows):
        lo = r["date"] - pd.Timedelta(days=WINDOW_DAYS)
        prior = [p for p in rows[:i] if p["date"] >= lo]
        same = [p for p in prior if p["type"] == r["type"]]
        parts, tags = [("Distance", round(r["km"] * 10))], []
        if prior and r["km"] > max(p["km"] for p in prior):
            parts.append(("Longest run in 90 days", 30))
        p3 = [p["pace"] for p in prior if p["km"] >= 3]
        if r["km"] >= 3 and p3 and r["pace"] < min(p3):
            parts.append(("Fastest pace in 90 days", 25))
        prior5 = [p["best5k"] for p in prior if p["best5k"] and not pd.isna(p["best5k"])]
        if r["best5k"] and not pd.isna(r["best5k"]) and prior5 and r["best5k"] < min(prior5):
            parts.append(("Season best 5K", 75))
            tags.append("SB 5K")
        for name in ("1k", "10k", "half-marathon"):
            t = r["efforts"].get(name)
            pt = [p["efforts"].get(name) for p in prior if p["efforts"].get(name)]
            if t and pt and t < min(pt):
                parts.append((f"Season best {PB_LABEL[name]}", 40))
                tags.append(f"SB {PB_LABEL[name]}")
        if r["best5k"] and not pd.isna(r["best5k"]) and grade_for(r["best5k"]) > grade_for(min(prior5) if prior5 else None):
            parts.append((f"Rank up: {GRADES[grade_for(r['best5k'])][1]}", 150))
            tags.append(f"Rank up: {GRADES[grade_for(r['best5k'])][1]}")
        pbs = [n for n in PB_NAMES if n in r["prs"]]
        if pbs:
            parts.append(("All-time PB", 100))
            tags = [f"PB {PB_LABEL[n]}" for n in pbs] + tags
        month_key = r["date"].strftime("%Y-%m")
        perk = perk_for(month_key)
        wxp, why = weather_bonus(r.get("weather"))
        if wxp:
            parts.append((f"Weather bonus: {', '.join(why)}{' (doubled, Storm Chaser)' if perk == 'weather' else ''}",
                          wxp * (2 if perk == "weather" else 1)))
        # ghost: the last run of the same type
        ghost = None
        if same:
            g = same[-1]
            d = min(r["km"], g["km"])
            gap = cum_time(r, d) - cum_time(g, d)
            ghost = {"id": g["id"], "date": g["date"], "km": d, "gap": gap, "beat": gap < -1}
            if ghost["beat"]:
                parts.append(("Beat your ghost", 20))
        # form result: against your last 5 runs of the same type
        base = same[-5:]
        res, sev, note = "N", 0, f"First {r['type'].lower()} run in 90 days. Nothing to beat yet."
        if base:
            if r["type"] == "Long":
                m = stats.mean(p["km"] for p in base)
                rel = (r["km"] - m) / m * 100
                res = "W" if rel >= 5 else "L" if rel <= -5 else "D"
                sev = abs(rel) / 10
                note = f"{abs(rel):.0f}% {'longer' if rel >= 0 else 'shorter'} than your last {len(base)} long runs"
            elif r["type"] == "Easy" and not pd.isna(r["score"]) and all(not pd.isna(p["score"]) for p in base):
                m = stats.mean(p["score"] for p in base)
                rel = (r["score"] - m) / m * 100
                res = "W" if rel >= 2 else "L" if rel <= -2 else "D"
                sev = abs(rel) / 6
                note = (f"Fitness score {abs(rel):.1f}% {'up' if rel >= 0 else 'down'} on your last "
                        f"{len(base)} easy runs (more distance per heartbeat)")
            else:
                m = stats.mean(p["pace"] for p in base)
                dlt = r["pace"] - m
                res = "W" if dlt <= -3 else "L" if dlt >= 3 else "D"
                sev = abs(dlt) / 12
                note = f"{abs(dlt):.0f} s/km {'quicker' if dlt <= 0 else 'slower'} than your last {len(base)} {r['type'].lower()} runs"
        # perks
        if perk == "early" and r["date"].hour < 8:
            parts.append(("Perk: Early Bird Contract", 20))
        if perk == "distance" and r["km"] >= 8:
            parts.append(("Perk: Distance Merchant", round(5 * r["km"])))
        if perk == "speed" and r["type"] in ("Intervals", "Tempo"):
            parts.append(("Perk: Speed Clause", 30))
        if perk == "weekend" and r["date"].dayofweek >= 5:
            parts.append(("Perk: Weekend Warrior", 25))
        if perk == "ghost" and ghost and ghost["beat"]:
            parts.append(("Perk: Ghost Buster", 30))
        if perk == "form" and res == "W":
            parts.append(("Perk: Form Player", 25))
        if perk == "hattrick":
            ws_ = r["date"].normalize() - pd.Timedelta(days=r["date"].dayofweek)
            if sum(1 for p in rows[:i] if p["date"] >= ws_) == 2:
                parts.append(("Perk: Hat-trick Bonus", 60))
        r.update(xp=sum(x for _, x in parts), parts=parts, tags=tags, ghost=ghost, res=res, sev=sev, note=note,
                 perk=perk, wxp=wxp, why=why)
    alltime = pd.DataFrame(rows) if rows else df.assign(xp=[], parts=[], tags=[])
    df = alltime[alltime["date"] >= cutoff].reset_index(drop=True)
    G.alltime, G.df = alltime, df
    G.days_off = int((today - alltime["date"].max().normalize()).days) if len(alltime) else 999

    # ---- streaks (weeks with 2+ runs)
    if len(df):
        wk = df.set_index("date")["km"].resample("W-SUN").agg(["count", "sum"])
        sunday = week_start + pd.Timedelta(days=6)
        weeks = wk.reindex(pd.date_range(wk.index[0], sunday, freq="W-SUN"), fill_value=0)
    else:
        weeks = pd.DataFrame({"count": [0], "sum": [0.0]}, index=[week_start + pd.Timedelta(days=6)])
    done_weeks = weeks.iloc[:-1]
    streak = 0
    for c in reversed(done_weeks["count"].tolist()):
        if c >= 2:
            streak += 1
        else:
            break
    if weeks["count"].iloc[-1] >= 2:
        streak += 1
    best_streak = run_ = 0
    for c in weeks["count"]:
        run_ = run_ + 1 if c >= 2 else 0
        best_streak = max(best_streak, run_)
    G.weeks, G.streak, G.best_streak = weeks, streak, best_streak

    _campaign(G, store, demo)
    _monthly(G)
    _league(G)
    _goals(G, store)
    _profile(G)
    _status(G)
    _xp_totals(G)
    _badges(G)
    _kits(G, store)
    _suggest(G)
    return G


# ---------------------------------------------------------------- campaign (weekly objectives)
def _campaign(G, store, demo):
    alltime, today, week_start = G.alltime, G.today, G.week_start
    if demo:
        camp_start = week_start - pd.Timedelta(weeks=14)
    else:
        from splits_data import secret
        camp_start = pd.Timestamp(str(secret("CAMPAIGN_START", "2026-10-26")))
        camp_start = camp_start - pd.Timedelta(days=camp_start.weekday())
    G.camp_start = camp_start

    def shave(t):
        pct = 0.03 if t > 1800 else 0.02 if t > 1500 else 0.015 if t > 1320 else 0.01 if t > 1140 else 0.006
        return max(5, round(t * pct))

    def form_at(when):
        hist = alltime[(alltime["date"] < when) & (alltime["date"] >= when - pd.Timedelta(days=FORM_DAYS))]
        last4 = hist[hist["date"] >= when - pd.Timedelta(weeks=4)]
        best = hist["best5k"].min() if hist["best5k"].notna().any() else None
        if best is None and len(last4):
            best = last4["pace"].median() * 5 * 0.97
        weekly_km = max(8.0, last4["km"].sum() / 4) if len(last4) else 8.0
        long_base = max(4.0, last4["km"].max()) if len(last4) else 4.0
        runs = 4 if best and best < 1500 and len(last4) >= 12 else 3
        return best, weekly_km, long_base, runs

    recent_pace = alltime["pace"].tail(10).mean()
    weeks_in = (today - camp_start).days // 7
    cur_block = weeks_in // 4 if weeks_in >= 0 else -1
    blocks, chapters, fails = [], [], 0
    for k in range(max(cur_block, 0) + 1):
        bstart = camp_start + pd.Timedelta(weeks=4 * k)
        best, weekly_km, long_base, nruns = form_at(bstart)
        easy = fails >= 2
        target = None if best is None else int((best - shave(best) / (2 if easy else 1)) // 5 * 5)
        block = {"k": k, "start": bstart, "best": best, "target": target, "easy": easy, "weeks": []}
        for w, (wname, km_mult, long_add) in enumerate(BLOCK):
            ws_ = bstart + pd.Timedelta(weeks=w)
            wr = alltime[(alltime["date"] >= ws_) & (alltime["date"] < ws_ + pd.Timedelta(weeks=1))]
            mult = km_mult * (0.85 if easy else 1)
            trial = wname == "Trial"
            nr = 2 if trial else nruns
            quests = [("🏃", f"Run {nr} times", len(wr), nr, "")]
            session = None
            if not trial:
                km_goal = round(weekly_km * mult)
                long_goal = min(MAX_LONG_KM, round((long_base + long_add) * 2) / 2)
                session = SESSIONS[((ws_ - pd.Timestamp("2024-01-01")).days // 7) % len(SESSIONS)]
                quests += [("📈", f"Cover {km_goal} km", round(wr["km"].sum(), 1), km_goal, "km"),
                           ("📏", f"One run of {long_goal:g} km+", round(wr["km"].max(), 1) if len(wr) else 0,
                            long_goal, "km"),
                           ("⚡", session[0], int(wr["speed"].sum()), 1, "")]
            else:
                b5 = wr["best5k"].min() if len(wr) and wr["best5k"].notna().any() else None
                beaten = b5 is not None and (target is None or b5 < target)
                label = f"5K under {clock(target)}" if target else "Set your baseline: run 5K flat out"
                quests.append(("⏱️", label, clock(b5) if b5 else "–", target, "", beaten))
            done = all((q[5] if len(q) > 5 else q[2] >= q[3]) for q in quests)
            prev_wr = alltime[(alltime["date"] >= ws_ - pd.Timedelta(weeks=1)) & (alltime["date"] < ws_)]
            pool = side_quests(prev_wr["km"].max() if len(prev_wr) else 0, wr, recent_pace)
            wk_no = (ws_ - pd.Timestamp("2024-01-01")).days // 7
            picks = [pool[(wk_no * 5 + j * 7) % len(pool)] for j in range(2)]
            if picks[0][1] == picks[1][1]:
                picks = picks[:1]
            daft_pool = daft_quests(wr, recent_pace)
            daft = daft_pool[(wk_no * 11 + 3) % len(daft_pool)]
            idx = 4 * k + w
            state = "done" if done else ("now" if idx == weeks_in else "failed" if idx < weeks_in else "locked")
            ch = {"block": k, "w": w, "name": wname, "start": ws_, "quests": quests, "state": state,
                  "reward": 200 if trial else 100, "long": quests[2][3] if not trial else None, "session": session,
                  "side": picks, "daft": daft}
            block["weeks"].append(ch)
            chapters.append(ch)
        trial_wk = block["weeks"][-1]
        block["beaten"] = trial_wk["quests"][-1][5]
        tw = alltime[(alltime["date"] >= trial_wk["start"]) & (alltime["date"] < trial_wk["start"] + pd.Timedelta(weeks=1))]
        block["trial_best"] = tw["best5k"].min() if tw["best5k"].notna().any() else None
        if k < cur_block:
            fails = 0 if block["beaten"] else fails + 1
        blocks.append(block)
    G.weeks_in, G.cur_block, G.blocks, G.chapters = weeks_in, cur_block, blocks, chapters
    G.chap_at = {c["start"]: c for c in chapters}
    G.camp_bonus = sum(c["reward"] for c in chapters
                       if c["state"] == "done" and c["start"] + pd.Timedelta(weeks=1) >= G.cutoff)
    live = [c for c in chapters if c["start"] + pd.Timedelta(weeks=1) >= G.cutoff and c["start"] <= today]
    G.camp_bonus += 50 * sum(ok for c in live for _, _, ok in c["side"]) + 75 * sum(c["daft"][2] for c in live)


# ---------------------------------------------------------------- monthly objectives
def _monthly(G):
    alltime, today = G.alltime, G.today

    def objectives(ms):
        me = (ms + pd.offsets.MonthBegin(1)).normalize()
        before = alltime[(alltime["date"] < ms) & (alltime["date"] >= ms - pd.Timedelta(weeks=4))]
        prior6 = alltime[(alltime["date"] < ms) & (alltime["date"] >= ms - pd.Timedelta(weeks=6))]
        mr = alltime[(alltime["date"] >= ms) & (alltime["date"] < me)]
        km_goal = max(20, int(round(before["km"].sum() / 4 * 4.3 * 1.1 / 5) * 5)) if len(before) else 30
        runs_goal = min(20, max(8, int(round(len(before) / 4 * 4.3)) + 1)) if len(before) else 8
        long_goal = min(21.1, max(5.0, round(((prior6["km"].max() if len(prior6) else 4) + 1) * 2) / 2))
        ghosts = sum(1 for g in mr["ghost"] if isinstance(g, dict) and g["beat"])
        sbs = sum(1 for t in mr["tags"] for x in t if x.startswith(("SB", "PB")))
        return me, [
            ("📈", f"Run {km_goal} km", round(mr["km"].sum(), 1), km_goal, "km"),
            ("🏃", f"{runs_goal} runs", len(mr), runs_goal, "runs"),
            ("📏", f"One run of {long_goal:g} km+", round(mr["km"].max(), 1) if len(mr) else 0, long_goal, "km"),
            ("👻", "Beat your ghost 3 times", ghosts, 3, ""),
            ("🏅", "Set a season best or PB", sbs, 1, ""),
        ]

    ms = today.replace(day=1)
    me, objs = objectives(ms)
    G.month_start, G.month_end, G.month_objs = ms, me, objs
    bonus = 0
    m = ms
    while m + pd.offsets.MonthBegin(1) > G.cutoff:
        _, o = objectives(m)
        bonus += 100 * sum(1 for q in o if q[2] >= q[3])
        m = (m - pd.offsets.MonthBegin(1)).normalize()
    G.month_bonus = bonus


# ---------------------------------------------------------------- league + rival
def _league(G):
    alltime, today, camp_start = G.alltime, G.today, G.camp_start
    now_ts = G.now
    chap_at = G.chap_at
    _wx, _rx = {}, {}

    def week_xp(ws):
        if ws not in _wx:
            wr_ = alltime[(alltime["date"] >= ws) & (alltime["date"] < ws + pd.Timedelta(weeks=1))]
            c = chap_at.get(ws)
            bonus = 0
            if c is not None:
                bonus = ((c["reward"] if c["state"] == "done" else 0) + 50 * sum(x[2] for x in c["side"])
                         + 75 * c["daft"][2])
            _wx[ws] = int(wr_["xp"].sum()) + bonus
        return _wx[ws]

    def rival_xp(ws):
        """Gav: your recent weeks plus a bit. Always just ahead."""
        if ws not in _rx:
            hist = [week_xp(ws - pd.Timedelta(weeks=i)) for i in range(1, 5)]
            base = max(120, 0.6 * hist[0] + 0.4 * sum(hist) / 4) if sum(hist) else 150
            _rx[ws] = int(base * 1.06 * random.Random(f"gav-{ws.date()}").uniform(0.92, 1.12))
        return _rx[ws]

    def to_goals(xp, mean, cap):
        return min(cap, int((max(xp, 0) / mean) ** 1.6 * 1.5 + 0.5))

    def xp_for_goals(g, mean):
        return int(mean * ((g - 0.5) / 1.5) ** (1 / 1.6)) + 1 if g > 0 else 0

    def div_teams(d):
        r = random.Random(f"div-{d}")
        names = r.sample(TEAM_POOL, 18)
        return [ME, RIVAL] + names, [None, None] + [r.uniform(0.65, 1.35) for _ in names]

    def season_fixtures(sn):
        arr, rounds = list(range(20)), []
        for _ in range(19):
            rounds.append([(arr[i], arr[19 - i]) for i in range(10)])
            arr = [arr[0], arr[-1]] + arr[1:-1]
        order = list(range(19))
        random.Random(f"fx-{sn}").shuffle(order)
        chosen = order[:SEASON_WEEKS]
        derby = next(i for i, rd in enumerate(rounds) if (0, 1) in rd or (1, 0) in rd)
        if derby not in chosen:
            chosen[7] = derby
        return [rounds[i] for i in chosen]

    seasons, div = [], 0
    weeks_in = G.weeks_in
    n_seasons = weeks_in // SEASON_WEEKS + 1 if weeks_in >= 0 else 0
    for sn in range(n_seasons):
        names, ratings = div_teams(div)
        mean = DIVS[div][1]
        fx = season_fixtures(sn)
        tb = {i: dict(P=0, W=0, D=0, L=0, GF=0, GA=0, Pts=0, form=[]) for i in range(20)}
        results, live = [], None
        for md in range(SEASON_WEEKS):
            ws = camp_start + pd.Timedelta(weeks=SEASON_WEEKS * sn + md)
            if ws > today:
                break

            def xp_of(t, ws=ws, md=md):
                if t == 0:
                    return week_xp(ws)
                if t == 1:
                    return rival_xp(ws)
                return int(mean * ratings[t] * random.Random(f"{sn}-{md}-{t}").uniform(0.7, 1.3))

            if ws + pd.Timedelta(weeks=1) <= today:
                for a, b in fx[md]:
                    xa, xb = xp_of(a), xp_of(b)
                    ga_, gb_ = to_goals(xa, mean, 9 if a == 0 else 7), to_goals(xb, mean, 9 if b == 0 else 7)
                    for t, f_, ag in ((a, ga_, gb_), (b, gb_, ga_)):
                        row = tb[t]
                        row["P"] += 1
                        row["GF"] += f_
                        row["GA"] += ag
                        res = "W" if f_ > ag else "D" if f_ == ag else "L"
                        row[res] += 1
                        row["Pts"] += {"W": 3, "D": 1, "L": 0}[res]
                        row["form"].append(res)
                    if 0 in (a, b):
                        opp = b if a == 0 else a
                        yg, og = (ga_, gb_) if a == 0 else (gb_, ga_)
                        yx, ox = (xa, xb) if a == 0 else (xb, xa)
                        results.append(dict(md=md, ws=ws, opp=opp, opp_name=names[opp], gf=yg, ga=og, xp=yx, oxp=ox,
                                            res="WIN" if yg > og else "DRAW" if yg == og else "LOSS", derby=opp == 1))
            else:
                pair = next(p for p in fx[md] if 0 in p)
                opp = pair[1] if pair[0] == 0 else pair[0]
                frac = min(1.0, max(0.0, (now_ts - ws).total_seconds() / (7 * 86400)))
                minute = max(1, min(90, int(frac * 90)))
                og_final = to_goals(xp_of(opp), mean, 7)
                gmins = sorted(random.Random(f"gm-{sn}-{md}").sample(range(1, 91), og_final))
                yx = week_xp(ws)
                yg = to_goals(yx, mean, 9)
                live = dict(md=md, ws=ws, opp=opp, opp_name=names[opp], yg=yg, og=sum(m <= minute for m in gmins),
                            minute=minute, xp=yx, next_at=xp_for_goals(yg + 1, mean), derby=opp == 1)
        order = sorted(range(20), key=lambda i: (-tb[i]["Pts"], -(tb[i]["GF"] - tb[i]["GA"]), -tb[i]["GF"], names[i]))
        done = tb[0]["P"] == SEASON_WEEKS
        pos = order.index(0) + 1
        start = camp_start + pd.Timedelta(weeks=SEASON_WEEKS * sn)
        seasons.append(dict(sn=sn, div=div, names=names, tb=tb, order=order, results=results, live=live,
                            done=done, pos=pos, start=start, end=start + pd.Timedelta(weeks=SEASON_WEEKS)))
        if done:
            div = min(len(DIVS) - 1, div + 1) if pos <= 3 else max(0, div - 1) if pos >= 18 else div
    for se in seasons:
        if se["done"]:
            se["wrapped"] = _wrapped(G, se, week_xp, rival_xp)
    G.seasons, G.week_xp, G.rival_xp = seasons, week_xp, rival_xp
    G.all_results = [r for se in seasons for r in se["results"]]
    G.league_last = next((r for r in G.all_results if r["ws"] == G.week_start - pd.Timedelta(weeks=1)), None)


def _wrapped(G, se, week_xp, rival_xp):
    """End-of-season review: the numbers and the awards."""
    runs = G.alltime[(G.alltime["date"] >= se["start"]) & (G.alltime["date"] < se["end"])]
    res = se["results"]
    W = SimpleNamespace(runs=len(runs), km=runs["km"].sum(), hours=runs["secs"].sum() / 3600,
                        gf=sum(r["gf"] for r in res), ga=sum(r["ga"] for r in res), pos=se["pos"],
                        div=DIVS[se["div"]][0], pts=se["tb"][0]["Pts"], awards=[])
    W.outcome = ("Champions" if se["pos"] == 1 else "Promoted" if se["pos"] <= 3 and se["div"] < len(DIVS) - 1
                 else "Relegated" if se["pos"] >= 18 and se["div"] > 0 else "Stayed put")
    gav = sum(1 for r in res if week_xp(r["ws"]) > rival_xp(r["ws"]))
    W.gav = (gav, len(res) - gav)
    if res:
        best = max(res, key=lambda r: (r["gf"] - r["ga"], r["gf"]))
        worst = min(res, key=lambda r: (r["gf"] - r["ga"], r["gf"]))
        W.awards.append(("🥇", "Golden Boot", f"MD{best['md'] + 1}: {best['gf']}–{best['ga']} v {best['opp_name']}"))
        if worst["res"] != "WIN":
            W.awards.append(("🤡", "Howler of the Season", f"MD{worst['md'] + 1}: {worst['gf']}–{worst['ga']} v {worst['opp_name']}"))
    if len(runs):
        lr = runs.loc[runs["km"].idxmax()]
        W.awards.append(("🦵", "Iron Legs", f"{lr['km']:.1f} km on {lr['date']:%d %b}"))
        fast = runs[runs["km"] >= 3]
        if len(fast):
            fr = fast.loc[fast["pace"].idxmin()]
            W.awards.append(("⚡", "Speed Demon", f"{clock(fr['pace'])}/km on {fr['date']:%d %b}"))
        b5 = runs["best5k"].dropna()
        if len(b5):
            W.awards.append(("⏱️", "Season's best 5K", clock(b5.min())))
        half = se["start"] + pd.Timedelta(weeks=SEASON_WEEKS // 2)
        a, b = runs[runs["date"] < half], runs[runs["date"] >= half]
        if len(a) >= 3 and len(b) >= 3:
            gain = a["pace"].mean() - b["pace"].mean()
            if gain > 0:
                W.awards.append(("📈", "Most Improved", f"{gain:.0f} s/km quicker in the second half"))
        wk = runs.set_index("date")["km"].resample("W-MON", label="left", closed="left").sum()
        wk = wk.reindex(pd.date_range(se["start"], se["end"] - pd.Timedelta(days=1), freq="W-MON"), fill_value=0)
        sofa = wk.idxmin()
        W.awards.append(("🛋️", "Sofa of the Season", f"w/c {sofa:%d %b}: {wk.min():.1f} km"))
    return W


# ---------------------------------------------------------------- goals
def _goals(G, store):
    goal = {**DEFAULT_GOAL, **(store.get("goal", {}) or {})}
    D = GOAL_DISTS.get(goal["dist"], 10.0)
    alltime, today = G.alltime, G.today
    pred = predict(alltime, D, G.now)
    hist = []
    for k in range(15, -1, -1):
        t = G.week_start - pd.Timedelta(weeks=k) + pd.Timedelta(days=6, hours=23)
        t = min(t, G.now)
        hist.append({"week": G.week_start - pd.Timedelta(weeks=k), "pred": predict(alltime, D, t)})
    hist = pd.DataFrame(hist)
    G.goal, G.goal_km, G.goal_pred, G.goal_hist = goal, D, pred, hist
    valid = hist.dropna(subset=["pred"])
    G.goal_4wk = valid[valid["week"] <= G.week_start - pd.Timedelta(weeks=4)]["pred"].iloc[-1] \
        if len(valid[valid["week"] <= G.week_start - pd.Timedelta(weeks=4)]) else None
    set_day = pd.Timestamp(goal["set"]) if goal.get("set") else G.week_start - pd.Timedelta(weeks=8)
    start_rows = valid[valid["week"] <= set_day]
    G.goal_base = start_rows["pred"].iloc[-1] if len(start_rows) else (valid["pred"].iloc[0] if len(valid) else None)
    G.goal_eta = None
    last8 = valid.tail(8)
    if pred and len(last8) >= 4 and pred > goal["target"]:
        xs = [(w - last8["week"].iloc[0]).days / 7 for w in last8["week"]]
        ys = list(last8["pred"])
        mx, my = stats.mean(xs), stats.mean(ys)
        den = sum((x - mx) ** 2 for x in xs)
        slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0
        if slope < -0.5:
            G.goal_eta = today + pd.Timedelta(weeks=(pred - goal["target"]) / -slope)
    G.goal_eff = None
    eff_name = GOAL_EFFORT.get(goal["dist"])
    rec = alltime[alltime["date"] > G.now - pd.Timedelta(days=FORM_DAYS)]
    times = [e.get(eff_name) for e in rec["efforts"] if e.get(eff_name)]
    if times:
        G.goal_eff = min(times)


# ---------------------------------------------------------------- scouting report ratings
def ratings_at(alltime, t):
    w42 = alltime[(alltime["date"] <= t) & (alltime["date"] > t - pd.Timedelta(days=FORM_DAYS))]
    w28 = alltime[(alltime["date"] <= t) & (alltime["date"] > t - pd.Timedelta(days=28))]
    p5 = predict(alltime, 5, t)
    speed = interp(-(p5 or 3600), [(-3000, 18), (-2700, 25), (-2100, 45), (-1800, 55), (-1620, 62), (-1500, 70),
                                   (-1320, 80), (-1200, 88), (-1080, 95)])
    longest = w42["km"].max() if len(w42) else 0
    wk_km = w28["km"].sum() / 4
    s_l = interp(longest, [(0, 5), (3, 30), (5, 42), (8, 58), (10, 66), (15, 78), (21.1, 88), (30, 95)])
    s_w = interp(wk_km, [(0, 5), (5, 30), (10, 45), (20, 62), (30, 74), (50, 88), (70, 95)])
    stamina = 0.5 * s_l + 0.5 * s_w
    w56 = alltime[(alltime["date"] <= t) & (alltime["date"] > t - pd.Timedelta(weeks=8))]
    if len(w56):
        counts = w56.set_index("date")["km"].resample("W-MON", label="left", closed="left").count()
        counts = counts.reindex(pd.date_range(t.normalize() - pd.Timedelta(weeks=8) - pd.Timedelta(days=t.weekday()),
                                              t, freq="W-MON"), fill_value=0)[-8:]
        f = (counts >= 2).mean()
        rpw = len(w56) / 8
        dates = sorted(w56["date"])
        gap = max([(b - a).days for a, b in zip(dates, dates[1:])] + [(t - dates[-1]).days])
        consistency = 20 + 55 * f + min(15, rpw * 5) - min(15, max(0, gap - 7))
    else:
        consistency = 5
    clampr = lambda x: int(max(1, min(99, round(x))))  # noqa: E731
    out = {"Speed": clampr(speed), "Stamina": clampr(stamina), "Consistency": clampr(consistency)}
    out["Overall"] = clampr(stats.mean(out.values()))
    return out, p5, longest, wk_km


def _profile(G):
    G.ratings, G.p5, G.longest42, G.wk_km = ratings_at(G.alltime, G.now)
    G.ratings_prev, *_ = ratings_at(G.alltime, G.now - pd.Timedelta(days=FORM_DAYS))
    r = G.ratings
    top = max(("Speed", "Stamina", "Consistency"), key=lambda k: r[k])
    low = min(("Speed", "Stamina", "Consistency"), key=lambda k: r[k])
    G.position = {"Speed": "Winger. Rapid, allergic to tracking back.",
                  "Stamina": "Box-to-box engine. Runs all day, Kanté-style.",
                  "Consistency": "Holding midfielder. Always turns up."}[top]
    G.strength, G.weakness = top, low
    o = r["Overall"]
    G.recommend = ("Sign him up. Immediately." if o >= 75 else "One to watch. Promising." if o >= 55
                   else "Needs a full pre-season." if o >= 40 else "Send him to the youth team.")


# ---------------------------------------------------------------- injury list + pre-season
def _status(G):
    d = G.days_off
    G.injury = (("✅", "Fit", "Available for selection") if d <= 3 else
                ("🟡", "Doubtful", f"Minor knock (sofa strain). {d} days out.") if d <= 6 else
                ("🟠", "Injured", f"Hamstring, allegedly. {d} days out. Back when the trainers are laced.") if d <= 13 else
                ("🔴", "Long-term injury", f"{d} days out. The physio has stopped asking.") if d <= 27 else
                ("⚫", "Out of contract", f"{d} days without a run. Pre-season required."))
    dates = sorted(G.alltime["date"]) if len(G.alltime) else []
    G.preseason = None
    if d >= 21:
        G.preseason = {"state": "out", "week": 1, "runs": 0}
    else:
        ret = None
        for a, b in zip(dates, dates[1:]):
            if (b - a).days >= 21:
                ret = b
        if ret is not None and (G.now - ret).days < 14:
            wk = (G.now.normalize() - ret.normalize()).days // 7 + 1
            ws = ret.normalize() + pd.Timedelta(weeks=wk - 1)
            G.preseason = {"state": "on", "week": wk, "since": ret,
                           "runs": int(((G.alltime["date"] >= ws) & (G.alltime["date"] < ws + pd.Timedelta(weeks=1))).sum())}


# ---------------------------------------------------------------- XP and level
def _xp_totals(G):
    df = G.df
    G.total_xp = int(df["xp"].sum()) + G.camp_bonus + G.month_bonus if len(df) else G.camp_bonus + G.month_bonus
    G.lvl, G.into, G.need = level_from_xp(G.total_xp)
    G.title = TITLES[G.lvl - 1] if G.lvl <= len(TITLES) else "Immortal"
    G.expiring = int(df.loc[df["date"] < G.cutoff + pd.Timedelta(days=7), "xp"].sum()) if len(df) else 0
    G.xp_week = int(df.loc[df["date"] >= G.week_start, "xp"].sum()) if len(df) else 0
    same_point = G.week_start - pd.Timedelta(weeks=1) + (G.now - G.week_start)
    G.xp_last_same = int(df.loc[(df["date"] >= G.week_start - pd.Timedelta(weeks=1)) & (df["date"] < same_point), "xp"].sum()) \
        if len(df) else 0


# ---------------------------------------------------------------- badges
def _badges(G):
    df, alltime, cutoff = G.df, G.alltime, G.cutoff
    form = df[df["date"] >= G.today - pd.Timedelta(days=FORM_DAYS)]
    G.best5k = form["best5k"].min() if len(form) and form["best5k"].notna().any() else None
    b5 = G.best5k or 9999
    if not len(df):
        G.badges = []
        return
    d = df["date"]
    days = d.dt.normalize().drop_duplicates().sort_values()
    in_a_row, best_row = 1, 1 if len(days) else 0
    for x, y in zip(days[:-1], days[1:]):
        in_a_row = in_a_row + 1 if (y - x).days == 1 else 1
        best_row = max(best_row, in_a_row)
    gaps = alltime["date"].diff().dt.days
    comeback = bool(((gaps >= 7) & (alltime["date"] >= cutoff)).any())
    wk_runs = df.set_index("date")["km"].resample("W-SUN").count()
    weekends = df.assign(wk=d.dt.to_period("W-SUN"), dow=d.dt.dayofweek)
    both_days = bool(weekends.groupby("wk")["dow"].apply(lambda x: {5, 6} <= set(x)).any())
    md = d.dt.strftime("%m-%d")
    trials = sum(bl["beaten"] for bl in G.blocks)
    hr_ok = df.dropna(subset=["hr"])
    ghosts = sum(1 for g in df["ghost"] if isinstance(g, dict) and g["beat"])
    wins = (df["res"] == "W").sum()
    pbs = sum(1 for t in df["tags"] for x in t if x.startswith("PB"))
    rainy = sum(1 for w in df["why"] if any("rain" in x for x in w))
    seasons_done = [s for s in G.seasons if s["done"] and s["end"] >= cutoff]
    promoted = any(s["pos"] <= 3 and s["div"] < len(DIVS) - 1 for s in seasons_done)
    champs = any(s["pos"] == 1 for s in seasons_done)
    derby = any(r["derby"] and r["res"] == "WIN" and r["ws"] >= cutoff for r in G.all_results)
    C, R, E, L = "common", "rare", "epic", "legendary"
    G.badges = [
        ("👟", "Just Go For A Run", "Literally any run", C, True),
        ("5️⃣", "5K Finisher", "Run 5K", C, df["km"].max() >= 5),
        ("🔟", "10K Club", "Run 10K", R, df["km"].max() >= 10),
        ("🥨", "Half Mad", "Run a half marathon", L, df["km"].max() >= 21.1),
        ("⏱️", "Sub-30", "5K under 30:00", C, b5 < 1800),
        ("💥", "Old Me Beaten", "5K under 27:00", E, b5 < 1620),
        ("⚡", "Sub-25", "5K under 25:00", L, b5 < 1500),
        ("🏅", "No Former Glory", "Set an all-time PB", E, pbs >= 1),
        ("⌚", "Beat the Clock", "Win a time trial", R, trials >= 1),
        ("🕰️", "Clockwork", "Win 3 time trials", E, trials >= 3),
        ("👻", "Ghostbuster", "Beat your ghost 5 times", R, ghosts >= 5),
        ("📈", "In Form", "10 wins on the form guide", R, wins >= 10),
        ("🎩", "Hat-trick", "3 runs in one week", C, bool((wk_runs >= 3).any())),
        ("📆", "Three in a Row", "Run 3 days running", R, best_row >= 3),
        ("🔥", "On Fire", "3-week streak", R, G.best_streak >= 3),
        ("🧱", "Unbreakable", "8-week streak", E, G.best_streak >= 8),
        ("🎯", "Grinder", "25 runs", R, len(df) >= 25),
        ("📏", "50 Club", "50 km total", C, df["km"].sum() >= 50),
        ("💯", "Centurion", "100 km total", E, df["km"].sum() >= 100),
        ("🌅", "Early Bird", "Run before 7am", R, bool((d.dt.hour < 7).any())),
        ("🦉", "Night Owl", "Run after 9pm", R, bool((d.dt.hour >= 21).any())),
        ("😩", "Monday Motivation", "Run on a Monday", C, bool((d.dt.dayofweek == 0).any())),
        ("🍺", "Weekend Warrior", "Sat and Sun, same weekend", R, both_days),
        ("☔", "Mad Dog", "5 runs in the rain", R, rainy >= 5),
        ("🛋️", "Off the Sofa", "Run after a week off", C, comeback),
        ("🐢", "Slow and Proud", "A run slower than 7:30/km", C, bool((df["pace"] > 450).any())),
        ("🔬", "Precision Engineer", "Exactly 5.00 km", R, bool(((df["km"] >= 4.995) & (df["km"] < 5.005)).any())),
        ("🍕", "Pizza Earned", "8 km+ in one go", R, df["km"].max() >= 8),
        ("⛰️", "Hill Botherer", "50 m+ climb in a run", R, bool((df["elev"] >= 50).any())),
        ("🧊", "Ice Cold", "5K+ with avg HR under 150", E, bool(((hr_ok["km"] >= 5) & (hr_ok["hr"] < 150)).any())),
        ("🎃", "Spooky Strides", "Run on Halloween", E, bool((md == "10-31").any())),
        ("🎄", "Christmas Pudding", "Run on Christmas Day", L, bool((md == "12-25").any())),
        ("🎆", "New Year, Same Legs", "Run on 1 January", E, bool((md == "01-01").any())),
        ("🆙", "Going Up", "Win promotion", R, promoted),
        ("⚔️", "Derby Day", "Beat Gav in a league derby", E, derby),
        ("🏆", "Champions", "Finish a season top", L, champs),
    ]
    G.badges.sort(key=lambda b: (not b[4], [C, R, E, L].index(b[3])))


# ---------------------------------------------------------------- kits
def _kits(G, store):
    has_sb5 = any("SB 5K" in t or "PB 5K" in t for t in G.df["tags"]) if len(G.df) else False
    done_season = any(s["done"] for s in G.seasons)
    unlocked = {"home": True, "away": G.lvl >= 3, "stripes": len(G.df) >= 10, "neon": has_sb5,
                "retro": done_season, "gold": G.lvl >= 10, "blackout": G.best_streak >= 8}
    G.kits = [(k, n, how, unlocked[k], v) for k, n, how, v in KITS]
    chosen = store.get("kit", "home")
    G.kit = chosen if unlocked.get(chosen) else "home"
    G.kit_vars = next(v for k, n, how, v in KITS if k == G.kit)


# ---------------------------------------------------------------- simple run suggestion
def _suggest(G):
    df = G.alltime
    if not len(df):
        G.suggest = ("Easy 3K today", "Any pace. Just get the first one done.")
        return
    last = df.iloc[-1]
    ran_today = last["date"].normalize() == G.today
    hard_yday = last["date"].normalize() == G.today - pd.Timedelta(days=1) and last["type"] in ("Intervals", "Tempo", "Race")
    easy_runs = G.df[G.df["type"] == "Easy"]
    easy_km = round(easy_runs["km"].median()) if len(easy_runs) else 5
    easy_p = easy_runs["pace"].median() if len(easy_runs) else None
    ep = f" Around {clock(easy_p - 5)}–{clock(easy_p + 10)}/km." if easy_p else ""
    if G.preseason:
        G.suggest = ("Easy 20–25 min today", "Pre-season. Slow, short, no heroics. Just rebuild the habit.")
    elif ran_today:
        G.suggest = ("Rest. You've done today.", "Eat, stretch, sleep. Tomorrow's run starts tonight.")
    elif hard_yday:
        G.suggest = ("Rest or a 20 min recovery jog", "Yesterday was hard. Today is boring on purpose." + ep)
    else:
        ch = G.chapters[G.weeks_in] if 0 <= G.weeks_in < len(G.chapters) else None
        need = []
        if ch:
            wr = df[(df["date"] >= ch["start"]) & (df["date"] < ch["start"] + pd.Timedelta(weeks=1))]
            if ch["name"] == "Trial":
                if not ch["quests"][-1][5]:
                    need.append(("5K time trial", "Warm up 10 min easy, then 5K flat out."))
            else:
                if not wr["speed"].any() and G.today.weekday() <= 4:
                    need.append((ch["session"][0], ch["session"][1]))
                if not (wr["km"] >= ch["long"]).any() and G.today.weekday() >= 4:
                    need.append((f"Long run {ch['long']:g} km", "Chatting pace. Slow is fine." + ep))
        G.suggest = need[0] if need else (f"Easy {easy_km}K today", "Conversation pace, nothing more." + ep)
