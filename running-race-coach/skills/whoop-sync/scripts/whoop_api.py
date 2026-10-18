#!/usr/bin/env python3
"""
Pull training and recovery data straight from the WHOOP developer API (v2)
and write it as a markdown training log.

One-time setup (run in your own terminal, not through Claude, so your
client secret never ends up in a chat):

    python3 whoop_api.py setup

Then, any time:

    python3 whoop_api.py status
    python3 whoop_api.py fetch --start 2026-10-12 --end 2026-10-18 --output week-3.md

Credentials and tokens are stored in ~/running-coach/.whoop/ (readable only
by you). Uses only the Python standard library.
"""

import argparse
import getpass
import json
import os
import secrets
import string
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import date, datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

from whoop_import import build_markdown, cycle_day, write_output

API_BASE = os.environ.get("WHOOP_API_BASE", "https://api.prod.whoop.com")
AUTH_URL = f"{API_BASE}/oauth/oauth2/auth"
TOKEN_URL = f"{API_BASE}/oauth/oauth2/token"
SCOPES = "offline read:workout read:recovery read:cycles read:sleep read:profile"
REDIRECT_PORT = 8765
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"
USER_AGENT = "claude-running-coach/1.0"

CONFIG_DIR = os.path.expanduser(os.environ.get("WHOOP_CONFIG_DIR", "~/running-coach/.whoop"))
CREDENTIALS_FILE = os.path.join(CONFIG_DIR, "credentials.json")
TOKENS_FILE = os.path.join(CONFIG_DIR, "tokens.json")
PENDING_STATE_FILE = os.path.join(CONFIG_DIR, "pending_login.json")


# ---------------------------------------------------------------- storage

def save_private_json(path, data):
    os.makedirs(CONFIG_DIR, mode=0o700, exist_ok=True)
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def load_credentials():
    creds = load_json(CREDENTIALS_FILE) or {}
    client_id = os.environ.get("WHOOP_CLIENT_ID") or creds.get("client_id")
    client_secret = os.environ.get("WHOOP_CLIENT_SECRET") or creds.get("client_secret")
    if not client_id or not client_secret:
        sys.exit("WHOOP is not set up yet. Run `python3 whoop_api.py setup` in your terminal first.")
    return client_id, client_secret


# ---------------------------------------------------------------- http

def http_request(url, data=None, headers=None, retries=3):
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json", **(headers or {})}
    body = None
    if data is not None:
        body = urllib.parse.urlencode(data).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=body, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read() or b"null")
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries:
                wait = int(e.headers.get("X-RateLimit-Reset") or e.headers.get("Retry-After") or 30)
                print(f"WHOOP rate limit hit, waiting {wait}s...", file=sys.stderr)
                time.sleep(min(wait, 120))
                continue
            raise


def describe_http_error(e):
    try:
        detail = e.read().decode()[:300]
    except Exception:
        detail = ""
    return f"HTTP {e.code} from WHOOP: {detail}"


# ---------------------------------------------------------------- oauth

def store_tokens(tokens):
    tokens["expires_at"] = time.time() + int(tokens.get("expires_in", 3600))
    save_private_json(TOKENS_FILE, tokens)
    return tokens


def exchange_code(code):
    client_id, client_secret = load_credentials()
    tokens = http_request(TOKEN_URL, data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "client_secret": client_secret,
    })
    if not tokens.get("refresh_token"):
        print("Warning: WHOOP did not return a refresh token; you'll need to log in again in an hour.",
              file=sys.stderr)
    return store_tokens(tokens)


def refresh_tokens(tokens):
    # WHOOP refresh tokens are single use: the new pair must be saved straight away.
    client_id, client_secret = load_credentials()
    try:
        new = http_request(TOKEN_URL, data={
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "offline",
        })
    except urllib.error.HTTPError as e:
        sys.exit(f"Could not refresh the WHOOP login ({describe_http_error(e)}).\n"
                 "Run `python3 whoop_api.py login` in your terminal to reconnect.")
    return store_tokens(new)


def access_token(force_refresh=False):
    tokens = load_json(TOKENS_FILE)
    if not tokens:
        sys.exit("Not logged in to WHOOP. Run `python3 whoop_api.py login` in your terminal.")
    if force_refresh or time.time() > tokens.get("expires_at", 0) - 60:
        if not tokens.get("refresh_token"):
            sys.exit("WHOOP login expired. Run `python3 whoop_api.py login` in your terminal.")
        tokens = refresh_tokens(tokens)
    return tokens["access_token"]


def make_state():
    return "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))


def authorize_url(state):
    client_id, _ = load_credentials()
    return AUTH_URL + "?" + urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
    })


