# 🍵 Hongkopoly — Live Board Renderer

A Hong Kong food-themed Monopoly board that live-updates in the browser
as the Python simulator runs.

```
MonopolySimulator/          ← existing cloned repo
hongkopoly/                 ← THIS repo (push to GitHub)
  public/
    index.html              ← the live board (served by Netlify)
    game_state.json         ← written by Python, read by browser
    icons/                  ← drop your food PNGs here
  scripts/
    export_state.py         ← runs the sim + writes game_state.json
  netlify.toml
  README.md
```

---

## 1 · Deploy to Netlify (one-time)

1. Push this folder to a **new GitHub repo** (e.g. `hongkopoly`)
2. Log in to [netlify.com](https://netlify.com) → **Add new site → Import from Git**
3. Pick your GitHub repo
4. Build settings:
   - **Build command**: *(leave blank)*
   - **Publish directory**: `public`
5. Click **Deploy site** — your board URL is live instantly

---

## 2 · Run the simulation locally

```bash
# From the hongkopoly/ folder:
pip install -r ../MonopolySimulator/requirements.txt

python scripts/export_state.py --delay 0.5
```

This writes `public/game_state.json` every turn.

---

## 3 · Push state updates to Netlify (live updates)

Because Netlify serves *static* files, you need to push `game_state.json`
to GitHub so Netlify can serve the new version. Two options:

### Option A — Auto-push with git (simplest)

```bash
# scripts/run_and_push.sh
#!/bin/bash
cd "$(dirname "$0")/.."
python scripts/export_state.py --delay 2 &
SIM_PID=$!

while kill -0 $SIM_PID 2>/dev/null; do
  git add public/game_state.json
  git commit -m "state update" --allow-empty-message 2>/dev/null
  git push origin main 2>/dev/null
  sleep 5
done
```

Then run: `bash scripts/run_and_push.sh`

### Option B — Netlify CLI (fastest, no git commits)

```bash
npm install -g netlify-cli
netlify login
netlify link          # link to your site
```

Then in `scripts/export_state.py`, after `write_state()`, add:
```python
os.system("netlify deploy --dir=public --prod --message='state'")
```

---

## 4 · Add your custom food icons

Drop your PNG/WebP images into `public/icons/`:

```
public/icons/
  pineapple_bun.png
  egg_waffle.png
  milk_tea.png
  egg_tart.png
  ...
```

Then in `public/index.html`, find the `SQUARES` array and update each
square's `icon` field from an emoji to an image path:

```js
{ type:'road', label:'Pineapple Bun', icon:'icons/pineapple_bun.png', color:'brown', price:60 },
```

The board renderer auto-detects image paths (anything containing `/` or `.`)
and renders them as `<img>` tags instead of emoji.

---

## 5 · Customize square names & prices

Edit the `SQUARES` array in `public/index.html` — each entry has:
- `label` — display name on the board
- `icon`  — emoji or image path
- `color` — property color group
- `price` — shown under the name

Match them to your `HK_NAMES` dict in `scripts/export_state.py`.
