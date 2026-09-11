# PRD: Weekly Staff Totals

**Status:** Draft — describes a working internal build · **Owner:** TBD · **Last updated:** 2026-09-11

**Artifact:** `https://claude.ai/code/artifact/c047d572-6fd5-4db7-b724-e0b4315a5565` · **Source:** `staff-totals.html` in this repository

**Scope decisions (confirmed):**
- TownHall CBUS (Columbus) only — one house, one management team.
- Manager-facing only. No staff-facing view, no guest-facing view.
- Records what actually happened on a shift. It is not a scheduling tool and does not tell anyone when to work.
- Positions in scope: Bar, Barback, Barista, Host, Runner, Server, Trainees, plus any position a manager adds.

---

## Problem Statement

Shift-level staffing is recorded today in whatever the manager on duty reaches for: a legal pad by the host stand, a note in a phone, a text to the GM. The numbers exist, but they live in seven different places and rarely survive the week. That makes three ordinary questions hard to answer: how many people did we actually run on Friday PM, was Tuesday AM overstaffed for the business we did, and who was working the night a guest complaint came in.

The problem compounds across managers. An opening manager and a closing manager each hold half of the day, and nobody holds the week. By the time anyone wants to look back — a payroll question, a labor conversation, planning the next holiday weekend — the detail is gone and what remains is memory. Without AM and PM kept apart, a whole-day headcount also hides the shape of the day, which is the part worth managing.

## Goals

- Give the management team one place to record staffing for the week, so the record survives past the shift that produced it.
- Keep AM and PM separate on every day, so the split that drives labor decisions is visible rather than averaged away.
- Let several managers fill in the same week at the same time without overwriting each other, since a day is routinely split across two people.
- Make each day's numbers attributable, so a question about a shift has someone to ask.
- Put the reason next to the number. A staffing spike should be readable alongside the event that caused it.
- Take under two minutes to fill in at the end of a shift, or it will not get filled in.

## Non-Goals

- **Not a scheduling system.** It records what happened, not what is planned. Whether it should also hold the forecast is an open question, not a decision.
- **Not payroll, and not a time clock.** Hours entered here are a manager's summary figure, not a punch record, and nothing here should be used to pay anyone.
- **Not POS-integrated.** Sales, covers, and labor percentage are not pulled in. Every figure is typed by a manager.
- **Not an identity system.** The name on an entry is typed and stored on that manager's own device, not verified against an account.
- **Not multi-location.** Columbus only. A location picker is deferred until the single-house version earns its keep.
- **Not an analytics product.** It shows the current week's totals and split. Trend analysis across weeks is out of scope for this build.
- **Not a replacement for the daily manager log.** Narrative, incidents, and guest issues stay wherever they live today.

## Target Users

- **Primary: managers on duty.** Fill in their own shift at or near the end of it, usually on a phone or the office desktop, often while doing three other things.
- **Secondary: the GM.** Reads the week rather than fills it in. Wants the AM/PM split, the busiest day, and whether the week is complete, without chasing anyone.
- **Tertiary: ownership and above-store leadership.** Look at a finished week occasionally, usually with a specific question, and need it to be legible without a walkthrough.

## User Stories

- As a closing manager, I want to enter PM staffing for tonight without touching the AM numbers, so the opener's work stays intact.
- As an opening manager, I want to fill in AM on a phone, so I do not have to go to the office to do it.
- As either manager, I want to see the other's numbers appear as they type, so we do not duplicate or contradict each other.
- As a manager, I want to record that Friday was a home game or a 40-cover wine dinner, so next quarter nobody wonders why we ran six servers.
- As a GM, I want to see who entered each number and when, so a question about Thursday PM goes to the right person and I can tell what changed after the fact.
- As a GM, I want to know a week is finished and not still being filled in, so I can read it as final.
- As a GM, I want to see the AM versus PM split for the week, so I can tell whether the day is balanced the way I think it is.
- As a manager, I want to track hours or tips in the same grid when I need to, without a second tool.
- As a manager, I want a blank printed week to post in the office, so the sheet still works on a day when nobody wants to open a laptop.
- As a GM, I want to pull a week out as a spreadsheet, so I can bring it into a labor conversation.

## Requirements

### Must-Have (P0) — built in the current version