def code_from_redirect(url, state):
    params = urllib.parse.parse_qs(urllib.parse.urlparse(url.strip()).query)
    if "error" in params:
        sys.exit(f"WHOOP login was not completed: {params.get('error_description', params['error'])[0]}")
    if params.get("state", [None])[0] != state:
        sys.exit("Login response did not match this login attempt (state mismatch). Please try again.")
    if "code" not in params:
        sys.exit("No authorization code found in that URL.")
    return params["code"][0]


def wait_for_callback(state, timeout=300):
    result = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if not self.path.startswith("/callback"):
                self.send_response(404)
                self.end_headers()
                return
            result["url"] = self.path
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>WHOOP connected to your running coach.</h2>"
                             b"<p>You can close this tab and go back to Claude Code.</p>")

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", REDIRECT_PORT), Handler)
    server.timeout = 1
    deadline = time.time() + timeout
    while "url" not in result and time.time() < deadline:
        server.handle_request()
    server.server_close()
    if "url" not in result:
        sys.exit("Timed out waiting for the WHOOP login. Run `python3 whoop_api.py login` to try again.")
    return code_from_redirect(result["url"], state)


def cmd_setup(args):
    print("Create a WHOOP app at https://developer-dashboard.whoop.com (sign in with your WHOOP account).")
    print(f"  - Redirect URL:  {REDIRECT_URI}")
    print("  - Scopes:        read:workout, read:recovery, read:cycles, read:sleep, read:profile")
    print("Then copy the Client ID and Client Secret it gives you.\n")
    client_id = args.client_id or input("Client ID: ").strip()
    client_secret = os.environ.get("WHOOP_CLIENT_SECRET") or getpass.getpass("Client Secret (hidden): ").strip()
    if not client_id or not client_secret:
        sys.exit("Both the Client ID and Client Secret are needed.")
    save_private_json(CREDENTIALS_FILE, {"client_id": client_id, "client_secret": client_secret})
    print(f"Saved to {CREDENTIALS_FILE}\n")
    cmd_login(args)


def cmd_login(args):
    if args.redirect_url:
        # Second half of a two-step login (e.g. a cloud session with no browser).
        pending = load_json(PENDING_STATE_FILE)
        if not pending:
            sys.exit("No login in progress. Run `whoop_api.py login --print-url` first.")
        code = code_from_redirect(args.redirect_url, pending["state"])
        os.remove(PENDING_STATE_FILE)
        finish_login(code)
        return
    state = make_state()
    url = authorize_url(state)
    if args.print_url:
        # First half of a two-step login: remember the state so --redirect-url can finish it later.
        save_private_json(PENDING_STATE_FILE, {"state": state})
        print(url)
        return
    if args.manual:
        print("Open this link, approve access, then paste the full address your browser ends up on")
        print("(it starts with http://localhost and the page may say it can't connect - that's fine):\n")
        print(url + "\n")
        code = code_from_redirect(input("Redirected URL: "), state)
    else:
        print("Opening your browser to log in to WHOOP. If it doesn't open, visit:\n")
        print(url + "\n")
        webbrowser.open(url)
        code = wait_for_callback(state)
    finish_login(code)


def finish_login(code):
    try:
        exchange_code(code)
    except urllib.error.HTTPError as e:
        sys.exit(f"Login failed: {describe_http_error(e)}")
    profile = api_get("/developer/v2/user/profile/basic")
    print(f"Connected to WHOOP as {profile.get('first_name', '')} {profile.get('last_name', '')}".rstrip())


# ---------------------------------------------------------------- api

def api_get(path, params=None):
    url = f"{API_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(2):
        token = access_token(force_refresh=attempt > 0)
        try:
            return http_request(url, headers={"Authorization": f"Bearer {token}"})
        except urllib.error.HTTPError as e:
            if e.code == 401 and attempt == 0:
                continue
            sys.exit(f"WHOOP API request failed: {describe_http_error(e)}")


def api_collection(path, start, end):
    records, next_token = [], None
    while True:
        params = {"limit": 25, "start": start, "end": end}
        if next_token:
            params["nextToken"] = next_token
        page = api_get(path, params)
        records += page.get("records", [])
        next_token = page.get("next_token")
        if not next_token:
            return records


