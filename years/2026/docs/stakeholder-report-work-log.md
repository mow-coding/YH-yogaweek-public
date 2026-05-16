# Stakeholder Report Work Log

## 2026-05-16 - Integrated stakeholder report draft

### Request

Create one integrated report that can speak clearly to nine stakeholder personas:

- 2026 participating Yeonhui yoga studios
- 2026 official partners such as UrbanPlay and Obud
- 2026 official sponsors such as F&B and goods sponsors
- 2026 consumer participants
- future participating Yeonhui yoga studios
- future official partners
- future official sponsors
- future consumer participants
- future public institutions

The user clarified that the output should not be nine separate reports. It should be one report with distinct messages for each persona.

### Methodology Research

Before writing the report, the report framing was checked against external evaluation and documentation references:

- CDC Program Evaluation Framework: stakeholder engagement, program description, evaluation question focus, credible evidence, supported conclusions, and action on findings.
- GOV.UK major event legacy and impact toolkit: event objectives, theory of change, stakeholder-relevant KPIs, and before/during/after data collection.
- eventIMPACTS impact types: attendance, economic, social, environmental, and media impact categories.
- Google Cloud and Snowflake data lineage guidance: source, transformation, dependency, and governance records.

### Local Evidence Rechecked

The report uses already-generated local public outputs, including:

- ON STUDIO public reservation and cancellation data.
- Obud review deidentified table after Google Vision OCR and Gemini structured validation.
- class and studio Hype metrics.
- class and studio Capacity + Hype metrics.
- GIS location, distance, and transition-feasibility tables.
- public external-web Viral metrics.
- F&B partner and sponsor asset inventory outputs.

Key figures rechecked before writing:

- ON STUDIO reservations: 1,611 rows.
- ON STUDIO cancellations: 1,048 rows.
- ON STUDIO classes: 125 rows.
- Obud reviews: 96 rows.
- Review rows needing public review after validation: 0.
- Event locations: 14 nodes.
- Confirmed external-web mentions: 58.
- F&B partner brands: 16.
- Sponsor asset inventory count: 174 assets.
- Capacity + Hype class groups: 86.
- Expand/repeat candidate class groups: 32.

### Writing Decisions

- The report uses `Hype` as a response profile, not as a total ranking.
- The report avoids claiming direct economic impact because actual F&B redemption, settlement, and participant spending records are not available.
- Public-sector interpretation is framed as a private community-led pilot with public relevance, not as a proven public policy outcome.
- Participant review data is described only in deidentified and aggregate terms.
- GIS movement is described as schedule-based feasibility, not real participant tracking.

### Output

- `years/2026/reports/stakeholders/yeonhui_yoga_week_integrated_stakeholder_report.md`

### Follow-up

- Review the integrated report for tone and stakeholder fit.
- If this report becomes an external deliverable, produce a PDF/DOCX version after the user confirms wording and public/private disclosure level.
- If the repository is ever made public, run the public-release audit again before changing visibility.

## 2026-05-16 - Final rewriter and public repo split

### Request

The user asked to rewrite the stakeholder report from the ground up after the full reanalysis, not to patch scattered paragraphs. The user also asked to prepare a separate public repository and to clearly state:

- responsible/admin account: Bigblue Yoga / 유동환 / `bigblue.yoga@gmail.com`
- analyst: 김성균 / `mow.coding@gmail.com`
- sensitive information was masked before public sharing

### Implementation

- Added `scripts/build_integrated_stakeholder_report.py`.
- Regenerated `reports/stakeholders/yeonhui_yoga_week_integrated_stakeholder_report.md` from current public CSV outputs.
- Updated outdated Gemini validation model counts from 24/72 to the final 29/67 split where they remained in methodology documents.
- Added `scripts/prepare_public_repository.py`.
- Created sanitized public staging folder at `C:\Users\mylifeisbusy\Documents\dev\YH-yogaweek-public`.
- Created and pushed the separate public GitHub repository: <https://github.com/mow-coding/YH-yogaweek-public>.

