// Builds the "Development + Operating Model" defense segment (Matthias's slides).
// Content: docs/report/project-presentation.md  ·  Design: Pavel's Night-Radar system
// (shared with build_deck.js)  ·  Brand logos used UNCHANGED via lib_logos.js.
// Run: node build_devops_segment.js
//
// These slides are one segment of a larger team deck, so there is deliberately no
// title slide, no closing slide, and no page numbers (they get renumbered on merge).

const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const { loadLogos } = require("./lib_logos");

// ---------------------------------------------------------------------------
// Palette — "Night Radar" (identical to build_deck.js) + spec's semantic colors
// ---------------------------------------------------------------------------
const NAVY = "0B1F3A";
const NAVY_DEEP = "071527";
const STEEL = "1C3D5A";
const STEEL_LIGHT = "2E5A7A";
const CYAN = "4CC9F0";
const CYAN_DIM = "2E8FB0";
const AMBER = "F2A93B";
const WHITE = "FFFFFF";
const OFFWHITE = "F7F9FB";
const CARD_BG = "FFFFFF";
const TEXT_DARK = "0B1F3A";
const TEXT_MUTED = "5A6B7D";
const TEXT_MUTED_LIGHT = "9FB2C6";
const BORDER = "E1E7ED";

// Spec's concept color-coding (§ Visual system):
const PLAN = "5B4FA6";      // project planning & reviewed change — purple
const DATA = "1B8A5A";      // managed data — green
const AWSO = "E8833A";      // AWS compute / IaC — orange
const CI = NAVY;            // CI / artifacts — navy
const QAMBER = "F2A93B";    // Q — amber
const PROD = "2E6DA4";      // production — blue
const EDGE = "F38020";      // Cloudflare / security boundary — orange
const NEXT = "C98A2B";      // future work — darker amber for text on light

const TITLE_FONT = "Cambria";
const BODY_FONT = "Calibri";

const W = 13.33;
const H = 7.5;

// ---------------------------------------------------------------------------
// Generic helpers (ported from build_deck.js, extended)
// ---------------------------------------------------------------------------
function lightBg(slide) {
  slide.background = { color: OFFWHITE };
}

function pageHeader(slide, kicker, title, opts = {}) {
  if (kicker) {
    slide.addText(kicker.toUpperCase(), {
      x: 0.6, y: 0.4, w: W - 1.2, h: 0.3,
      fontFace: BODY_FONT, fontSize: 12, bold: true, color: CYAN_DIM,
      charSpacing: 2, margin: 0,
    });
  }
  slide.addText(title, {
    x: 0.6, y: kicker ? 0.68 : 0.5, w: opts.titleW || W - 1.2, h: 0.7,
    fontFace: TITLE_FONT, fontSize: opts.fontSize || 29, bold: true, color: TEXT_DARK, margin: 0,
  });
}