def parse_iso(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def to_local(value, offset):
    """WHOOP returns UTC times plus the member's timezone offset (e.g. '-04:00')."""
    moment = parse_iso(value)
    if moment is None:
        return None
    try:
        sign = -1 if offset.startswith("-") else 1
        hours, minutes = offset.lstrip("+-").split(":")
        tz = timezone(sign * timedelta(hours=int(hours), minutes=int(minutes)))
    except (AttributeError, ValueError):
        tz = timezone.utc
    return moment.astimezone(tz).replace(tzinfo=None)


def convert_workout(record):
    offset = record.get("timezone_offset") or "+00:00"
    started = to_local(record["start"], offset)
    ended = to_local(record.get("end"), offset)
    duration_min = (ended - started).total_seconds() / 60 if ended else 0.0
    score = record.get("score") or {}
    zones_ms = score.get("zone_durations") or {}
    zone_keys = {1: "zone_one_milli", 2: "zone_two_milli", 3: "zone_three_milli",
                 4: "zone_four_milli", 5: "zone_five_milli"}
    total_ms = duration_min * 60000
    zones = {z: (zones_ms[k] / total_ms * 100) for z, k in zone_keys.items()
             if zones_ms.get(k) is not None and total_ms}
    kilojoule = score.get("kilojoule")
    return {
        "start": started,
        "name": (record.get("sport_name") or "Activity").replace("_", " ").title(),
        "duration": duration_min,
        "strain": score.get("strain"),
        "calories": kilojoule / 4.184 if kilojoule is not None else None,
        "max_hr": score.get("max_heart_rate"),
        "avg_hr": score.get("average_heart_rate"),
        "distance_m": score.get("distance_meter"),
        "altitude_m": score.get("altitude_gain_meter"),
        "zones": zones,
    }


def convert_days(cycles, recoveries, sleeps, start, end):
    recovery_by_cycle = {r.get("cycle_id"): r for r in recoveries}
    sleep_by_id = {s.get("id"): s for s in sleeps if not s.get("nap")}
    sleep_by_cycle = {s.get("cycle_id"): s for s in sleeps if not s.get("nap") and s.get("cycle_id")}
    days = []
    for cycle in cycles:
        started = to_local(cycle["start"], cycle.get("timezone_offset") or "+00:00")
        day = cycle_day(started)
        if not (start <= day <= end):
            continue
        recovery = recovery_by_cycle.get(cycle.get("id")) or {}
        rec_score = recovery.get("score") or {}
        sleep = sleep_by_id.get(recovery.get("sleep_id")) or sleep_by_cycle.get(cycle.get("id")) or {}
        sleep_score = sleep.get("score") or {}
        days.append({
            "date": day,
            "recovery": rec_score.get("recovery_score"),
            "rhr": rec_score.get("resting_heart_rate"),
            "hrv": rec_score.get("hrv_rmssd_milli"),
            "strain": (cycle.get("score") or {}).get("strain"),
            "sleep": sleep_score.get("sleep_performance_percentage"),
        })
    return sorted(days, key=lambda d: d["date"])


def cmd_status(args):
    load_credentials()
    profile = api_get("/developer/v2/user/profile/basic")
    print(f"WHOOP connected as {profile.get('first_name', '')} {profile.get('last_name', '')}".rstrip())


def cmd_fetch(args):
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    # Query a day either side so local-time and evening-cycle edges are covered, then filter by local date.
    query_start = f"{start - timedelta(days=1)}T00:00:00.000Z"
    query_end = f"{end + timedelta(days=2)}T00:00:00.000Z"

    workouts = [convert_workout(w) for w in api_collection("/developer/v2/activity/workout", query_start, query_end)
                if w.get("score_state") == "SCORED"]
    workouts = sorted((w for w in workouts if start <= w["start"].date() <= end), key=lambda w: w["start"])
    cycles = api_collection("/developer/v2/cycle", query_start, query_end)
    recoveries = api_collection("/developer/v2/recovery", query_start, query_end)
    sleeps = api_collection("/developer/v2/activity/sleep", query_start, query_end)
    days = convert_days(cycles, recoveries, sleeps, start, end)

    markdown = build_markdown(workouts, days, start, end, args.unit, source="WHOOP API")
    write_output(markdown, args.output, workouts, days)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("setup", help="Save your WHOOP app credentials and log in (run in your own terminal)")
    p.add_argument("--client-id", help="Client ID (otherwise you'll be asked)")
    p.add_argument("--manual", action="store_true", help="Paste the redirect URL instead of using a local callback")
    p.set_defaults(func=cmd_setup)

    p = sub.add_parser("login", help="Log in to WHOOP again (if the connection expired)")
    p.add_argument("--manual", action="store_true", help="Paste the redirect URL instead of using a local callback")
    p.add_argument("--print-url", action="store_true",
                   help="Two-step login, part 1: print the approval link and exit")
    p.add_argument("--redirect-url", help="Two-step login, part 2: the http://localhost... address after approving")
    p.set_defaults(func=cmd_login)

    p = sub.add_parser("status", help="Check the WHOOP connection")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("fetch", help="Download a date range as a markdown training log")
    p.add_argument("--start", required=True, help="Start date YYYY-MM-DD (inclusive)")
    p.add_argument("--end", required=True, help="End date YYYY-MM-DD (inclusive)")
    p.add_argument("--unit", choices=["mi", "km"], default="mi", help="Distance unit (default: mi)")
    p.add_argument("--output", help="Write markdown to this file instead of stdout")
    p.set_defaults(func=cmd_fetch)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
