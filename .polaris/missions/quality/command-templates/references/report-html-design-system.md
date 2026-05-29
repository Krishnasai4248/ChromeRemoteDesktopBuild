# Report HTML Design System

## HTML SKELETON

Every report MUST follow this structure. Sections marked `[REQUIRED]` are mandatory. Sections marked `[CONDITIONAL]` are included when relevant to the report type.

```
 1. DOCTYPE + <head> with full CSS design system            [REQUIRED]
 2. <header class="report-header">                          [REQUIRED]
 3. Framework / methodology note                            [REQUIRED]
 4. Executive summary with score cards                      [REQUIRED]
 5. Dimension score bars                                    [CONDITIONAL - scored reports]
 6. Severity distribution strip                             [CONDITIONAL - findings reports]
 7. Summary narrative box                                   [REQUIRED]
 8. Top priority actions table                              [REQUIRED]
 9. Human vs AI effort comparison                           [CONDITIONAL - first assessments]
10. Detailed findings sections (one <h2> per dimension)     [REQUIRED]
11. Recommendations / roadmap                               [REQUIRED]
12. Methodology & grading scale                             [REQUIRED]
13. Disclaimer callout                                      [REQUIRED]
14. <footer class="report-footer">                          [REQUIRED]
```

---

## DESIGN SYSTEM

CSS variables and typography are defined in the Full CSS Stylesheet section below. Use ONLY those variables -- no ad-hoc hex colors.

---

## COMPONENT CATALOG

Each component below is a reusable building block. Copy the HTML patterns exactly, substituting only the `{{PLACEHOLDER}}` values with actual content.

### 1. Report Header [REQUIRED]

Navy gradient banner with project logo, report title, tag line, metadata, and optional grade circle.

```html
<header class="report-header">
  <div class="container">
    <div class="brand">
      <!-- Project logo SVG goes here (40x38 recommended). -->
      <!-- If no project logo, omit the SVG entirely. -->
      <div>
        <h1>{{REPORT_TITLE}}</h1>
        <span class="tag">{{TAG_LINE}}</span>
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:1.5rem;">
      <div class="meta">
        <span>{{FULL_DATE}}</span>
        <span>{{PROJECT_NAME}}</span>
        <span>{{SCOPE_SUMMARY}}</span>
      </div>
      <!-- Grade circle: include ONLY for scored/graded reports -->
      <div class="grade" style="background:var({{GRADE_COLOR}})">{{GRADE_LETTER}}</div>
    </div>
  </div>
</header>
```

Tag lines: assessment=`ISO 25010 &middot; OWASP TOP 10 &middot; CWE/SANS TOP 25`, security=`OWASP TOP 10 &middot; CWE/SANS TOP 25 &middot; NIST CSF`, NFR=`ISO 25010 &middot; PERFORMANCE &middot; RELIABILITY`, bug=`ROOT CAUSE ANALYSIS &middot; PATTERN DETECTION`, migration=`MODERNIZATION &middot; RISK ASSESSMENT`, deps=`CVE ANALYSIS &middot; LICENSE COMPLIANCE`, general=`POLARIS ANALYSIS`.

Grade colors: A=`--good`, B=`--aptean-teal`, C=`--aptean-orange`, D=`--high`, F=`--critical`.

### 2. Score Cards [REQUIRED for quantitative reports]

```html
<div class="score-grid">
  <div class="score-card">
    <div class="label">{{METRIC_LABEL}}</div>
    <div class="value" style="color:var({{COLOR}})">{{VALUE}}</div>
    <div class="sublabel">{{OPTIONAL_SUBLABEL}}</div>
  </div>
</div>
```

Value colors: neutral=`--aptean-navy`, good=`--good`, warning=`--aptean-orange`, bad=`--high`/`--critical`.

### 3. Score Bars [CONDITIONAL -- scored/graded reports]

```html
<div class="score-bar-row">
  <span class="score-bar-label">{{DIMENSION_NAME}}</span>
  <div class="score-bar-bg">
    <div class="score-bar-fill {{FILL_CLASS}}" style="width:{{PERCENT}}%">
      {{SCORE}} / 10
    </div>
  </div>
  <span class="score-bar-weight">{{WEIGHT}}%</span>
</div>
```

