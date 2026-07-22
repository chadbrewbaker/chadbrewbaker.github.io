// rr.js — a small railroad-diagram compiler after Chiplunkar & Pit-Claudel,
// "Automatic layout of railroad diagrams" (arXiv:2509.15834).
// Diagram language (their Fig. 6): "term"  [nonterm]  (d ...)  (+ d d)  (- d d)
// This is a deliberately small subset of their system: greedy first-fit
// wrapping toward a target width (not their preference-ordered optimization),
// default tips only, nested positive stacks flattened for rendering (their
// Fig. 7b collapse). DOM-free: parse(dsl) -> AST, layout(ast, width) -> SVG.
'use strict';

// ---------------- DSL parser ----------------
function parse(src) {
  let i = 0;
  const err = m => { throw new Error(m + ' (at offset ' + i + ': "' + src.slice(i, i + 12) + '")'); };
  const ws = () => { while (i < src.length && /[\s,]/.test(src[i])) i++; };
  function node() {
    ws();
    const c = src[i];
    if (c === undefined) err('unexpected end of input');
    if (c === '"') {
      const j = src.indexOf('"', i + 1);
      if (j < 0) err('unterminated string');
      const label = src.slice(i + 1, j); i = j + 1;
      return { t: 'term', label };
    }
    if (c === '[') {
      const j = src.indexOf(']', i + 1);
      if (j < 0) err('unterminated [nonterminal]');
      const label = src.slice(i + 1, j); i = j + 1;
      return { t: 'nonterm', label };
    }
    if (c === '(') {
      i++; ws();
      if (src[i] === '+' || src[i] === '-') {
        const pol = src[i]; i++;
        const subs = [];
        for (;;) { ws(); if (src[i] === ')') { i++; break; } subs.push(node()); }
        if (subs.length < 2) err('stack (' + pol + ' ...) needs at least two subdiagrams');
        // n-ary convenience: fold to binary, right-associated (paper: stacks are binary)
        let d = subs[subs.length - 1];
        for (let k = subs.length - 2; k >= 0; k--) d = { t: 'stack', pol, top: subs[k], bottom: d };
        return d;
      }
      const items = [];
      for (;;) { ws(); if (src[i] === ')') { i++; break; } if (src[i] === undefined) err('unclosed ('); items.push(node()); }
      return { t: 'seq', items };
    }
    err('expected "term", [nonterm], or (');
  }
  const d = node(); ws();
  if (i < src.length) err('trailing input');
  return d;
}

// ---------------- geometry constants ----------------
const S = 10;          // unit width around curves (paper §2.3)
const CW = 7.85;       // monospace char width at 13px
const PAD = 9;         // text padding inside stations
const BH = 26;         // station height
const GAP = 10;        // rail between items in a row
const VGAP = 9;        // vertical gap between stack branches
const WRAPCH = 16;     // height of the wrap channel between rows

// ---------------- measurement + layout ----------------
// Each layout node returns { w, h, ey, draw(x, y, out) } where ey is the
// y-offset of the entry/exit rail (equal on both sides in this subset) and
// draw emits SVG with the node's top-left at (x, y + something)... concretely
// draw(x, railY, out): x = left edge, railY = absolute y of the entry rail.
function station(label, terminal) {
  const w = Math.max(2, label.length) * CW + 2 * PAD;
  return {
    w: w + 2 * S, h: BH, ey: BH / 2, minw: w + 2 * S,
    draw(x, railY, out) {
      const bx = x + S, by = railY - BH / 2;
      out.push(`<path d="M ${x} ${railY} h ${S}" class="rail"/>`);
      out.push(`<rect x="${bx}" y="${by}" width="${w}" height="${BH}" rx="${terminal ? BH / 2 : 3}" class="${terminal ? 'term' : 'nonterm'}"/>`);
      out.push(`<text x="${bx + w / 2}" y="${railY}" class="lbl${terminal ? '' : ' nt'}">${esc(label)}</text>`);
      out.push(`<path d="M ${bx + w} ${railY} h ${S}" class="rail"/>`);
    }
  };
}
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function epsilon() {
  return { w: 2 * S, h: 2, ey: 1, minw: 2 * S,
    draw(x, railY, out) { out.push(`<path d="M ${x} ${railY} h ${2 * S}" class="rail"/>`); } };
}

