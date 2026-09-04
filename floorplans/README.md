# Ball State game day floor plan — table sections

`townhall-floorplan-ball-state-game-day-sections.json` is the exported game day
plan with three service sections layered on top of it. The Café side is
deliberately left out: it runs off its own register/barista team, so C1–C10 and
C20–C21 carry no section.

## How the sections are stored

The edit is purely additive, so the file still loads anywhere the original did:

- a top-level `sections` array — `id`, `name`, `color`, `zone`, and the table
  numbers in that section;
- a `"section": "<id>"` key on each table item in the Dining Room and Patio
  zones.

Nothing else in the export was touched — geometry, walls, fixtures, zones, and
the staffing grid are byte-for-byte the original.

## The sections

| Section | Where | Tables | Est. covers |
|---|---|---|---|
| 1 — Bar Side | Dining Room, bar side + east wall two-tops | 31, 32, 33, 34, 35, 41, 42, 43, 44, 45 | ~40 |
| 2 — Dining / Entry | Dining Room, entry side through the center | 11, 12, 13, 14, 15, 16, 21, 22, 23, 24, 25, 26 | ~54 |
| 3 — Patio | Patio, wrapping the south wall to the patio bar | 51, 52, 53, 61–68, 71, 72, 73, 81–85 | ~76 |

Each section is one contiguous walk. Section 1 works off the main bar, Section 2
off the entry and host stand, Section 3 off the patio bar.

Cover counts are estimated from table footprints in the plan (four tops for the
round and square tables, eight for the 15/21/31 communals, two for the small
rail and wall tables) — sanity-check them against how you actually set the room.

## Game day note

Section 3 is roughly 40% of the seats outside the Café, which is more than one
server should carry on a Ball State game day. The clean split is at the door
line around x=1150:

- **3A (patio west):** 51, 52, 53, 61, 62, 63, 64, 65, 66 — ~36 covers
- **3B (patio east, off the patio bar):** 67, 68, 71, 72, 73, 81, 82, 83, 84, 85 — ~40 covers

That gives four near-even sections if the game day count justifies the extra
body; leave it as one section for slower shifts.