### Public Release Checks

- Public package files: 137.
- Forbidden pattern findings: 0.
- raw/interim/private/database path findings: 0.
- Allowed emails in the public package are limited to the declared responsibility/source accounts:
  - `bigblue.yoga@gmail.com`
  - `mow.coding@gmail.com`
  - `rightnow.yogi@gmail.com`

### Output

- `years/2026/reports/stakeholders/yeonhui_yoga_week_integrated_stakeholder_report.md`
- `years/2026/reports/public_release/public_repository_audit.md`
- `years/2026/reports/public_release/public_repository_manifest.csv`
- public repo commit: `8970cf2 Update public package audit and current status`

## 2026-05-16 - Public site readability and map-based space-time cube correction

### Request

The user said the original `시간-공간 큐브` was too difficult to understand because it was not shown on a map. The user also asked that public GitHub Pages output should read like a polished public website, not like raw Markdown in a browser.

### Method Reference Check

Before changing the visualization, the GIS visualization method was checked against:

- Esri/ArcGIS space-time cube references, which describe the method as x/y map position plus time on the z axis.
- deck.gl ColumnLayer and CARTO + deck.gl references, which show a common web mapping pattern for vertical columns on top of maps.
- existing time geography references already recorded in `docs/gis-method-references.md`.

### Implementation

- Reworked `scripts/build_gis_deep_report.py` so `yeonhui_yoga_week_space_time_cube.html` is a map-based 2.5D time tower visualization.
- Each venue keeps its real map position.
- Each venue gets a vertical time axis: bottom means early event period, top means late event period.
- Each dot on the axis is one class session.
- Dot size represents reservation scale.
- Dot color represents review Hype signal.
- Fixed a Folium popup reuse bug where the same popup object was attached to both the tower marker and the venue base marker. That bug stopped the JavaScript before the tower layer rendered.
- Reworked `scripts/prepare_public_repository.py` so GitHub Pages has a clearer report hub, improved report typography, safer table wrapping, and a more explicit map link section.

### Verification

- `python -m py_compile years\2026\scripts\build_gis_deep_report.py years\2026\scripts\prepare_public_repository.py` passed.
- `python years\2026\scripts\build_gis_deep_report.py` regenerated GIS deep report and three HTML maps.
- Playwright screenshot check confirmed the map-based time towers render on top of the Leaflet map.
- Public package generation reported forbidden findings 0, raw/interim/private/database path findings 0, and Markdown table structure findings 0.

## 2026-05-17 - Public website refinement and core GIS map consolidation

### Request

The user pointed out that the public stakeholder report repeated the title at the top and still felt too much like raw Markdown. The user also noted that, for public readers, `지도 위 시간-공간 큐브` and `동선 가능성 지도` are the two essential GIS views. The older `GIS 기본 지도` and `시간 흐름 지도` should be treated as supporting material, not as primary navigation.

### Implementation

- Updated `scripts/prepare_public_repository.py` so generated HTML reports remove the duplicate first Markdown `# title` when the wrapper already provides the same title.
- Wrapped the opening report metadata in a cleaner two-column cover block.
- Adjusted report heading scale and Korean line breaking so the title does not split awkwardly.
- Reworked the public landing page map section around two primary map cards:
  - `지도 위 시간-공간 큐브`
  - `동선 가능성 지도`
- Moved `GIS 기본 지도` and `시간 흐름 지도` into a collapsed supporting-map section.
- Added a time filter slider directly inside `지도 위 시간-공간 큐브`, so the cube now also covers the main use case of the separate time-flow map.
- Polished Leaflet map panels, legends, layer controls, and popups for a more consistent public-report style.

### Verification

- Python compile checks passed for the public repository and GIS scripts.
- GIS deep report and public repository staging were regenerated.
- Playwright screenshot checks were run for:
  - public landing page
  - integrated stakeholder report HTML
  - map-based space-time cube
