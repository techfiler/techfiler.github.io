# Landing Autopilot — Workflow UI (Scrape → LLM → Build → Deploy)

This template gives you:

- A static landing page generator (`landing.json` → `dist/`)
- An optional scraper (reference URL → draft copy + download images)
- An optional LLM rewrite step (OpenAI Responses API)
- A local **Workflow UI** to run steps in sequence and deploy to GitHub

---

## Start the Workflow UI

```bash
npm install
npm run ui
```

Open the URL printed in the terminal (default):
- http://localhost:8787

> ✅ Important: **Do not double-click `ui/index.html`** to open it as `file://...`  
> If you do, the UI can’t reach the backend and you’ll see **“Failed to fetch”**.
>
> If you *must* host the UI elsewhere, set **API Base URL** (in the UI) to your server URL.

---

## Fixing “Failed to fetch”

This error means the browser couldn’t reach the backend API.

Checklist:

1. Confirm the server is running:
   - Terminal should show: `Workflow UI running: http://localhost:8787`
2. Click **“Test API”** inside the UI:
   - Should log “✅ API OK”
3. Ensure you opened the UI from the server URL (http://localhost:8787), not as a local file.
4. If using a different port, set `PORT=xxxx` and update the UI **API Base URL**.

---

## GitHub Pages (one-time setting)

After you deploy/push the repo:

1. Repo → **Settings → Pages**
2. **Source** = **GitHub Actions**

Now every push to `main` deploys to GitHub Pages.

---

## Tokens / keys

### GitHub token (PAT)
Create a Personal Access Token with:
- `repo` scope
- `workflow` scope (needed if uploading `.github/workflows/*` via API)

Paste the token into the UI (not saved).

### OpenAI API key (optional)
If you want the LLM rewrite step:
- Paste your API key into the UI
- Choose a model (default: `gpt-5`)

---

## Local CLI usage (optional)

### Scrape
```bash
npm run scrape -- --url https://example.com --max-images 8
```

### Build
```bash
npm run build
npm run preview
```

---

## Notes on scraping and content rights

Only scrape/reuse content you have permission to use. Treat scraped output as a draft and rewrite it.

---

## Folder overview

- `ui/` - Workflow UI page
- `server/` - Express server + GitHub + OpenAI integrations
- `scripts/` - scrape + generate scripts
- `src/` - landing page template assets
- `landing.json` - your content “script”


## Scrape step note

If Scrape fails with a Cheerio import error, update to v2.1.2 and run `npm install` again.


## Scrape overwrite

The scraper **does not overwrite** existing template fields by default in older versions, so you might keep seeing “Your Brand”.

In v2.1.4+, turn on **Scrape overwrite = Yes** in the UI (or pass `--overwrite` in CLI) to replace brand/headline/links/images from the reference URL.
