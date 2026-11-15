"""Splits: data layer. Strava runs (with splits and best efforts), demo runs, weather, and a tiny store."""
import datetime as dt
import json
import os
import random

import pandas as pd
import requests
import streamlit as st

TOKEN_URL = "https://www.strava.com/oauth/token"
API = "https://www.strava.com/api/v3"
RUN_SPORTS = {"Run", "TrailRun", "VirtualRun"}
DETAIL_DAYS = 100          # fetch full detail (splits, best efforts, weather) for runs this recent
PB_NAMES = ["1k", "1 mile", "5k", "10k", "half-marathon", "marathon"]
PB_LABEL = {"400m": "400 m", "1/2 mile": "½ mile", "1k": "1K", "1 mile": "1 mile", "2 mile": "2 mile",
            "5k": "5K", "10k": "10K", "15k": "15K", "10 mile": "10 mile", "20k": "20K",
            "half-marathon": "Half marathon", "30k": "30K", "marathon": "Marathon"}
EFFORT_KM = {"400m": 0.4, "1/2 mile": 0.8047, "1k": 1.0, "1 mile": 1.6093, "2 mile": 3.2187, "5k": 5.0,
             "10k": 10.0, "15k": 15.0, "10 mile": 16.093, "20k": 20.0, "half-marathon": 21.0975,
             "30k": 30.0, "marathon": 42.195}


def secret(key, default=None):
    try:
        return st.secrets[key]
    except Exception:
        return default


# ---------------------------------------------------------------- Strava
@st.cache_data(ttl=3000, show_spinner=False)
def access_token(client_id, client_secret, refresh_token):
    r = requests.post(TOKEN_URL, data={"client_id": client_id, "client_secret": client_secret,
                                       "grant_type": "refresh_token", "refresh_token": refresh_token}, timeout=20)
    r.raise_for_status()
    return r.json()["access_token"]


@st.cache_data(ttl=600, show_spinner=False)
def fetch_activities(token):
    out, page = [], 1
    while page <= 5:
        r = requests.get(f"{API}/athlete/activities", headers={"Authorization": f"Bearer {token}"},
                         params={"per_page": 200, "page": page}, timeout=30)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        out += batch
        page += 1
    return out


@st.cache_data(persist="disk", show_spinner=False)
def activity_detail(_token, activity_id):
    """Splits, best efforts and PRs for one run. Cached on disk so Strava isn't asked twice."""
    r = requests.get(f"{API}/activities/{activity_id}", headers={"Authorization": f"Bearer {_token}"}, timeout=30)
    r.raise_for_status()   # errors are not cached, so it retries next time
    j = r.json()
    splits = [{"n": s.get("split", i + 1), "km": (s.get("distance") or 0) / 1000,
               "secs": s.get("moving_time") or s.get("elapsed_time") or 0, "hr": s.get("average_heartrate")}
              for i, s in enumerate(j.get("splits_metric") or [])]
    efforts, prs = {}, []
    for e in j.get("best_efforts") or []:
        name = str(e.get("name", "")).lower()
        efforts[name] = e.get("moving_time") or e.get("elapsed_time")
        if e.get("pr_rank") == 1:
            prs.append(name)
    return {"splits": [s for s in splits if s["km"] > 0.05], "efforts": efforts, "prs": prs,
            "max_hr": j.get("max_heartrate")}


def strava_runs(client_id, client_secret, refresh_token):
    token = access_token(client_id, client_secret, refresh_token)
    acts = [a for a in fetch_activities(token) if a.get("sport_type", a.get("type")) in RUN_SPORTS]
    now = pd.Timestamp.now()
    rows = []
    for a in acts:
        km = (a.get("distance") or 0) / 1000
        if km < 0.2:
            continue
        when = pd.to_datetime(a["start_date_local"]).tz_localize(None)
        det = {"splits": [], "efforts": {}, "prs": [], "max_hr": a.get("max_heartrate")}
        if when >= now - pd.Timedelta(days=DETAIL_DAYS):
            try:
                det = activity_detail(token, a["id"])
            except Exception:
                pass
        best5 = det["efforts"].get("5k") or (a["moving_time"] * 5 / km if km >= 4.95 else None)
        ll = a.get("start_latlng") or None
        rows.append({"id": str(a["id"]), "name": a.get("name") or "Run", "date": when, "km": km,
                     "secs": a.get("moving_time") or 0, "hr": a.get("average_heartrate"),
                     "max_hr": det.get("max_hr"), "elev": a.get("total_elevation_gain") or 0,
                     "wtype": a.get("workout_type"), "latlng": tuple(ll) if ll and len(ll) == 2 else None,
                     "splits": det["splits"], "efforts": det["efforts"], "prs": det["prs"],
                     "best5k": best5, "weather": None})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- weather (Open-Meteo, free, no key)