- Browser DOM check confirmed the cube slider works:
  - before moving slider: 261/261 class dots visible
  - at 50% slider: 122/261 class dots visible, 139 future dots dimmed

## 2026-05-17 - Public website visual polish pass

### Request

The user said the public website still felt visually awkward even though the report and GIS structure were now correct. The user specifically asked to use frontend/UI skills and make the public-facing site more polished.

### Frontend Direction

- Visual thesis: a warm branded report hub using the official orange yoga-week banner as the main visual anchor, with quiet editorial report sections below it.
- Content plan: hero and primary actions first, compact evidence summary second, then the two required report links and the two primary GIS map links.
- Interaction thesis: restrained entrance motion on the hero, clear hover affordances on report/map links, and a cleaner map panel treatment without adding extra decorative clutter.

### Implementation

- Reworked `scripts/prepare_public_repository.py` so the public landing page reads like a designed report hub rather than a document index.
- Used the official banner image as a full-bleed hero background while preserving the right-side festival mark by anchoring the image to the right.
- Added a compact evidence summary strip: non-identifying reservation rows, OCR review count, GIS location nodes, and primary map count.
- Reworked the report and map sections with clearer hierarchy, larger spacing, stronger call-to-action buttons, and a less cluttered navigation bar.
- Improved generated HTML report styling with a cleaner report header, brand mark, safer table wrapping, stronger section hierarchy, and a more official report-shell layout.
- Further polished the core GIS map panels in `scripts/build_gis_deep_report.py` with clearer panel borders, stronger title treatment, improved layer-control surfaces, and better hover feedback for the space-time cube dots.

### Verification

- `python -m py_compile years\2026\scripts\prepare_public_repository.py years\2026\scripts\build_gis_deep_report.py` passed.
- GIS deep HTML outputs were regenerated.
- Public repository staging was regenerated with forbidden findings 0, raw/interim/private/database path findings 0, and Markdown table structure findings 0.
- Local public text scan found no forbidden account, secret, phone-number, or common mojibake markers.
- Playwright screenshot checks were run for:
  - public landing page, desktop
  - public landing page, mobile
  - integrated stakeholder report HTML
  - map-based space-time cube
  - transition feasibility map

## 2026-05-17 - Studio key normalization correction and Korean copy pass

### Request

The user noticed that the public integrated report showed `대저택프라이빗` and `대저택 프라이빗` as separate rows in the capacity table. The user also said the public report and UI copy felt slightly AI-translated and asked for more natural Korean.

### Investigation

- Confirmed that the issue was real, not just a display typo.
- GIS location outputs were already normalized through `studio_locations_public.csv`.
- Hype, capacity, and settlement aggregates still had a missing alias path for:
  - `대저택 프라이빗 -> 대저택프라이빗`
  - `숨 명상센터 -> 숨명상센터`

### Implementation

- Updated the central studio normalization helper in `scripts/review_processing_utils.py`.
- Added the same normalization to `scripts/build_capacity_hype_analysis.py`.
- Made `scripts/build_obud_settlement_analysis.py` reuse the canonical studio-key helper.
- Regenerated Hype, capacity, settlement, GIS, DuckDB, and the integrated stakeholder report.
- Reworded visible public report and landing-page copy from mixed Korean/English operational terms toward more natural Korean, while keeping technical terms where they are part of the analysis axis.

### Verification

- Public aggregate files now have 0 `studio_key` rows equal to `대저택 프라이빗` or `숨 명상센터`.
- `studio_hype_metrics.csv` now has 12 rows.
- `studio_capacity_hype_metrics.csv` now has 12 rows.
- `obud_settlement_estimate_by_studio_month.csv` now has 19 rows.
- The integrated stakeholder report capacity table shows one `대저택프라이빗` row: 98 reservations, 6 reviews, 100.0% weighted fill rate, 11 sold-out sessions out of 11 sessions.
