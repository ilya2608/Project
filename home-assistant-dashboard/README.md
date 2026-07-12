# Home Assistant Dashboard — Lights & Security

A room-by-room Lovelace dashboard built for the Home Assistant companion app (mobile-friendly "Sections" layout), focused on **lights** and **security** (motion, presence, covers), with temperature sensors as secondary content. Media players, the vacuum, switches, and the to-do list are kept reachable in a single deprioritized **Other** tab.

## Tabs

| Tab | Contents |
|---|---|
| Home | Presence (iPhone), Big Blind, Sunscreen — house-wide security at a glance |
| Living Room | 5 lights + 6 scenes |
| Bedroom | Light, scenes, Motion Sensor - AC4 (motion + temperature) |
| Master Bedroom | 4 lights, 1 scene |
| Kitchen | Light |
| Dining Room | Light, Small Blind |
| Bathroom | Light |
| Hallway | Light, Hue motion sensor (motion + temperature), 2 scenes |
| Pantry | Light |
| Garage | 3D printer heatbed/nozzle temperature sensors |
| Other | Media players, vacuum, switches, shopping list (compact, low-priority) |

Devices that were reporting `unavailable` at discovery time (some lights, Master Bedroom TV, one bedroom speaker) are included on purpose — they'll activate automatically once back online.

## How to import

1. In Home Assistant: **Settings → Dashboards → + Add Dashboard → New dashboard from scratch**.
2. Open it, tap the **⋮** menu → **Edit Dashboard** → **⋮** again → **Edit in YAML**.
3. Delete the placeholder and paste the contents of [`dashboard.yaml`](./dashboard.yaml).
4. Save.

## Known caveat: entity IDs are best-effort

The Home Assistant MCP connector used to discover your devices only exposes friendly names, areas, and state — not raw `entity_id`s. The IDs in `dashboard.yaml` are slugified from device names using Home Assistant's standard naming convention (e.g. "Bathroom Light" → `light.bathroom_light`), which is usually correct but not guaranteed.

If a tile shows **"Entity not available"**: open that card in the visual editor and re-pick the correct entity from the autocomplete dropdown — a few seconds per fix. You'll likely need to do this for a handful of entities, especially ones with less predictable naming (e.g. `prusa-mk4` sensors, duplicated devices).

## Corrections applied from your review

- Living Room TV and Soundbar (which appeared twice in the raw discovery data) are each included **once**.
- Small Blind, Big Blind, and Sunscreen are three **independent** covers — no grouped card.
- Motion Sensor - AC4 is placed under **Bedroom** (its real location, despite no area tag in the raw data).
