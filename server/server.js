import express from "express";
import cors from "cors";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { runScrape, runBuild, runLLMRewrite, runDeploy } from "./workflow.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, "..");

const app = express();
app.use(express.json({ limit: "2mb" }));

// Allow hosting UI elsewhere (optional). Same-origin still works without this.
app.use(cors({ origin: true }));

// Health endpoint (used by UI "Test API")
app.get("/api/health", (req, res) => res.json({ ok: true }));

// Serve UI
app.use("/", express.static(path.join(root, "ui")));

app.post("/api/run/scrape", async (req, res) => {
  try {
    const out = await runScrape(req.body || {});
    res.json({ ok: true, log: out });
  } catch (e) {
    res.status(400).json({ error: String(e?.message || e) });
  }
});

app.post("/api/run/llm", async (req, res) => {
  try {
    const out = await runLLMRewrite(req.body || {});
    res.json({ ok: true, log: out });
  } catch (e) {
    res.status(400).json({ error: String(e?.message || e) });
  }
});

app.post("/api/run/build", async (req, res) => {
  try {
    const out = await runBuild(req.body || {});
    res.json({ ok: true, log: out });
  } catch (e) {
    res.status(400).json({ error: String(e?.message || e) });
  }
});

app.post("/api/run/deploy", async (req, res) => {
  try {
    const out = await runDeploy(req.body || {});
    res.json({ ok: true, log: out });
  } catch (e) {
    res.status(400).json({ error: String(e?.message || e) });
  }
});

const port = process.env.PORT ? Number(process.env.PORT) : 8787;
app.listen(port, () => {
  console.log(`Workflow UI running: http://localhost:${port}`);
});