Fill classes: >=6 `s-good` (teal), 4-5 `s-ok` (orange), <=3 `s-low` (red).

### 4. Severity Badges [REQUIRED for all findings]

```html
<span class="badge badge-critical">CRITICAL</span>
<span class="badge badge-high">HIGH</span>
<span class="badge badge-medium">MEDIUM</span>
<span class="badge badge-low">LOW</span>
<span class="badge badge-good">GOOD</span>       <!-- or STRENGTH / PASS -->
<span class="badge badge-na">N/A</span>
<span class="badge badge-pass">PASS</span>
<span class="badge badge-partial">PARTIAL</span>
<span class="badge badge-missing">MISSING</span>
<span class="badge badge-fail">FAIL</span>
```

### 5. Dimension Score Tags [CONDITIONAL -- inline with h2]

`<h2>1. Security <span class="dim-score warn">4/10</span></h2>` -- Classes: >=8 `great`, 6-7 `good`, 4-5 `ok`, 2-3 `warn`, 0-1 `bad`.

### 6. Summary Boxes [REQUIRED -- at least one per section]

```html
<!-- Standard (teal accent) -->
<div class="summary-box"><p>{{NARRATIVE}}</p></div>

<!-- Danger (red accent) -- for critical findings -->
<div class="summary-box danger"><p>{{CRITICAL_NARRATIVE}}</p></div>

<!-- Warning (orange accent) -->
<div class="summary-box warn"><p>{{WARNING_NARRATIVE}}</p></div>
```

### 7. Framework / Methodology Note [REQUIRED]

```html
<div class="framework-note">
  <h3>{{METHODOLOGY_TITLE}}</h3>
  <p>{{DESCRIPTION}}</p>
  <ul>
    <li><strong>Scan strategy:</strong> {{STRATEGY_DETAIL}}</li>
    <li><strong>Standards applied:</strong> {{STANDARDS_LIST}}</li>
    <li><strong>Scope:</strong> {{SCOPE_DETAIL}}</li>
  </ul>
</div>
```

Critical variant: add `style="background:var(--critical-bg);border-color:#ffcdd2;"` and `style="color:var(--critical);"` on h3.

### 8. Tables [REQUIRED for findings]

```html
<table>
  <thead>
    <tr>
      <th style="width:75px">Severity</th>
      <th>Finding</th>
      <th style="width:200px">Location</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><span class="badge badge-critical">CRITICAL</span></td>
      <td><strong>{{FINDING_TITLE}}.</strong> {{FINDING_DESCRIPTION}}</td>
      <td><code>{{FILE_PATH}}</code></td>
    </tr>
  </tbody>
</table>
```

Tables: always `<thead>`, `class="num"` on numeric cells, `<code>` for paths, explicit `width` on narrow columns.

### 9. Callout Boxes [CONDITIONAL]

```html
<!-- Warning (orange) -->
<div class="callout"><strong>{{TITLE}}:</strong> {{MESSAGE}}</div>

<!-- Danger (red) -->
<div class="callout danger"><strong>{{TITLE}}:</strong> {{MESSAGE}}</div>

<!-- Info (teal) -->
<div class="callout info"><strong>{{TITLE}}:</strong> {{MESSAGE}}</div>
```

### 10. Evidence Blocks [CONDITIONAL -- for supporting data]

```html
<div class="evidence">
  <strong>Evidence:</strong> {{EVIDENCE_DESCRIPTION}}
</div>
```

### 11. Code Blocks [CONDITIONAL -- for code samples]

```html
<div class="code-block">
<span class="comment">// Comment text</span>
<span class="keyword">var</span> example = <span class="string">"value"</span>;
<span class="highlight">functionCall</span>();
<span class="error">// ERROR: problem description</span>
</div>
```

### 12. Severity Distribution Strip [CONDITIONAL -- findings summary]

```html
<div class="severity-strip">
  <div class="severity-item">
    <div class="severity-dot" style="background:var(--critical)"></div> {{N}} Critical
  </div>
  <div class="severity-item">
    <div class="severity-dot" style="background:var(--high)"></div> {{N}} High
  </div>
  <div class="severity-item">
    <div class="severity-dot" style="background:var(--medium)"></div> {{N}} Medium
  </div>
  <div class="severity-item">
    <div class="severity-dot" style="background:var(--good)"></div> {{N}} Low
  </div>
</div>
```

