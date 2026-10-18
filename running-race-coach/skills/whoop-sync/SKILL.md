---
name: whoop-sync
description: Imports running and recovery data from WHOOP (workouts, heart rate zones, strain, recovery, resting HR, HRV, sleep) via the official WHOOP API or a WHOOP data export, and saves it as a weekly training log. Also walks the athlete through connecting the WHOOP API. Use when the athlete mentions WHOOP, wants to sync or import their WHOOP data, shares a WHOOP export or screenshot, or when the running-coach skill needs WHOOP as the data source.
---

# WHOOP Training Log Sync

## Overview

Turns WHOOP data into the same weekly markdown training log the rest of the running coach uses, with extra focus on what WHOOP is good at: **heart rate zones, strain, and recovery**. This is what lets the coach check that easy runs really stayed in Zone 2 and that training load matches how recovered the athlete is.

All files are stored in the coach's home folder `~/running-coach/` (see "Where Files Live" in the running-coach skill) so every Claude Code session sees the same history.

## Workflow

### 1. Work Out the Date Range and Week Number

- Default to the last 7 days ending today, unless the athlete names a week.
- Look in `~/running-coach/training-log/` for existing `week-N.md` files and suggest the next number. If the athlete is following a plan in `~/running-coach/training-plan.md`, match the plan's week number.
- Confirm in one short question, e.g. "I'll grab Oct 12-18 as week 3 - sound right?"

### 2. Pick How to Get the Data (in this order)

**Option A - WHOOP API (recommended, automatic).** Check whether the athlete has connected the API:

```bash
python3 scripts/whoop_api.py status
```

If it says "connected", fetch the week (non-interactive, safe to run yourself):

```bash
mkdir -p ~/running-coach/training-log
python3 scripts/whoop_api.py fetch --start 2026-10-12 --end 2026-10-18 --unit mi \
  --output ~/running-coach/training-log/week-3.md
```

Then go to step 4. If it says "not set up" or the login expired, offer to connect (see "Connecting the WHOOP API" below), or fall back to Option B/C for today.

**Option B - WHOOP data export (no setup).** Ask the athlete for their export:
- In the WHOOP app: **More (or Profile) → App Settings → Data Export → Create Export**. WHOOP emails a zip file.
- Unzip it and tell Claude the folder path (e.g. `~/Downloads/my_whoop_data_2026_10_18`). It contains `workouts.csv`, `physiological_cycles.csv`, `sleeps.csv`, and `journal_entries.csv`.
- The exact menu names can change between app versions - if the athlete can't find it, suggest searching "export" in the app settings or WHOOP's help center.

**Option C - Screenshots or conversational.** The athlete can paste screenshots of WHOOP activity screens or just describe their runs ("45 min run, avg HR 142, mostly Zone 2, strain 10.2, recovery was 72%"). Build the log by hand in the same format.

### 3. Run the Export Import Script (Option B)

**IMPORTANT**: Use the scripts to do all the maths - never total zones or average recovery by hand.

