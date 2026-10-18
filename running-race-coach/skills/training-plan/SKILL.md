---
name: training-plan
description: Create personalized training plans for 5K, 10K, Half Marathon, and Marathon races, or heart-rate-zone based aerobic base building plans for runners with no race who want to run more and get fitter. Use when the user requests a training plan for any of these distances, wants to prepare for a race, wants to build their aerobic base or run more without overdoing it, or asks for a structured running program. This skill generates comprehensive markdown training plans that include race goals, training paces, phased progression, and week-by-week workout schedules.
---

# Training Plan Creator

## Overview

This skill creates personalized, evidence-based training plans for 5K, 10K, Half Marathon, and Marathon distances, plus open-ended **aerobic base building** plans for athletes without a race (see "Base-Building Plans" below).

**Save location**: Always save the plan to `~/running-coach/training-plan.md` (create the folder if needed) so it's available from every Claude Code session. Read `~/running-coach/profile.md` first if it exists - it may already answer most of the questions below. Plans are delivered as structured markdown documents with clear progression, appropriate training intensities, and race-specific preparation.

## Workflow

### 1. Gather Essential Information

Before creating a plan, collect these key details from the user:

**Required:**
- **Race distance**: 5K, 10K, Half Marathon, or Marathon
- **Race date**: When the race occurs
- **Current weekly mileage**: Average miles/km per week over the last 4 weeks
- **Available training days**: Number of days per week the athlete can train (typically 3-6)

**Recommended:**
- **Target race time**: Goal finish time or pace
- **Recent race results**: Previous race times to establish current fitness level
- **Training background**: Months/years of consistent running
- **Injury history**: Any recurring issues or limitations
- **Other constraints**: Schedule restrictions, terrain access, weather, life stress

**Handling missing information:**
- If target time is not provided, ask about recent race performance or typical training paces
- If training days are unclear, suggest 4-5 days as a reasonable starting point
- If race date creates a very short timeline (< 8 weeks for marathon), flag this concern

### Base-Building Plans (No Race)

If the athlete has no race and wants to run more, build their aerobic base, or improve pace without overdoing it, use this path instead of the race steps below. The plan is built around **heart rate zones**, not paces.

**Gather (one question at a time, skip anything already in `profile.md`):**
- Current running: days per week, typical run length (time or distance), longest recent run
- Days available per week
- Their HR zone ranges in bpm (from the WHOOP app or their device) or max HR. If unknown, use effort/talk test until they have them
- Any recent race or time trial result (optional - used only to show reference paces)
- Injury history and other training (e.g. lifting)

**Plan design:**
- **Length**: 8-12 week block, ending with an easier week; at the end, review and build the next block.
- **Intensity**: ~80-90% of running time in Zones 1-2. Easy runs and long runs are capped at the top of Zone 2 - slowing down, or walking briefly on hills, to stay in zone is expected and correct.
- **Quality**: First 3-4 weeks: no hard sessions, just easy running plus 4-6 relaxed **strides** (20 sec quick-but-relaxed, full recovery) 1-2x/week. After that, add at most one moderate session per week (e.g. short tempo/threshold segments in Zone 3-4, or hill strides). This builds pace without wrecking the aerobic focus.
- **Volume progression**: grow weekly running time by ~5-10% per week, 3 build weeks then 1 lighter week (~20-30% less). Grow the long run gradually to ~25-30% of weekly time. Add a run day before making individual runs much longer.
- **Write workouts in time + zone**, e.g. "Easy 40 min, Zone 2 (HR 130-145) + 6 strides". Distance-based interval rules below apply only to the occasional quality session.
- **Aerobic test** every 4 weeks (week 1, 4/5, 8/9...): after a 10 min easy warm-up, run 20-30 min on a flat route or treadmill holding a fixed HR near the top of Zone 2; record average pace. Same HR, faster pace over time = aerobic base improving. This is how pace improves without chasing it.
- **WHOOP recovery rule** (if they use WHOOP): green = as planned; yellow = do it, but keep it easy and cut 10-20% if tired; red = rest, walk, or very easy 20-30 min.
- If they lift or cross-train, place it on easy days or after easy runs, not before long runs or quality days.

