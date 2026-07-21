// Shared logo loader: rasterize brand SVG/PNG marks to PNG data URIs at high DPI,
// preserving each mark's intrinsic aspect ratio (logos are used UNCHANGED — never
// recolored or distorted). Used by build_devops_segment.js.
const fs = require("fs");
const path = require("path");
const sharp = require("sharp");

const LOGO_DIR = path.join(__dirname, "..", "docs", "report", "logos");

async function loadLogo(file, hPx = 260) {
  const p = path.join(LOGO_DIR, file);
  if (!fs.existsSync(p)) throw new Error(`Logo not found: ${p}`);
  const isSvg = /\.svg$/i.test(file);
  const src = isSvg ? sharp(p, { density: 400 }) : sharp(p);
  const buf = await src
    .resize({ height: hPx, fit: "inside", withoutEnlargement: false })
    .png()
    .toBuffer();
  const meta = await sharp(buf).metadata();
  return {
    data: "image/png;base64," + buf.toString("base64"),
    wPx: meta.width,
    hPx: meta.height,
    ar: meta.width / meta.height,
  };
}

async function loadLogos(files) {
  const out = {};
  for (const [key, file] of Object.entries(files)) {
    out[key] = await loadLogo(file);
  }
  return out;
}

module.exports = { loadLogo, loadLogos, LOGO_DIR };