@st.cache_data(persist="disk", show_spinner=False)
def _weather_lookup(lat, lng, day_iso, hour):
    day = dt.date.fromisoformat(day_iso)
    days_ago = (dt.date.today() - day).days
    base = ("https://api.open-meteo.com/v1/forecast" if days_ago <= 85
            else "https://archive-api.open-meteo.com/v1/archive")
    r = requests.get(base, params={"latitude": round(lat, 3), "longitude": round(lng, 3), "start_date": day_iso,
                                   "end_date": day_iso, "timezone": "auto",
                                   "hourly": "temperature_2m,precipitation,wind_speed_10m,weather_code"},
                     timeout=10)
    r.raise_for_status()
    h = r.json()["hourly"]
    i = min(hour, len(h["time"]) - 1)
    return {"temp": h["temperature_2m"][i], "rain": h["precipitation"][i] or 0,
            "wind": h["wind_speed_10m"][i] or 0, "code": h["weather_code"][i]}


def add_weather(df):
    """Fill the weather column for recent runs that have a GPS start. Fails quietly."""
    if df.empty:
        return df
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=DETAIL_DAYS)
    out = []
    for _, r in df.iterrows():
        w = r.get("weather")
        if not isinstance(w, dict) and r["latlng"] and r["date"] >= cutoff:
            try:
                w = _weather_lookup(r["latlng"][0], r["latlng"][1], r["date"].date().isoformat(), r["date"].hour)
            except Exception:
                w = None
        out.append(w if isinstance(w, dict) else None)
    df["weather"] = out
    return df


# ---------------------------------------------------------------- demo runs
def _split_list(km, paces, hrs):
    full, rest = int(km), km - int(km)
    out = [{"n": i + 1, "km": 1.0, "secs": paces[i], "hr": hrs[i]} for i in range(full)]
    if rest > 0.05:
        out.append({"n": full + 1, "km": rest, "secs": paces[min(full, len(paces) - 1)] * rest,
                    "hr": hrs[min(full, len(hrs) - 1)]})
    return out


def _efforts(splits):
    """Best rolling windows over whole-km splits (good enough for demo PBs)."""
    fulls = [s["secs"] for s in splits if s["km"] >= 0.99]
    eff = {}
    for name, k in (("1k", 1), ("5k", 5), ("10k", 10)):
        if len(fulls) >= k:
            eff[name] = min(sum(fulls[i:i + k]) for i in range(len(fulls) - k + 1))
    return eff


