import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, "..");

function b64(buf) {
  return Buffer.from(buf).toString("base64");
}

function shouldIgnore(rel) {
  const p = rel.replace(/\\/g, "/");
  if (p.startsWith("node_modules/")) return true;
  if (p.startsWith("dist/")) return true; // Actions builds dist
  if (p.startsWith(".git/")) return true;
  if (p === ".env") return true;
  if (p.startsWith("workspace/")) return true;
  return false;
}

function walkDir(dir, baseDir = dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    const rel = path.relative(baseDir, full);
    if (shouldIgnore(rel)) continue;

    if (entry.isDirectory()) out.push(...walkDir(full, baseDir));
    else out.push({ full, rel: rel.replace(/\\/g, "/") });
  }
  return out;
}

async function ghRequest(token, method, url, body) {
  const res = await fetch(url, {
    method,
    headers: {
      "authorization": `Bearer ${token}`,
      "accept": "application/vnd.github+json",
      "content-type": "application/json",
      "user-agent": "landing-autopilot-workflow-ui"
    },
    body: body ? JSON.stringify(body) : undefined
  });
  const text = await res.text();
  let json;
  try { json = JSON.parse(text); } catch { json = { raw: text }; }
  if (!res.ok) {
    const msg = json?.message || text || `HTTP ${res.status}`;
    const err = new Error(msg);
    err.status = res.status;
    err.details = json;
    throw err;
  }
  return json;
}

async function ensureRepoExists({ token, owner, repo, createRepo }) {
  const repoUrl = `https://api.github.com/repos/${owner}/${repo}`;
  try {
    await ghRequest(token, "GET", repoUrl);
    return "Repo exists";
  } catch (e) {
    if (!createRepo || e.status !== 404) throw e;
  }

  // Create repo under the authenticated user
  const created = await ghRequest(token, "POST", "https://api.github.com/user/repos", {
    name: repo,
    private: true,
    auto_init: false
  });
  return `Created repo: ${created.full_name}`;
}

async function getFileSha({ token, owner, repo, branch, filePath }) {
  const url = `https://api.github.com/repos/${owner}/${repo}/contents/${encodeURIComponent(filePath)}?ref=${encodeURIComponent(branch)}`;
  try {
    const json = await ghRequest(token, "GET", url);
    return json.sha;
  } catch (e) {
    if (e.status === 404) return null;
    throw e;
  }
}

async function upsertFile({ token, owner, repo, branch, filePath, contentB64, message }) {
  const sha = await getFileSha({ token, owner, repo, branch, filePath });

  const url = `https://api.github.com/repos/${owner}/${repo}/contents/${encodeURIComponent(filePath)}`;
  const body = {
    message,
    content: contentB64,
    branch
  };
  if (sha) body.sha = sha;

  await ghRequest(token, "PUT", url, body);
  return sha ? "updated" : "created";
}

export async function deployToGitHub({ token, owner, repo, branch, createRepo }) {
  let log = "";
  const say = (s) => (log += s + "\n");

  say("🔐 Checking repo...");
  say(await ensureRepoExists({ token, owner, repo, createRepo }));

  say("📦 Collecting files to upload...");
  const files = walkDir(root, root);
  say(`Found ${files.length} file(s).`);

  const commitMsg = "chore: update landing autopilot workflow";

  for (let i = 0; i < files.length; i++) {
    const { full, rel } = files[i];
    const buf = fs.readFileSync(full);
    const status = await upsertFile({
      token,
      owner,
      repo,
      branch,
      filePath: rel,
      contentB64: b64(buf),
      message: commitMsg
    });
    if ((i + 1) % 20 === 0) say(`… uploaded ${i + 1}/${files.length}`);
    // keep logs lightweight
  }

  say(`✅ Uploaded ${files.length} file(s) to ${owner}/${repo}@${branch}.`);
  say("ℹ️ Next: In GitHub repo → Settings → Pages → Source: GitHub Actions (once).");
  say("ℹ️ Pushing to the branch triggers the deploy workflow.");
  return log;
}