function card(slide, x, y, w, h, opts = {}) {
  slide.addShape("roundRect", {
    x, y, w, h,
    rectRadius: opts.radius ?? 0.08,
    fill: opts.fill ? { color: opts.fill } : { color: CARD_BG },
    line: opts.line || { color: BORDER, width: 1 },
    shadow: opts.noShadow
      ? undefined
      : { type: "outer", color: "1A2B3D", opacity: opts.shadowOpacity ?? 0.12, blur: 8, offset: 2, angle: 90 },
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

// Rounded "pill" node with centered label.
function pill(slide, x, y, w, h, text, o = {}) {
  slide.addShape("roundRect", {
    x, y, w, h,
    rectRadius: o.radius ?? Math.min(h / 2, 0.1),
    fill: { color: o.fill || CARD_BG },
    line: o.line || { color: o.stroke || BORDER, width: o.strokeW || 1 },
    shadow: o.shadow ? { type: "outer", color: "1A2B3D", opacity: 0.16, blur: 6, offset: 2, angle: 90 } : undefined,
  });
  slide.addText(text, {
    x: x + 0.04, y, w: w - 0.08, h,
    align: "center", valign: "middle",
    fontFace: BODY_FONT, fontSize: o.fontSize || 10.5, bold: o.bold ?? true,
    italic: o.italic, color: o.color || TEXT_DARK, margin: 0, lineSpacing: o.lineSpacing || 12,
  });
}

// Thin horizontal flow arrow.
function hArrow(slide, x, yMid, w, color = CYAN_DIM) {
  slide.addShape("rightArrow", {
    x, y: yMid - 0.07, w, h: 0.14,
    fill: { color }, line: { type: "none" },
  });
}

// Small status/legend dot.
function dot(slide, x, yMid, color, d = 0.16) {
  slide.addShape("ellipse", { x, y: yMid - d / 2, w: d, h: d, fill: { color }, line: { type: "none" } });
}

// Place a brand logo inside a box, preserving aspect ratio (never distorted).
function placeLogo(slide, logo, x, y, boxW, boxH, o = {}) {
  const ar = logo.ar;
  let w = boxW, h = boxW / ar;
  if (h > boxH) { h = boxH; w = boxH * ar; }
  const align = o.align || "center";
  const valign = o.valign || "middle";
  const ox = align === "left" ? x : align === "right" ? x + boxW - w : x + (boxW - w) / 2;
  const oy = valign === "top" ? y : valign === "bottom" ? y + boxH - h : y + (boxH - h) / 2;
  slide.addImage({ data: logo.data, x: ox, y: oy, w, h });
}

// Small caps zone label.
function zoneLabel(slide, x, y, w, text, color, align = "left") {
  slide.addText(text.toUpperCase(), {
    x, y, w, h: 0.28, align,
    fontFace: BODY_FONT, fontSize: 11, bold: true, color, charSpacing: 1.5, margin: 0,
  });
}

// ===========================================================================
async function build() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.author = "Matthias Köhler";
  pres.company = "DataScientest Data Engineer Bootcamp";
  pres.title = "Development + Operating Model — Final Defense segment";

  const L = await loadLogos({
    github: "github.svg",
    mongodb: "mongodb.svg",
    postgresql: "postgresql.svg",
    aws: "aws.svg",
    cloudflare: "cloudflare.png",
    docker: "docker.svg",
    portainer: "portainer.png",
    gitops: "gitops.svg",
    supabase: "supabase.svg",
  });

  // =========================================================================
  // SLIDE 1 — Everything as Code — One Source of Truth
  // =========================================================================
  {
    const s = pres.addSlide();
    lightBg(s);
    pageHeader(
      s,
      "Our working principle · development model + operating model",
      "Everything as Code — One Source of Truth"
    );
    s.addText("From idea to running data product", {
      x: 0.6, y: 1.28, w: W - 1.2, h: 0.35,
      fontFace: BODY_FONT, italic: true, fontSize: 15, color: CYAN_DIM, margin: 0,
    });

    // --- Development band: GitHub system of record (bracket container) ---
    const devY = 2.15, devH = 1.42;
    card(s, 0.6, devY, W - 1.2, devH, { fill: WHITE, line: { color: PLAN, width: 1.25 }, radius: 0.1, shadowOpacity: 0.08 });
    zoneLabel(s, 0.8, devY + 0.12, 6, "Development model · GitHub system of record", PLAN);
    placeLogo(s, L.github, W - 3.15, devY + 0.1, 2.35, 0.34, { align: "right", valign: "middle" });

    const devNodes = ["Project", "Issue", "Branch", "App-code PR", "Q preview", "Review", "main"];
    const drX = 0.85, drW = W - 1.7, drNH = 0.5, drY = devY + 0.62;
    const gap = 0.26;
    const nW = (drW - gap * (devNodes.length - 1)) / devNodes.length;
    devNodes.forEach((label, i) => {
      const nx = drX + i * (nW + gap);
      const hinge = i === devNodes.length - 1;
      pill(s, nx, drY, nW, drNH, label, {
        fill: hinge ? NAVY : OFFWHITE,
        color: hinge ? CYAN : TEXT_DARK,
        stroke: hinge ? NAVY : BORDER,
        strokeW: hinge ? 1.5 : 1,
        fontSize: 10.5, bold: true, shadow: hinge,
      });
      if (i < devNodes.length - 1) hArrow(s, nx + nW + 0.015, drY + drNH / 2, gap - 0.03, PLAN);
    });
    s.addText("Secrets & live telemetry stay outside Git", {
      x: 0.85, y: devY + devH - 0.02, w: 6, h: 0.26,
      fontFace: BODY_FONT, italic: true, fontSize: 10, color: TEXT_MUTED, margin: 0,
    });

    // --- Operating model: three flow lines out of main ---
    const opY = 4.02;
    zoneLabel(s, 0.6, opY, 6, "Operating model · from main to a running system", PROD);
    const opLines = [
      { c: QAMBER, t: "selected PR  →  Actions / GHCR  →  Q  via Portainer API" },
      { c: CI, t: "main  →  Actions  →  GHCR : latest" },
      { c: PROD, t: "production  ←  main config via Portainer  ·  GHCR : latest via Docker" },
    ];
    let oy = opY + 0.34;
    opLines.forEach((ln) => {
      dot(s, 0.66, oy + 0.13, ln.c, 0.14);
      s.addText(ln.t, {
        x: 0.92, y: oy, w: W - 1.6, h: 0.28,
        fontFace: BODY_FONT, fontSize: 12.5, bold: false, color: TEXT_DARK, margin: 0,
      });
      oy += 0.34;
    });

    // --- Data rail (Bronze → ETL → Silver) + infra/edge rail ---
    const dataY = 5.5;
    card(s, 0.6, dataY, W - 1.2, 1.3, { fill: WHITE, line: { color: BORDER, width: 1 }, radius: 0.1, shadowOpacity: 0.08 });
    zoneLabel(s, 0.85, dataY + 0.14, 6, "Running data product", DATA);

    const rY = dataY + 0.5, rH = 0.56;
    placeLogo(s, L.mongodb, 0.9, rY, 0.46, rH);
    pill(s, 1.5, rY, 2.75, rH, "MongoDB Atlas  ·  Bronze", { fill: OFFWHITE, stroke: DATA, color: TEXT_DARK, fontSize: 11 });
    hArrow(s, 4.3, rY + rH / 2, 0.4, DATA);
    pill(s, 4.75, rY, 1.5, rH, "ETL", { fill: NAVY, color: CYAN, stroke: NAVY, fontSize: 11 });
    hArrow(s, 6.3, rY + rH / 2, 0.4, DATA);
    pill(s, 6.75, rY, 2.95, rH, "Supabase Postgres  ·  Silver", { fill: OFFWHITE, stroke: DATA, color: TEXT_DARK, fontSize: 11 });
    placeLogo(s, L.postgresql, 9.75, rY, 0.46, rH);

    // infra/edge rail on the right — marks with captions
    s.addShape("line", { x: 10.5, y: dataY + 0.22, w: 0, h: 0.86, line: { color: BORDER, width: 1 } });
    placeLogo(s, L.aws, 10.72, dataY + 0.3, 0.72, 0.24, { align: "left", valign: "middle" });
    s.addText("Terraform → Q infra", { x: 11.5, y: dataY + 0.28, w: 1.25, h: 0.28, valign: "middle", fontFace: BODY_FONT, fontSize: 8.5, color: TEXT_MUTED, margin: 0, lineSpacing: 10 });
    placeLogo(s, L.cloudflare, 10.72, dataY + 0.72, 0.72, 0.22, { align: "left", valign: "middle" });
    s.addText("Tunnel → edge", { x: 11.5, y: dataY + 0.7, w: 1.25, h: 0.28, valign: "middle", fontFace: BODY_FONT, fontSize: 8.5, color: TEXT_MUTED, margin: 0 });

    // Footer
    s.addText(
      [
        { text: "Plan", options: {} }, { text: "  ·  ", options: { color: CYAN } },
        { text: "review", options: {} }, { text: "  ·  ", options: { color: CYAN } },
        { text: "provision", options: {} }, { text: "  ·  ", options: { color: CYAN } },
        { text: "package", options: {} }, { text: "  ·  ", options: { color: CYAN } },
        { text: "deploy", options: {} }, { text: "  ·  ", options: { color: CYAN } },
        { text: "operate", options: {} },
      ],
      { x: 0.6, y: 6.95, w: W - 1.2, h: 0.35, align: "center", fontFace: BODY_FONT, bold: true, fontSize: 12.5, color: NAVY, margin: 0 }
    );
  }

  // =========================================================================
  // SLIDE 2 — From idea to reviewed change
  // =========================================================================
  {
    const s = pres.addSlide();
    lightBg(s);
    pageHeader(s, "Lightweight project management · engineering control", "From idea to reviewed change");
    placeLogo(s, L.github, W - 2.75, 0.5, 1.95, 0.42, { align: "right", valign: "top" });

    // Proof ribbon
    s.addShape("roundRect", { x: 0.6, y: 1.35, w: 5.1, h: 0.4, rectRadius: 0.2, fill: { color: NAVY }, line: { type: "none" } });
    s.addText("Public GitHub Project  ·  Kanban + Roadmap", {
      x: 0.6, y: 1.35, w: 5.1, h: 0.4, align: "center", valign: "middle",
      fontFace: BODY_FONT, bold: true, fontSize: 12, color: WHITE, margin: 0,
    });

    // --- Kanban board (native, sanitized illustration) ---
    const boardX = 0.6, boardY = 2.05, boardW = 7.35, boardH = 4.05;
    card(s, boardX, boardY, boardW, boardH, { fill: WHITE, radius: 0.08 });
    s.addText("AIRLINE PROJECT", {
      x: boardX + 0.25, y: boardY + 0.16, w: 4, h: 0.28, fontFace: BODY_FONT, bold: true, fontSize: 11, color: TEXT_MUTED, charSpacing: 1, margin: 0,
    });
    // view tabs
    s.addText([
      { text: "Kanban", options: { color: NAVY, bold: true } },
      { text: "   Roadmap", options: { color: TEXT_MUTED_LIGHT } },
    ], { x: boardX + boardW - 2.4, y: boardY + 0.16, w: 2.2, h: 0.28, align: "right", fontFace: BODY_FONT, fontSize: 10.5, margin: 0 });

    const cols = [
      { name: "Ideas", tint: "EEF1F5", cards: ["Redshift history", "Metrics + alerts"] },
      { name: "Todo", tint: "EAF4FB", cards: ["Isolate Q Mongo", "Promote digest"] },
      { name: "In Progress", tint: "FDF3E3", cards: ["Cloudflare → IaC"] },
      { name: "Done", tint: "E9F6EF", cards: ["#15 fallback source", "Cloudflare Tunnel", "Q environment"] },
    ];
    const colGap = 0.2;
    const colW = (boardW - 0.5 - colGap * (cols.length - 1)) / cols.length;
    const colY = boardY + 0.6, colH = boardH - 0.8;
    cols.forEach((c, ci) => {
      const cx = boardX + 0.25 + ci * (colW + colGap);
      s.addShape("roundRect", { x: cx, y: colY, w: colW, h: colH, rectRadius: 0.05, fill: { color: c.tint }, line: { type: "none" } });
      s.addText([
        { text: c.name, options: { bold: true, color: TEXT_DARK } },
        { text: `   ${c.cards.length}`, options: { color: TEXT_MUTED_LIGHT, bold: true } },
      ], { x: cx + 0.12, y: colY + 0.1, w: colW - 0.24, h: 0.26, fontFace: BODY_FONT, fontSize: 10, margin: 0 });
      let cy = colY + 0.46;
      c.cards.forEach((card_, idx) => {
        const done = c.name === "Done";
        const highlight = card_.startsWith("#15");
        s.addShape("roundRect", {
          x: cx + 0.12, y: cy, w: colW - 0.24, h: 0.52, rectRadius: 0.05,
          fill: { color: WHITE },
          line: highlight ? { color: CYAN_DIM, width: 1.5 } : { color: BORDER, width: 0.75 },
          shadow: { type: "outer", color: "1A2B3D", opacity: 0.08, blur: 3, offset: 1, angle: 90 },
        });
        dot(s, cx + 0.26, cy + 0.26, done ? DATA : highlight ? CYAN_DIM : TEXT_MUTED_LIGHT, 0.12);
        s.addText(card_, {
          x: cx + 0.4, y: cy, w: colW - 0.52, h: 0.52, valign: "middle",
          fontFace: BODY_FONT, fontSize: 8.8, color: TEXT_DARK, margin: 0, lineSpacing: 10,
        });
        cy += 0.62;
      });
    });

    // --- Evidence stack (right) ---
    const evX = 8.25, evW = 4.5;
    // TRACE chip
    card(s, evX, 2.05, evW, 1.9, { fill: WHITE, radius: 0.08 });
    s.addText([{ text: "TRACE", options: { color: PLAN, bold: true } }], { x: evX + 0.25, y: 2.22, w: evW - 0.5, h: 0.28, fontFace: BODY_FONT, fontSize: 11, charSpacing: 1, margin: 0 });
    s.addText("Board-to-change traceability", { x: evX + 0.25, y: 2.48, w: evW - 0.5, h: 0.28, fontFace: BODY_FONT, fontSize: 12.5, bold: true, color: TEXT_DARK, margin: 0 });
    // mini flow
    const tY = 3.02;
    pill(s, evX + 0.25, tY, 1.15, 0.44, "Issue #15", { fill: OFFWHITE, stroke: BORDER, fontSize: 10 });
    hArrow(s, evX + 1.42, tY + 0.22, 0.3, PLAN);
    pill(s, evX + 1.75, tY, 1.1, 0.44, "PR #20", { fill: OFFWHITE, stroke: BORDER, fontSize: 10 });
    hArrow(s, evX + 2.87, tY + 0.22, 0.3, PLAN);
    pill(s, evX + 3.2, tY, 1.05, 0.44, "Done", { fill: "E9F6EF", stroke: DATA, color: DATA, fontSize: 10 });
    s.addText("assignment · Todo → In Progress → Done · linked, merged to main", {
      x: evX + 0.25, y: tY + 0.52, w: evW - 0.5, h: 0.34, fontFace: BODY_FONT, italic: true, fontSize: 9.5, color: TEXT_MUTED, margin: 0, lineSpacing: 12,
    });

    // REVIEW chip
    card(s, evX, 4.2, evW, 1.9, { fill: NAVY, radius: 0.08, line: { type: "none" } });
    s.addText([{ text: "REVIEW", options: { color: CYAN, bold: true } }], { x: evX + 0.25, y: 4.37, w: evW - 0.5, h: 0.28, fontFace: BODY_FONT, fontSize: 11, charSpacing: 1, margin: 0 });
    s.addText("Second-person review is team policy (ADR 012)", { x: evX + 0.25, y: 4.63, w: evW - 0.5, h: 0.3, fontFace: BODY_FONT, fontSize: 12, bold: true, color: WHITE, margin: 0 });
    const rY2 = 5.17;
    pill(s, evX + 0.25, rY2, 1.0, 0.44, "PR #9", { fill: STEEL, stroke: STEEL, color: WHITE, fontSize: 10 });
    hArrow(s, evX + 1.27, rY2 + 0.22, 0.22, CYAN);
    pill(s, evX + 1.51, rY2, 1.2, 0.44, "changes\nrequested", { fill: "3A2E1A", stroke: QAMBER, color: QAMBER, fontSize: 8.5, lineSpacing: 9.5 });
    hArrow(s, evX + 2.73, rY2 + 0.22, 0.22, CYAN);
    pill(s, evX + 2.97, rY2, 0.95, 0.44, "approved", { fill: "16332A", stroke: DATA, color: "6FD0A0", fontSize: 9 });
    hArrow(s, evX + 3.94, rY2 + 0.22, 0.18, CYAN);
    pill(s, evX + 4.14, rY2, 0.11, 0.44, "", { fill: CYAN, stroke: CYAN });
    s.addText("changes requested → corrected → approved → merged", {
      x: evX + 0.25, y: rY2 + 0.52, w: evW - 0.5, h: 0.3, fontFace: BODY_FONT, italic: true, fontSize: 9.5, color: TEXT_MUTED_LIGHT, margin: 0,
    });

    // Footer
    s.addText("Visible work  →  linked change  →  reviewed merge", {
      x: 0.6, y: 6.55, w: 7.35, h: 0.35, align: "center",
      fontFace: BODY_FONT, bold: true, fontSize: 12.5, color: NAVY, margin: 0,
    });
  }

  // =========================================================================
  // SLIDE 3 — Application-code PRs become running Q previews  (HERO)
  // =========================================================================
  {
    const s = pres.addSlide();
    lightBg(s);
    pageHeader(s, "The delivery flow · CI · CD · git-driven ops", "Application-code PRs become running Q previews");

    // --- CI band (top, full width) ---
    const ciY = 1.5, bandH = 1.15;
    s.addShape("roundRect", { x: 0.6, y: ciY, w: W - 1.2, h: bandH, rectRadius: 0.08, fill: { color: "0B1F3A" }, line: { type: "none" } });
    s.addText([{ text: "CI", options: { color: CYAN, bold: true } }, { text: "   build & publish container images", options: { color: TEXT_MUTED_LIGHT } }], {
      x: 0.8, y: ciY + 0.1, w: 6, h: 0.26, fontFace: BODY_FONT, fontSize: 10.5, charSpacing: 1, margin: 0,
    });
    const ciNodes = ["feature branch", "PR · app paths", "Actions build", "GHCR : pr-N + sha-*"];
    const ciNX = 0.85, ciNW_total = W - 1.7, ciNH = 0.5, ciNY = ciY + 0.5;
    const cg = 0.3;
    const ciW = (ciNW_total - cg * (ciNodes.length - 1)) / ciNodes.length;
    ciNodes.forEach((label, i) => {
      const nx = ciNX + i * (ciW + cg);
      pill(s, nx, ciNY, ciW, ciNH, label, { fill: STEEL, stroke: STEEL_LIGHT, color: WHITE, fontSize: 10 });
      if (i < ciNodes.length - 1) hArrow(s, nx + ciW + 0.02, ciNY + ciNH / 2, cg - 0.04, CYAN);
    });
    // small marks on CI band
    placeLogo(s, L.github, 9.9, ciY + 0.12, 1.15, 0.26, { align: "right", valign: "top" });
    placeLogo(s, L.docker, 11.2, ciY + 0.12, 1.4, 0.26, { align: "right", valign: "top" });

    // --- Q lane (amber) ---
    const qY = 3.15, laneH = 1.05;
    s.addShape("roundRect", { x: 0.6, y: qY, w: W - 1.2, h: laneH, rectRadius: 0.08, fill: { color: "FBF1DE" }, line: { color: QAMBER, width: 1 } });
    s.addText([{ text: "CD", options: { color: NEXT, bold: true } }, { text: "   API-triggered Q deployment", options: { color: TEXT_MUTED } }], {
      x: 0.8, y: qY + 0.1, w: 6, h: 0.26, fontFace: BODY_FONT, fontSize: 10.5, charSpacing: 1, margin: 0,
    });
    const qNodes = ["pr-N image tag", "Portainer API", "Q Compose stacks", "q_map1"];
    const qNY = qY + 0.48, qNH = 0.46;
    const qStartX = 0.9, qTotalW = 8.0;
    const qW = (qTotalW - cg * (qNodes.length - 1)) / qNodes.length;
    qNodes.forEach((label, i) => {
      const nx = qStartX + i * (qW + cg);
      const isDb = label === "q_map1";
      pill(s, nx, qNY, qW, qNH, label, { fill: isDb ? "E9F6EF" : WHITE, stroke: isDb ? DATA : QAMBER, color: isDb ? DATA : TEXT_DARK, fontSize: 9.5, italic: isDb });
      if (i < qNodes.length - 1) hArrow(s, nx + qW + 0.02, qNY + qNH / 2, cg - 0.04, NEXT);
    });
    placeLogo(s, L.portainer, 3.35, qY + 0.05, 0.3, 0.3, { align: "left", valign: "top" });
    // honesty annotation Q
    s.addText("⚠ Q MongoDB is shared with production", {
      x: 9.15, y: qY + 0.34, w: 3.5, h: 0.5, valign: "middle",
      fontFace: BODY_FONT, italic: true, fontSize: 10, color: NEXT, margin: 0, lineSpacing: 12,
    });

    // gate between lanes: review + squash merge
    s.addText("review the running Q system + approve   →   squash-merge   →   main build : latest + sha-*", {
      x: 0.6, y: qY + laneH + 0.08, w: W - 1.2, h: 0.3, align: "center",
      fontFace: BODY_FONT, bold: true, italic: true, fontSize: 11, color: PLAN, margin: 0,
    });

    // --- Production lane (blue) ---
    const pY = 4.98;
    s.addShape("roundRect", { x: 0.6, y: pY, w: W - 1.2, h: laneH, rectRadius: 0.08, fill: { color: "EAF1F8" }, line: { color: PROD, width: 1 } });
    s.addText([{ text: "GIT-DRIVEN OPS", options: { color: PROD, bold: true } }, { text: "   Portainer polls main configuration", options: { color: TEXT_MUTED } }], {
      x: 0.8, y: pY + 0.1, w: 6.5, h: 0.26, fontFace: BODY_FONT, fontSize: 10.5, charSpacing: 1, margin: 0,
    });
    const pNodes = ["GHCR : latest", "Portainer Git polling", "production stacks", "map1"];
    const pNY = pY + 0.48, pNH = 0.46;
    const pW = (qTotalW - cg * (pNodes.length - 1)) / pNodes.length;
    pNodes.forEach((label, i) => {
      const nx = qStartX + i * (pW + cg);
      const isDb = label === "map1";
      pill(s, nx, pNY, pW, pNH, label, { fill: isDb ? "E9F6EF" : WHITE, stroke: isDb ? DATA : PROD, color: isDb ? DATA : TEXT_DARK, fontSize: 9.5, italic: isDb });
      if (i < pNodes.length - 1) hArrow(s, nx + pW + 0.02, pNY + pNH / 2, cg - 0.04, PROD);
    });
    placeLogo(s, L.gitops, 4.75, pY + 0.06, 0.44, 0.28, { align: "left", valign: "top" });
    s.addText("⚠ Rebuild after merge; no sequenced production deploy job", {
      x: 9.15, y: pY + 0.34, w: 3.5, h: 0.5, valign: "middle",
      fontFace: BODY_FONT, italic: true, fontSize: 10, color: PROD, margin: 0, lineSpacing: 12,
    });

    // workflow-filter honesty note + bottom callout
    s.addText("⚠ Workflow filters: selected application / Dockerfile / build-workflow paths — Compose, Portainer, docs & Terraform-only changes get no pre-merge Q preview", {
      x: 0.6, y: pY + laneH + 0.1, w: 8.3, h: 0.5, valign: "middle",
      fontFace: BODY_FONT, italic: true, fontSize: 9.5, color: TEXT_MUTED, margin: 0, lineSpacing: 12,
    });
    s.addShape("roundRect", { x: 9.05, y: pY + laneH + 0.1, w: 3.68, h: 0.62, rectRadius: 0.08, fill: { color: NAVY }, line: { type: "none" } });
    s.addText("The VMs pull images;\nthey never build application code.", {
      x: 9.05, y: pY + laneH + 0.1, w: 3.68, h: 0.62, align: "center", valign: "middle",
      fontFace: BODY_FONT, bold: true, fontSize: 11, color: CYAN, margin: 0, lineSpacing: 13,
    });
  }

  // =========================================================================
  // SLIDE 4 — Code-defined boundaries reduce operational risk
  // =========================================================================
  {
    const s = pres.addSlide();
    lightBg(s);
    pageHeader(s, "Infrastructure ownership · SecOps", "Code-defined boundaries reduce operational risk");

    const cardY = 1.55, cardW = 3.9, cardH = 3.1, cgap = 0.28;
    const cxs = [0.6, 0.6 + cardW + cgap, 0.6 + 2 * (cardW + cgap)];
    const boundaries = [
      {
        tag: "PROVISION", tagColor: AWSO, tool: "Terraform + AWS API",
        detail: "Q VM · static IP · firewall", logo: "aws",
        note: "Terraform owns Q only. Production VM predates this IaC boundary.",
      },
      {
        tag: "RUN", tagColor: NAVY, tool: "Portainer + Compose",
        detail: "Pull GHCR images · configure · restart · observe", logo: "portainer",
        note: "A VM only pulls images; builds live in CI, never on a host.",
      },
      {
        tag: "EDGE", tagColor: EDGE, tool: "Cloudflare Tunnel",
        detail: "Outbound-only ingress · API / dashboard rules", logo: "cloudflare",
        note: "Removes inbound HTTP/HTTPS + VM-side TLS. Routing is remote API state.",
      },
    ];
    boundaries.forEach((b, i) => {
      const x = cxs[i];
      card(s, x, cardY, cardW, cardH, { fill: WHITE, radius: 0.08 });
      // header strip
      s.addShape("roundRect", { x, y: cardY, w: cardW, h: 0.5, rectRadius: 0.08, fill: { color: b.tagColor }, line: { type: "none" } });
      s.addShape("rect", { x, y: cardY + 0.25, w: cardW, h: 0.25, fill: { color: b.tagColor }, line: { type: "none" } });
      s.addText(b.tag, { x: x + 0.2, y: cardY, w: cardW - 0.4, h: 0.5, valign: "middle", fontFace: BODY_FONT, bold: true, fontSize: 14, color: WHITE, charSpacing: 2, margin: 0 });
      // logo / text tile
      if (b.logo === "aws") {
        placeLogo(s, L.aws, x + 0.3, cardY + 0.7, cardW - 0.6, 0.55, { align: "left" });
        // Terraform text tile
        s.addShape("roundRect", { x: x + 0.3, y: cardY + 1.34, w: 1.75, h: 0.4, rectRadius: 0.06, fill: { color: "EEEAF6" }, line: { color: PLAN, width: 1 } });
        s.addText("Terraform", { x: x + 0.3, y: cardY + 1.34, w: 1.75, h: 0.4, align: "center", valign: "middle", fontFace: BODY_FONT, bold: true, fontSize: 11, color: PLAN, margin: 0 });
      } else if (b.logo === "portainer") {
        placeLogo(s, L.portainer, x + 0.3, cardY + 0.72, 0.5, 0.5, { align: "left" });
        placeLogo(s, L.docker, x + 1.0, cardY + 0.72, 1.9, 0.5, { align: "left" });
      } else {
        placeLogo(s, L.cloudflare, x + 0.3, cardY + 0.78, 2.4, 0.42, { align: "left" });
      }
      s.addText(b.tool, { x: x + 0.3, y: cardY + 1.86, w: cardW - 0.6, h: 0.3, fontFace: BODY_FONT, bold: true, fontSize: 12.5, color: TEXT_DARK, margin: 0 });
      s.addText(b.detail, { x: x + 0.3, y: cardY + 2.16, w: cardW - 0.6, h: 0.5, fontFace: BODY_FONT, fontSize: 10.5, color: TEXT_MUTED, margin: 0, lineSpacing: 13 });
      // divider + per-boundary honesty note in the lower card space
      s.addShape("line", { x: x + 0.3, y: cardY + 2.62, w: cardW - 0.6, h: 0, line: { color: BORDER, width: 0.75 } });
      s.addText(b.note, { x: x + 0.3, y: cardY + 2.7, w: cardW - 0.6, h: 0.35, fontFace: BODY_FONT, italic: true, fontSize: 9.5, color: TEXT_MUTED, margin: 0, lineSpacing: 12 });
      // connector arrow between cards
      if (i < boundaries.length - 1) {
        s.addShape("rightArrow", { x: x + cardW + 0.02, y: cardY + cardH / 2 - 0.1, w: cgap - 0.04, h: 0.2, fill: { color: CYAN_DIM }, line: { type: "none" } });
      }
    });

    // sequence note under cards
    s.addText("Terraform  —AWS API→  Q Lightsail   ·   manual trust bootstrap → Portainer / Compose   ·   containers  —outbound tunnel→  Cloudflare edge → users", {
      x: 0.6, y: cardY + cardH + 0.12, w: W - 1.2, h: 0.3, align: "center",
      fontFace: BODY_FONT, italic: true, fontSize: 10, color: TEXT_MUTED, margin: 0,
    });

    // Security strip (navy) + known-gaps panel (amber) + operator note below
    const secY = 5.2, secH = 1.5;
    s.addShape("roundRect", { x: 0.6, y: secY, w: 8.15, h: secH, rectRadius: 0.08, fill: { color: NAVY }, line: { type: "none" } });
    s.addText("SECURITY POSTURE", { x: 0.85, y: secY + 0.16, w: 5, h: 0.26, fontFace: BODY_FONT, bold: true, fontSize: 11, color: CYAN, charSpacing: 1.5, margin: 0 });
    const sec = [
      "No secrets in Git or Lightsail user data",
      "Zero inbound web ports (SSH remains)",
      "Scoped image-build permissions",
    ];
    let sy = secY + 0.55;
    sec.forEach((t) => {
      dot(s, 0.9, sy + 0.13, CYAN, 0.14);
      s.addText(t, { x: 1.15, y: sy, w: 7.4, h: 0.28, fontFace: BODY_FONT, fontSize: 11.5, color: WHITE, margin: 0 });
      sy += 0.3;
    });

    // Known gaps (amber exception panel)
    const gX = 8.95;
    s.addShape("roundRect", { x: gX, y: secY, w: W - 0.6 - gX, h: secH, rectRadius: 0.08, fill: { color: "FBF1DE" }, line: { color: QAMBER, width: 1.25 } });
    s.addText("⚠ KNOWN GAPS", { x: gX + 0.22, y: secY + 0.16, w: 3.3, h: 0.26, fontFace: BODY_FONT, bold: true, fontSize: 11, color: NEXT, charSpacing: 1, margin: 0 });
    s.addText(
      bullets([
        "Production VM + Cloudflare routing outside IaC",
        "Atlas permits all source IPs (0.0.0.0/0)",
      ], { fontSize: 10.5, color: TEXT_DARK, bulletColor: NEXT, spaceAfter: 8 }),
      { x: gX + 0.22, y: secY + 0.52, w: W - 0.6 - gX - 0.44, h: 0.85, valign: "top" }
    );

    // Operator note — full width, below both panels
    s.addText("AWS CLI = authenticated inspection capability, not a deployment engine", {
      x: 0.6, y: secY + secH + 0.12, w: W - 1.2, h: 0.28, align: "center",
      fontFace: BODY_FONT, italic: true, fontSize: 10.5, color: TEXT_MUTED, margin: 0,
    });
  }

  // =========================================================================
  // SLIDE 5 — Operational proof today, hardening path tomorrow
  // =========================================================================
  {
    const s = pres.addSlide();
    lightBg(s);
    pageHeader(s, "Day-two operations · honest limits", "Operational proof today, hardening path tomorrow");

    const colY = 1.65, colH = 3.7, colW = 5.95, colGap = 0.43;
    const leftX = 0.6, rightX = leftX + colW + colGap;

    // Left column — OPERATES TODAY
    card(s, leftX, colY, colW, colH, { fill: WHITE, radius: 0.08 });
    s.addShape("roundRect", { x: leftX, y: colY, w: colW, h: 0.62, rectRadius: 0.08, fill: { color: NAVY }, line: { type: "none" } });
    s.addShape("rect", { x: leftX, y: colY + 0.3, w: colW, h: 0.32, fill: { color: NAVY }, line: { type: "none" } });
    // heartbeat polyline behind heading
    const hbPts = [[0.2, 0.31], [0.55, 0.31], [0.7, 0.12], [0.85, 0.5], [1.0, 0.31], [1.25, 0.31]];
    s.addShape("line", { x: leftX + 3.2, y: colY + 0.31, w: colW - 3.4, h: 0, line: { color: STEEL_LIGHT, width: 1, dashType: "solid" } });
    s.addText("OPERATES TODAY", { x: leftX + 0.25, y: colY, w: 4, h: 0.62, valign: "middle", fontFace: BODY_FONT, bold: true, fontSize: 14, color: WHITE, charSpacing: 1.5, margin: 0 });
    const today = [
      "ETL heartbeat + API health checks",
      "Restart policies + local container logs",
      "Independent Bronze / Silver lifecycles",
      "Separate production / Q compute",
    ];
    let ty = colY + 0.9;
    today.forEach((t) => {
      s.addShape("ellipse", { x: leftX + 0.3, y: ty + 0.02, w: 0.26, h: 0.26, fill: { color: "E9F6EF" }, line: { color: DATA, width: 1 } });
      s.addText("✓", { x: leftX + 0.3, y: ty + 0.02, w: 0.26, h: 0.26, align: "center", valign: "middle", fontFace: BODY_FONT, bold: true, fontSize: 12, color: DATA, margin: 0 });
      s.addText(t, { x: leftX + 0.72, y: ty, w: colW - 1.0, h: 0.3, valign: "middle", fontFace: BODY_FONT, fontSize: 12.5, color: TEXT_DARK, margin: 0 });
      ty += 0.66;
    });

    // Right column — NEXT HARDENING STEPS
    card(s, rightX, colY, colW, colH, { fill: "FCF6EA", radius: 0.08, line: { color: QAMBER, width: 1.25 } });
    s.addShape("roundRect", { x: rightX, y: colY, w: colW, h: 0.62, rectRadius: 0.08, fill: { color: QAMBER }, line: { type: "none" } });
    s.addShape("rect", { x: rightX, y: colY + 0.3, w: colW, h: 0.32, fill: { color: QAMBER }, line: { type: "none" } });
    s.addText("NEXT HARDENING STEPS", { x: rightX + 0.25, y: colY, w: 5, h: 0.62, valign: "middle", fontFace: BODY_FONT, bold: true, fontSize: 14, color: NAVY, charSpacing: 1.5, margin: 0 });
    const next = [
      "Unit, lint, image-scan & SBOM gates in CI",
      "Promote the tested image digest after merge",
      "Central metrics, alerts & log aggregation",
      "Isolate Q MongoDB; Cloudflare + prod under IaC",
    ];
    let ny = colY + 0.9;
    next.forEach((t, i) => {
      s.addShape("roundRect", { x: rightX + 0.3, y: ny + 0.01, w: 0.42, h: 0.28, rectRadius: 0.05, fill: { color: WHITE }, line: { color: NEXT, width: 1 } });
      s.addText(String(i + 1), { x: rightX + 0.3, y: ny + 0.01, w: 0.42, h: 0.28, align: "center", valign: "middle", fontFace: BODY_FONT, bold: true, fontSize: 11, color: NEXT, margin: 0 });
      s.addText(t, { x: rightX + 0.85, y: ny, w: colW - 1.15, h: 0.3, valign: "middle", fontFace: BODY_FONT, fontSize: 12.5, color: TEXT_DARK, margin: 0 });
      ny += 0.66;
    });
    // feedback loop card
    s.addText("gaps return to the visible GitHub Project ↩", {
      x: rightX + 0.3, y: colY + colH - 0.42, w: colW - 0.6, h: 0.3, align: "right",
      fontFace: BODY_FONT, italic: true, bold: true, fontSize: 10.5, color: PLAN, margin: 0,
    });

    // Decision note
    s.addShape("roundRect", { x: 0.6, y: 5.55, w: W - 1.2, h: 0.62, rectRadius: 0.08, fill: { color: "EEF1F5" }, line: { color: BORDER, width: 1 } });
    s.addText(
      [
        { text: "Architectural judgment:  ", options: { bold: true, color: NAVY } },
        { text: "Docker Compose is sufficient at this scale — Kubernetes would add an operations platform before the project needs one.", options: { color: TEXT_DARK } },
      ],
      { x: 0.85, y: 5.55, w: W - 1.7, h: 0.62, valign: "middle", fontFace: BODY_FONT, fontSize: 12, margin: 0, lineSpacing: 15 }
    );

    // Final takeaway band
    s.addShape("roundRect", { x: 0.6, y: 6.35, w: W - 1.2, h: 0.72, rectRadius: 0.08, fill: { color: NAVY }, line: { type: "none" } });
    s.addText("Everything as Code — One Source of Truth.", {
      x: 0.6, y: 6.35, w: W - 1.2, h: 0.72, align: "center", valign: "middle",
      fontFace: TITLE_FONT, bold: true, fontSize: 20, color: WHITE, margin: 0,
    });
  }

  // =========================================================================
  // SLIDE 6 — Curriculum alignment
  // =========================================================================
  {
    const s = pres.addSlide();
    lightBg(s);
    pageHeader(s, "Why this segment belongs in the defense", "Course curriculum, proven by project evidence");

    const rows = [
      { sprint: "Sprint 3", area: "SQL & MongoDB", evidence: "MongoDB Atlas Bronze + Supabase Postgres Silver", color: DATA, logos: ["mongodb", "postgresql"] },
      { sprint: "Sprint 5", area: "ETL & AWS Cloud Practitioner", evidence: "Managed data services + AWS Lightsail compute", color: AWSO, logos: ["aws"] },
      { sprint: "Sprint 7", area: "DevOps / isolation", evidence: "Docker · FastAPI health endpoints · env separation · API security", color: PROD, logos: ["docker"] },
      { sprint: "Sprint 8", area: "CI/CD", evidence: "GitHub Actions · GHCR · PR previews · release flow", color: NAVY, logos: ["github"] },
      { sprint: "Sprint 9", area: "Monitoring & Terraform", evidence: "Health checks · restart/logging policy · Terraform-managed Q infra", color: PLAN, logos: [], tile: "Terraform" },
    ];
    const tX = 0.6, tY = 1.6, tW = W - 1.2;
    const rH = 0.82, rGap = 0.12;
    rows.forEach((r, i) => {
      const y = tY + i * (rH + rGap);
      card(s, tX, y, tW, rH, { fill: WHITE, radius: 0.06, shadowOpacity: 0.08 });
      // sprint chip
      s.addShape("roundRect", { x: tX + 0.2, y: y + 0.19, w: 1.35, h: 0.44, rectRadius: 0.08, fill: { color: r.color }, line: { type: "none" } });
      s.addText(r.sprint, { x: tX + 0.2, y: y + 0.19, w: 1.35, h: 0.44, align: "center", valign: "middle", fontFace: BODY_FONT, bold: true, fontSize: 11.5, color: WHITE, margin: 0 });
      // area
      s.addText(r.area, { x: tX + 1.75, y, w: 3.15, h: rH, valign: "middle", fontFace: BODY_FONT, bold: true, fontSize: 13, color: TEXT_DARK, margin: 0, lineSpacing: 15 });
      // divider
      s.addShape("line", { x: tX + 4.95, y: y + 0.16, w: 0, h: rH - 0.32, line: { color: BORDER, width: 1 } });
      // evidence
      s.addText(r.evidence, { x: tX + 5.15, y, w: tW - 5.15 - 1.5, h: rH, valign: "middle", fontFace: BODY_FONT, fontSize: 11.5, color: TEXT_MUTED, margin: 0, lineSpacing: 14 });
      // logos on the right (or a text tile where no official mark exists, e.g. Terraform)
      const boxX = tX + tW - 1.35;
      r.logos.forEach((lg, li) => {
        placeLogo(s, L[lg], boxX + li * 0.62, y + 0.19, 0.55, 0.44, { align: "center" });
      });
      if (r.tile) {
        const tileX = tX + tW - 1.55;
        s.addShape("roundRect", { x: tileX, y: y + 0.21, w: 1.35, h: 0.4, rectRadius: 0.06, fill: { color: "EEEAF6" }, line: { color: PLAN, width: 1 } });
        s.addText(r.tile, { x: tileX, y: y + 0.21, w: 1.35, h: 0.4, align: "center", valign: "middle", fontFace: BODY_FONT, bold: true, fontSize: 11, color: PLAN, margin: 0 });
      }
    });

    // honest note
    s.addShape("roundRect", { x: 0.6, y: 6.35, w: W - 1.2, h: 0.72, rectRadius: 0.08, fill: { color: "FBF1DE" }, line: { color: QAMBER, width: 1 } });
    s.addText(
      [
        { text: "⚠ Shown honestly:  ", options: { bold: true, color: NEXT } },
        { text: "Kubernetes · Prometheus · Grafana are course topics but ", options: { color: TEXT_DARK } },
        { text: "not implemented", options: { bold: true, color: TEXT_DARK } },
        { text: " here — stated plainly, not hidden behind a technology logo wall.", options: { color: TEXT_DARK } },
      ],
      { x: 0.85, y: 6.35, w: W - 1.7, h: 0.72, valign: "middle", fontFace: BODY_FONT, fontSize: 11.5, margin: 0, lineSpacing: 15 }
    );
  }

  // -------------------------------------------------------------------------
  const outPath = path.join(__dirname, "..", "docs", "report", "imnput other", "development-operating-model.pptx");
  await pres.writeFile({ fileName: outPath });
  console.log("Wrote", outPath);
}

build().catch((e) => { console.error(e); process.exit(1); });