### 13. Human vs AI Effort Comparison [CONDITIONAL -- first assessments]

```html
<div class="time-compare">
  <div class="time-card human">
    <div class="time-label">Human Team (Realistic)</div>
    <div class="time-value" style="color:var(--aptean-orange)">{{HUMAN_TIME}}</div>
    <div class="time-sub">{{HUMAN_DETAIL}}</div>
  </div>
  <div class="time-card ai">
    <div class="time-label">AI-Powered (Polaris Framework)</div>
    <div class="time-value" style="color:var(--aptean-teal)">{{AI_TIME}}</div>
    <div class="time-sub">{{AI_DETAIL}}</div>
  </div>
</div>
```

### 14. Disclaimer [REQUIRED -- placed before footer]

```html
<div class="callout" style="margin-top:1.5rem;">
  <strong>Disclaimer:</strong> This {{REPORT_TYPE_LOWER}} is based on {{METHODOLOGY_SUMMARY}}.
  Findings should be validated against production telemetry and prioritized based on business impact.
  Analysis performed on {{DATE}} against branch <code>{{BRANCH}}</code>.
</div>
```

### 15. Report Footer [REQUIRED]

```html
<footer class="report-footer">
  <strong>Polaris Software Intelligence Framework</strong>
  &middot; {{REPORT_TYPE}} &middot; {{PROJECT_NAME}}<br>
  Generated {{DATE}} &middot; {{SCOPE_STATS}}<br>
  &copy; {{YEAR}} {{ORG_NAME}}. All rights reserved.
</footer>
```

---

## FULL CSS STYLESHEET

Every report MUST include this exact CSS block inside `<style>` in the `<head>`. Do NOT modify these styles. If a report type needs a unique visualization (spider chart, treemap, Sankey diagram), ADD new classes at the end -- never change existing ones. All additions MUST reference the existing CSS variables.