def demo_runs():
    rnd = random.Random(7)
    now = pd.Timestamp.now().floor("min")
    week0 = now.normalize() - pd.Timedelta(days=now.weekday()) - pd.Timedelta(weeks=16)
    rows = []

    def add(name, when, km, paces, hrs, wtype=None, weather=None):
        sp = _split_list(km, paces, hrs)
        secs = sum(s["secs"] for s in sp)
        rows.append({"id": f"d{len(rows)}", "name": name, "date": when, "km": round(km, 2), "secs": secs,
                     "hr": sum(hrs[:max(1, int(km))]) / max(1, int(km)), "max_hr": max(hrs) + 6,
                     "elev": rnd.choice([12, 18, 26, 41, 58]), "wtype": wtype, "latlng": None, "splits": sp,
                     "efforts": _efforts(sp), "prs": [], "best5k": None, "weather": weather})

    # the glory days, two years ago
    glory = now - pd.Timedelta(days=740)
    for i in range(14):
        when = glory + pd.Timedelta(days=4 * i, hours=7)
        km = rnd.choice([5.0, 5.0, 6.0])
        p = 334 - i * 0.8
        add("Morning Run", when, km, [p + rnd.uniform(-6, 6) for _ in range(7)], [152] * 7)

    for aw in range(17):                                   # 16 full weeks + this week
        if aw == 6:
            continue                                       # the week the sofa won
        mon = week0 + pd.Timedelta(weeks=aw)
        prog = aw / 16
        easy, longp = 395 - 28 * prog, 392 - 30 * prog
        cw = aw - 2
        plan = [(0, "Easy", "Lunch Run"), (2, "Session", None), (5 if aw % 2 else 6, "Long", "Long Run")]
        if aw in (9, 12, 14, 16):
            plan.insert(2, (4, "Easy", "Easy Run"))
        for day, kind, name in plan:
            when = mon + pd.Timedelta(days=day, hours=rnd.choice([6, 7, 12, 18]), minutes=rnd.randint(0, 50))
            if aw == 16 and day == 6:
                when = now.normalize() + pd.Timedelta(hours=9, minutes=12)
            if when > now:
                continue
            weather = {"temp": rnd.choice([4, 7, 9, 11, 13]), "rain": rnd.choice([0, 0, 0, 0.6, 1.8]),
                       "wind": rnd.choice([8, 12, 18, 27, 36]), "code": 3}
            if kind == "Easy":
                km = round(rnd.choice([4.6, 5.0, 5.3, 6.0]) + prog, 2)
                add(name, when, km, [easy + rnd.uniform(-8, 8) for _ in range(9)],
                    [150 - 6 * prog + rnd.uniform(-3, 3) for _ in range(9)], weather=weather)
            elif kind == "Long":
                km = round(6.2 + 3.6 * prog + rnd.uniform(-0.2, 0.2), 2)
                if aw == 16:
                    km = 10.21
                    weather = {"temp": 5, "rain": 2.4, "wind": 38, "code": 63}
                add(name, when, km, [longp + 4 * i + rnd.uniform(-6, 6) for i in range(12)],
                    [148 - 4 * prog + i * 1.2 for i in range(12)], wtype=2, weather=weather)
            else:
                if cw >= 0 and cw % 4 == 3:
                    p = 352 - 32 * prog
                    add("5K time trial", when, 5.02, [p + 4, p + 2, p + 1, p, p - 6],
                        [168, 173, 176, 178, 182], wtype=1, weather=weather)
                elif aw % 2:
                    p = 372 - 30 * prog
                    add("Tempo", when, 6.1, [easy + 10, p, p - 3, p - 2, p + 1, easy + 15, easy],
                        [150, 165, 168, 169, 170, 158, 150], weather=weather)
                else:
                    fast, jog = 330 - 30 * prog, 420 - 20 * prog
                    add("4x4 intervals", when, 6.3, [easy + 15, fast, jog, fast - 3, jog, fast - 6, easy + 20],
                        [148, 170, 158, 173, 160, 175, 152], weather=weather)
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    # Strava-style PRs: an effort is a PR if it beats every earlier effort at that distance
    best = {}
    prs = []
    for eff in df["efforts"]:
        mine = []
        for name, t in eff.items():
            if name not in best or t < best[name]:
                mine.append(name)          # Strava marks your first effort at a distance as a PR too
                best[name] = t
        prs.append(mine)
    df["prs"] = prs
    df["best5k"] = [e.get("5k") for e in df["efforts"]]
    return df


# ---------------------------------------------------------------- store (Google Sheet, or a local file)
class Store:
    """Tiny key-value store. Google Sheet if configured, otherwise a JSON file next to the app."""

    def __init__(self, demo=False):
        self.data, self.ws, self.rows = {}, None, {}
        self.kind = "file"
        self.path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 ".splits_demo.json" if demo else ".splits_store.json")
        url, creds = secret("GSHEET_URL"), secret("gcp_service_account")
        if url and creds and not demo:
            try:
                import gspread
                gc = gspread.service_account_from_dict(dict(creds))
                self.ws = gc.open_by_url(url).sheet1
                for i, row in enumerate(self.ws.get_all_values(), start=1):
                    if row and row[0]:
                        self.rows[row[0]] = i
                        try:
                            self.data[row[0]] = json.loads(row[1]) if len(row) > 1 and row[1] else None
                        except ValueError:
                            self.data[row[0]] = row[1]
                self.kind = "sheet"
                return
            except Exception as e:  # fall back to the file so the app still works
                self.error = str(e)
        try:
            with open(self.path) as f:
                self.data = json.load(f)
        except Exception:
            self.data = {}

    def get(self, key, default=None):
        v = self.data.get(key, default)
        return default if v is None else v

    def set(self, key, value):
        self.data[key] = value
        if self.ws is not None:
            payload = json.dumps(value)
            if key in self.rows:
                self.ws.update_cell(self.rows[key], 2, payload)
            else:
                self.ws.append_row([key, payload])
                self.rows[key] = max(self.rows.values(), default=0) + 1
            return
        try:
            with open(self.path, "w") as f:
                json.dump(self.data, f)
        except Exception:
            pass

