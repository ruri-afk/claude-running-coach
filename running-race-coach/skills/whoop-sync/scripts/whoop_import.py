#!/usr/bin/env python3
"""
Summarize a WHOOP data export (the CSVs WHOOP emails you from the app) for a
date range, as a markdown training log.

Reads workouts.csv (required) and physiological_cycles.csv (optional, for
recovery / resting HR / HRV / strain). Column names are matched loosely so
small changes in WHOOP's export format don't break the import.
"""

import argparse
import csv
import os
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta

METERS_PER_MILE = 1609.344


def parse_datetime(value):
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value[:19], fmt)
        except ValueError:
            continue
    return None


def cycle_day(started):
    """The calendar day a WHOOP cycle belongs to. Cycles begin when you fall
    asleep, so one starting in the evening counts as the next day."""
    return (started + timedelta(days=1)).date() if started.hour >= 18 else started.date()


def parse_number(value):
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def find_column(headers, *keywords, exclude=()):
    """Return the first header containing all keywords (case-insensitive)."""
    for header in headers:
        lower = header.lower()
        if all(k in lower for k in keywords) and not any(x in lower for x in exclude):
            return header
    return None


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def format_duration(minutes):
    total_seconds = int(round(minutes * 60))
    hours, rem = divmod(total_seconds, 3600)
    mins, secs = divmod(rem, 60)
    return f"{hours}:{mins:02d}:{secs:02d}"


def format_pace(minutes, distance):
    if not distance:
        return None
    pace = minutes / distance
    whole = int(pace)
    secs = int(round((pace - whole) * 60))
    if secs == 60:
        whole, secs = whole + 1, 0
    return f"{whole}:{secs:02d}"


def is_run(activity_name):
    name = activity_name.lower()
    return "run" in name or "jog" in name


def load_workouts(path, start, end):
    headers, rows = read_csv(path)
    cols = {
        "start": find_column(headers, "workout start"),
        "name": find_column(headers, "activity name") or find_column(headers, "sport"),
        "duration": find_column(headers, "duration"),
        "strain": find_column(headers, "strain"),
        "calories": find_column(headers, "energy") or find_column(headers, "cal"),
        "max_hr": find_column(headers, "max hr"),
        "avg_hr": find_column(headers, "average hr") or find_column(headers, "avg hr"),
        "distance": find_column(headers, "distance"),
        "altitude": find_column(headers, "altitude gain") or find_column(headers, "elevation"),
    }
    if not cols["start"]:
        sys.exit(f"Could not find a 'Workout start time' column in {path}. Headers: {headers}")
    zone_cols = {}
    for zone in range(1, 6):
        col = find_column(headers, f"zone {zone}")
        if col:
            zone_cols[zone] = col

    workouts = []
    for row in rows:
        started = parse_datetime(row.get(cols["start"]))
        if not started or not (start <= started.date() <= end):
            continue
        get = lambda key: parse_number(row.get(cols[key])) if cols[key] else None
        workouts.append({
            "start": started,
            "name": (row.get(cols["name"]) or "Activity").strip() if cols["name"] else "Activity",
            "duration": get("duration") or 0.0,
            "strain": get("strain"),
            "calories": get("calories"),
            "max_hr": get("max_hr"),
            "avg_hr": get("avg_hr"),
            "distance_m": get("distance"),
            "altitude_m": get("altitude"),
            "zones": {z: parse_number(row.get(c)) for z, c in zone_cols.items()},
        })
    return sorted(workouts, key=lambda w: w["start"])


def load_cycles(path, start, end):
    headers, rows = read_csv(path)
    cols = {
        "start": find_column(headers, "cycle start"),
        "recovery": find_column(headers, "recovery"),
        "rhr": find_column(headers, "resting heart rate"),
        "hrv": find_column(headers, "heart rate variability") or find_column(headers, "hrv"),
        "strain": find_column(headers, "day strain") or find_column(headers, "strain"),
        "sleep": find_column(headers, "sleep performance"),
    }
    if not cols["start"]:
        return []
    days = []
    for row in rows:
        started = parse_datetime(row.get(cols["start"]))
        if not started or not (start <= cycle_day(started) <= end):
            continue
        get = lambda key: parse_number(row.get(cols[key])) if cols[key] else None
        days.append({
            "date": cycle_day(started),
            "recovery": get("recovery"),
            "rhr": get("rhr"),
            "hrv": get("hrv"),
            "strain": get("strain"),
            "sleep": get("sleep"),
        })
    return sorted(days, key=lambda d: d["date"])


