#!/usr/bin/env node
/**
 * Polaris Status Line for Claude Code
 *
 * Outputs a 4-line rich statusline:
 *
 *   ⭐ Polaris  ●  │  ⎇ master  │  009-signup-ui-demo
 *   ─────────────────────────────────────────────────────
 *   📋  WP02: Core Implementation   [●●○○○]  2/5   🏃 doing
 *   📊  planned: 1  │  doing: 1  │  for_review: 0  │  done: 3
 */

'use strict';

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// ---------------------------------------------------------------------------
// stdin -- Claude Code passes JSON context here
// ---------------------------------------------------------------------------
let input = null;
try {
  const raw = fs.readFileSync('/dev/stdin', 'utf8').trim();
  if (raw) input = JSON.parse(raw);
} catch (_) { /* not available -- fine */ }

const cwd = (input && (input.cwd || (input.workspace && input.workspace.current_dir)))
  || process.cwd();

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Parse a simple YAML frontmatter block into a key→value map (strings only). */
function parseFrontmatter(content) {
  const map = {};
  const fmMatch = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!fmMatch) return map;
  for (const line of fmMatch[1].split(/\r?\n/)) {
    const kv = line.match(/^\s*(\w+)\s*:\s*(.+?)\s*$/);
    if (kv) map[kv[1]] = kv[2];
  }
  return map;
}