// flatten chains of positive stacks for rendering (paper Fig. 7b)
function flattenChoice(d) {
  if (d.t === 'stack' && d.pol === '+')
    return [...flattenChoice(d.top), ...flattenChoice(d.bottom)];
  return [d];
}

function layout(d, targetW) {
  if (d.t === 'term') return station(d.label, true);
  if (d.t === 'nonterm') return station(d.label, false);
  if (d.t === 'seq') return seqLayout(d.items.map(x => layout(x, targetW)), targetW, d.items.length === 0);
  if (d.t === 'stack' && d.pol === '+') return choiceLayout(flattenChoice(d).map(x => layout(x, targetW)));
  if (d.t === 'stack' && d.pol === '-') return loopLayout(layout(d.top, targetW), layout(d.bottom, targetW));
  throw new Error('unknown node');
}

function choiceLayout(branches) {
  const W = Math.max(...branches.map(b => b.w));
  const w = W + 4 * S;
  let y = 0;
  const rows = branches.map(b => { const railY = y + b.ey; y += b.h + VGAP; return railY; });
  const h = y - VGAP;
  return {
    w, h, ey: rows[0], minw: w,
    draw(x, railY, out) {
      const top = railY - rows[0];
      const xL = x + S, xR = x + w - S;
      for (let i = 0; i < branches.length; i++) {
        const b = branches[i], by = top + rows[i];
        const bx = x + 2 * S + (W - b.w) / 2;
        if (i === 0) {
          out.push(`<path d="M ${x} ${railY} h ${2 * S}" class="rail"/>`);
          out.push(`<path d="M ${x + w - 2 * S} ${railY} h ${2 * S}" class="rail"/>`);
        } else {
          // arcs from the main line down to this branch and back up
          out.push(`<path d="M ${x} ${railY} q ${S} 0 ${S} ${S} V ${by - S} q 0 ${S} ${S} ${S}" class="rail"/>`);
          out.push(`<path d="M ${xR - 0} ${by} q ${S} 0 ${S} ${-S} V ${railY + S} q 0 ${-S} ${S} ${-S}" class="rail"/>`);
        }
        // fill rails to the centered branch
        out.push(`<path d="M ${x + 2 * S} ${by} H ${bx}" class="rail"/>`);
        out.push(`<path d="M ${bx + b.w} ${by} H ${x + w - 2 * S}" class="rail"/>`);
        b.draw(bx, by, out);
      }
    }
  };
}

function loopLayout(fwd, back) {
  const W = Math.max(fwd.w, back.w);
  const w = W + 4 * S;
  const fwdRail = fwd.ey;
  const backTop = fwd.h + VGAP;
  const backRail = backTop + back.ey;
  const h = backTop + back.h;
  return {
    w, h, ey: fwdRail, minw: w,
    draw(x, railY, out) {
      const top = railY - fwdRail;
      const fy = railY, by = top + backRail;
      const fx = x + 2 * S + (W - fwd.w) / 2;
      const bx = x + 2 * S + (W - back.w) / 2;
      out.push(`<path d="M ${x} ${fy} h ${2 * S}" class="rail"/>`);
      out.push(`<path d="M ${x + 2 * S} ${fy} H ${fx}" class="rail"/>`);
      fwd.draw(fx, fy, out);
      out.push(`<path d="M ${fx + fwd.w} ${fy} H ${x + w - 2 * S}" class="rail"/>`);
      out.push(`<path d="M ${x + w - 2 * S} ${fy} h ${2 * S}" class="rail"/>`);
      // return path: down on the right, back through `back` (reversed), up on the left
      out.push(`<path d="M ${x + w - 2 * S} ${fy} q ${S} 0 ${S} ${S} V ${by - S} q 0 ${S} ${-S} ${S}" class="rail"/>`);
      out.push(`<path d="M ${x + w - 2 * S} ${by} H ${bx + back.w}" class="rail"/>`);
      back.draw(bx, by, out);
      out.push(`<path d="M ${bx} ${by} H ${x + 2 * S}" class="rail"/>`);
      out.push(`<path d="M ${x + 2 * S} ${by} q ${-S} 0 ${-S} ${-S} V ${fy + S} q 0 ${-S} ${S} ${-S}" class="rail"/>`);
    }
  };
}