| Requirement | Acceptance Criteria |
|---|---|
| Weekly grid by position | Monday through Sunday, one row per position, with the seven named positions present by default and the position column fixed while the grid scrolls sideways. |
| AM / PM separation | Every day carries two independent entry columns. Nothing in the app collapses them into one number except explicit totals. |
| Shift view control | The grid can show both shifts, AM only, or PM only. Totals reflect the current view. |
| Position, shift, and week totals | Row totals per position, subtotals per day-shift, a week total, and an AM/PM split summary — all recalculating as numbers are typed. |
| Concurrent multi-manager entry | Two managers editing different days, shifts, or positions in the same week never overwrite one another. Each entry writes only the value it changed. |
| Live updates | A manager sees another manager's entries appear without reloading, with a brief highlight on what changed. |
| Per-entry attribution | Every cell records who entered it, what they entered, and when. The cell carries a marker and shows it on hover, and a week-level edit history lists each change with name, value, date, and time. The day header still shows who last touched that day. |
| Events per day | Each date has a free-text line for what was on the books that day, visible in the grid and carried into copy and CSV output. |
| Week notes | A single free-text field per week for anything that explains the numbers as a whole. |
| Week completion marker | A manager can mark the week complete, stamping their name; the state is visible in the header and reversible. |
| Track staff, hours, or tips | The same grid accepts headcount, hours, or tips, each stored separately, selected by a control. |
| Custom positions | A manager can add a position beyond the seven, and it appears for everyone on that week. |
| Works on a phone | Usable at roughly 400px wide, with the position column fixed and the grid scrolling horizontally. |
| Print a blank or filled week | The week prints legibly in landscape without app controls. |
| Export | A week can be copied as formatted text for messaging, or exported as CSV including the events and attribution rows. |
| Manager-only access | The sheet is private. Only people explicitly granted access can open it, and only those granted edit access can enter numbers. A viewer without edit rights sees the week read-only with every field locked. |
| Offline-tolerant fallback | Opened as a local file with no shared store, the app still works and saves to that browser. |

### Nice-to-Have (P1)

| Requirement | Notes |
|---|---|
| Week-over-week view | Compare this week's totals and AM/PM split against prior weeks without opening each week one at a time. |
| Verified identity | Replace the typed name with the signed-in account, so attribution is a fact rather than a convention. |
| Reminder to fill in | A nudge when a shift that has passed has no numbers, rather than relying on memory. |
| Copy last week's shape | Start a week pre-filled from a comparable prior week, so managers edit rather than type from zero. |
| Per-position notes | A short note on a single cell, for the times the day-level event line is the wrong place to explain a number. |
| Locked weeks | A completed week becomes read-only until an authorized manager reopens it. |

### Future Considerations (P2)

| Requirement | Notes |
|---|---|
| Multi-location | A location picker with separate records per house, and a roll-up view for above-store leadership. |
| Sales and covers alongside labor | Enter or import sales so the sheet can show labor against volume rather than headcount alone. |
| POS or scheduling integration | Pull actual hours or scheduled headcount automatically instead of typing them. |
| Forecast column | Record planned staffing next to actual, making the sheet a variance tool. |
| Longer retention and archive | A deliberate policy for how many weeks are kept live and where older weeks go. |

## Success Metrics

**Leading indicators**
- Share of shifts with numbers entered, by shift and by manager — the single measure that decides whether this is a tool or a well-intentioned artifact.
- Median time between the end of a shift and its entry. Same-day entry is the target; a multi-day lag means the workflow is wrong.
- Share of weeks marked complete by the following Monday.
- Share of days carrying an event note in weeks that had events.

**Lagging indicators**
- Number of staffing questions the GM can answer from the sheet without asking a manager.
- Whether AM/PM staffing decisions for recurring events (home games, holidays, private dinners) start referencing prior weeks.
- Manager-reported time to fill in a shift, against the two-minute goal.

*None of this is instrumented today. Adoption would have to be read off the sheet itself, by looking at which days are filled in and by whom.*

## Risks and Constraints

- **Adoption is the whole risk.** Nothing here is technically hard; the failure mode is a sheet that three managers use and two ignore, which makes the week's data worse than a blank page because it looks complete.
- **Typed names are a convention, not a control.** Anyone can type any name. It is enough for "who do I ask", and not enough for anything that has to hold up.
- **Manager-entered hours are estimates.** They must not be treated as payroll data, and the interface should not imply they can be.
- **Same-cell collisions still resolve last-writer-wins.** Different days, shifts, and positions are safe; two managers typing the same box at the same moment are not.
- **Access is a managed list, not a link.** The sheet is private. Managers are granted edit access individually; nobody else can open it. Onboarding a new manager to the sheet is therefore part of the rollout, and off-boarding one means removing their access the same day.
- **Data lives in the app's own store.** Retention, backup, and what happens to a week when the artifact is deleted are undefined and need an owner.

## Open Questions

**Resolved:**
- ~~One sheet per day or per week?~~ → Per week, filled in daily.
- ~~Whole-day totals or AM/PM?~~ → AM and PM kept separate on every day.
- ~~One metric or several?~~ → Staff, hours, and tips in the same grid, stored separately.
- ~~Who can edit?~~ → Any manager the sheet is shared with, with entries attributed by name.

**Still open:**
- **[Operations]** Who owns the sheet day to day, and what is the standing expectation — every manager fills in their own shift, or the closer fills in the whole day?
- **[Operations]** Is the headcount a snapshot at peak, or everyone who clocked in during the shift? The number is only comparable across weeks if this is settled and written down.
- **[Operations]** Where does AM end and PM begin? Managers need one definition, particularly for mid-shifts that straddle it.
- **[Leadership]** Does tips entry belong in the same tool as labor, given tips touch payroll and this is explicitly not a payroll system?
- **[Leadership]** Should a completed week lock, and who can reopen it?
- **[Product]** Is the next real need trend view across weeks, or sales and covers alongside labor? Those point at different products.
- **[IT/Compliance]** Retention and backup: how long do weeks stay live, who can export them, and where does an archive live?