```html
<style>
  /* Suisse Intl is embedded via @font-face when using report_theme.py.
     For standalone HTML, fall back to system fonts. Do NOT use Google Fonts. */

  :root {
    --aptean-navy: #050852;
    --aptean-navy-light: #0a2e6b;
    --aptean-teal: #54B3BE;
    --aptean-teal-dark: #3D8A93;
    --aptean-teal-light: #8FD0D1;
    --aptean-teal-bg: rgba(84,179,190,0.06);
    --aptean-blue: #2459A9;
    --aptean-orange: #E6612E;
    --bg: #f8f9fb;
    --surface: #ffffff;
    --surface-alt: #f1f4f8;
    --border: #e2e7ef;
    --border-light: #edf0f5;
    --text: #262626;
    --text-secondary: #5a6776;
    --text-muted: #8694a1;
    --critical: #d32f2f; --critical-bg: #fef2f2;
    --high: #e65100; --high-bg: #fff7ed;
    --medium: #f57f17; --medium-bg: #fffde7;
    --low: #5c6bc0; --low-bg: #eef0fb;
    --good: #2e7d32; --good-bg: #f0fdf4;
  }

  * { margin:0; padding:0; box-sizing:border-box; }
  h1, h2, h3 { font-family:'Suisse Intl Condensed','Barlow Condensed','Arial Narrow',sans-serif; }

  body {
    font-family:'Suisse Intl',-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;
    background:var(--bg);
    color:var(--text);
    line-height:1.65;
    -webkit-font-smoothing:antialiased;
  }

  /* -- Layout -- */
  .container { max-width:1140px; margin:0 auto; padding:0 2rem; }
  .content { padding:2rem 0 3rem; }

  /* -- Report Header -- */
  .report-header {
    background:linear-gradient(135deg,var(--aptean-navy) 0%,var(--aptean-navy-light) 100%);
    color:white; padding:2.5rem 0;
  }
  .report-header .container {
    display:flex; align-items:center; justify-content:space-between;
    flex-wrap:wrap; gap:1.5rem;
  }
  .report-header .brand { display:flex; align-items:center; gap:1rem; }
  .report-header h1 { font-size:1.5rem; font-weight:700; letter-spacing:-0.02em; }
  .report-header .tag {
    display:inline-block;
    background:rgba(38,198,218,0.2); border:1px solid rgba(38,198,218,0.4);
    color:var(--aptean-teal-light); padding:2px 12px; border-radius:20px;
    font-size:0.75rem; font-weight:600; margin-top:0.3rem; letter-spacing:0.04em;
  }
  .report-header .meta {
    font-size:0.85rem; opacity:0.7; display:flex; gap:1.5rem; flex-wrap:wrap;
  }
  .report-header .grade {
    display:flex; align-items:center; justify-content:center;
    width:64px; height:64px; border-radius:50%;
    font-size:1.75rem; font-weight:800; background:var(--aptean-orange);
    color:white; flex-shrink:0;
  }

  /* -- Headings -- */
  h2 {
    font-size:1.25rem; font-weight:700; color:var(--aptean-navy);
    margin:2.5rem 0 1rem; padding-bottom:0.5rem;
    border-bottom:2px solid var(--aptean-teal);
    display:flex; align-items:center; justify-content:space-between;
    flex-wrap:wrap; gap:0.5rem;
  }
  h3 { font-size:1rem; font-weight:600; color:var(--aptean-navy); margin:1.5rem 0 0.75rem; }
  h4 { font-size:0.92rem; font-weight:600; color:var(--aptean-navy); margin:1rem 0 0.5rem; }

  /* -- Framework Note -- */
  .framework-note {
    background:var(--aptean-teal-bg); border:1px solid rgba(30,105,120,0.15);
    border-radius:12px; padding:1.5rem; margin:1.25rem 0;
  }
  .framework-note h3 { margin-top:0; font-size:0.95rem; }
  .framework-note p { color:var(--text-secondary); font-size:0.88rem; margin-top:0.35rem; }
  .framework-note ul { margin:0.5rem 0 0 1.25rem; font-size:0.85rem; color:var(--text-secondary); }
  .framework-note li { margin:0.25rem 0; }

  /* -- Score Grid -- */
  .score-grid {
    display:grid; grid-template-columns:repeat(auto-fit,minmax(135px,1fr));
    gap:0.75rem; margin:1.25rem 0;
  }
  .score-card {
    background:var(--surface); border:1px solid var(--border);
    border-radius:10px; padding:1rem 1.25rem; text-align:center;
    transition:box-shadow 0.15s;
  }
  .score-card:hover { box-shadow:0 2px 12px rgba(0,31,84,0.07); }
  .score-card .label {
    font-size:0.7rem; font-weight:600; text-transform:uppercase;
    letter-spacing:0.06em; color:var(--text-muted); margin-bottom:0.25rem;
  }
  .score-card .value { font-size:1.6rem; font-weight:800; line-height:1.2; }
  .score-card .sublabel { font-size:0.66rem; color:var(--text-muted); margin-top:0.15rem; }

  /* -- Score Bars -- */
  .score-bar-row { display:flex; align-items:center; gap:0.75rem; margin:0.4rem 0; }
  .score-bar-label { min-width:130px; font-size:0.85rem; font-weight:600; color:var(--text); }
  .score-bar-bg {
    flex:1; height:24px; background:#e8edf3; border-radius:4px;
    position:relative; overflow:hidden;
  }
  .score-bar-fill {
    height:100%; border-radius:4px; display:flex; align-items:center;
    padding:0 10px; font-size:0.72rem; font-weight:700; color:white;
    transition:width 0.4s;
  }
  .score-bar-fill.s-good { background:var(--aptean-teal); }
  .score-bar-fill.s-ok   { background:var(--aptean-orange); }
  .score-bar-fill.s-low  { background:var(--critical); }
  .score-bar-weight { min-width:45px; font-size:0.72rem; color:var(--text-muted); text-align:right; }

  /* -- Badges -- */
  .badge {
    display:inline-block; padding:2px 10px; border-radius:10px;
    font-size:0.7rem; font-weight:700; letter-spacing:0.04em; text-transform:uppercase;
  }
  .badge-critical { background:var(--critical-bg); color:var(--critical); border:1px solid #ffcdd2; }
  .badge-high     { background:var(--high-bg);     color:var(--high);     border:1px solid #ffe0b2; }
  .badge-medium   { background:var(--medium-bg);   color:var(--medium);   border:1px solid #fff9c4; }
  .badge-low      { background:var(--low-bg);      color:var(--low);      border:1px solid #c5cae9; }
  .badge-good     { background:var(--good-bg);     color:var(--good);     border:1px solid #c8e6c9; }
  .badge-na       { background:var(--surface-alt);  color:var(--text-muted); border:1px solid var(--border); }
  .badge-pass     { background:var(--good-bg);     color:var(--good);     border:1px solid #c8e6c9; }
  .badge-partial  { background:var(--medium-bg);   color:var(--medium);   border:1px solid #fff9c4; }
  .badge-missing  { background:var(--critical-bg); color:var(--critical); border:1px solid #ffcdd2; }
  .badge-fail     { background:#b71c1c;            color:white;           border:1px solid #b71c1c; }

  /* -- Dimension Scores (inline with h2) -- */
  .dim-score { font-size:0.85rem; font-weight:700; padding:3px 12px; border-radius:8px; }
  .dim-score.great { background:var(--good-bg);     color:var(--good); }
  .dim-score.good  { background:#e0f7fa;            color:var(--aptean-teal); }
  .dim-score.ok    { background:var(--medium-bg);   color:var(--medium); }
  .dim-score.warn  { background:var(--high-bg);     color:var(--high); }
  .dim-score.bad   { background:var(--critical-bg); color:var(--critical); }

  /* -- Summary Box -- */
  .summary-box {
    background:var(--surface); border:1px solid var(--border);
    border-left:4px solid var(--aptean-teal);
    border-radius:0 10px 10px 0; padding:1.25rem 1.5rem; margin:0.75rem 0;
  }
  .summary-box p { color:var(--text-secondary); font-size:0.9rem; }
  .summary-box.danger { border-left-color:var(--critical); }
  .summary-box.warn   { border-left-color:var(--high); }

  /* -- Evidence Block -- */
  .evidence {
    background:var(--aptean-teal-bg); border:1px solid rgba(30,105,120,0.15);
    border-radius:8px; padding:1rem 1.25rem; margin:0.75rem 0;
    font-size:0.85rem; color:var(--text-secondary);
  }
  .evidence strong { color:var(--aptean-teal); }

  /* -- Code Block -- */
  .code-block {
    background:#1a1a2e; color:#e0e0e0; padding:1rem 1.25rem;
    border-radius:8px; font-family:'Cascadia Code','Fira Code',monospace;
    font-size:0.78rem; line-height:1.6; margin:0.75rem 0;
    white-space:pre-wrap; overflow-x:auto;
  }
  .code-block .comment   { color:#6a9955; }
  .code-block .keyword   { color:#569cd6; }
  .code-block .string    { color:#ce9178; }
  .code-block .highlight { color:#dcdcaa; }
  .code-block .error     { color:#f44747; }

  /* -- Callout -- */
  .callout {
    background:#fff3e0; border:1px solid #ffe0b2; border-radius:10px;
    padding:1rem 1.25rem; margin:1rem 0; font-size:0.88rem; color:#bf360c;
  }
  .callout strong { color:#e65100; }
  .callout.danger { background:var(--critical-bg); border-color:#ffcdd2; color:#b71c1c; }
  .callout.danger strong { color:var(--critical); }
  .callout.info { background:var(--aptean-teal-bg); border-color:rgba(30,105,120,0.25); color:var(--aptean-teal); }
  .callout.info strong { color:var(--aptean-navy); }

  /* -- Severity Strip -- */
  .severity-strip { display:flex; gap:1.5rem; margin:1rem 0; flex-wrap:wrap; }
  .severity-item { display:flex; align-items:center; gap:0.5rem; font-size:0.85rem; font-weight:600; }
  .severity-dot { width:12px; height:12px; border-radius:50%; }

  /* -- Tables -- */
  table { width:100%; border-collapse:collapse; margin:0.75rem 0; font-size:0.88rem; }
  th {
    background:var(--surface-alt); color:var(--text-muted); font-weight:600;
    font-size:0.73rem; text-transform:uppercase; letter-spacing:0.05em;
    padding:0.65rem 0.75rem; text-align:left; border-bottom:2px solid var(--border);
  }
  td { padding:0.65rem 0.75rem; border-bottom:1px solid var(--border-light); vertical-align:top; }
  tr:hover td { background:var(--surface-alt); }
  td code {
    background:var(--surface-alt); padding:1px 6px; border-radius:4px;
    font-size:0.8rem; color:var(--aptean-teal); border:1px solid var(--border);
    word-break:break-all;
  }
  .text-right { text-align:right; }
  .num {
    font-variant-numeric:tabular-nums;
    font-family:'SF Mono','Cascadia Code',monospace; font-size:0.82rem;
  }

  /* -- Time Comparison Cards -- */
  .time-compare { display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; margin:1rem 0; }
  .time-card {
    background:var(--surface); border:1px solid var(--border);
    border-radius:12px; padding:1.5rem; text-align:center;
  }
  .time-card.human { border-top:4px solid var(--aptean-orange); }
  .time-card.ai    { border-top:4px solid var(--aptean-teal); }
  .time-card .time-label {
    font-size:0.75rem; font-weight:600; text-transform:uppercase;
    letter-spacing:0.06em; color:var(--text-muted); margin-bottom:0.5rem;
  }
  .time-card .time-value { font-size:2rem; font-weight:800; line-height:1.2; }
  .time-card .time-sub { font-size:0.78rem; color:var(--text-secondary); margin-top:0.25rem; }
  .time-detail { font-size:0.82rem; color:var(--text-secondary); text-align:left; margin-top:1rem; }
  .time-detail li { margin:0.3rem 0; }

  /* -- Hotspot Bars -- */
  .hotspot-bar { display:flex; align-items:center; gap:0.5rem; margin:0.35rem 0; font-size:0.82rem; }

  /* -- Footer -- */
  .report-footer {
    background:var(--aptean-navy); color:rgba(255,255,255,0.6);
    text-align:center; padding:1.5rem 2rem; font-size:0.78rem;
  }
  .report-footer strong { color:rgba(255,255,255,0.9); }

  /* -- Print & Responsive -- */
  @media print {
    body { background:white; }
    .report-header { print-color-adjust:exact; -webkit-print-color-adjust:exact; }
  }
  @media (max-width:800px) {
    .container { padding:0 1rem; }
    .score-grid { grid-template-columns:repeat(2,1fr); }
    .time-compare { grid-template-columns:1fr; }
  }
</style>
```

