# GeoKviz — brief for extending the app (read me first)

This file is written so a fresh AI chat can pick up and extend this project **without any extra explanation from the user**. Download the repo, drop it into a new chat, and say something like *"Read FUTURE_WORK_PROMPT.md and add …"*. Everything you need to know is here.

---

## 1. What this is

A single self-contained GeoGuessr-style **geography study app**. It shows the name of a place, the user clicks where they think it is on a blank world map, and it scores how close they were (distance → points). It tracks streaks, has a "smart practice" mode, optional progress saving, statistics, and PC↔phone sync.

- **The entire app is ONE file: `index.html`.** No build step, no dependencies to install. It loads Leaflet + map tiles from CDNs at runtime (so it needs internet to show the map). Just open it in a browser.
- UI language: **Serbian, Latin script, ekavian.** Keep all user-facing text in that style and plain (no technical jargon).
- When chatting with the user, **reply in English** even though the app is Serbian.
- The repo also contains `tools/` — helper Python scripts used to generate geometry (see §6).

> Local dev note: the user's working copy lives at `C:\Users\andra\claude\geo-quiz.html`; in the GitHub repo the same file is published as `index.html`. They are the same file.

---

## 2. The data model (this is the heart of it)

Everything is keyed by a **feature id = its index in the `DATA` array**. Three parallel structures share that id:

### `DATA` — one row per place
```js
const DATA = [
  ["Srpsko ime","English name", lat, lng, "regija", "tip"],
  ...
];
```
- `lat,lng` decimal degrees (WGS84). For an area/river this is a *representative point* used as a fallback when there's no shape.
- `"regija"` is a region code (see §3). `"tip"` is a type key (see `TYPES`).
- **The row's position in the array IS its id.** Index 0 = first row, etc. **Never reorder or delete rows** — it would shift every id and break `DESC`, `GEO`, saved progress, and sync. Only **append**.

### `DESC` — descriptions, keyed by id
```js
const DESC = { 0:"...", 1:"...", 188:"...", ... };
```
One short Serbian (Latin, ekavian) sentence per id, shown in the info card after a guess.

### `GEO` — shapes, keyed by id (in its own `<script>` block, defined BEFORE the main script)
```js
const GEO = { 0:{"m":"poly","c":[[[lat,lng],...]]}, 12:{"m":"line","c":[[[lat,lng],...],...]}, ... };
```
- `m:"poly"` → polygon(s). `c` is an array of rings; each ring is an array of `[lat,lng]` points. Click inside the polygon = max points; outside = scored from nearest edge.
- `m:"line"` → polyline(s) (rivers, mountain ranges). `c` is an array of paths; each path an array of `[lat,lng]`. Scored from the nearest point on the line.
- **Coordinates are `[lat, lng]`** here (note: GeoJSON is the opposite, `[lng,lat]` — convert when importing).
- Not every id needs a `GEO` entry. Without one, scoring falls back to the point in `DATA` (fine for peaks, capitals, single points).

### `TYPES` — category + scoring scale per type
```js
const TYPES = { island:{cat:"Ostrva",scale:250}, river:{cat:"Reke",scale:500}, ... };
```
`cat` is the human category label (the chips in the menu group features by `cat`). `scale` controls score falloff (bigger = more forgiving). There's also a user-facing **sensitivity slider** that multiplies this.

### `FEATURES` — the runtime objects (built automatically)
```js
const FEATURES = DATA.map((d,i)=>({ id:i, sr, en, lat, lng, region, type, cat, scale, desc:DESC[i] }));
```
Reverse lookups use `FEATURES[id]`, so ids must stay dense (0,1,2,… no gaps). Appending keeps them dense.

### `GREF` — geometry sharing (for duplicates)
```js
const GREF = { 217:78, ... }; // feature 217 reuses the shape of feature 78
```
If two features are the same place (e.g. Florida appears in both the main set and the Keva set), give the second one a `GREF` entry pointing at the first one's id instead of duplicating the polygon. `preprocessGeo()` copies the shape over at startup.

---

## 3. Regions, and the "separate menu per person" pattern (IMPORTANT)

A **region code** does two jobs: it groups features, and it decides **which menu they appear in**.

- `REGIONS = {sa, na, au}` are the **main menu** regions (South America, North America, Australia/Oceania). Only codes listed in `REGIONS` get a chip in the main menu.
- `regionName(r)` returns the display label for any region, including ones not in the main menu.

### The "Keva" set — a second, themed menu limited to its own features
The user built a **separate orange/fiery "Keva" menu** for a friend with a different curriculum. The whole mechanism is the template for adding more people:

- All Keva features use region code **`"kv"`** (so they are invisible in the main menu).
- There's a second setup screen `#kevaSetup` (a clone of `#setup`) with its own orange theme via CSS variable overrides scoped to `#kevaSetup`.
- A tab row (`.tabs`) on each menu switches between **🌍 Glavni** and **🔥 Keva**.
- `state.mode` is `'main'` or `'keva'`. `openMenu()` opens the right screen for the current mode.
- Keva has its own category chips (`renderKeva`), its own option inputs (ids suffixed `K`, e.g. `optEnK`), and start/adaptive functions (`kevaStart`, `kevaAdaptive`) that set `state.selRegions = new Set(['kv'])` and reuse the shared engine (`startGame`, `adaptivePool`, `nextQuestion`).
- The engine is **state-driven**: `startGame()` reads `state`, not the DOM. That's why the same engine serves both menus.