function seqLayout(items, targetW, isEps) {
  if (isEps || items.length === 0) return epsilon();
  if (items.length === 1) return items[0];
  // greedy first-fit wrapping ("less and shallower wrapping" as a heuristic;
  // the paper frames this step as preference-ordered optimization, §3.2)
  const margin = 2 * S;                      // room for wrap connectors
  const avail = Math.max(targetW - 2 * margin, Math.max(...items.map(it => it.w)));
  const rows = [[]];
  let x = 0;
  for (const it of items) {
    const need = it.w + (rows[rows.length - 1].length ? GAP : 0);
    if (x + need > avail && rows[rows.length - 1].length) { rows.push([]); x = 0; }
    x += (rows[rows.length - 1].length ? GAP : 0) + it.w;
    rows[rows.length - 1].push(it);
  }
  const rowW = rows.map(r => r.reduce((s, it, i) => s + it.w + (i ? GAP : 0), 0));
  const multi = rows.length > 1;
  const w = (multi ? Math.max(...rowW) + 2 * margin : rowW[0]);
  const rowEy = rows.map(r => Math.max(...r.map(it => it.ey)));
  const rowH = rows.map((r, k) => rowEy[k] + Math.max(...r.map(it => it.h - it.ey)));
  let acc = 0;
  const rowTop = rows.map((r, k) => { const t = acc; acc += rowH[k] + (k < rows.length - 1 ? WRAPCH : 0); return t; });
  const h = acc;
  return {
    w, h, ey: rowEy[0], minw: w, rows: rows.length,
    draw(x0, railY, out) {
      const top = railY - rowEy[0];
      for (let k = 0; k < rows.length; k++) {
        const ry = top + rowTop[k] + rowEy[k];
        let cx = x0 + (multi ? margin : 0);
        const rowStart = cx;
        for (let i = 0; i < rows[k].length; i++) {
          const it = rows[k][i];
          if (i) { out.push(`<path d="M ${cx} ${ry} h ${GAP}" class="rail"/>`); cx += GAP; }
          it.draw(cx, ry, out);
          cx += it.w;
        }
        if (multi) {
          if (k === 0) out.push(`<path d="M ${x0} ${ry} h ${margin}" class="rail"/>`);
          if (k === rows.length - 1) out.push(`<path d="M ${cx} ${ry} H ${x0 + w}" class="rail"/>`);
          if (k < rows.length - 1) {
            // wrap connector: right edge, down to the channel, left, down into next row
            const chY = top + rowTop[k] + rowH[k] + WRAPCH / 2;
            const nextY = top + rowTop[k + 1] + rowEy[k + 1];
            const xR = x0 + w - S, xL = x0 + S;
            out.push(`<path d="M ${cx} ${ry} H ${xR - S} q ${S} 0 ${S} ${S} V ${chY - S} q 0 ${S} ${-S} ${S} H ${xL + S} q ${-S} 0 ${-S} ${S} V ${nextY - S} q 0 ${S} ${S} ${S} h ${margin - 2 * S}" class="rail"/>`);
          }
        }
      }
    }
  };
}

// ---------------- top-level render ----------------
function render(dsl, targetW) {
  const ast = typeof dsl === 'string' ? parse(dsl) : dsl;
  const L = layout(ast, targetW - 4 * S);
  const out = [];
  const x0 = 2 * S, railY = L.ey + S;
  out.push(`<circle cx="${x0 - S}" cy="${railY}" r="4" class="endpt"/>`);
  out.push(`<path d="M ${x0 - S + 4} ${railY} H ${x0}" class="rail"/>`);
  L.draw(x0, railY, out);
  out.push(`<path d="M ${x0 + L.w} ${railY} h ${S}" class="rail"/>`);
  out.push(`<circle cx="${x0 + L.w + S + 4}" cy="${railY}" r="4" class="endpt"/>`);
  const W = x0 + L.w + 2 * S + 10, H = L.h + 2 * S + 6;
  return { svg:
`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" class="rr">
<style>
.rail { fill: none; stroke: #333; stroke-width: 2; }
.term { fill: #fff; stroke: #333; stroke-width: 1.6; }
.nonterm { fill: #fff; stroke: #333; stroke-width: 1.6; }
.endpt { fill: #333; }
.lbl { font: 13px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
       text-anchor: middle; dominant-baseline: central; fill: #111; }
.lbl.nt { font-style: italic; font-family: Georgia, 'Times New Roman', serif; font-size: 14px; }
</style>
${out.join('\n')}
</svg>`, w: W, h: H, rows: L.rows || 1 };
}

if (typeof module !== 'undefined') module.exports = { parse, layout, render };
