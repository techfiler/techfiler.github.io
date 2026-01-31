import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, "..");

const landingPath = path.join(root, "landing.json");
const templatePath = path.join(root, "src", "index.template.html");
const cssPath = path.join(root, "src", "style.css");
const jsPath = path.join(root, "src", "app.js");
const imagesDir = path.join(root, "src", "images");

const distDir = path.join(root, "dist");
const assetsDir = path.join(distDir, "assets");
const distImagesDir = path.join(assetsDir, "images");

function mustRead(filePath, label) {
  if (!fs.existsSync(filePath)) throw new Error(`Missing ${label}: ${filePath}`);
  return fs.readFileSync(filePath, "utf8");
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function copyDirIfExists(from, to) {
  if (!fs.existsSync(from)) return;
  ensureDir(to);
  for (const entry of fs.readdirSync(from, { withFileTypes: true })) {
    const src = path.join(from, entry.name);
    const dst = path.join(to, entry.name);
    if (entry.isDirectory()) copyDirIfExists(src, dst);
    else fs.copyFileSync(src, dst);
  }
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function digitsOnly(phone) {
  return String(phone || "").replace(/\D/g, "");
}

function buildWhatsAppLink(number, message) {
  const n = digitsOnly(number);
  if (!n) return "#";
  const text = encodeURIComponent(message || "");
  return text ? `https://wa.me/${n}?text=${text}` : `https://wa.me/${n}`;
}

function buildSectionsHtml(sections) {
  if (!Array.isArray(sections) || sections.length === 0) return "";
  return sections
    .map((s) => {
      const title = escapeHtml(s?.title ?? "");
      const items = Array.isArray(s?.items) ? s.items : [];
      const li = items.map((x) => `<li>${escapeHtml(x)}</li>`).join("");
      return `
        <div class="section-card">
          <h2>${title}</h2>
          <ul>${li}</ul>
        </div>
      `.trim();
    })
    .join("\n");
}

function buildHeroImageHtml(heroImagePath) {
  if (!heroImagePath) return "";
  const safe = escapeHtml(heroImagePath);
  return `
    <div class="hero-image">
      <img src="./assets/${safe}" alt="Hero image" loading="lazy" />
    </div>
  `.trim();
}

function buildGalleryHtml(gallery) {
  if (!Array.isArray(gallery) || gallery.length === 0) {
    return `<p class="hint">No gallery images yet.</p>`;
  }
  const items = gallery
    .slice(0, 9)
    .map((p) => {
      const safe = escapeHtml(p);
      return `<div class="gallery-item"><img src="./assets/${safe}" alt="Gallery image" loading="lazy" /></div>`;
    })
    .join("");
  return `
    <div class="gallery-grid">
      ${items}
    </div>
  `.trim();
}

function replaceAll(template, map) {
  let out = template;
  for (const [k, v] of Object.entries(map)) out = out.split(`{{${k}}}`).join(v);
  return out;
}

function main() {
  const raw = mustRead(landingPath, "landing.json");
  const data = JSON.parse(raw);

  const template = mustRead(templatePath, "src/index.template.html");
  const css = mustRead(cssPath, "src/style.css");
  const js = mustRead(jsPath, "src/app.js");

  const siteTitle = data?.site?.title ?? "Landing Page";
  const siteDesc = data?.site?.description ?? "";
  const lang = data?.site?.language ?? "en";

  const brandName = data?.brand?.name ?? "Brand";
  const brandTagline = data?.brand?.tagline ?? "";
  const accent = data?.brand?.accentColor ?? "#6d28d9";

  const heroHeadline = data?.hero?.headline ?? "";
  const heroSub = data?.hero?.subheadline ?? "";
  const primaryText = data?.hero?.primaryCtaText ?? "Chat on WhatsApp";
  const secondaryText = data?.hero?.secondaryCtaText ?? "Visit Instagram";

  const waNumber = data?.hero?.whatsappNumber ?? "";
  const waMessage = data?.hero?.whatsappMessage ?? "";
  const waLink = buildWhatsAppLink(waNumber, waMessage);

  const igUrl = data?.hero?.instagramUrl ?? "#";

  const footerEmail = data?.footer?.email ?? "";
  const copyrightName = data?.footer?.copyrightName ?? brandName;

  const sectionsHtml = buildSectionsHtml(data?.sections);

  const heroImagePath = data?.media?.heroImage || "";
  const gallery = data?.media?.gallery || [];

  const html = replaceAll(template, {
    LANG: escapeHtml(lang),
    TITLE: escapeHtml(siteTitle),
    DESCRIPTION: escapeHtml(siteDesc),

    ACCENT_COLOR: escapeHtml(accent),

    BRAND_NAME: escapeHtml(brandName),
    BRAND_TAGLINE: escapeHtml(brandTagline),

    HERO_HEADLINE: escapeHtml(heroHeadline),
    HERO_SUBHEADLINE: escapeHtml(heroSub),

    PRIMARY_CTA_TEXT: escapeHtml(primaryText),
    SECONDARY_CTA_TEXT: escapeHtml(secondaryText),

    WHATSAPP_LINK: escapeHtml(waLink),
    INSTAGRAM_URL: escapeHtml(igUrl),

    SECTIONS_HTML: sectionsHtml,
    HERO_IMAGE_HTML: buildHeroImageHtml(heroImagePath),
    GALLERY_HTML: buildGalleryHtml(gallery),

    FOOTER_EMAIL: escapeHtml(footerEmail),
    COPYRIGHT_NAME: escapeHtml(copyrightName)
  });

  fs.rmSync(distDir, { recursive: true, force: true });
  ensureDir(assetsDir);
  ensureDir(distImagesDir);

  fs.writeFileSync(path.join(distDir, "index.html"), html, "utf8");
  fs.writeFileSync(path.join(assetsDir, "style.css"), css, "utf8");
  fs.writeFileSync(path.join(assetsDir, "app.js"), js, "utf8");

  copyDirIfExists(imagesDir, distImagesDir);

  console.log("✅ Generated dist/index.html");
  if (fs.existsSync(imagesDir)) console.log("✅ Copied images to dist/assets/images");
}

main();