The scripts are in `scripts/` (relative to this skill's directory).

```bash
mkdir -p ~/running-coach/training-log
python3 scripts/whoop_import.py \
  --dir "<path to unzipped export>" \
  --start 2026-10-12 --end 2026-10-18 \
  --unit mi \
  --output ~/running-coach/training-log/week-3.md
```

Notes for both scripts:
- Use `--unit km` if the athlete prefers kilometres (check `~/running-coach/profile.md` first).
- Runs are any activity whose name contains "run" or "jog"; everything else is listed as cross-training.
- Runs recorded without GPS have no distance or pace - mention this and ask if they know the distance (e.g. treadmill display), then add it to the file.
- WHOOP days start when you fall asleep, so a cycle that starts in the evening is counted as the next day.

### 4. Review the Log and Add Context

Read the generated file and add a short `## Notes` section at the bottom with anything useful the athlete tells you (treadmill vs outside, heat, how it felt, niggles).

### 5. Give a Quick Summary

Keep it short and friendly:
- Runs, total distance and time
- **Percentage of run time in Zones 1-2** - this is the headline number for aerobic base building (target roughly 80%+ for base building)
- Average recovery and any red-recovery days that had hard sessions
- Where the file was saved

Then offer to start a coaching session ("Want to talk through the week?") which hands off to the running-coach skill.

## Connecting the WHOOP API (one-time)

WHOOP has an official developer API (v2). Any WHOOP member can make a free personal "app" for their own account - no approval needed for personal use (unapproved apps are limited to 10 WHOOP members, which is plenty for one person). Walk the athlete through it one step at a time:

1. Go to **https://developer-dashboard.whoop.com** and sign in with their normal WHOOP login. Create a Team if asked (any name).
2. Click **Create App** and fill in:
   - **Name**: anything, e.g. "My Running Coach"
   - **Redirect URL**: `http://localhost:8765/callback` (must match exactly)
   - **Scopes**: `read:workout`, `read:recovery`, `read:cycles`, `read:sleep`, `read:profile`
   - If it asks for a privacy policy or other URLs, they can use their GitHub repo link
3. Copy the **Client ID** and **Client Secret** it shows.
4. Have them run the setup **in their own terminal app** (not through Claude), so the secret never lands in the chat. Work out the absolute path to this skill's `scripts/whoop_api.py` and give them one copy-paste line, e.g.:
   ```bash
   python3 "/full/path/to/whoop-sync/scripts/whoop_api.py" setup
   ```
   It asks for the Client ID and Secret (secret input is hidden), opens the browser to approve access, and prints "Connected to WHOOP as <name>".
   - If the browser step fails, run it again with `--manual` and paste the final `http://localhost...` address back into the terminal.
5. Run `python3 scripts/whoop_api.py status` to confirm, and note `data source: WHOOP API` in `profile.md`.

**If they paste their Client Secret into the chat anyway**, don't repeat it back; suggest they regenerate it in the dashboard later if they're worried.

**Things to know:**
- Credentials and login tokens are stored in `~/running-coach/.whoop/` with owner-only permissions. Never print, read out, or commit these files.
- The login refreshes itself automatically. If WHOOP ever says it can't refresh (e.g. not used for a long time, or access was revoked), have them run `whoop_api.py login` in their terminal.
- Rate limits are 100 requests/minute and 10,000/day - a weekly sync uses a handful.
- The API gives per-workout summaries (avg/max HR, time in each zone, strain, distance) and daily recovery, resting HR, HRV, and sleep. It does **not** give second-by-second heart rate, so HR drift within a run can't be measured from WHOOP data - ask how the second half felt instead, or use Strava/watch laps if they have them.
- Workouts WHOOP hasn't finished scoring yet are skipped; sync again later if a very recent run is missing.

## Reading WHOOP Data as a Coach

- **HR zones**: WHOOP zones are set from max heart rate (shown in the app under heart rate zones). Zone 2 is the aerobic base-building zone; Zone 3 is the "grey zone" that easy runs drift into. Rising Zone 3 time on easy runs = going too hard.
- **Recovery**: Green (67-100%) good to train, yellow (34-66%) keep it easy/moderate, red (0-33%) prioritize rest or very easy movement.
- **Resting HR and HRV trends**: a rising resting HR or falling HRV over several days is an early fatigue/illness signal. Compare to the athlete's own baseline, not general numbers.
- **Strain**: useful for overall load (including non-running stress); not a substitute for pace and zone analysis.
- **Aerobic progress signal**: the same easy pace at a lower average HR, or a faster pace at the same Zone 2 HR, over several weeks.

## Error Handling

- `redirect_uri not whitelisted` / redirect mismatch during setup: the Redirect URL in the WHOOP dashboard must be exactly `http://localhost:8765/callback`.
- `Address already in use` during login: something else is using port 8765 - rerun with `--manual`.
- `workouts.csv not found`: the path is wrong or the zip wasn't unzipped - ask them to check.
- Missing columns: the script matches column names loosely; if it still fails, read the CSV header and summarize manually using Python.
- No workouts in range: double-check dates (WHOOP uses the cycle's local time) and ask if the watch/strap recorded them.
