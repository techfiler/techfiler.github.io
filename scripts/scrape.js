import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as cheerio from "cheerio";
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, "..");

const landingPath = path.join(root, "landing.json");
const imagesDir = path.join(root, "src", "images");

function ensureDir(dir) { fs.mkdirSync(dir, { recursive: true }); }

function parseArgs(argv) {
  const out = {};
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--url" && argv[i + 1]) out.url = argv[++i];
    else if (a === "--max-images" && argv[i + 1]) out.maxImages = Number(argv[++i]);
    else if (a === "--timeout" && argv[i + 1]) out.timeoutMs = Number(argv[++i]);
    else if (a === "--overwrite") out.overwrite = true;
  }
  return out;
}

function safeText(s) { return String(s || "").replace(/\s+/g, " ").trim(); }
function firstNonEmpty(...vals) { for (const v of vals) { const t = safeText(v); if (t) return t; } return ""; }

function parseInstagramTitle(title) {
  // Example: "Dome Castle (@dome.castle) • Instagram photos and videos"
  const t = safeText(title);
  const m = t.match(/^(.+?)\s*\(@([^\)]+)\)/);
  if (!m) return { name: "", handle: "" };
  return { name: safeText(m[1]), handle: safeText(m[2]) };
}

function unique(list) { const seen = new Set(); const out = []; for (const x of list) { const k = String(x||"").trim(); if(!k||seen.has(k)) continue; seen.add(k); out.push(k);} return out; }
function isProbablyImageUrl(u) { const s = String(u||"").toLowerCase(); if(!s) return false; if(s.startsWith("data:")) return false; if(s.endsWith(".svg")) return false; return true; }
function resolveUrl(base, maybeRel) { try { return new URL(maybeRel, base).toString(); } catch { return ""; } }

async function fetchText(url, timeoutMs = 20000) {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { redirect: "follow", headers: { "user-agent": "landing-autopilot-scraper/2.0 (+https://github.com)" }, signal: controller.signal });
    if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);
    return { url: res.url, text: await res.text() };
  } finally { clearTimeout(t); }
}

function extFromContentType(ct) {
  const s = String(ct || "").toLowerCase();
  if (s.includes("image/jpeg")) return ".jpg";
  if (s.includes("image/png")) return ".png";
  if (s.includes("image/webp")) return ".webp";
  if (s.includes("image/gif")) return ".gif";
  return "";
}
function extFromUrl(u) {
  try {
    const p = new URL(u).pathname.toLowerCase();
    for (const ext of [".jpg", ".jpeg", ".png", ".webp", ".gif"]) if (p.endsWith(ext)) return ext === ".jpeg" ? ".jpg" : ext;
    return "";
  } catch { return ""; }
}

async function downloadImage(url, fileBase, timeoutMs = 20000) {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { redirect: "follow", headers: { "user-agent": "landing-autopilot-scraper/2.0 (+https://github.com)" }, signal: controller.signal });
    if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);
    const ct = res.headers.get("content-type") || "";
    const ext = extFromContentType(ct) || extFromUrl(res.url) || ".img";
    const fileName = `${fileBase}${ext}`;
    const outPath = path.join(imagesDir, fileName);
    const arr = new Uint8Array(await res.arrayBuffer());
    fs.writeFileSync(outPath, arr);
    return { fileName, contentType: ct, finalUrl: res.url };
  } finally { clearTimeout(t); }
}

