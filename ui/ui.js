const logEl = document.getElementById("log");
const noticeEl = document.getElementById("notice");

function showNotice(msg) {
  noticeEl.textContent = msg;
  noticeEl.classList.add("show");
}
function hideNotice() {
  noticeEl.textContent = "";
  noticeEl.classList.remove("show");
}

function log(msg) {
  const ts = new Date().toLocaleTimeString();
  logEl.textContent += `[${ts}] ${msg}\n`;
  logEl.scrollTop = logEl.scrollHeight;
}

function defaultApiBase() {
  // If served by the Express server, use same-origin. If opened as file://, default to localhost.
  if (location.protocol === "file:") return "http://localhost:8787";
  return location.origin;
}

function getConfig() {
  return {
    apiBase: document.getElementById("apiBase").value.trim() || defaultApiBase(),
    referenceUrl: document.getElementById("referenceUrl").value.trim(),
    maxImages: Number(document.getElementById("maxImages").value || 8),
    openaiKey: document.getElementById("openaiKey").value.trim(),
    openaiModel: document.getElementById("openaiModel").value.trim() || "gpt-5",
    ghToken: document.getElementById("ghToken").value.trim(),
    ghRepo: document.getElementById("ghRepo").value.trim(),
    ghBranch: document.getElementById("ghBranch").value.trim() || "main",
    createRepo: document.getElementById("createRepo").value === "yes",
    overwriteScrape: document.getElementById("overwriteScrape")?.value === "yes"
  };
}

function saveConfig() {
  const cfg = getConfig();
  // Store non-secret only
  localStorage.setItem("workflowCfg", JSON.stringify({
    apiBase: cfg.apiBase,
    referenceUrl: cfg.referenceUrl,
    maxImages: cfg.maxImages,
    openaiModel: cfg.openaiModel,
    ghRepo: cfg.ghRepo,
    ghBranch: cfg.ghBranch,
    createRepo: cfg.createRepo,
    overwriteScrape: cfg.overwriteScrape
  }));
  log("Saved config (non-secret fields) to localStorage.");
}

function loadConfig() {
  document.getElementById("apiBase").value = defaultApiBase();
  const raw = localStorage.getItem("workflowCfg");
  if (!raw) return;
  try {
    const cfg = JSON.parse(raw);
    if (cfg.apiBase) document.getElementById("apiBase").value = cfg.apiBase;
    if (cfg.referenceUrl) document.getElementById("referenceUrl").value = cfg.referenceUrl;
    if (cfg.maxImages) document.getElementById("maxImages").value = cfg.maxImages;
    if (cfg.openaiModel) document.getElementById("openaiModel").value = cfg.openaiModel;
    if (cfg.ghRepo) document.getElementById("ghRepo").value = cfg.ghRepo;
    if (cfg.ghBranch) document.getElementById("ghBranch").value = cfg.ghBranch;
    document.getElementById("createRepo").value = cfg.createRepo ? "yes" : "no";
    if (document.getElementById("overwriteScrape") && typeof cfg.overwriteScrape !== "undefined") {
      document.getElementById("overwriteScrape").value = cfg.overwriteScrape ? "yes" : "no";
    }
    log("Loaded saved config.");
  } catch {}
}

const steps = [
  { id: "scrape", name: "Scrape reference site", desc: "Fetch headline/description/sections + download images into src/images and update landing.json", enabled: true },
  { id: "llm", name: "LLM rewrite (optional)", desc: "Rewrite the draft landing.json copy into original marketing copy (OpenAI Responses API)", enabled: true },
  { id: "build", name: "Build site", desc: "Generate dist/ from landing.json (and copy images into dist/assets/images)", enabled: true },
  { id: "deploy", name: "Deploy to GitHub", desc: "Upload project files to your GitHub repo (push triggers GitHub Pages workflow)", enabled: true }
];

