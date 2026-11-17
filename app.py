"""Splits: running stats from Strava. No former glory."""
import pandas as pd
import requests
import streamlit as st

import splits_data as D
import splits_engine as E
import splits_ui as U
import splits_v2 as V

st.set_page_config(page_title="Splits", page_icon="🏃", layout="centered", initial_sidebar_state="collapsed")

CLIENT_ID = D.secret("STRAVA_CLIENT_ID")
CLIENT_SECRET = D.secret("STRAVA_CLIENT_SECRET")
REFRESH_TOKEN = D.secret("STRAVA_REFRESH_TOKEN")
APP_URL = D.secret("APP_URL", "")
PIN = D.secret("APP_PIN")

st.markdown(U.CSS, unsafe_allow_html=True)

# ---------- optional PIN lock
if PIN and not st.session_state.get("unlocked"):
    st.markdown("### 🔒 Splits")
    entered = st.text_input("PIN", type="password")
    if entered == str(PIN):
        st.session_state.unlocked = True
        st.rerun()
    elif entered:
        st.error("Wrong PIN")
    st.stop()

# ---------- one-off Strava connection (the redirect lands back here with ?code=)
code = st.query_params.get("code")
if code and CLIENT_ID and not REFRESH_TOKEN:
    r = requests.post(D.TOKEN_URL, data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
                                         "code": code, "grant_type": "authorization_code"}, timeout=20)
    if r.ok:
        st.success("Strava connected. Last step:")
        st.write("Copy this line into your app's **Secrets**, save, then reboot the app.")
        st.code(f'STRAVA_REFRESH_TOKEN = "{r.json()["refresh_token"]}"', language="toml")
    else:
        st.error(f"Strava said no ({r.status_code}). Try connecting again.")
    st.stop()

demo = not (CLIENT_ID and CLIENT_SECRET and REFRESH_TOKEN)


@st.cache_resource
def get_store(is_demo):
    return D.Store(demo=is_demo)


store = get_store(demo)

if demo:
    raw = D.demo_runs()
else:
    try:
        with st.spinner("Pulling your runs from Strava..."):
            raw = D.strava_runs(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)
            raw = D.add_weather(raw)
    except Exception as e:
        st.error(f"Couldn't reach Strava: {e}")
        st.stop()

if raw.empty:
    st.markdown('<div class="card"><div class="mid">No runs yet</div>'
                '<div class="sub">Record a run on Strava and it lands here.</div></div>', unsafe_allow_html=True)
    st.stop()

G = E.build(raw, store, demo=demo)

# ---------- kit colours
v = G.kit_vars
st.markdown(f"<style>:root{{--g1:{v['g1']};--g2:{v['g2']};--base:{v['base']};--card:{v['card']};"
            f"--line:{v['line']};--acc:{v['acc']};--acc2:{v['acc2']}}}</style>", unsafe_allow_html=True)

V.header(G, store)
if demo:
    st.caption("Demo data. Connect Strava to see your own runs.")
    if CLIENT_ID and APP_URL:
        url = (f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code"
               f"&redirect_uri={APP_URL}&approval_prompt=force&scope=activity:read_all")
        st.link_button("Connect Strava", url, width="stretch")
tabs = st.tabs(["Run", "League", "Objectives", "Goals"])
with tabs[0]:
    V.page_run(G, store)
with tabs[1]:
    V.page_league(G)
with tabs[2]:
    V.page_objectives(G, store)
with tabs[3]:
    V.page_goals2(G, store)

# celebrate a fresh PB once per visit
fresh = G.alltime[G.alltime["date"] >= G.today - pd.Timedelta(days=2)]
if not st.session_state.get("celebrated") and any(t.startswith("PB") for tags in fresh["tags"] for t in tags):
    st.session_state.celebrated = True
    st.balloons()
