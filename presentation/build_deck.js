// Builds presentation/output/Airline-Data-Platform-Final-Defense.pptx
// Run: node build_deck.js

const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const Fa = require("react-icons/fa");

const OUT_DIR = path.join(__dirname, "output");
const ICON_DIR = path.join(__dirname, "assets", "icons");
fs.mkdirSync(OUT_DIR, { recursive: true });
fs.mkdirSync(ICON_DIR, { recursive: true });

// ---------------------------------------------------------------------------
// Palette — "Night Radar": deep navy dominant, steel-blue support, cyan accent
// ---------------------------------------------------------------------------
const NAVY = "0B1F3A"; // dominant
const NAVY_DEEP = "071527"; // darker shade for gradients/depth
const STEEL = "1C3D5A"; // secondary
const STEEL_LIGHT = "2E5A7A";
const CYAN = "4CC9F0"; // accent
const CYAN_DIM = "2E8FB0";
const AMBER = "F2A93B"; // sparingly, for "exploratory/draft" status only
const WHITE = "FFFFFF";
const OFFWHITE = "F7F9FB";
const CARD_BG = "FFFFFF";
const TEXT_DARK = "0B1F3A";
const TEXT_MUTED = "5A6B7D";
const TEXT_MUTED_LIGHT = "9FB2C6";
const BORDER = "E1E7ED";

const TITLE_FONT = "Cambria";
const BODY_FONT = "Calibri";

// ---------------------------------------------------------------------------
// Icon rasterizer: react-icons -> SVG -> PNG (base64), colored per call
// ---------------------------------------------------------------------------
const iconCache = new Map();
async function renderIcon(name, color, sizePx = 256) {
  const key = `${name}_${color}_${sizePx}`;
  if (iconCache.has(key)) return iconCache.get(key);
  const IconComp = Fa[name];
  if (!IconComp) throw new Error(`Unknown icon ${name}`);
  const svgMarkup = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComp, { color: `#${color}`, size: sizePx })
  );
  const buf = await sharp(Buffer.from(svgMarkup)).png().toBuffer();
  const filePath = path.join(ICON_DIR, `${key}.png`);
  fs.writeFileSync(filePath, buf);
  const dataUri = "image/png;base64," + buf.toString("base64");
  iconCache.set(key, dataUri);
  return dataUri;
}

