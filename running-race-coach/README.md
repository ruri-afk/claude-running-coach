# Claude Running Race Coach

An AI-powered running coach that provides personalized training plans, analyzes your workouts, and offers evidence-based coaching guidance. Built for [Claude Code](https://code.claude.com/) and [Claude Desktop](https://claude.ai/download) using the [Skills framework](https://code.claude.com/docs/skills). Packaged as a plugin for easy installation.

## Install in Claude Code

Run this inside Claude Code (any folder):

```
/plugin install running-coach --marketplace ruri-afk/claude-running-coach
```

On older Claude Code versions, use the two-step version instead:

```
/plugin marketplace add ruri-afk/claude-running-coach
/plugin install running-coach@ruri-running
```

Then restart Claude Code. The coach is now available in every session - just say **"running"** (or talk about a run) and it will pick up where you left off. Your plan, logs, and coaching notes are kept in `~/running-coach/` so every session sees the same history.

To get updates after changes are pushed to GitHub, run `/plugin marketplace update ruri-running`.

## Features

- **Training Plan Generation**: Create personalized 5K, 10K, Half Marathon, and Marathon training plans with scientifically-backed progression and pacing
- **Aerobic Base Building**: No race? Get a heart-rate-zone based plan to run more and get faster without leaving your easy zones
- **Flexible Data Input**: Works with multiple training data sources:
  - **WHOOP** (official WHOOP API, data export, or screenshots) - includes HR zones, strain, recovery, HRV
  - **Strava** (automatic sync via MCP server)
  - **Other platforms** (Garmin Connect, Apple Health, Polar Flow, etc.)
  - **Manual logs** (create markdown files directly)
  - **Conversational** (describe your training verbally)
- **Weekly Training Logs**: Generate detailed markdown summaries of your workouts, including lap-by-lap analysis for interval sessions
- **Weekly Coaching Sessions**: Compare actual training against planned workouts, analyze performance metrics, and receive personalized coaching feedback
- **Pace Calculation**: Scientific training pace zones calculated from your race goals
- **Evidence-Based Coaching**: Built on established training principles and progressive overload strategies

## Requirements

- [Claude Code](https://code.claude.com/) or [Claude Desktop](https://claude.ai/download)
- Python 3.8+ (for pace calculation and interval distance scripts)
- Training data from any source (Strava, Garmin, manual entry, etc.)
- **Optional**: Strava MCP server for automatic Strava sync

## Setup

### Using WHOOP

**Recommended: connect the WHOOP API (about 5 minutes, one time).** WHOOP lets any member create a free personal app for their own data:

1. Sign in at [developer-dashboard.whoop.com](https://developer-dashboard.whoop.com) with your WHOOP login and click **Create App**
2. Set the Redirect URL to `http://localhost:8765/callback` and pick the scopes `read:workout`, `read:recovery`, `read:cycles`, `read:sleep`, `read:profile`
3. Copy the Client ID and Client Secret
4. Ask Claude "connect my WHOOP" - it'll give you a one-line command to run in your terminal that saves your keys privately (in `~/running-coach/.whoop/`) and logs you in through your browser

After that, saying "sync my WHOOP" pulls your runs, HR zones, strain, recovery, resting HR, HRV and sleep automatically. Limits: personal apps work for up to 10 WHOOP accounts without approval, 100 requests/minute, and the API gives per-workout summaries rather than second-by-second heart rate.

**No setup option:** export your data from the WHOOP app (**App Settings → Data Export**), unzip the file WHOOP emails you, and tell Claude where the folder is. You can also paste screenshots or just describe your runs.

Tell the coach your WHOOP heart rate zone ranges (in bpm) on your first session so it can check your easy runs stay in Zone 2.

### 1. (Optional) Configure Strava MCP Server

If you want automatic Strava sync, add the Strava MCP server to your Claude Code configuration (`~/.claude/config.json`):

```json
{
  "mcpServers": {
    "strava": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-strava"]
    }
  }
}
```

**Note**: This step is optional. You can use Claude Coach without Strava by:
- Manually creating training log files in the `~/running-coach/training-log/` folder
- Providing data from other platforms (Garmin, Apple Health, etc.)
- Describing your training conversationally

### 2. (Optional) Connect Your Strava Account

If using Strava sync, Claude will prompt you to authenticate with Strava when you first use the strava-sync skill. Follow the authorization flow in your browser.

## Usage

### Generate a Training Plan

Ask Claude to create a training plan:

```
Create a 12-week half marathon training plan. My race is on March 15th,
I'm currently running 25 miles per week, and my goal is to finish in 1:35:00.
```

Claude will use the `training-plan` skill to generate a comprehensive markdown training plan with:
- Calculated training pace zones
- Phase-by-phase progression
- Week-by-week workout schedules
- Distance-based interval workouts
- Tapering strategy

### Sync Your Training Data

You have multiple options for getting your training data into Claude Coach:

#### Option 1: Sync from Strava (Automatic)

Download and summarize your recent Strava activities:

```
Sync my last week of training from Strava
```

The `strava-sync` skill will:
- Fetch your recent activities from Strava
- Generate a markdown summary with weekly totals
- Include detailed lap analysis for workout runs
- Save to the `training-log/` directory

#### Option 2: Use Other Platforms

Export data from Garmin Connect, Apple Health, Polar Flow, or other platforms and share it with Claude. Claude will help format it into training log files.

```
I have my training data from Garmin Connect - can you help me create a training log?
```

#### Option 3: Manual Entry

Create training log files manually in the `training-log/` folder using markdown format (see the strava-sync skill output for format examples).

#### Option 4: Conversational

Simply describe your training verbally:

```
This week I ran 5 miles easy on Monday at 8:00 pace, did a threshold workout
on Wednesday (1 mile warmup, 3x1 mile at 6:30 with 400m recovery, 1 mile cooldown),
and did a 10-mile long run on Saturday.
```

### Get Weekly Coaching

After getting your training data (via any method), request a coaching session:

```
Coach me on this week
```

Claude will ask where you'd like to get your training data from (Strava, manual log, other platform, or conversational).

The `running-coach` skill will:
- Compare your actual training against the planned workouts
- Analyze pacing, heart rate, and workout execution
- Assess your progress toward your race goal
- Provide actionable recommendations and adjustments
- Generate coaching notes saved to `coaching-log/`

### Ask Training Questions

Get evidence-based coaching advice:

```
How should I pace my long runs during marathon training?
What should my heart rate zones be for easy runs?
Should I do my threshold workout if my legs are tired?
```

## What You Get

When you use Claude Running Race Coach, you'll receive:

- **Training Plans**: Comprehensive markdown plans with weekly schedules, calculated pace zones, and periodized progression
- **Training Logs**: Detailed workout summaries saved in `training-log/` with metrics and lap analysis
- **Coaching Notes**: Personalized feedback and recommendations saved in `coaching-log/`
- **Evidence-Based Guidance**: All coaching advice is grounded in established training principles

## Limitations

- **Not a substitute for professional coaching**: Always consult qualified coaches and medical professionals for personalized advice
- **Individual variability**: Training plans may not account for individual physiology, injury history, life circumstances, or recovery capacity
- **Data quality**: Coaching analysis depends on accurate heart rate, pace, and GPS data from your activities
- **Platform flexibility**: While Strava integration is seamless, other platforms require manual data entry

## Support & Feedback

Have questions or suggestions? Feel free to:
- Open issues on [GitHub](https://github.com/ColinEberhardt/claude-running-coach)
- Share your training success stories
- Suggest improvements to training plans or coaching feedback

For technical details and development information, see the [main project README](../README.md).

## License

MIT License - see [LICENSE](../LICENSE) for details.

Always consult with qualified professionals for personalized training advice.

## Acknowledgments

- Built with [Claude Code](https://code.claude.com/) by Anthropic
- Training principles based on established coaching literature and periodization frameworks
- Powered by [Strava API](https://developers.strava.com/) via the [MCP Strava server](https://github.com/modelcontextprotocol/servers/tree/main/src/strava)
- Inspired by evidence-based coaching from Jack Daniels, Pete Pfitzinger, and other endurance training experts

---

**Disclaimer**: Always listen to your body, consult with medical professionals before starting a new training program, and adjust plans based on your individual needs and circumstances.