function renderSteps() {
  const root = document.getElementById("steps");
  root.innerHTML = "";
  steps.forEach((s, idx) => {
    const div = document.createElement("div");
    div.className = "step";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = s.enabled;
    checkbox.addEventListener("change", () => (s.enabled = checkbox.checked));

    const info = document.createElement("div");
    info.innerHTML = `<div class="name">${s.name}</div><div class="desc">${s.desc}</div>`;

    const controls = document.createElement("div");
    controls.className = "controls";

    const up = document.createElement("button");
    up.className = "iconbtn";
    up.textContent = "↑";
    up.title = "Move up";
    up.disabled = idx === 0;
    up.onclick = () => {
      const [x] = steps.splice(idx, 1);
      steps.splice(idx - 1, 0, x);
      renderSteps();
    };

    const down = document.createElement("button");
    down.className = "iconbtn";
    down.textContent = "↓";
    down.title = "Move down";
    down.disabled = idx === steps.length - 1;
    down.onclick = () => {
      const [x] = steps.splice(idx, 1);
      steps.splice(idx + 1, 0, x);
      renderSteps();
    };

    const run = document.createElement("button");
    run.className = "btn";
    run.textContent = "Run";
    run.onclick = async () => { await runStep(s.id); };

    controls.appendChild(up);
    controls.appendChild(down);
    controls.appendChild(run);

    div.appendChild(checkbox);
    div.appendChild(info);
    div.appendChild(controls);

    root.appendChild(div);
  });
}

async function api(path, body) {
  const cfg = getConfig();
  const base = cfg.apiBase.replace(/\/+$/, "");
  const url = base + path;

  const res = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body || {})
  });

  const text = await res.text();
  let data = {};
  try { data = JSON.parse(text); } catch { data = { raw: text }; }
  if (!res.ok) throw new Error(data?.error || `HTTP ${res.status}`);
  return data;
}

async function testConn() {
  hideNotice();
  const cfg = getConfig();
  try {
    const base = cfg.apiBase.replace(/\/+$/, "");
    const res = await fetch(base + "/api/health");
    const data = await res.json();
    if (data?.ok) log("✅ API OK");
    else throw new Error("Unexpected response");
  } catch (e) {
    log(`❌ API not reachable: ${e.message || e}`);
    showNotice("API not reachable. Start the server with: npm run ui, and open the UI from that URL (not by double-clicking index.html). If hosting UI elsewhere, set API Base URL to the server origin.");
  }
}

async function runStep(stepId) {
  hideNotice();
  const cfg = getConfig();

  log(`▶ Running step: ${stepId}`);
  try {
    let out;
    if (stepId === "scrape") out = await api("/api/run/scrape", cfg);
    else if (stepId === "llm") out = await api("/api/run/llm", cfg);
    else if (stepId === "build") out = await api("/api/run/build", cfg);
    else if (stepId === "deploy") out = await api("/api/run/deploy", cfg);
    else throw new Error("Unknown step");

    if (out?.log) log(String(out.log).trim());
    log(`✅ Step complete: ${stepId}`);
  } catch (e) {
    log(`❌ Step failed: ${stepId}: ${e.message || e}`);
    if (String(e?.message || "").toLowerCase().includes("failed to fetch")) {
      showNotice("“Failed to fetch” usually means the UI cannot reach the server. Click “Test API”, confirm the server is running, and set API Base URL correctly.");
    }
    throw e;
  }
}

async function runWorkflow() {
  hideNotice();
  const active = steps.filter(s => s.enabled);
  if (!active.length) { log("No steps enabled."); return; }

  log(`▶ Running workflow: ${active.map(s => s.id).join(" → ")}`);

  for (const s of active) {
    if (s.id === "scrape" && !getConfig().referenceUrl) {
      log("ℹ️  Skipping scrape (no reference URL).");
      continue;
    }
    if (s.id === "llm" && !getConfig().openaiKey) {
      log("ℹ️  Skipping LLM rewrite (no OpenAI API key).");
      continue;
    }
    await runStep(s.id);
  }
  log("🎉 Workflow finished.");
}

document.getElementById("runAll").addEventListener("click", () => runWorkflow());
document.getElementById("saveConfig").addEventListener("click", () => saveConfig());
document.getElementById("resetLogs").addEventListener("click", () => (logEl.textContent = ""));
document.getElementById("testConn").addEventListener("click", () => testConn());

loadConfig();
renderSteps();

if (location.protocol === "file:") {
  showNotice("You opened this UI as a local file (file://). Start the server with: npm run ui, then open http://localhost:8787. Or set API Base URL to your server.");
}
log("UI ready. Tip: Click “Test API” first. Then run Scrape (optional), LLM rewrite (optional), Build, Deploy.");