// ---------------------------------------------------------------------------
// Build
// ---------------------------------------------------------------------------
async function build() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
  pres.author = "Matthias Köhler, Pavel, Chaithra";
  pres.company = "DataScientest Data Engineer Bootcamp";
  pres.title = "Airline Data Engineering Platform — Final Defense";

  const W = 13.33,
    H = 7.5;

  // Pre-render every icon used across the deck, once, at good resolution.
  // Keys are `${IconName}_${COLOR_LABEL}` (e.g. "FaPlane_CYAN") so call sites
  // can reference them as readable literals instead of interpolating hex values.
  const icons = {};
  const iconSpecs = [
    ["FaPlane", "CYAN", CYAN],
    ["FaPlane", "WHITE", WHITE],
    ["FaUsers", "WHITE", WHITE],
    ["FaUserAstronaut", "WHITE", WHITE],
    ["FaTasks", "WHITE", WHITE],
    ["FaSitemap", "WHITE", WHITE],
    ["FaSatelliteDish", "WHITE", WHITE],
    ["FaExchangeAlt", "WHITE", WHITE],
    ["FaChartLine", "WHITE", WHITE],
    ["FaCloud", "WHITE", WHITE],
    ["FaBrain", "WHITE", WHITE],
    ["FaRocket", "WHITE", WHITE],
    ["FaQuoteLeft", "CYAN", CYAN],
    ["FaLock", "NAVY", NAVY],
    ["FaNetworkWired", "NAVY", NAVY],
    ["FaSyncAlt", "NAVY", NAVY],
    ["FaGithub", "WHITE", WHITE],
    ["FaDatabase", "NAVY", NAVY],
    ["FaServer", "NAVY", NAVY],
    ["FaShieldAlt", "NAVY", NAVY],
    ["FaCheckCircle", "CYAN", CYAN],
    ["FaFlask", "AMBER", AMBER],
    ["FaMapMarkedAlt", "WHITE", WHITE],
    ["FaClipboardCheck", "WHITE", WHITE],
  ];
  for (const [name, label, hex] of iconSpecs) {
    icons[`${name}_${label}`] = await renderIcon(name, hex, 256);
  }

  // -------------------------------------------------------------------------
  // Helpers
  // -------------------------------------------------------------------------
  function darkBg(slide) {
    slide.background = { color: NAVY };
    // subtle depth gradient substitute: darker rect band at bottom
    slide.addShape("rect", {
      x: 0,
      y: H - 1.2,
      w: W,
      h: 1.2,
      fill: { color: NAVY_DEEP, transparency: 40 },
      line: { type: "none" },
    });
  }

  function radarMotif(slide, cx, cy, opts = {}) {
    const rings = opts.rings || [1.0, 1.7, 2.4];
    for (const r of rings) {
      slide.addShape("ellipse", {
        x: cx - r,
        y: cy - r,
        w: r * 2,
        h: r * 2,
        fill: { type: "none" },
        line: { color: CYAN, width: 1, transparency: 65 },
      });
    }
  }

  function lightBg(slide) {
    slide.background = { color: OFFWHITE };
  }

  // Content-slide header: kicker + title, on light background. No underline rule.
  function pageHeader(slide, kicker, title, opts = {}) {
    if (kicker) {
      slide.addText(kicker.toUpperCase(), {
        x: 0.6,
        y: 0.42,
        w: W - 1.2,
        h: 0.3,
        fontFace: BODY_FONT,
        fontSize: 12,
        bold: true,
        color: CYAN_DIM,
        charSpacing: 2,
        margin: 0,
      });
    }
    slide.addText(title, {
      x: 0.6,
      y: kicker ? 0.7 : 0.5,
      w: opts.titleW || W - 1.2,
      h: 0.75,
      fontFace: TITLE_FONT,
      fontSize: opts.fontSize || 30,
      bold: true,
      color: TEXT_DARK,
      margin: 0,
    });
  }

  function pageNumber(slide, n) {
    slide.addText(String(n).padStart(2, "0"), {
      x: W - 0.9,
      y: H - 0.5,
      w: 0.6,
      h: 0.3,
      fontFace: BODY_FONT,
      fontSize: 10,
      color: TEXT_MUTED,
      align: "right",
      margin: 0,
    });
  }

  function iconCircle(slide, iconKey, x, y, d, bgColor) {
    slide.addShape("ellipse", {
      x,
      y,
      w: d,
      h: d,
      fill: { color: bgColor },
      line: { type: "none" },
      shadow: {
        type: "outer",
        color: "1A2B3D",
        opacity: 0.25,
        blur: 6,
        offset: 2,
        angle: 90,
      },
    });
    const pad = d * 0.27;
    slide.addImage({
      data: icons[iconKey],
      x: x + pad,
      y: y + pad,
      w: d - pad * 2,
      h: d - pad * 2,
    });
  }

  function card(slide, x, y, w, h, opts = {}) {
    slide.addShape("roundRect", {
      x,
      y,
      w,
      h,
      rectRadius: 0.08,
      fill: { color: opts.fill || CARD_BG },
      line: opts.line || { color: BORDER, width: 1 },
      shadow: opts.noShadow
        ? undefined
        : {
            type: "outer",
            color: "1A2B3D",
            opacity: 0.12,
            blur: 8,
            offset: 2,
            angle: 90,
          },
    });
  }

  function bullets(items, opts = {}) {
    return items.map((it, i) => ({
      text: it,
      options: {
        bullet: { code: "25AA", color: opts.bulletColor || CYAN_DIM },
        color: opts.color || TEXT_DARK,
        fontSize: opts.fontSize || 14,
        fontFace: BODY_FONT,
        breakLine: i !== items.length - 1,
        paraSpaceAfter: opts.spaceAfter || 10,
      },
    }));
  }

  // ===========================================================================
  // SLIDE 1 — Title
  // ===========================================================================
  {
    const s = pres.addSlide();
    darkBg(s);
    radarMotif(s, W - 2.3, 2.0, { rings: [0.8, 1.4, 2.0, 2.6] });
    s.addImage({
      data: icons.FaPlane_CYAN,
      x: W - 2.55,
      y: 1.75,
      w: 0.5,
      h: 0.5,
      rotate: -20,
    });

    s.addText("AIRLINE DATA ENGINEERING PLATFORM", {
      x: 0.9,
      y: 2.55,
      w: W - 3.2,
      h: 1.3,
      fontFace: TITLE_FONT,
      fontSize: 40,
      bold: true,
      color: WHITE,
      margin: 0,
      lineSpacing: 44,
    });
    s.addText("A live medallion pipeline for airline & flight data", {
      x: 0.9,
      y: 3.75,
      w: W - 3.2,
      h: 0.5,
      fontFace: BODY_FONT,
      fontSize: 17,
      color: CYAN,
      margin: 0,
    });
    s.addText("DataScientest Data Engineer Bootcamp — Capstone Project · Final Defense", {
      x: 0.9,
      y: 4.25,
      w: W - 3.2,
      h: 0.4,
      fontFace: BODY_FONT,
      fontSize: 13,
      color: TEXT_MUTED_LIGHT,
      margin: 0,
    });

    s.addShape("line", {
      x: 0.9,
      y: 6.35,
      w: W - 1.8,
      h: 0,
      line: { color: STEEL_LIGHT, width: 0.75, transparency: 30 },
    });
    s.addText("Matthias Köhler   ·   Pavel   ·   Chaithra", {
      x: 0.9,
      y: 6.55,
      w: 7,
      h: 0.4,
      fontFace: BODY_FONT,
      fontSize: 14,
      bold: true,
      color: WHITE,
      margin: 0,
    });
    s.addText("20 July 2026", {
      x: W - 3.4,
      y: 6.55,
      w: 2.5,
      h: 0.4,
      fontFace: BODY_FONT,
      fontSize: 14,
      color: CYAN,
      align: "right",
      margin: 0,
    });
  }

  // ===========================================================================
  // SLIDE 2 — The Challenge
  // ===========================================================================
  {
    const s = pres.addSlide();
    lightBg(s);
    pageHeader(s, "Introduction", "The Challenge");

    s.addText(
      "Build a complete, production-style Data Engineering architecture around live " +
        "airline / flight data — collection, storage, transformation, an API, automation, " +
        "containerization, and a live dashboard.",
      {
        x: 0.6,
        y: 1.55,
        w: 7.0,
        h: 1.3,
        fontFace: BODY_FONT,
        fontSize: 15,
        color: TEXT_DARK,
        margin: 0,
        lineSpacing: 21,
      }
    );

    const rows = [
      ["FaLock_NAVY", "No premium API access", "Lufthansa's public API stayed closed — no token was ever issued to the project."],
      ["FaNetworkWired_NAVY", "A partially network-restricted VM", "OpenSky blocks the training/production VM's egress outright — the pipeline had to design around it, not ignore it."],
      ["FaSyncAlt_NAVY", "An evolving team and feature set", "The team started at four, dropped to three mid-project, and scope shifted with it."],
    ];
    let ry = 3.0;
    for (const [iconKey, head, body] of rows) {
      iconCircle(s, iconKey, 0.6, ry, 0.55, "E9F3F8");
      s.addText(head, {
        x: 1.35,
        y: ry - 0.02,
        w: 5.3,
        h: 0.3,
        fontFace: BODY_FONT,
        bold: true,
        fontSize: 13.5,
        color: TEXT_DARK,
        margin: 0,
      });
      s.addText(body, {
        x: 1.35,
        y: ry + 0.28,
        w: 5.3,
        h: 0.55,
        fontFace: BODY_FONT,
        fontSize: 11.5,
        color: TEXT_MUTED,
        margin: 0,
        lineSpacing: 15,
      });
      ry += 1.15;
    }

    // Mentor quote card
    card(s, 8.1, 1.55, 4.65, 4.6, { fill: NAVY });
    s.addImage({ data: icons.FaQuoteLeft_CYAN, x: 8.5, y: 1.95, w: 0.5, h: 0.5 });
    s.addText(
      "Machine Learning performance is NOT the main objective. The main evaluation " +
        "criterion is Data Engineering mastery.",
      {
        x: 8.5,
        y: 2.6,
        w: 3.85,
        h: 2.1,
        fontFace: TITLE_FONT,
        italic: true,
        fontSize: 17,
        color: WHITE,
        margin: 0,
        lineSpacing: 24,
      }
    );
    s.addText("— Nicolas, Mentor (DataScientest)", {
      x: 8.5,
      y: 4.85,
      w: 3.85,
      h: 0.35,
      fontFace: BODY_FONT,
      fontSize: 12,
      color: CYAN,
      margin: 0,
    });
    s.addShape("line", { x: 8.5, y: 5.35, w: 3.85, h: 0, line: { color: STEEL_LIGHT, width: 0.75, transparency: 40 } });
    s.addText("Recommended ML effort: 1–2 days max, Kaggle-inspired, ship and move on.", {
      x: 8.5,
      y: 5.5,
      w: 3.85,
      h: 0.6,
      fontFace: BODY_FONT,
      fontSize: 11,
      color: TEXT_MUTED_LIGHT,
      margin: 0,
      lineSpacing: 15,
    });

    pageNumber(s, 2);
  }

  // ===========================================================================
  // SLIDE 3 — The Team
  // ===========================================================================
  {
    const s = pres.addSlide();
    lightBg(s);
    pageHeader(s, "Introduction", "The Team");

    const members = [
      {
        name: "Matthias Köhler",
        role: "Infrastructure, Deployment, GitOps",
        note: "Owns cloud infra, CI/CD, GitOps, ingress, and the Q staging environment.",
      },
      {
        name: "Pavel",
        role: "Data Engineering, API Integration",
        note: "API integration across the pipeline; designed and shipped the ML flight-delay service.",
      },
      {
        name: "Chaithra",
        role: "Data Engineering",
        note: "Warehouse exploration (Redshift silver-history) and ETL scheduling proposals.",
      },
    ];
    const cardW = 3.75,
      gap = 0.35,
      startX = 0.6,
      cardY = 1.7,
      cardH = 3.9;
    members.forEach((m, i) => {
      const x = startX + i * (cardW + gap);
      card(s, x, cardY, cardW, cardH);
      iconCircle(s, "FaUserAstronaut_WHITE", x + cardW / 2 - 0.5, cardY + 0.45, 1.0, STEEL);
      s.addText(m.name, {
        x: x + 0.25,
        y: cardY + 1.65,
        w: cardW - 0.5,
        h: 0.4,
        align: "center",
        fontFace: TITLE_FONT,
        bold: true,
        fontSize: 17,
        color: TEXT_DARK,
        margin: 0,
      });
      s.addText(m.role, {
        x: x + 0.25,
        y: cardY + 2.05,
        w: cardW - 0.5,
        h: 0.55,
        align: "center",
        fontFace: BODY_FONT,
        bold: true,
        fontSize: 12,
        color: CYAN_DIM,
        margin: 0,
        lineSpacing: 15,
      });
      s.addText(m.note, {
        x: x + 0.35,
        y: cardY + 2.65,
        w: cardW - 0.7,
        h: 1.1,
        align: "center",
        fontFace: BODY_FONT,
        fontSize: 11,
        color: TEXT_MUTED,
        margin: 0,
        lineSpacing: 15,
      });
    });

    s.addText(
      "Supervised by mentor Nicolas (DataScientest). The team started at four; one member " +
        "left early to focus on remaining bootcamp coursework.",
      {
        x: 0.6,
        y: 5.85,
        w: W - 1.2,
        h: 0.5,
        fontFace: BODY_FONT,
        italic: true,
        fontSize: 11.5,
        color: TEXT_MUTED,
        margin: 0,
      }
    );
    pageNumber(s, 3);
  }

  // ===========================================================================
  // SLIDE 4 — Project Management & Workflow
  // ===========================================================================
  {
    const s = pres.addSlide();
    lightBg(s);
    pageHeader(s, "Project Management", "Milestones & Workflow");

    // Stepper
    const steps = [
      ["0", "Scoping", "07 May"],
      ["1", "Data Discovery", "20 May"],
      ["2", "API & Consumption", "10 Jun"],
      ["3", "Automation", "16 Jun"],
      ["4", "Deployment", "02 Jul"],
      ["🎓", "Final Defense", "20 Jul"],
    ];
    const stepY = 1.75,
      trackX = 0.9,
      trackW = 11.5;
    s.addShape("line", {
      x: trackX + 0.3,
      y: stepY + 0.3,
      w: trackW - 0.6,
      h: 0,
      line: { color: BORDER, width: 3 },
    });
    const stepGap = trackW / (steps.length - 1);
    steps.forEach((st, i) => {
      const cx = trackX + stepGap * i;
      const isLast = i === steps.length - 1;
      s.addShape("ellipse", {
        x: cx - 0.3,
        y: stepY,
        w: 0.6,
        h: 0.6,
        fill: { color: isLast ? CYAN_DIM : NAVY },
        line: { type: "none" },
      });
      s.addText(st[0], {
        x: cx - 0.3,
        y: stepY,
        w: 0.6,
        h: 0.6,
        align: "center",
        valign: "middle",
        fontFace: BODY_FONT,
        bold: true,
        fontSize: 13,
        color: WHITE,
        margin: 0,
      });
      s.addText(st[1], {
        x: cx - 0.85,
        y: stepY + 0.72,
        w: 1.7,
        h: 0.55,
        align: "center",
        fontFace: BODY_FONT,
        bold: true,
        fontSize: 10.5,
        color: TEXT_DARK,
        margin: 0,
        lineSpacing: 13,
      });
      s.addText(st[2], {
        x: cx - 0.85,
        y: stepY + 1.28,
        w: 1.7,
        h: 0.3,
        align: "center",
        fontFace: BODY_FONT,
        fontSize: 10,
        color: CYAN_DIM,
        margin: 0,
      });
    });

    // Workflow cards
    card(s, 0.6, 3.85, 5.8, 2.9);
    iconCircle(s, "FaGithub_WHITE", 0.95, 4.15, 0.55, NAVY);
    s.addText("GitHub Flow", {
      x: 1.7,
      y: 4.2,
      w: 4.5,
      h: 0.35,
      fontFace: TITLE_FONT,
      bold: true,
      fontSize: 15,
      color: TEXT_DARK,
      margin: 0,
    });
    s.addText(
      bullets(
        [
          "Feature branches (feature/ · fix/ · chore/), never pushed to main",
          "Every change reviewed and merged through a PR",
          "Squash-and-merge — one commit per PR, linear history",
        ],
        { fontSize: 12 }
      ),
      { x: 0.95, y: 4.85, w: 5.15, h: 1.75, valign: "top" }
    );

    card(s, 6.7, 3.85, 6.03, 2.9, { fill: NAVY, noShadow: false });
    iconCircle(s, "FaClipboardCheck_WHITE", 7.05, 4.15, 0.55, CYAN_DIM);
    s.addText("Lesson learned — PR #24 → #25", {
      x: 7.8,
      y: 4.15,
      w: 4.7,
      h: 0.55,
      fontFace: TITLE_FONT,
      bold: true,
      fontSize: 14,
      color: WHITE,
      margin: 0,
      lineSpacing: 17,
    });
    s.addText(
      "A clean, “obviously safe” hotfix was merged on sight — it turned out to belong " +
        "inside a larger effort instead, and had to be reverted.",
      {
        x: 7.05,
        y: 4.85,
        w: 5.35,
        h: 1.05,
        fontFace: BODY_FONT,
        fontSize: 11.5,
        color: TEXT_MUTED_LIGHT,
        margin: 0,
        lineSpacing: 15,
      }
    );
    s.addText("Now codified as policy: never merge without asking — even a clean hotfix.", {
      x: 7.05,
      y: 5.95,
      w: 5.35,
      h: 0.65,
      fontFace: BODY_FONT,
      bold: true,
      italic: true,
      fontSize: 12,
      color: CYAN,
      margin: 0,
      lineSpacing: 15,
    });

    pageNumber(s, 4);
  }

  // ===========================================================================
  // SLIDE 5 — Task Ownership
  // ===========================================================================
  {
    const s = pres.addSlide();
    lightBg(s);
    pageHeader(s, "Project Management", "Task Ownership");

    const tableRows = [
      [
        { text: "Area", options: { bold: true, color: WHITE, fill: { color: NAVY }, fontFace: BODY_FONT, fontSize: 12 } },
        { text: "Owner", options: { bold: true, color: WHITE, fill: { color: NAVY }, fontFace: BODY_FONT, fontSize: 12 } },
        { text: "Status", options: { bold: true, color: WHITE, fill: { color: NAVY }, fontFace: BODY_FONT, fontSize: 12 } },
      ],
      [
        { text: "Cloud infrastructure, deployment, GitOps, CI/CD, ingress" },
        { text: "Matthias" },
        { text: "Live in production", options: { color: "1B8A5A", bold: true } },
      ],
      [
        { text: "API integration; ML flight-delay prediction service" },
        { text: "Pavel" },
        { text: "Live in production", options: { color: "1B8A5A", bold: true } },
      ],
      [
        { text: "Warehouse exploration (Redshift silver-history), ETL scheduling proposal" },
        { text: "Chaithra" },
        { text: "Exploratory / draft", options: { color: AMBER, bold: true } },
      ],
      [
        { text: "Architecture decisions — 16 ADRs documenting the why" },
        { text: "Shared" },
        { text: "Ongoing", options: { color: CYAN_DIM, bold: true } },
      ],
    ];
    const styledRows = tableRows.map((row, ri) =>
      row.map((cell) => ({
        text: cell.text,
        options: {
          fontFace: BODY_FONT,
          fontSize: 12.5,
          color: TEXT_DARK,
          fill: ri === 0 ? { color: NAVY } : { color: ri % 2 === 0 ? OFFWHITE : WHITE },
          valign: "middle",
          margin: [6, 10, 6, 10],
          ...cell.options,
        },
      }))
    );
    s.addTable(styledRows, {
      x: 0.6,
      y: 1.7,
      w: W - 1.2,
      colW: [7.0, 1.8, 3.53],
      rowH: [0.5, 0.85, 0.85, 0.95, 0.75],
      border: { type: "solid", color: BORDER, pt: 0.75 },
      autoPage: false,
    });

    s.addText(
      "Ownership is grouped by delivered area rather than raw commit counts — commit " +
        "history skews toward whoever's account carries shared/AI-assisted commits, which " +
        "doesn't reflect who actually drove each part of the system.",
      {
        x: 0.6,
        y: 6.1,
        w: W - 1.2,
        h: 0.6,
        fontFace: BODY_FONT,
        italic: true,
        fontSize: 11,
        color: TEXT_MUTED,
        margin: 0,
        lineSpacing: 15,
      }
    );
    pageNumber(s, 5);
  }

  // ===========================================================================
  // SLIDE 6 — Architecture Overview (hero diagram)
  // ===========================================================================
  {
    const s = pres.addSlide();
    lightBg(s);
    pageHeader(s, "Architecture", "The Medallion Pipeline");

    const boxH = 1.05;
    const y = 3.1;
    const gap = 0.42;

    function flowBox(x, w, label, sub, fill, textColor = WHITE) {
      card(s, x, y, w, boxH, { fill, noShadow: false, line: { type: "none" } });
      s.addText(label, {
        x: x + 0.12,
        y: y + 0.1,
        w: w - 0.24,
        h: 0.45,
        fontFace: BODY_FONT,
        bold: true,
        fontSize: 12.5,
        color: textColor,
        margin: 0,
        lineSpacing: 14,
      });
      s.addText(sub, {
        x: x + 0.12,
        y: y + 0.55,
        w: w - 0.24,
        h: 0.45,
        fontFace: BODY_FONT,
        fontSize: 9.5,
        color: textColor === WHITE ? TEXT_MUTED_LIGHT : TEXT_MUTED,
        margin: 0,
        lineSpacing: 12,
      });
    }
    function arrow(xStart, xEnd) {
      s.addShape("rightArrow", {
        x: xStart,
        y: y + boxH / 2 - 0.09,
        w: xEnd - xStart,
        h: 0.18,
        fill: { color: BORDER },
        line: { type: "none" },
      });
    }

    const colW = [2.15, 2.05, 1.55, 2.05, 2.45];
    let x = 0.6;
    const xs = [];
    for (const w of colW) {
      xs.push(x);
      x += w + gap;
    }

    flowBox(xs[0], colW[0], "OpenSky + adsb.lol", "Live states, ~50s cycle", STEEL);
    arrow(xs[0] + colW[0], xs[1]);
    flowBox(xs[1], colW[1], "MongoDB Atlas", "Bronze — raw landing zone", "FF6B35");
    arrow(xs[1] + colW[1], xs[2]);
    flowBox(xs[2], colW[2], "Python ETL", "silver.py, freshest-wins", NAVY);
    arrow(xs[2] + colW[2], xs[3]);
    flowBox(xs[3], colW[3], "Supabase Postgres", "Silver — map1", "FF6B35");
    arrow(xs[3] + colW[3], xs[4]);
    flowBox(xs[4], colW[4], "Streamlit + FastAPI/Dash", "Gold — two live stacks", CYAN_DIM, NAVY);

    // Legend row
    s.addText("Bronze — raw   ·   Silver — normalized   ·   Gold — consumption", {
      x: 0.6,
      y: y + boxH + 0.35,
      w: W - 1.2,
      h: 0.35,
      align: "center",
      fontFace: BODY_FONT,
      italic: true,
      fontSize: 11.5,
      color: TEXT_MUTED,
      margin: 0,
    });

    // Bottom row: exposure
    card(s, 3.9, 5.3, 5.5, 1.15, { fill: NAVY, line: { type: "none" } });
    s.addImage({ data: icons.FaShieldAlt_NAVY, x: 4.2, y: 5.55, w: 0.5, h: 0.5 });
    s.addShape("ellipse", { x: 4.15, y: 5.5, w: 0.6, h: 0.6, fill: { color: CYAN_DIM }, line: { type: "none" } });
    s.addImage({ data: icons.FaShieldAlt_NAVY, x: 4.32, y: 5.67, w: 0.26, h: 0.26 });
    s.addText("Cloudflare Tunnel — the only ingress", {
      x: 5.0,
      y: 5.45,
      w: 4.3,
      h: 0.35,
      fontFace: BODY_FONT,
      bold: true,
      fontSize: 12.5,
      color: WHITE,
      margin: 0,
    });
    s.addText("Outbound-only connection to the edge — zero inbound web ports on either VM.", {
      x: 5.0,
      y: 5.8,
      w: 4.3,
      h: 0.55,
      fontFace: BODY_FONT,
      fontSize: 10.5,
      color: TEXT_MUTED_LIGHT,
      margin: 0,
      lineSpacing: 13,
    });

    s.addText(
      "Data stores are managed cloud services; every application service is one Docker " +
        "container, deployed as its own Portainer GitOps stack auto-pulling main.",
      {
        x: 0.6,
        y: 6.65,
        w: W - 1.2,
        h: 0.4,
        align: "center",
        fontFace: BODY_FONT,
        fontSize: 10.5,
        color: TEXT_MUTED,
        margin: 0,
      }
    );
    pageNumber(s, 6);
  }

  // ===========================================================================
  // Pillar deep-dive template
  // ===========================================================================
  function pillarSlide(n, pillarLabel, title, iconKey, bulletItems, statLabel, statValue, extra) {
    const s = pres.addSlide();
    lightBg(s);
    pageHeader(s, `Deep Dive — ${pillarLabel}`, title);
    iconCircle(s, iconKey, W - 1.55, 0.55, 0.85, NAVY);

    s.addText(bullets(bulletItems, { fontSize: 14.5, spaceAfter: 14 }), {
      x: 0.6,
      y: 1.85,
      w: 7.3,
      h: 4.3,
      valign: "top",
    });

    card(s, 8.25, 1.85, 4.5, 1.7, { fill: NAVY, line: { type: "none" } });
    s.addText(statValue, {
      x: 8.25,
      y: 2.05,
      w: 4.5,
      h: 0.85,
      align: "center",
      fontFace: TITLE_FONT,
      bold: true,
      fontSize: 30,
      color: CYAN,
      margin: 0,
    });
    s.addText(statLabel, {
      x: 8.25,
      y: 2.9,
      w: 4.5,
      h: 0.5,
      align: "center",
      fontFace: BODY_FONT,
      fontSize: 11.5,
      color: TEXT_MUTED_LIGHT,
      margin: 0,
      lineSpacing: 14,
    });

    if (extra) {
      card(s, 8.25, 3.75, 4.5, 2.4);
      s.addText(extra.title, {
        x: 8.55,
        y: 3.95,
        w: 3.9,
        h: 0.3,
        fontFace: BODY_FONT,
        bold: true,
        fontSize: 12,
        color: CYAN_DIM,
        margin: 0,
      });
      s.addText(extra.body, {
        x: 8.55,
        y: 4.28,
        w: 3.9,
        h: 1.75,
        fontFace: BODY_FONT,
        fontSize: 11,
        color: TEXT_MUTED,
        margin: 0,
        lineSpacing: 15,
      });
    }
    pageNumber(s, n);
    return s;
  }

  // SLIDE 7 — Bronze
  pillarSlide(
    7,
    "Pillar 1 of 4",
    "Bronze — Ingestion",
    "FaSatelliteDish_WHITE",
    [
      "Dual-stream: OpenSky /states/all (primary, OAuth2) + adsb.lol (secondary, no auth) — every cycle, both sources",
      "Lands raw and untransformed in MongoDB Atlas — “ingestion ≠ modeling,” Silver decides what to keep",
      "Frankfurt bounding box (~150×150 km); adsb.lol's radius was tuned down after it filled the free-tier cluster in under a day",
    ],
    "every ~50 seconds",
    "2 feeds",
    {
      title: "WHY TWO SOURCES",
      body: "OpenSky is richer but gets blocked outright from the production VM's AWS IP range. adsb.lol needs no auth and covers the same geography — built in as a safety net from day one.",
    }
  );

  // SLIDE 8 — Silver
  pillarSlide(
    8,
    "Pillar 2 of 4",
    "Silver — Transform & Warehouse",
    "FaExchangeAlt_WHITE",
    [
      "silver.py flattens the freshest Bronze snapshot into a single live table, map1, on Supabase Postgres",
      "Freshest-wins fallback by fetched_at — no manual failover branching, no environment-specific code",
      "Real incident: OpenSky blocked the whole production VM IP range — adsb.lol took over automatically, dashboard never went dark",
      "Target star schema (fact_states + dimension tables) is designed and documented — build-out is next",
    ],
    "since 2026-06-09",
    "map1 live",
    {
      title: "NEXT UP",
      body: "The flat map1 table works for a live map today. The dimensional model (dim_aircraft, dim_airlines, dim_airports) is the next Silver milestone.",
    }
  );

  // SLIDE 9 — Gold
  {
    const s = pres.addSlide();
    lightBg(s);
    pageHeader(s, "Deep Dive — Pillar 3 of 4", "Gold — Consumption");
    iconCircle(s, "FaChartLine_WHITE", W - 1.55, 0.55, 0.85, NAVY);

    card(s, 0.6, 1.75, 3.55, 2.55);
    s.addText("Streamlit Dashboard", {
      x: 0.85,
      y: 1.95,
      w: 3.05,
      h: 0.35,
      fontFace: BODY_FONT,
      bold: true,
      fontSize: 13.5,
      color: TEXT_DARK,
      margin: 0,
    });
    s.addText(
      bullets(
        ["Reads map1 directly via psycopg2", "Cached queries, live map + metrics", "airline-dashboard.matthiaskoehler.com"],
        { fontSize: 10.5, spaceAfter: 7 }
      ),
      { x: 0.85, y: 2.4, w: 3.05, h: 1.8, valign: "top" }
    );

    card(s, 4.35, 1.75, 3.55, 2.55);
    s.addText("FastAPI + Dash", {
      x: 4.6,
      y: 1.95,
      w: 3.05,
      h: 0.35,
      fontFace: BODY_FONT,
      bold: true,
      fontSize: 13.5,
      color: TEXT_DARK,
      margin: 0,
    });
    s.addText(
      bullets(
        ["Read-only API over Supavisor pooler", "Dash frontend polls every 45s", "airlive.matthiaskoehler.com"],
        { fontSize: 10.5, spaceAfter: 7 }
      ),
      { x: 4.6, y: 2.4, w: 3.05, h: 1.8, valign: "top" }
    );

    card(s, 8.1, 1.75, 4.65, 2.55, { fill: NAVY, line: { type: "none" } });
    s.addText("Two independent stacks, one source of truth", {
      x: 8.4,
      y: 1.95,
      w: 4.05,
      h: 0.55,
      fontFace: TITLE_FONT,
      bold: true,
      fontSize: 14,
      color: WHITE,
      margin: 0,
      lineSpacing: 17,
    });
    s.addText(
      "Both read the same map1 table, built and deployed independently. Scope is deliberately " +
        "positions, aircraft, and airline only — the live States feed carries no origin/" +
        "destination or scheduled times, so no route or delay analytics.",
      {
        x: 8.4,
        y: 2.55,
        w: 4.05,
        h: 1.65,
        fontFace: BODY_FONT,
        fontSize: 11,
        color: TEXT_MUTED_LIGHT,
        margin: 0,
        lineSpacing: 15,
      }
    );

    // dashboard screenshot
    const imgPath = path.join(__dirname, "..", "docs", "images", "dashboard-screenshot.jpg");
    if (fs.existsSync(imgPath)) {
      card(s, 0.6, 4.55, 12.13, 2.55, { line: { type: "none" } });
      s.addImage({ path: imgPath, x: 0.75, y: 4.7, w: 11.83, h: 2.25, sizing: { type: "contain", w: 11.83, h: 2.25 } });
    }
    pageNumber(s, 9);
  }

  // SLIDE 10 — Deployment & Infra
  pillarSlide(
    10,
    "Pillar 4 of 4",
    "Deployment & Infrastructure",
    "FaCloud_WHITE",
    [
      "Every service is one Docker container, one Portainer GitOps stack, auto-pulled from main",
      "Images built once by CI and pushed to GHCR — nothing is ever built on the VM",
      "Cloudflare Tunnel is the only ingress: outbound-only, zero inbound web ports, nginx removed",
      "A full Q (staging) environment, Terraform-managed, mirrors production for PR previews",
    ],
    "GitOps everywhere",
    "0 open ports",
    {
      title: "SECURITY POSTURE",
      body: "With cloudflared handling all public ingress, the only thing reachable from the open internet by IP is SSH — everything else is edge-routed.",
    }
  );

  // SLIDE 11 — Bonus: ML
  {
    const s = pres.addSlide();
    lightBg(s);
    pageHeader(s, "Bonus — Beyond Scope", "ML: Flight Delay Prediction");
    iconCircle(s, "FaBrain_WHITE", W - 1.55, 0.55, 0.85, NAVY);

    s.addText(
      bullets(
        [
          "Built despite the mentor explicitly de-prioritizing ML performance as an evaluation criterion",
          "Kaggle Airlines Delay dataset — 539,382 flights, no missing values",
          "Three candidates compared; HistGradientBoostingClassifier selected on validation ROC-AUC",
          "Shipped as its own live FastAPI service — /predict and /predict/batch, deployed via Portainer",
        ],
        { fontSize: 14.5, spaceAfter: 14 }
      ),
      { x: 0.6, y: 1.85, w: 7.3, h: 4.3, valign: "top" }
    );

    const stats = [
      ["539,382", "training flights"],
      ["0.721", "test ROC-AUC"],
      ["0.667", "test accuracy"],
    ];
    let sx = 8.25;
    for (const [val, label] of stats) {
      card(s, sx, 1.85, 1.42, 1.5, { fill: NAVY, line: { type: "none" } });
      s.addText(val, {
        x: sx,
        y: 2.0,
        w: 1.42,
        h: 0.65,
        align: "center",
        fontFace: TITLE_FONT,
        bold: true,
        fontSize: 20,
        color: CYAN,
        margin: 0,
      });
      s.addText(label, {
        x: sx + 0.08,
        y: 2.68,
        w: 1.26,
        h: 0.6,
        align: "center",
        fontFace: BODY_FONT,
        fontSize: 9,
        color: TEXT_MUTED_LIGHT,
        margin: 0,
        lineSpacing: 11,
      });
      sx += 1.55;
    }

    card(s, 8.25, 3.55, 4.5, 2.6);
    s.addImage({ data: icons.FaFlask_AMBER, x: 8.55, y: 3.78, w: 0.35, h: 0.35 });
    s.addText("HONEST LIMITATION", {
      x: 9.0,
      y: 3.78,
      w: 3.55,
      h: 0.3,
      fontFace: BODY_FONT,
      bold: true,
      fontSize: 11,
      color: AMBER,
      margin: 0,
    });
    s.addText(
      "An ROC-AUC around 0.72 is in line with published results on this dataset: delays are " +
        "driven heavily by factors it doesn't capture — weather, ATC, mechanical issues, " +
        "cascading delays from an aircraft's earlier leg.",
      {
        x: 8.55,
        y: 4.15,
        w: 3.9,
        h: 1.9,
        fontFace: BODY_FONT,
        fontSize: 11,
        color: TEXT_MUTED,
        margin: 0,
        lineSpacing: 15,
      }
    );
    pageNumber(s, 11);
  }

  // ===========================================================================
  // SLIDE 12 — Where We Stand Today
  // ===========================================================================
  {
    const s = pres.addSlide();
    lightBg(s);
    pageHeader(s, "Results", "Where We Stand Today");

    const tiles = [
      ["16", "ADRs documenting every major decision"],
      ["2", "live ingestion sources, dual-stream"],
      ["2", "independent Gold consumption stacks"],
      ["1", "ML service live in production"],
      ["0", "inbound web ports open on either VM"],
      ["1", "full staging environment (Q) for PR previews"],
    ];
    const tw = 3.85,
      th = 2.05,
      gx = 0.35,
      gy = 0.35,
      startX = 0.6,
      startY = 1.85;
    tiles.forEach((t, i) => {
      const col = i % 3,
        row = Math.floor(i / 3);
      const x = startX + col * (tw + gx);
      const y = startY + row * (th + gy);
      card(s, x, y, tw, th, { fill: row === 0 ? NAVY : CARD_BG, line: row === 0 ? { type: "none" } : { color: BORDER, width: 1 } });
      s.addText(t[0], {
        x,
        y: y + 0.2,
        w: tw,
        h: 0.9,
        align: "center",
        fontFace: TITLE_FONT,
        bold: true,
        fontSize: 40,
        color: row === 0 ? CYAN : NAVY,
        margin: 0,
      });
      s.addText(t[1], {
        x: x + 0.35,
        y: y + 1.15,
        w: tw - 0.7,
        h: 0.8,
        align: "center",
        fontFace: BODY_FONT,
        fontSize: 12,
        color: row === 0 ? TEXT_MUTED_LIGHT : TEXT_MUTED,
        margin: 0,
        lineSpacing: 15,
      });
    });
    pageNumber(s, 12);
  }

  // ===========================================================================
  // SLIDE 13 — Next Steps
  // ===========================================================================
  {
    const s = pres.addSlide();
    lightBg(s);
    pageHeader(s, "Conclusion", "Next Steps — Taking It Further");
    iconCircle(s, "FaRocket_WHITE", W - 1.55, 0.55, 0.85, NAVY);

    const roadmap = [
      ["Build the target star schema", "Promote map1 into fact_states + dim_aircraft / dim_airlines / dim_airports, as already designed in ADR 008/009."],
      ["Ship the planned FastAPI", "03-gold/api's /states, /aircraft, /airlines, /airports endpoints are designed but not yet built — the current APIs are narrower, read-only services."],
      ["Route & delay analytics", "Needs a data source with origin/destination and scheduled times — the live States feed doesn't carry them."],
      ["Orchestrated automation", "Move batch scheduling from a Docker sleep-loop toward Airflow as volume and complexity grow."],
      ["Redshift silver-history warehouse", "Chaithra's exploratory draft (PR #33) — a historical analytics store alongside the live Silver table."],
      ["Harden CI/CD", "Broaden automated test coverage and formalize the release pipeline beyond lint + build."],
    ];
    const rw = 5.95,
      rh = 1.35,
      rgx = 0.35,
      rgy = 0.3,
      rsx = 0.6,
      rsy = 1.75;
    roadmap.forEach((r, i) => {
      const col = i % 2,
        row = Math.floor(i / 2);
      const x = rsx + col * (rw + rgx);
      const y = rsy + row * (rh + rgy);
      card(s, x, y, rw, rh);
      s.addShape("ellipse", { x: x + 0.25, y: y + 0.25, w: 0.45, h: 0.45, fill: { color: CYAN_DIM }, line: { type: "none" } });
      s.addText(String(i + 1), {
        x: x + 0.25,
        y: y + 0.25,
        w: 0.45,
        h: 0.45,
        align: "center",
        valign: "middle",
        fontFace: BODY_FONT,
        bold: true,
        fontSize: 14,
        color: WHITE,
        margin: 0,
      });
      s.addText(r[0], {
        x: x + 0.85,
        y: y + 0.15,
        w: rw - 1.1,
        h: 0.35,
        fontFace: BODY_FONT,
        bold: true,
        fontSize: 12.5,
        color: TEXT_DARK,
        margin: 0,
      });
      s.addText(r[1], {
        x: x + 0.85,
        y: y + 0.5,
        w: rw - 1.1,
        h: 0.8,
        fontFace: BODY_FONT,
        fontSize: 10.5,
        color: TEXT_MUTED,
        margin: 0,
        lineSpacing: 13,
      });
    });
    pageNumber(s, 13);
  }

  // ===========================================================================
  // SLIDE 14 — Thank You
  // ===========================================================================
  {
    const s = pres.addSlide();
    darkBg(s);
    radarMotif(s, 2.1, H - 1.7, { rings: [0.7, 1.3, 1.9] });
    s.addImage({ data: icons.FaPlane_CYAN, x: 1.85, y: H - 1.95, w: 0.5, h: 0.5, rotate: -20 });

    s.addText("Thank You", {
      x: 0,
      y: 2.6,
      w: W,
      h: 1.1,
      align: "center",
      fontFace: TITLE_FONT,
      bold: true,
      fontSize: 46,
      color: WHITE,
      margin: 0,
    });
    s.addText("Questions & Live Demo", {
      x: 0,
      y: 3.65,
      w: W,
      h: 0.6,
      align: "center",
      fontFace: BODY_FONT,
      fontSize: 18,
      color: CYAN,
      margin: 0,
    });

    s.addText("airline-dashboard.matthiaskoehler.com   ·   airlive.matthiaskoehler.com", {
      x: 0,
      y: 5.3,
      w: W,
      h: 0.4,
      align: "center",
      fontFace: BODY_FONT,
      fontSize: 13,
      color: TEXT_MUTED_LIGHT,
      margin: 0,
    });
    s.addText("Matthias Köhler   ·   Pavel   ·   Chaithra", {
      x: 0,
      y: 5.75,
      w: W,
      h: 0.4,
      align: "center",
      fontFace: BODY_FONT,
      bold: true,
      fontSize: 13,
      color: WHITE,
      margin: 0,
    });
    pageNumber(s, 14);
  }

  const outPath = path.join(OUT_DIR, "Airline-Data-Platform-Final-Defense.pptx");
  await pres.writeFile({ fileName: outPath });
  console.log("Wrote", outPath);
}

build().catch((e) => {
  console.error(e);
  process.exit(1);
});
