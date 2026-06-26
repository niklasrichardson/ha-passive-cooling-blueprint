# Setup generator

A small browser tool that turns a list of your rooms into ready-to-paste YAML —
the per-room helpers, the global setting helpers, an overview dashboard, and
automation stubs. **No Python, no install, nothing uploaded** — it runs entirely
in your browser.

The tool lives at [`docs/generator/index.html`](generator/index.html).

## Use it

**Option A — open it locally (works for a private repo too).**
Download/clone the repo and open `docs/generator/index.html` in your browser
(double-click, or drag it into a tab). It's a single self-contained file and runs
offline.

**Option B — the hosted page (once the repo is public).**
With GitHub Pages enabled, it's available at:

```
https://niklasrichardson.github.io/ha-passive-cooling-blueprint/docs/generator/
```

> GitHub Pages only serves **public** repositories (private needs a paid GitHub
> plan), so use Option A while the repo is private.

## What you do

1. Set the **shared outdoor sensor** (one sensor can serve every room).
2. **Add a room** for each room: its name and indoor sensor, plus optional trend
   sensors. The outdoor field defaults to the shared one.
3. Tick what you want generated and click **Generate YAML**.
4. **Copy** each block and paste it where it belongs:
   - *Global setting helpers* and *Per-room helpers* → `configuration.yaml` (or a
     package), then restart.
   - *Overview dashboard* → a new dashboard's raw configuration editor.
   - *Automation stubs* → a starting point; link each `status_helper` in
     the editor and replace `notify.notify` with your service.

The generated entity ids follow the project's
[naming conventions](global-overrides.md) (`input_boolean.passive_cooling_<room>`,
`input_number.passive_cooling_*`), so everything lines up with the blueprint's
suggested names.

## Enabling GitHub Pages (maintainers)

Once the repo is public: *Settings → Pages → Build and deployment → Source:
Deploy from a branch → Branch: `main` / root*. The repo includes a `.nojekyll`
file so the static HTML is served as-is. The tool is then at the URL above.