---

## CONTENT GUIDELINES

**Writing**: Evidence-based (cite files+lines in `<code>`), actionable (recommendation+effort), quantified (exact counts, no "many"/"several"), bold key terms (`<strong>`), narrative `summary-box` before each table.

**Severity**: CRITICAL=security/data-loss/production-breaking, HIGH=significant debt/missing critical tests, MEDIUM=quality/moderate debt, LOW=style/cosmetic.

**Grades**: A(8-10)=excellent, B(6-7.9)=good, C(4-5.9)=fair, D(2-3.9)=poor, F(0-1.9)=critical.

**Encoding**: UTF-8 only. Use HTML entities: `&mdash;`, `&ndash;`, `&middot;`, `&copy;`, `&lt;`/`&gt;`. No smart quotes or Office-pasted characters.

---

## EXECUTION STEPS (HTML)

**Step 1: Report Type** -- If not specified, ask: codebase assessment, security audit, NFR readiness, bug root cause, migration readiness, dependency audit, repo cleanup, or custom.

**Step 2: Gather Data** -- Use Grep/Glob/Bash to collect evidence with specific file paths and line numbers.

**Step 3: Compose HTML** -- Assembly: DOCTYPE+head with full CSS -> header -> container.content -> framework-note -> executive summary (score cards, bars, strip) -> summary-box -> priority actions table -> h2 per dimension with findings -> recommendations -> methodology/grading -> disclaimer callout -> close container -> footer.

**Step 4: Save** -- `.polaris/reports/{project-slug}-{report-slug}-{YYYY-MM-DD}.html`

**HTML Checklist**: Only CSS variables (no inline hex), report-header, framework-note, score-grid, summary-box per section, priority table, severity badges on findings, file paths in `<code>`, disclaimer callout, report-footer, HTML entities for special chars, print+responsive styles.