/** Extract the first markdown H1/H2 title from body text (after frontmatter). */
function extractTitle(content) {
  // Strip frontmatter first
  const body = content.replace(/^---[\s\S]*?---\r?\n/, '');
  const m = body.match(/^#{1,2}\s+(.+)/m);
  return m ? m[1].trim() : null;
}

/** Return sorted list of feature directory names under polaris-specs/. */
function getFeatureDirs(specsDir) {
  try {
    return fs.readdirSync(specsDir, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name)
      .sort();
  } catch (_) {
    return [];
  }
}

/**
 * WP record shape:
 *   { id, file, feature, lane, title, fm }
 */
function loadAllWPs(specsDir) {
  const wps = [];
  for (const feature of getFeatureDirs(specsDir)) {
    const tasksDir = path.join(specsDir, feature, 'tasks');
    try {
      const files = fs.readdirSync(tasksDir)
        .filter(f => /^WP\d+\.md$/i.test(f))
        .sort();
      for (const file of files) {
        try {
          const content = fs.readFileSync(path.join(tasksDir, file), 'utf8');
          const fm = parseFrontmatter(content);
          const lane = (fm.lane || 'planned').toLowerCase().trim();
          const id   = file.replace(/\.md$/i, '').toUpperCase();
          const title = fm.title || extractTitle(content) || id;
          wps.push({ id, file, feature, lane, title, fm });
        } catch (_) { /* skip unreadable */ }
      }
    } catch (_) { /* skip missing tasks dir */ }
  }
  return wps;
}

// ---------------------------------------------------------------------------
// Git branch
// ---------------------------------------------------------------------------
function getBranch() {
  try {
    return execSync('git rev-parse --abbrev-ref HEAD', {
      cwd,
      timeout: 2000,
      stdio: ['ignore', 'pipe', 'ignore'],
      env: { ...process.env, GIT_OPTIONAL_LOCKS: '0' }
    }).toString().trim();
  } catch (_) {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Most-recently-modified feature dir (fallback when no active WP found)
// ---------------------------------------------------------------------------
function getMostRecentFeature(specsDir) {
  try {
    let latest = null;
    let latestMtime = 0;
    for (const feature of getFeatureDirs(specsDir)) {
      const tasksDir = path.join(specsDir, feature, 'tasks');
      try {
        const stat = fs.statSync(tasksDir);
        if (stat.mtimeMs > latestMtime) {
          latestMtime = stat.mtimeMs;
          latest = feature;
        }
      } catch (_) {
        // Fall back to the feature dir itself
        try {
          const stat = fs.statSync(path.join(specsDir, feature));
          if (stat.mtimeMs > latestMtime) {
            latestMtime = stat.mtimeMs;
            latest = feature;
          }
        } catch (_2) { /* skip */ }
      }
    }
    return latest;
  } catch (_) {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Progress dots: ● = done or for_review, ○ = planned or doing
// ---------------------------------------------------------------------------
function progressDots(wpsInFeature) {
  return wpsInFeature.map(wp => {
    const l = wp.lane;
    return (l === 'done' || l === 'for_review') ? '\u25CF' : '\u25CB';
  }).join('');
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
try {
  const specsDir = path.join(cwd, 'polaris-specs');
  const specsExists = fs.existsSync(specsDir);

  const branch = getBranch();
  const allWPs  = specsExists ? loadAllWPs(specsDir) : [];

  // Find the first WP with lane: doing
  const activeWP = allWPs.find(wp => wp.lane === 'doing') || null;

  // Determine the active feature slug
  let activeFeature = activeWP ? activeWP.feature : null;
  if (!activeFeature && specsExists) {
    activeFeature = getMostRecentFeature(specsDir);
  }

  // WPs belonging to the active feature
  const featureWPs = activeFeature
    ? allWPs.filter(wp => wp.feature === activeFeature).sort((a, b) => a.id.localeCompare(b.id))
    : [];

  // Progress counters for active feature
  const totalWPs   = featureWPs.length;
  const completedWPs = featureWPs.filter(wp => wp.lane === 'done' || wp.lane === 'for_review').length;
  const dots       = totalWPs > 0 ? progressDots(featureWPs) : '';

  // Global lane counts across ALL features
  const laneCounts = { planned: 0, doing: 0, for_review: 0, done: 0 };
  for (const wp of allWPs) {
    const l = wp.lane;
    if (l in laneCounts) laneCounts[l]++;
    else laneCounts.planned++; // unknown lanes treated as planned
  }

  // ---------------------------------------------------------------------------
  // Line 1: header
  // ---------------------------------------------------------------------------
  const branchPart   = branch        ? ' \u23E3 ' + branch          : '';
  const featurePart  = activeFeature ? ' ' + activeFeature           : ' \u2014';
  const line1 = '\u2B50 Polaris  \u25CF  \u2502 ' + branchPart.trimStart() + '  \u2502 ' + featurePart.trimStart();

  // ---------------------------------------------------------------------------
  // Line 2: separator -- match line 1 visible length (approx)
  // ---------------------------------------------------------------------------
  const SEP_WIDTH = 53;
  const line2 = '\u2500'.repeat(SEP_WIDTH);

  // ---------------------------------------------------------------------------
  // Line 3: active WP detail
  // ---------------------------------------------------------------------------
  let line3;
  if (activeWP) {
    const dotsStr   = totalWPs > 0 ? '[\u200B' + dots + ']' : '';
    const countStr  = totalWPs > 0 ? '  ' + completedWPs + '/' + totalWPs : '';
    line3 = '\uD83D\uDCCB  ' + activeWP.id + ': ' + activeWP.title
      + (dotsStr  ? '   ' + dotsStr  : '')
      + (countStr ? countStr         : '')
      + '   \uD83C\uDFC3 ' + activeWP.lane;
  } else if (featureWPs.length > 0) {
    // Feature found but nothing is "doing" right now
    const dotsStr  = '[\u200B' + dots + ']';
    const countStr = completedWPs + '/' + totalWPs;
    line3 = '\uD83D\uDCCB  No active work package   ' + dotsStr + '  ' + countStr;
  } else {
    line3 = '\uD83D\uDCCB  No active work package';
  }

  // ---------------------------------------------------------------------------
  // Line 4: global lane summary
  // ---------------------------------------------------------------------------
  const line4 = '\uD83D\uDCCA  planned: ' + laneCounts.planned
    + '  \u2502  doing: '      + laneCounts.doing
    + '  \u2502  for_review: ' + laneCounts.for_review
    + '  \u2502  done: '       + laneCounts.done;

  // ---------------------------------------------------------------------------
  // Output
  // ---------------------------------------------------------------------------
  process.stdout.write([line1, line2, line3, line4].join('\n'));

} catch (_) {
  process.stdout.write('\u2B50 Polaris');
}