def average(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def fmt(value, digits=0, suffix=""):
    return "n/a" if value is None else f"{value:.{digits}f}{suffix}"


def zone_minutes(workout):
    return {z: workout["duration"] * pct / 100 for z, pct in workout["zones"].items() if pct is not None}


def build_markdown(workouts, cycles, start, end, unit, source="WHOOP data export"):
    to_unit = (lambda m: m / METERS_PER_MILE) if unit == "mi" else (lambda m: m / 1000)
    elev_unit = "ft" if unit == "mi" else "m"
    to_elev = (lambda m: m * 3.28084) if unit == "mi" else (lambda m: m)
    out = [f"# Training Log: {start} to {end}", "", f"*Source: {source}*", "", "## Week Summary", ""]

    by_type = defaultdict(list)
    for w in workouts:
        by_type["Run" if is_run(w["name"]) else w["name"]].append(w)

    total_minutes = sum(w["duration"] for w in workouts)
    out += ["### Overall Totals",
            f"- **Total Activities**: {len(workouts)}",
            f"- **Total Time**: {format_duration(total_minutes)}", ""]

    runs = by_type.get("Run", [])
    if runs:
        run_distance = sum(to_unit(w["distance_m"]) for w in runs if w["distance_m"])
        run_minutes = sum(w["duration"] for w in runs)
        zone_totals = defaultdict(float)
        for w in runs:
            for z, mins in zone_minutes(w).items():
                zone_totals[z] += mins
        out += ["### Running",
                f"- **Runs**: {len(runs)}",
                f"- **Distance**: {run_distance:.2f} {unit}" + ("" if run_distance else " (no GPS distance recorded)"),
                f"- **Time**: {format_duration(run_minutes)}"]
        if zone_totals:
            tracked = sum(zone_totals.values())
            easy = zone_totals.get(1, 0) + zone_totals.get(2, 0)
            if tracked:
                out.append(f"- **Time in Zones 1-2 (easy/aerobic)**: {format_duration(easy)} "
                           f"({easy / tracked * 100:.0f}% of run time)")
            out += ["", "| Zone | Minutes | % of run time |", "|------|---------|---------------|"]
            for z in range(1, 6):
                mins = zone_totals.get(z, 0)
                pct = mins / tracked * 100 if tracked else 0
                out.append(f"| {z} | {mins:.0f} | {pct:.0f}% |")
        out.append("")

    others = {k: v for k, v in by_type.items() if k != "Run"}
    if others:
        out += ["### Cross-Training"]
        for name, items in sorted(others.items()):
            out.append(f"- **{name}**: {len(items)}x, {format_duration(sum(w['duration'] for w in items))}")
        out.append("")

    if cycles:
        out += ["### Recovery & Readiness",
                f"- **Avg Recovery**: {fmt(average(d['recovery'] for d in cycles), 0, '%')}",
                f"- **Avg Resting HR**: {fmt(average(d['rhr'] for d in cycles), 0, ' bpm')}",
                f"- **Avg HRV**: {fmt(average(d['hrv'] for d in cycles), 0, ' ms')}",
                f"- **Avg Day Strain**: {fmt(average(d['strain'] for d in cycles), 1)}",
                f"- **Avg Sleep Performance**: {fmt(average(d['sleep'] for d in cycles), 0, '%')}",
                "",
                "| Date | Recovery | Resting HR | HRV | Day Strain | Sleep |",
                "|------|----------|------------|-----|------------|-------|"]
        for d in cycles:
            out.append(f"| {d['date']} | {fmt(d['recovery'], 0, '%')} | {fmt(d['rhr'])} | "
                       f"{fmt(d['hrv'])} | {fmt(d['strain'], 1)} | {fmt(d['sleep'], 0, '%')} |")
        out.append("")

    out += ["## Activities", ""]
    for w in workouts:
        out.append(f"### {w['start']:%Y-%m-%d %a} - {w['name']}")
        out.append("")
        out.append(f"**Type**: {'Run' if is_run(w['name']) else w['name']}  ")
        if w["distance_m"]:
            dist = to_unit(w["distance_m"])
            out.append(f"**Distance**: {dist:.2f} {unit}  ")
        out.append(f"**Duration**: {format_duration(w['duration'])}  ")
        if w["distance_m"] and is_run(w["name"]):
            out.append(f"**Pace**: {format_pace(w['duration'], to_unit(w['distance_m']))} /{unit}  ")
        if w["altitude_m"] is not None:
            out.append(f"**Elevation Gain**: {to_elev(w['altitude_m']):.0f} {elev_unit}  ")
        out.append(f"**Heart Rate**: {fmt(w['avg_hr'])} avg (max: {fmt(w['max_hr'])})  ")
        out.append(f"**Strain**: {fmt(w['strain'], 1)}  ")
        zm = zone_minutes(w)
        if zm:
            out.append("**HR Zones**: " + " · ".join(f"Z{z} {m:.0f}min" for z, m in sorted(zm.items())))
        out += ["", "---", ""]
    if not workouts:
        out += ["No workouts found in this date range.", ""]
    return "\n".join(out)


def write_output(markdown, output, workouts, cycles):
    if output:
        os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
        with open(output, "w") as f:
            f.write(markdown)
        print(f"Wrote {output} ({len(workouts)} workouts, {len(cycles)} days of recovery data)")
    else:
        print(markdown)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", required=True, help="Folder containing the unzipped WHOOP export CSVs")
    parser.add_argument("--start", required=True, help="Start date YYYY-MM-DD (inclusive)")
    parser.add_argument("--end", required=True, help="End date YYYY-MM-DD (inclusive)")
    parser.add_argument("--unit", choices=["mi", "km"], default="mi", help="Distance unit (default: mi)")
    parser.add_argument("--output", help="Write markdown to this file instead of stdout")
    args = parser.parse_args()

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    workouts_path = os.path.join(args.dir, "workouts.csv")
    if not os.path.exists(workouts_path):
        sys.exit(f"workouts.csv not found in {args.dir}")
    workouts = load_workouts(workouts_path, start, end)
    cycles_path = os.path.join(args.dir, "physiological_cycles.csv")
    cycles = load_cycles(cycles_path, start, end) if os.path.exists(cycles_path) else []

    markdown = build_markdown(workouts, cycles, start, end, args.unit)
    write_output(markdown, args.output, workouts, cycles)


if __name__ == "__main__":
    main()