### To add ANOTHER person's set (e.g. "Mika"), copy the Keva pattern:
1. Pick a new region code, e.g. `"mk"`. Add a label in `regionName()` (or a `KV_LABEL`-style constant).
2. Append their `DATA` rows with region `"mk"`, their `DESC`, and `GEO`/`GREF` as needed (see §5–6).
3. Duplicate the `#kevaSetup` HTML block → `#mikaSetup`, give it new element ids (e.g. suffix `M`) and a new theme color (override the CSS vars in a `#mikaSetup{ --accent:…; … }` rule).
4. Add a tab button for it on the menus and extend `state.mode`.
5. Duplicate `renderKeva`/`kevaStart`/`kevaAdaptive`/`openKeva` as `renderMika`/etc., swapping ids and the region code.
6. Wire the buttons at the bottom of the script.

That's the whole pattern. Each person gets an isolated set that never bleeds into the others, because region codes gate menu visibility.

---

## 4. Saving, stats, sync (so you don't break them)

- Progress is stored in **`localStorage`** (`geoquizSave_v1` + `geoquizSavePref`), gated by the "💾 Čuvaj napredak" toggle. Autosaves after every guess/skip/timeout and each new question; per-feature stats and the in-progress session are keyed by feature id.
- Because everything is id-keyed, **appending features is safe** for existing saves. **Reordering/deleting is not** (it remaps ids).
- localStorage is per-origin, so the local file and the published site keep separate saves — that's why there's an export/import + QR/link **sync** feature.

---

## 5. Adding features to an EXISTING set (e.g. expanding a curriculum)

1. **Append** rows to `DATA` with the right region code. Don't touch existing rows.
2. Add a matching `DESC` entry for each new id (Serbian, Latin, ekavian, one sentence).
3. Add geometry if the feature is an area/river (see §6); or rely on the point for single-point features; or add a `GREF` if it duplicates an existing shape.
4. **Verify coordinates** (the user cares about this — cross-check lat/lng against a reliable source like Wikipedia/GeoHack).
5. Run the validation in §7.

---

## 6. Generating geometry (real shapes)

Real shapes come from **Natural Earth** data. The reusable scripts are in `tools/`:

- `tools/_keva_geom.py` — the worked example: extracts **river polylines** from `ne_10m_rivers_lake_centerlines.geojson` by name, and **island polygons** from `ne_10m_land.geojson` by point-in-polygon (pick the smallest land polygon that contains the island's centre), then Douglas-Peucker–simplifies and emits `GEO`-format JS (`[lat,lng]`, rounded). Adjust the id→name / id→centre tables and rerun.
- `tools/_keva_assemble.py` — inserts generated `DATA`/`DESC`/`GEO`/`GREF` blocks into the HTML at the right anchors.
- `tools/_balance.py` — bracket-balance sanity check per `<script>` block.

Natural Earth GeoJSON is fetched from `https://cdn.jsdelivr.net/gh/nvkelso/natural-earth-vector@v5.1.2/geojson/<file>.geojson`. Use `10m` for detail, `50m` for smaller files. (The large `.geojson` files are **not** committed — re-download them as needed.)

**Peninsulas** rarely have a clean standalone polygon (they're part of a bigger landmass), so the app uses **hand-authored approximate polygons** — 8–14 `[lat,lng]` points tracing the coast is enough; the scorer only needs a recognizable blob over the right area.

Conversion reminders: GeoJSON is `[lng,lat]`; `GEO` wants `[lat,lng]`. Features near the antimeridian (±180°, e.g. Fiji) are handled by `preprocessGeo()` — keep using `[lat,lng]` and let it wrap.

---

## 7. Validate before shipping

1. **Counts:** `DATA` rows == `DESC` entries == highest id + 1, and there are no gaps. Every region code used in `DATA` is either in `REGIONS` or has a `regionName()` label and a menu.
2. **GEO:** valid JS object; ids referenced exist; coords are `[lat,lng]`.
3. **Syntax/balance:** run `tools/_balance.py` (note: the main block historically reports a harmless +1/+1 from a regex in the original code — compare the delta against the previous version, don't chase the absolute number).
4. **Open `index.html` in a browser** and actually click through: each menu opens, chips filter, a guess scores, the shape highlights, the info card shows the right name/description, stats update.

---

## 8. Publishing to GitHub

- Repo: **`Lhespov/GeoKviz`**, published file: **`index.html`** (GitHub Pages at `https://lhespov.github.io/GeoKviz/`).
- Push **only** the app (`index.html`), this prompt, and `tools/`. **Never** publish personal files (WhatsApp images, KiCad projects, local backups, the large `_ne/*.geojson` data, transcripts).
- Pushing is outward-facing — confirm with the user before each push.

---

## 9. Working style the user expects

- **Delegate grunt work to a cheaper model (Sonnet)**: bulk data transcription, coordinate lookups, mechanical edits, validation runs. Keep the expensive model for planning, integration, and review. Give each subagent a precise, self-contained spec.
- Keep user-facing Serbian text plain and jargon-free.
- Verify coordinates; don't guess silently.
