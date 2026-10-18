---
name: whoop-sync
description: Imports running and recovery data from WHOOP (workouts, heart rate zones, strain, recovery, resting HR, HRV, sleep) and saves it as a weekly training log. Use when the athlete mentions WHOOP, wants to sync or import their WHOOP data, shares a WHOOP export or screenshot, or when the running-coach skill needs WHOOP as the data source.
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

**Option A - WHOOP MCP tools (automatic).** Check whether any tools with `whoop` in their name are available (e.g. `mcp__whoop__*`). If so, use them to fetch workouts and recovery/cycle data for the date range, then go to step 4 and write the log in the same format the script produces.

**Option B - WHOOP data export (most detailed, no setup).** If there are no WHOOP tools, ask the athlete for their export:
- In the WHOOP app: **More (or Profile) → App Settings → Data Export → Create Export**. WHOOP emails a zip file.
- Unzip it and tell Claude the folder path (e.g. `~/Downloads/my_whoop_data_2026_10_18`). It contains `workouts.csv`, `physiological_cycles.csv`, `sleeps.csv`, and `journal_entries.csv`.
- The exact menu names can change between app versions - if the athlete can't find it, suggest searching "export" in the app settings or WHOOP's help center.

**Option C - Screenshots or conversational.** The athlete can paste screenshots of WHOOP activity screens or just describe their runs ("45 min run, avg HR 142, mostly Zone 2, strain 10.2, recovery was 72%"). Build the log by hand in the same format.

### 3. Run the Import Script (Option B)

**IMPORTANT**: Use the script to do all the maths - never total zones or average recovery by hand.

The script is at `scripts/whoop_import.py` (relative to this skill's directory).

```bash
mkdir -p ~/running-coach/training-log
python3 scripts/whoop_import.py \
  --dir "<path to unzipped export>" \
  --start 2026-10-12 --end 2026-10-18 \
  --unit mi \
  --output ~/running-coach/training-log/week-3.md
```

- Use `--unit km` if the athlete prefers kilometres (check `~/running-coach/profile.md` first).
- Runs are any activity whose name contains "run" or "jog"; everything else is listed as cross-training.
- Runs recorded without GPS have no distance or pace - mention this and ask if they know the distance (e.g. treadmill display), then add it to the file.

### 4. Review the Log and Add Context

Read the generated file and add a short `## Notes` section at the bottom with anything useful the athlete tells you (treadmill vs outside, heat, how it felt, niggles).

### 5. Give a Quick Summary

Keep it short and friendly:
- Runs, total distance and time
- **Percentage of run time in Zones 1-2** - this is the headline number for aerobic base building (target roughly 80%+ for base building)
- Average recovery and any red-recovery days that had hard sessions
- Where the file was saved

Then offer to start a coaching session ("Want to talk through the week?") which hands off to the running-coach skill.

## Reading WHOOP Data as a Coach

- **HR zones**: WHOOP zones are set from max heart rate (shown in the app under heart rate zones). Zone 2 is the aerobic base-building zone; Zone 3 is the "grey zone" that easy runs drift into. Rising Zone 3 time on easy runs = going too hard.
- **Recovery**: Green (67-100%) good to train, yellow (34-66%) keep it easy/moderate, red (0-33%) prioritize rest or very easy movement.
- **Resting HR and HRV trends**: a rising resting HR or falling HRV over several days is an early fatigue/illness signal. Compare to the athlete's own baseline, not general numbers.
- **Strain**: useful for overall load (including non-running stress); not a substitute for pace and zone analysis.
- **Aerobic progress signal**: the same easy pace at a lower average HR, or a faster pace at the same Zone 2 HR, over several weeks.

## Error Handling

- `workouts.csv not found`: the path is wrong or the zip wasn't unzipped - ask them to check.
- Missing columns: the script matches column names loosely; if it still fails, read the CSV header and summarize manually using Python.
- No workouts in range: double-check dates (WHOOP uses the cycle's local time) and ask if the watch/strap recorded them.
