# Splits: setup

About 20 minutes, one-off. Do steps 1 and 3 on a laptop, the rest works on your phone.

## What's in the folder
- `app.py` (the main file), `splits_data.py`, `splits_engine.py`, `splits_ui.py`, `splits_lines.py`
- `requirements.txt`
- `.streamlit/config.toml` (colours). On a Mac it's hidden: press **Cmd + Shift + .** in Finder to see it.

## 1. GitHub: where the code lives (laptop)
1. Go to github.com and sign in.
2. You already made a repo called **Scoreboard**, so reuse it: open github.com/jameshenderson9921-hue/Scoreboard.
3. On the empty repo page, click the blue link **uploading an existing file** (it's in the "Quick setup" box).
4. Unzip `splits.zip`. Open the folder, select everything inside it (including `.streamlit`) and drag it onto the GitHub page.
5. Wait for the files to list, scroll down, click the green **Commit changes**.
6. You should now see `app.py` and friends on the repo page. That's GitHub done.

## 2. Strava: get your two keys
1. Go to **strava.com/settings/api**.
2. Application name: `Splits`. Category: Training. Website: `https://example.com`.
3. Authorization Callback Domain: the web address you'll pick in step 3, without https, e.g. `james-splits.streamlit.app`.
4. Save. Keep the **Client ID** and **Client Secret** handy.

## 3. Streamlit: put it online (laptop)
1. Go to **share.streamlit.io** and **Continue with GitHub**. Allow it to see private repos.
2. **Create app**, then **Deploy a public app from GitHub**.
3. Repository: `jameshenderson9921-hue/Scoreboard`. Branch: `main`. Main file: `app.py`.
4. App URL: `james-splits` (must match the Strava callback domain).
5. **Advanced settings → Secrets**, paste:
   ```
   STRAVA_CLIENT_ID = "your client id"
   STRAVA_CLIENT_SECRET = "your client secret"
   APP_URL = "https://james-splits.streamlit.app"
   CAMPAIGN_START = "2026-11-16"
   ```
6. **Deploy**. Two minutes later you'll see the demo version with a **Connect Strava** button.

## 4. Connect Strava (phone is fine)
1. Open the app, tap **Connect Strava**, then **Authorize**.
2. It shows a line starting `STRAVA_REFRESH_TOKEN = ...`. Copy it.
3. Streamlit: your app's **⋮ → Settings → Secrets**, paste the line under the others, save, then **⋮ → Reboot app**.
4. Open the app. Your runs are in.

## 5. Home screen
Open the link in **Safari → Share → Add to Home Screen**. One tap from now on.

## 6. Optional but recommended: a Google Sheet for your choices
Everything is worked out from Strava, so nothing gets lost. The only things the app saves are your own taps: run types you correct, your goal, your transfer signing and your kit. Without a sheet those can reset when the app restarts. To keep them for good:

1. Make a new Google Sheet called **Splits data**. Copy its link.
2. Go to **console.cloud.google.com** → create a project → search **Google Sheets API**, enable it, and enable **Google Drive API** too.
3. **IAM & Admin → Service Accounts → Create**. Name it `splits`. Then open it → **Keys → Add key → JSON**. A file downloads.
4. Share your Google Sheet with the service account's email (ends in `iam.gserviceaccount.com`) as **Editor**.
5. Add to your Streamlit Secrets (fill in from the JSON file):
   ```
   GSHEET_URL = "https://docs.google.com/spreadsheets/d/..."

   [gcp_service_account]
   type = "service_account"
   project_id = "..."
   private_key_id = "..."
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "splits@....iam.gserviceaccount.com"
   client_id = "..."
   token_uri = "https://oauth2.googleapis.com/token"
   ```
6. Reboot the app.

## Good to know
- Record runs with the Watch (Strava app, or the Workout app synced to Strava) so heart rate and splits come through.
- Run types are guessed from your splits. If one's wrong, tap the right one under the run.
- Weather comes from Open-Meteo using the run's start point and time. Treadmill runs get no weather.
- No notifications. It updates when you open it. If it's been asleep, the first open takes about 30 seconds.
- Optional extra secret: `APP_PIN = "1234"` locks the app with a PIN.
