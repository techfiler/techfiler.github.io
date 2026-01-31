import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import OpenAI from "openai";
import { deployToGitHub } from "./github.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, "..");

function run(cmd, args, env = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, args, {
      cwd: root,
      env: { ...process.env, ...env },
      shell: process.platform === "win32"
    });

    let out = "";
    child.stdout.on("data", (d) => (out += d.toString()));
    child.stderr.on("data", (d) => (out += d.toString()));

    child.on("close", (code) => {
      if (code === 0) resolve(out);
      else reject(new Error(out || `Command failed (${code})`));
    });
  });
}

export async function runScrape(cfg) {
  const url = String(cfg.referenceUrl || "").trim();
  if (!url) throw new Error("referenceUrl is required for scrape");
  const maxImages = Number.isFinite(cfg.maxImages) ? String(cfg.maxImages) : "8";
  return await run("node", ["scripts/scrape.js", "--url", url, "--max-images", maxImages]);
}

export async function runBuild() {
  return await run("node", ["scripts/generate.js"]);
}

function tryParseJson(text) {
  const t = String(text || "").trim();
  // Try direct parse
  try { return JSON.parse(t); } catch {}
  // Try to extract first JSON object
  const m = t.match(/\{[\s\S]*\}/);
  if (m) return JSON.parse(m[0]);
  throw new Error("LLM output was not valid JSON.");
}

export async function runLLMRewrite(cfg) {
  const apiKey = String(cfg.openaiKey || process.env.OPENAI_API_KEY || "").trim();
  if (!apiKey) throw new Error("OpenAI API key missing (openaiKey)");
  const model = String(cfg.openaiModel || "gpt-5").trim();

  const landingPath = path.join(root, "landing.json");
  const raw = fs.readFileSync(landingPath, "utf8");
  const landing = JSON.parse(raw);

  // Prompt-injection safe-ish: treat scraped content as data, instruct to ignore instructions inside it.
  const instructions = [
    "You are a marketing copywriter and editor.",
    "Rewrite the landing page content to be ORIGINAL and non-infringing.",
    "Do NOT copy text verbatim from any reference site; paraphrase and improve.",
    "Keep WhatsApp number/message and Instagram URL as-is.",
    "Return ONLY valid JSON that matches the same schema as the input (same keys/structure).",
    "If a field is missing, fill it reasonably."
  ].join("\n");

  const userPayload = {
    task: "Rewrite landing.json copy",
    input_schema_note: "Keep the same JSON keys and nesting. Only modify text fields (title/description/tagline/headlines/sections).",
    landing_json: landing
  };

  const client = new OpenAI({ apiKey });
  const response = await client.responses.create({
    model,
    reasoning: { effort: "low" },
    instructions,
    input: JSON.stringify(userPayload)
  });

  const outText = response.output_text;
  const updated = tryParseJson(outText);

  // Preserve social/contact fields in case the model changed them
  updated.hero = updated.hero || {};
  updated.hero.whatsappNumber = landing?.hero?.whatsappNumber || updated.hero.whatsappNumber;
  updated.hero.whatsappMessage = landing?.hero?.whatsappMessage || updated.hero.whatsappMessage;
  updated.hero.instagramUrl = landing?.hero?.instagramUrl || updated.hero.instagramUrl;

  fs.writeFileSync(landingPath, JSON.stringify(updated, null, 2) + "\n", "utf8");
  return "✅ LLM rewrite applied to landing.json";
}

export async function runDeploy(cfg) {
  const token = String(cfg.ghToken || process.env.GITHUB_TOKEN || "").trim();
  if (!token) throw new Error("GitHub token missing (ghToken)");
  const repoFull = String(cfg.ghRepo || "").trim();
  if (!repoFull.includes("/")) throw new Error("ghRepo must be like owner/repo");

  const [owner, repo] = repoFull.split("/");
  const branch = String(cfg.ghBranch || "main").trim();
  const createRepo = Boolean(cfg.createRepo);

  const result = await deployToGitHub({
    token,
    owner,
    repo,
    branch,
    createRepo
  });

  return result;
}