function extractFromHtml(baseUrl, html) {
  const $ = cheerio.load(html);
  const ogTitle = $('meta[property="og:title"]').attr("content");
  const titleTag = $("title").first().text();
  const siteName = $('meta[property="og:site_name"]').attr("content");

  const ogDesc = $('meta[property="og:description"]').attr("content");
  const metaDesc = $('meta[name="description"]').attr("content");

  const h1 = $("h1").first().text();
  const firstP = $("h1").first().nextAll("p").first().text();

  const sections = [];
  $("h2").each((i, el) => {
    if (sections.length >= 3) return;
    const title = safeText($(el).text());
    if (!title) return;

    const items = [];
    const nextList = $(el).nextAll("ul,ol").first();
    if (nextList && nextList.length) {
      nextList.find("li").each((_, li) => {
        const t = safeText($(li).text());
        if (t) items.push(t);
      });
    }
    if (items.length) sections.push({ title, items: items.slice(0, 6) });
  });

  const links = $("a").map((_, a) => $(a).attr("href")).get().filter(Boolean);
  const instagramUrl = links.find((u) => String(u).includes("instagram.com")) || "";
  const whatsappLink = links.find((u) => String(u).includes("wa.me") || String(u).includes("whatsapp.com")) || "";

  const ogImage = $('meta[property="og:image"]').attr("content") || "";
  const imgSrcs = $("img")
    .map((_, img) => $(img).attr("src") || $(img).attr("data-src") || $(img).attr("data-lazy-src"))
    .get()
    .filter(Boolean);

  const allImages = unique([ogImage, ...imgSrcs])
    .map((u) => resolveUrl(baseUrl, u))
    .filter((u) => isProbablyImageUrl(u));

  return {
    title: firstNonEmpty(ogTitle, titleTag, siteName),
    description: firstNonEmpty(ogDesc, metaDesc),
    headline: firstNonEmpty(h1, ogTitle, titleTag),
    subheadline: firstNonEmpty(firstP, ogDesc, metaDesc),
    sections,
    instagramUrl,
    whatsappLink,
    imageUrls: allImages
  };
}

function extractWhatsAppNumberFromLink(u) {
  try {
    const url = new URL(u);
    if (url.hostname === "wa.me") {
      const digits = url.pathname.replace(/\D/g, "");
      return digits ? `+${digits}` : "";
    }
    const phone = url.searchParams.get("phone") || "";
    const digits = phone.replace(/\D/g, "");
    return digits ? `+${digits}` : "";
  } catch { return ""; }
}
function extractWhatsAppTextFromLink(u) {
  try {
    const url = new URL(u);
    return url.searchParams.get("text") || url.searchParams.get("message") || "";
  } catch { return ""; }
}

function readExistingJson() {
  try { return JSON.parse(fs.readFileSync(landingPath, "utf8")); } catch { return {}; }
}