**Output**: Use the template in step 7 but replace "Goal Summary" with the athlete's base-building goals, replace the "Training Paces" table with a **Heart Rate Zones** table (zone, bpm range, purpose, how it feels), add an **Aerobic Test Log** table (date, HR, pace, notes) for them to fill in, and use time-based weekly volume. Include every week. Optionally run `calculate_paces.py` from a recent race/time trial to show reference easy/threshold paces, but make clear HR leads.

Then skip to step 7 to write the file.

### 2. Calculate Training Paces

**IMPORTANT**: Use the `calculate_paces.py` script to generate training paces based on the target race time and distance. This ensures consistent and accurate pace calculations.

**How to use the pace calculator:**

The script is located at `scripts/calculate_paces.py` (relative to this skill's directory).

```bash
python3 scripts/calculate_paces.py --distance <km> --time <HH:MM:SS or MM:SS>
```

**Examples:**
```bash
# 5K in 20:00 (paces per mile by default)
python3 scripts/calculate_paces.py -d 5 -t 20:00

# 10K in 45:30
python3 scripts/calculate_paces.py -d 10 -t 45:30

# Half Marathon in 1:35:00
python3 scripts/calculate_paces.py -d 21.0975 -t 1:35:00

# Marathon in 3:30:00
python3 scripts/calculate_paces.py -d 42.195 -t 3:30:00

# For per-km paces instead of per-mile
python3 scripts/calculate_paces.py -d 10 -t 45:00 --per-km
```

**Output format:**
The script calculates six pace zones based on percentage adjustments from race pace:
- **Easy**: 120-130% of race pace (recovery and aerobic development)
- **Steady**: 110-115% of race pace (aerobic endurance, used primarily for marathon/HM)
- **Threshold**: 103-107% of race pace (comfortably hard, lactate threshold work)
- **VO₂max**: 95-98% of race pace (interval training, hard but repeatable)
- **Repetition**: 90-93% of race pace (short, fast reps for speed and economy)
- **Race**: 100% of race pace (target race effort)

**Workflow:**
1. Run `calculate_paces.py` with the user's target race distance and time
2. Copy the pace ranges from the script output into the training plan
3. Include these paces in the "Training Paces" table of the plan
4. Reference `coaches-guide.md` sections 3 and 6 for additional context on intensity definitions and how to apply these paces in workouts

**Note**: The script provides pace ranges in minute/mile format by default (use `--per-km` for minute/km format). Pace ranges account for terrain, weather conditions, and day-to-day variation. Always remind athletes that these are guidelines and should be adjusted based on how they feel.

### 3. Design the Phased Structure

Read `references/coaches-guide.md` for comprehensive guidance on plan design principles, phase structures, and distance-specific emphases.

**Key sections to reference:**
- Section 1: Core Principles
- Section 2: The "Shape" of a Good Plan (Phases A-E)
- Section 4: Weekly Architecture
- Section 6: Distance-Specific Emphases

**Determine phase durations** based on total plan length and race distance:
- **Foundation/Base**: Build aerobic capacity and durability
- **Build/Development**: Introduce and expand quality workouts
- **Specific/Peak**: Race-specific preparation and intensity
- **Taper**: Reduce fatigue while maintaining sharpness
- **Transition**: (Brief mention for post-race)

**Apply the plan length guidelines** from section 7:
- 8 weeks: Short build, assumes existing base
- 10-12 weeks: Standard for 5K/10K, workable for HM
- 12-16 weeks: Common for HM, minimum for experienced marathoners
- 16-20 weeks: Marathon standard

**Scale appropriately** using section 8 guidelines:
- Adjust volume, workout duration, and recovery based on ability level
- Apply the "minimum effective dose" principle for newer athletes
- Avoid common design errors from section 9

### 4. Structure the Weekly Microcycles

Build each week using the principles from section 4 of the coaches guide:

**Weekly template:**
- 1-2 quality sessions (threshold, intervals, or race-pace work)
- 1 long run
- Remaining days easy (with strides 1-3x/week)
- Optional: 1 strength training day

**Important workout structure rules:**
- ALL interval workouts must be **distance-based** (e.g., "5 x 1 mile", "4 x 800m", "3 x 1km")
- Never use time-based intervals (e.g., "5 x 4 min")
- Every interval workout follows: **warm-up → intervals → cool-down** structure
- Specify distances in miles, meters, or km (e.g., 1.5 miles, 400m, 2km)

**Progressive overload:**
- Increase volume gradually (typically 5-10% per week)
- Follow 3:1 or 2:1 build-to-recovery patterns
- Include planned deload weeks (~15-30% volume reduction)

**Distance-specific emphases** (from section 6):
- **5K**: Focus on VO₂max and speed-endurance
- **10K**: Emphasize threshold work with supporting speed
- **Half Marathon**: Threshold durability and long run progression
- **Marathon**: Volume, marathon pace durability, and fueling practice

### 5. Create Week-by-Week Schedule

For each week of the plan, specify:
- Week number and phase
- Total weekly mileage/volume
- Specific workouts for each training day:
  - Day of week (or Training Day 1, 2, etc.)
  - Workout type (Easy, Threshold, Intervals, Long Run, etc.)
  - Workout details (distance-based, pace, structure)
  - Purpose or focus of the session

**CRITICAL: All interval workouts MUST follow this structure:**
- **Warm-up** (distance + pace)
- **Intervals** (number x distance @ pace, with recovery distance/time)
- **Cool-down** (distance + pace)

**All intervals must be DISTANCE-BASED, not time-based.** Use miles, meters, or kilometers (e.g., "5 x 1 mile", "4 x 800m", "3 x 1km") rather than time-based intervals (e.g., "5 x 4 min").

**Workout description format examples:**
- "Easy 45 min + 6 strides"
- "Threshold: 1 mile easy warm-up, 4 x 1 mile @ T pace (0.25 mile jog recovery), 1 mile easy cool-down"
- "Long Run: 90 min easy"
- "Intervals: 1 mile easy warm-up, 5 x 1 mile @ I pace (0.25 mile jog recovery), 1 mile easy cool-down"
- "Marathon Pace: 1 mile easy warm-up, 2 x 2 miles @ MP (0.5 mile jog recovery), 1 mile easy cool-down"
- "Long Run with quality: 14 miles, last 3 miles @ steady pace (S)"

**Recovery within intervals:**
- Use distance-based recovery: "0.25 mile jog", "0.5 mile jog", "400m jog"
- Or time-based recovery: "2:00 jog", "90 sec jog" (but prefer distance-based)

### 6. Verify Weekly Mileage Using interval_calculator.py

**IMPORTANT**: Before finalizing the weekly mileage totals, use the `interval_calculator.py` script to accurately compute the distance for each interval workout.

**Why this is critical:**
- Manual calculations of workout distances are prone to error
- The script ensures accurate totals including warm-up, intervals, recovery, and cool-down
- This prevents understating or overstating weekly mileage (which can lead to overtraining or undertraining)

**How to use the calculator:**

For each interval workout in your plan, run the calculator with the workout parameters. The script is located at `scripts/interval_calculator.py` (relative to this skill's directory).

```bash
python3 scripts/interval_calculator.py \
  --warmup <distance> \
  --intervals <number> --interval-dist <distance> --interval-pace <pace> \
  --recovery <distance> \
  --cooldown <distance> \
  --easy-pace <pace>
```

**Example:** For "1 mile easy warm-up, 5 x 1 mile @ I pace (0.25 mile jog recovery), 1 mile easy cool-down":

```bash
python3 scripts/interval_calculator.py \
  --warmup 1mi \
  --intervals 5 --interval-dist 1mi --interval-pace 6:15 \
  --recovery 0.25mi \
  --cooldown 1mi \
  --easy-pace 8:00
```

Output:
```
TOTAL DISTANCE: 8.25 mi
TOTAL TIME:     1:01:15
```

**Workflow:**
1. Design your interval workouts following the standard structure
2. Run `interval_calculator.py` for each interval workout to get exact distance
3. Add up all training day distances (easy runs, intervals, long runs) for the week
4. Verify the weekly total matches your intended volume progression
5. Update the "**Total Volume**: X miles/km" for each week with accurate totals

**Note:** For easy runs and long runs without structured intervals, you can estimate distances directly. Only use the calculator for workouts with warm-up, intervals, recovery, and cool-down components. The calculator defaults to miles but can use kilometers with `--unit km`.

### 7. Generate the training-plan.md Output

Save to `~/running-coach/training-plan.md`. If a plan already exists there, ask before replacing it (offer to save the old one as `training-plan-<date>.md`). Create a comprehensive markdown document with the following structure:

```markdown
# Training Plan: [Race Distance] in [Number] Weeks

## Goal Summary
- **Race**: [Race name if provided]
- **Date**: [Race date]
- **Distance**: [5K / 10K / Half Marathon / Marathon]
- **Target Time**: [Goal time]
- **Target Pace**: [Goal pace per mile/km]
- **Training Days**: [X] days per week
- **Plan Duration**: [X] weeks

## Training Paces

Use these paces for workouts throughout the plan:

| Pace Type | Description | Pace Range | Effort (RPE) |
|-----------|-------------|------------|--------------|
| Easy (E) | Recovery and aerobic development | [pace range] | 2-4/10 |
| Steady (S) | Aerobic endurance (marathon/HM) | [pace range] | 4-5/10 |
| Threshold (T) | Comfortably hard, sustainable | [pace range] | 6-7/10 |
| Interval (I) | VO₂max, hard but repeatable | [pace range] | 8-9/10 |
| Repetition (R) | Short, fast reps | [pace range] | Fast/crisp |
| [Race] Pace | Target race effort | [pace range] | Race effort |

**Note**: Adjust paces for terrain, weather, and how you feel. These are guidelines.

## Plan Structure

### Phase 1: [Phase Name] (Weeks X-Y)
**Focus**: [Primary training focus for this phase]
**Volume**: [Typical weekly mileage range]
**Key Sessions**: [Types of workouts emphasized]

### Phase 2: [Phase Name] (Weeks X-Y)
**Focus**: [Primary training focus for this phase]
**Volume**: [Typical weekly mileage range]
**Key Sessions**: [Types of workouts emphasized]

[Continue for all phases...]

## Week-by-Week Training Schedule

### Week 1: [Phase Name]
**Total Volume**: [X] miles/km
**Focus**: [Key focus for this week]

- **Monday**: Rest or cross-training
- **Tuesday**: [Workout details]
- **Wednesday**: [Workout details]
- **Thursday**: [Workout details]
- **Friday**: Rest or easy 30 min
- **Saturday**: [Workout details]
- **Sunday**: [Long run details]

[Continue for all weeks...]

## Important Notes

- **Easy days should feel easy**: [Distance-specific guidance]
- **Fueling**: [If HM or Marathon, include fueling practice guidance]
- **Strength training**: [Brief recommendation]
- **Listen to your body**: [Injury prevention advice]
- **Adjust as needed**: [Flexibility guidance]

```

## Output Guidelines

**Tone**: Clear, supportive, practical. Avoid over-complication.

**Completeness**: Include every week of the plan with specific workouts. Don't abbreviate with "continue similar pattern."

**Flexibility reminders**: Acknowledge that plans may need adjustment. Include notes about when to modify (illness, excessive fatigue, life events).

**Safety**: Include appropriate warnings about injury prevention, gradual progression, and listening to the body.

## References

- **coaches-guide.md**: Comprehensive framework for training plan design covering principles, phases, intensities, weekly structure, progression models, distance-specific emphases, plan lengths, scaling across abilities, common errors, and a practical recipe for building plans. Reference this extensively when designing the plan structure and selecting workouts.

- **scripts/calculate_paces.py**: Command-line tool for calculating training paces based on target race time and distance. Located in the skill's scripts directory. Use this at the beginning of every training plan creation to generate accurate, consistent pace zones (Easy, Steady, Threshold, VO₂max, Repetition, Race). Defaults to minute/mile paces (use `--per-km` for minute/km). Run with `--help` flag for usage details.

- **scripts/interval_calculator.py**: Command-line tool for accurately computing workout distances. Located in the skill's scripts directory. Use this to calculate total distance for all interval workouts (warm-up + intervals + recovery + cool-down) to ensure accurate weekly mileage totals. Defaults to miles (use `--unit km` for kilometers). Run with `--help` flag for usage details.
