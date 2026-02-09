# PyCalendar Styles

This directory hosts all CSS building blocks for the generated interface.

## Layering

| Layer | Location | Purpose |
| --- | --- | --- |
| Core | `core/00-05-*.css` | Design tokens, reset, base typography, layout scaffolding, effects and decorations |
| Components | `components/*.css` | Reusable widgets (filters, match cards, tabs, modals, etc.) |
| Views | `views/*.css` | View-level layouts/overrides (agenda, pools, penalties) |
| Themes | `themes/*.css` | Palette overrides and skins loaded last |

## Manifest-driven order

The generator reads `manifest.json` to determine the order in which styles are concatenated. Each
section declares either explicit files or globbing patterns:

```json
[
  {
    "name": "core",
    "files": [
      "core/00-tokens.css",
      "core/01-reset.css"
    ]
  },
  {
    "name": "components",
    "files": [
      "components/*.css"
    ]
  }
]
```

- Entries are relative to `assets/styles/`
- Wildcards (`*`, `?`, `[a-z]`) are supported
- Duplicates are deduplicated automatically in generation order
- The manifest is mandatory. The generator aborts if the file is missing or produces an empty list

To add a new stylesheet:

1. Create the file under the appropriate layer (core/components/views/themes)
2. Reference it inside the manifest (explicit entry or covered by an existing glob)
3. Regenerate the interface (`generator.py`) — no Python changes are required beyond the manifest