function mergeLanding(existing, scraped, downloadedFiles, baseUrl, overwrite = false) {
  const getExisting = (pathArr, fallback = "") => {
    let cur = existing;
    for (const k of pathArr) cur = cur?.[k];
    const v = typeof cur === "string" ? cur : "";
    return v || fallback;
  };

  const prefer = (existingVal, scrapedVal, fallback = "") => {
    const s = safeText(scrapedVal);
    const e = safeText(existingVal);
    if (overwrite && s) return s;
    return e || s || fallback;
  };

  const isInstagram = String(baseUrl || "").includes("instagram.com");
  const igMeta = isInstagram ? parseInstagramTitle(scraped.title) : { name: "", handle: "" };

  const brandName = prefer(getExisting(["brand","name"]), igMeta.name || scraped.title, "Brand");
  const accentColor = getExisting(["brand","accentColor"], "#6d28d9");

  const whatsappNumber = prefer(
    getExisting(["hero","whatsappNumber"]),
    extractWhatsAppNumberFromLink(scraped.whatsappLink),
    "+91 98765 43210"
  );

  const whatsappMessage = prefer(
    getExisting(["hero","whatsappMessage"]),
    extractWhatsAppTextFromLink(scraped.whatsappLink),
    "Hi! I came from your landing page and I'd like to know more."
  );

  const instagramUrl = prefer(
    getExisting(["hero","instagramUrl"]),
    // If the scraped page IS Instagram, just use the input URL
    isInstagram ? baseUrl : scraped.instagramUrl,
    "https://www.instagram.com/yourhandle/"
  );

  // If we downloaded at least one image, always use it as hero image.
  const heroImage = downloadedFiles[0]
    ? `images/${downloadedFiles[0]}`
    : prefer(getExisting(["media","heroImage"]), "", "");

  const gallery = downloadedFiles.slice(1, 10).map((f) => `images/${f}`);

  const sectionsExisting = existing?.sections || [];
  const sectionsScraped = scraped.sections && scraped.sections.length ? scraped.sections : [];
  const sections = overwrite ? (sectionsScraped.length ? sectionsScraped : sectionsExisting) : (sectionsExisting.length ? sectionsExisting : sectionsScraped);
  const sectionsFinal = (sections || []).slice(0, 5);

  return {
    site: {
      title: prefer(getExisting(["site","title"]), scraped.title, "Landing Page"),
      description: prefer(getExisting(["site","description"]), scraped.description, ""),
      language: getExisting(["site","language"], "en")
    },
    brand: {
      name: brandName,
      tagline: prefer(getExisting(["brand","tagline"]), scraped.description, ""),
      accentColor
    },
    hero: {
      headline: prefer(getExisting(["hero","headline"]), scraped.headline || scraped.title, "Welcome"),
      subheadline: prefer(getExisting(["hero","subheadline"]), scraped.subheadline || scraped.description, ""),
      primaryCtaText: getExisting(["hero","primaryCtaText"], "Chat on WhatsApp"),
      whatsappNumber,
      whatsappMessage,
      secondaryCtaText: getExisting(["hero","secondaryCtaText"], "Visit Instagram"),
      instagramUrl
    },
    media: { heroImage, gallery },
    sections: sectionsFinal,
    footer: {
      copyrightName: prefer(getExisting(["footer","copyrightName"]), brandName, brandName),
      email: getExisting(["footer","email"], "hello@example.com")
    },
    scrape: {
      sourceUrl: baseUrl,
      scrapedAt: new Date().toISOString(),
      overwrite,
      note: "Drafted via scraper. Ensure you have rights to reuse any content/images."
    }
  };
}


async function main() {
  const args = parseArgs(process.argv);
  const url = args.url || process.env.REFERENCE_URL || "";
  const maxImages = Number.isFinite(args.maxImages) ? args.maxImages : 8;
  const timeoutMs = Number.isFinite(args.timeoutMs) ? args.timeoutMs : 20000;
  const overwrite = !!args.overwrite;

  if (!url) { console.error("Missing --url"); process.exit(1); }

  ensureDir(imagesDir);

  console.log(`Fetching: ${url}`);
  const { url: finalUrl, text: html } = await fetchText(url, timeoutMs);
  const scraped = extractFromHtml(finalUrl, html);

  const imageUrls = (scraped.imageUrls || []).slice(0, maxImages);
  const downloaded = [];
  const report = [];

  for (let i = 0; i < imageUrls.length; i++) {
    const imgUrl = imageUrls[i];
    const base = `img-${String(i+1).padStart(3, "0")}`;
    try {
      console.log(`Downloading (${i+1}/${imageUrls.length}): ${imgUrl}`);
      const res = await downloadImage(imgUrl, base, timeoutMs);
      downloaded.push(res.fileName);
      report.push({ requested: imgUrl, finalUrl: res.finalUrl, fileName: res.fileName, contentType: res.contentType });
    } catch (e) {
      report.push({ requested: imgUrl, error: String(e?.message || e) });
      console.warn(`Skipped image: ${imgUrl}`);
    }
  }

  const existing = readExistingJson();
  const merged = mergeLanding(existing, scraped, downloaded, finalUrl, overwrite);

  fs.writeFileSync(landingPath, JSON.stringify(merged, null, 2) + "\n", "utf8");
  fs.writeFileSync(path.join(root, "scrape-report.json"), JSON.stringify({ source: finalUrl, report }, null, 2) + "\n", "utf8");

  console.log("Updated landing.json");
  console.log("Saved scrape-report.json");
  console.log(`Downloaded images: ${downloaded.length}`);
}

main().catch((e) => { console.error("Scrape failed:", e); process.exit(1); });
