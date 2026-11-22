"""Emit the layout enhancement pack. Not product runtime.

Regenerate from this folder:
  .\\venv\\Scripts\\python.exe docs\\mockups\\layout_enhancement_pack\\_gen_mockups.py
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>{title}</title>
<link rel="stylesheet" href="../settings_layout_grammar/grammar.css" />
<link rel="stylesheet" href="../secondary_areas_rest/rest.css" />
<link rel="stylesheet" href="enhance.css" />
</head>
<body class="{body}">
<p class="page-note">{note}</p>
{anno}
"""

FOOT = """</body>
</html>
"""

JS = r"""
<script>
(function () {
  var toggle = document.querySelector("[data-lep-empty-toggle]");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var on = document.body.classList.toggle("show-empty");
      toggle.textContent = on ? "Show rows" : "Empty preview";
    });
  }
  document.querySelectorAll("[data-lep-tabset]").forEach(function (scope) {
    var buttons = scope.querySelectorAll("[data-lep-rail] button, [data-lep-tabs] button");
    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-tab");
        buttons.forEach(function (b) {
          var on = b.getAttribute("data-tab") === id;
          if (b.closest("[data-lep-rail]")) {
            if (on) b.setAttribute("aria-current", "true");
            else b.removeAttribute("aria-current");
          }
          if (b.closest("[data-lep-tabs]")) {
            b.setAttribute("aria-selected", on ? "true" : "false");
          }
        });
        scope.querySelectorAll("[data-panel]").forEach(function (panel) {
          panel.hidden = panel.getAttribute("data-panel") !== id;
        });
        scope.querySelectorAll("[data-show]").forEach(function (el) {
          el.hidden = el.getAttribute("data-show") !== id;
        });
      });
    });
  });
  document.querySelectorAll("[data-lep-scan]").forEach(function (table) {
    table.addEventListener("keydown", function (e) {
      var rows = Array.prototype.slice.call(table.querySelectorAll("tbody tr"));
      if (!rows.length || document.body.classList.contains("show-empty")) return;
      var i = rows.findIndex(function (r) { return r.classList.contains("is-focus"); });
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        if (i < 0) i = 0;
        else if (e.key === "ArrowDown") i = Math.min(rows.length - 1, i + 1);
        else i = Math.max(0, i - 1);
        rows.forEach(function (r, n) { r.classList.toggle("is-focus", n === i); });
        var live = document.querySelector("[data-lep-focus-name]");
        var name = rows[i].getAttribute("data-name");
        if (live && name) live.textContent = name;
        rows[i].scrollIntoView({ block: "nearest" });
      } else if (e.key === "Enter") {
        e.preventDefault();
        document.body.classList.remove("show-empty");
        if (toggle) toggle.textContent = "Empty preview";
      } else if (e.key === " " || e.key === "Spacebar") {
        var t = e.target;
        if (t && t.matches && t.matches("input[type=checkbox], input[type=radio]")) return;
        e.preventDefault();
      }
    });
  });
})();
</script>
"""

FROZEN = """<header class="frozen-bar">
  <button class="btn ghost" type="button">Back</button>
  <h1 class="area-title">{title}</h1>
  <span class="frozen-tag">Frozen chrome · synthetic</span>
</header>
"""

EVIDENCE = """<div class="evidence" data-lep-evidence="phase2">
  <span class="tag">Phase 2</span>
  Hint slot for one screenshot or trace name. Not a gallery. Out of the Phase 1 build.
</div>"""


def page(name, title, note, body_class, inner, anno="", script=True):
    text = HEAD.format(title=title, body=body_class, note=note, anno=anno) + inner
    if script:
        text += JS
    text += FOOT
    (OUT / name).write_text(text, encoding="utf-8")
    print(name)


def anno(structure, verbs, extra=""):
    chips = "".join(f'<span class="chip">{v}</span>' for v in verbs)
    if not chips:
        chips = '<span class="chip muted">No row checkbox</span>'
    more = f"{extra} " if extra else ""
    return f"""<div class="anno-bar" data-lep-structure="{structure}" data-lep-lexicon="1">
  <span class="label">Studio note · not product chrome</span>
  <span class="chip">{structure}</span>
  {chips}
  {more}<span class="kbd" data-lep-kbd="1">↑</span><span class="kbd">↓</span> focus
  <span class="kbd">Enter</span> detail
  <span class="kbd">Space</span> checkbox cell only
</div>"""


def scan(marker, headers, rows, focus=0, group="cmp"):
    ths = []
    for h in headers:
        cls = ' class="hit"' if h in ("Sel", "Keep", "Include", "Enabled", "A", "B") else ""
        ths.append(f"<th{cls}>{h}</th>")
    body = []
    for i, row in enumerate(rows):
        attrs = []
        if i == focus:
            attrs.append("is-focus")
        cells = list(row)
        name = ""
        if cells and isinstance(cells[-1], tuple) and cells[-1][0] == "__name__":
            name = cells[-1][1]
            cells = cells[:-1]
        cls = " ".join(["row-hit"] + attrs)
        tds = []
        for h, cell in zip(headers, cells):
            if h in ("Sel", "Keep", "Include", "Enabled") and cell in ("cb", "on"):
                checked = " checked" if cell == "on" else ""
                tds.append(
                    f'<td class="hit"><input type="checkbox"{checked} aria-label="{h}" /></td>'
                )
            elif h in ("A", "B"):
                checked = " checked" if cell == "on" else ""
                tds.append(
                    f'<td class="hit"><input type="radio" name="{group}-{h}"{checked} aria-label="Compare {h}" /></td>'
                )
            else:
                tds.append(f"<td>{cell}</td>")
        nm = f' data-name="{name}"' if name else ""
        body.append(f'<tr class="{cls}"{nm}>{"".join(tds)}</tr>')
    return f"""<table class="scan" data-lep-scan tabindex="0" {marker}>
<thead><tr>{"".join(ths)}</tr></thead>
<tbody>
{chr(10).join(body)}
</tbody>
</table>"""


def named(cells, name):
    return list(cells) + [("__name__", name)]


def work(title, hint, table_html, empty, extra=""):
    return f"""<div class="work scroll-host">
  <div class="work-head">
    <h3>{title}</h3>
    <p class="hint">{hint}</p>
  </div>
  <div class="pane-scroll" data-lep-scroll="scan">
    <p class="empty-line" data-lep-empty>{empty}</p>
    {table_html}
    {extra}
  </div>
</div>"""


def detail(title, inner, evidence=False, pin=""):
    ev = EVIDENCE if evidence else ""
    pin_html = f'<div class="pin" data-lep-pin>{pin}</div>' if pin else ""
    return f"""<aside class="detail scroll-host">
  <div class="detail-live pane-scroll">
    <h3 data-lep-focus-name>{title}</h3>
    {inner}
    {ev}
  </div>
  <div class="detail-empty" data-lep-unfocused>
    <h3>Detail</h3>
    <p class="empty-line">Select a row</p>
  </div>
  {pin_html}
</aside>"""


def stage(area, title, toolbar, body, tabset=False):
    toggle = '<button class="btn ghost" type="button" data-lep-empty-toggle>Empty preview</button>'
    open_set = '<div data-lep-tabset>' if tabset else ""
    close_set = "</div>" if tabset else ""
    return f"""<div class="stage" data-layout-enhancement-pack="1" data-lep-area="{area}" data-lep-no-outer-scroll="1">
{FROZEN.format(title=title)}
{open_set}
<div class="toolbar">{toolbar}{toggle}<span class="status">OFFICIAL</span></div>
{body}
{close_set}
</div>"""


def pill(kind, text):
    return f'<span class="pill {kind}">{text}</span>'


def settings():
    blocks = scan(
        'data-settings-blocks-scan="1"',
        ["Include", "Block", "Export"],
        [
            named(("on", "Summary", pill("ok", "On")), "Summary"),
            named(("cb", "Documents", pill("warn", "Bodies off")), "Documents"),
            named(("on", "Evidence", pill("ok", "On")), "Evidence"),
            named(("cb", "Heal", pill("idle", "Off")), "Heal"),
            named(("on", "Trace", pill("ok", "On")), "Trace"),
            named(("cb", "Environments", pill("ok", "On")), "Environments"),
            named(("on", "Steps", pill("ok", "On")), "Steps"),
            named(("cb", "Known issues", pill("idle", "Off")), "Known issues"),
        ],
        focus=1,
    )
    envs = scan(
        'data-settings-env-scan="1"',
        ["Status", "Name", "Target"],
        [
            named((pill("ok", "Active"), "local", '<span class="mono">https://app.example.test</span>'), "local"),
            named((pill("idle", "Idle"), "test", '<span class="mono">https://test.example.test</span>'), "test"),
            named((pill("idle", "Idle"), "staging", '<span class="mono">https://staging.example.test</span>'), "staging"),
        ],
        focus=0,
    )
    stub = """<div class="panel pane-fill" data-panel="{pid}" hidden>
  <div class="work-head"><h3>{label}</h3>
  <p class="hint">Same one-scroll rule. This pack does not redraw the form. Masked status only.</p></div>
  <div class="pane-scroll"><p class="fake">{label} · stored locally · values not shown</p></div>
</div>"""
    rails = [
        ("layout", "Layout"),
        ("connections", "Connections"),
        ("env", "Environments"),
        ("model", "Model &amp; runner"),
        ("blocks", "Report blocks"),
        ("credentials", "Credentials"),
    ]
    buttons = []
    for pid, label in rails:
        cur = ' aria-current="true"' if pid == "blocks" else ""
        buttons.append(f'<button type="button" data-tab="{pid}"{cur}>{label}</button>')
    stubs = "".join(
        stub.format(pid=pid, label=label)
        for pid, label in rails
        if pid not in ("blocks", "env")
    )
    body = f"""<div class="split">
  <nav class="rail" aria-label="Settings sections" data-lep-rail="1">
    <p class="rail-label">Sections</p>
    {"".join(buttons)}
  </nav>
  <div class="work scroll-host">
    <div class="panel pane-fill" data-panel="blocks">
      <div class="work-head">
        <h3>Report blocks</h3>
        <p class="hint">Include is the only checkbox hit. Arrow keys move the row. Space toggles Include only when that cell is focused.</p>
      </div>
      <div class="pane-scroll" data-lep-scroll="scan">
        <p class="empty-line" data-lep-empty>No report blocks.</p>
        {blocks}
      </div>
    </div>
    <div class="panel pane-fill" data-panel="env" hidden>
      <div class="work-head">
        <h3>Named environments</h3>
        <p class="hint">No checkbox on this collection. Row focuses the environment. Delete stays in the detail.</p>
      </div>
      <div class="pane-scroll" data-lep-scroll="scan">
        <p class="empty-line" data-lep-empty>No environments in this level.</p>
        {envs}
      </div>
    </div>
    {stubs}
  </div>
  <aside class="detail scroll-host">
    <div class="panel pane-fill" data-panel="blocks">
      <div class="detail-live pane-scroll">
        <h3 data-lep-focus-name>Documents</h3>
        <p class="hint">Focused block. Include stays in the scan cell, not this pane.</p>
        <label class="field">Export<input class="fake" value="Bodies off" readonly /></label>
        <p class="hint">One level. No secret values on this surface.</p>
      </div>
      <div class="detail-empty" data-lep-unfocused><h3>Detail</h3><p class="empty-line">Select a row</p></div>
    </div>
    <div class="panel pane-fill" data-panel="env" hidden>
      <div class="detail-live pane-scroll">
        <h3>local</h3>
        <label class="field">Target<input class="fake mono" value="https://app.example.test" readonly /></label>
        <div class="danger-zone"><button class="btn danger" type="button">Delete environment…</button></div>
      </div>
      <div class="detail-empty"><h3>Detail</h3><p class="empty-line">Select a row</p></div>
    </div>
    {"".join(f'''<div class="panel pane-fill" data-panel="{pid}" hidden>
      <div class="detail-live pane-scroll"><h3>{label}</h3><p class="hint">Masked. Nothing to reveal in this mock.</p></div>
      <div class="detail-empty"><h3>Detail</h3><p class="empty-line">Select a row</p></div>
    </div>''' for pid, label in rails if pid not in ("blocks", "env"))}
  </aside>
</div>"""
    inner = stage(
        "settings",
        "Settings",
        "<span>Level one at a time</span>",
        body,
        tabset=True,
    )
    page(
        "01a-themed-settings.html",
        "Settings — enhancement pack",
        "<strong>Phase 1.</strong> Rail stays (≥3 sections). Include cell, one scroll per pane, sticky header, quiet empty. Click Empty preview. Arrow keys move focus when the table has focus. Synthetic OFFICIAL only.",
        "",
        inner,
        anno("Rail · ≥3 sections", ["Include"]),
    )


def suites():
    rows = []
    samples = [
        ("on", "fail", "Fail", "Checkout totals", "checkout.spec.js", "22 Nov 09:12"),
        ("on", "ok", "Pass", "Guest search", "search.spec.js", "22 Nov 09:10"),
        ("cb", "ok", "Pass", "Cart badge", "cart.spec.js", "21 Nov 18:02"),
        ("cb", "warn", "Fail", "Pay button", "pay.spec.js", "21 Nov 16:40"),
        ("cb", "idle", "Idle", "Order email", "email.spec.js", "20 Nov 11:02"),
        ("cb", "ok", "Pass", "Address book", "address.spec.js", "20 Nov 09:18"),
        ("cb", "ok", "Pass", "Promo code", "promo.spec.js", "19 Nov 15:44"),
        ("cb", "warn", "Fail", "Stock lookup", "stock.spec.js", "19 Nov 12:01"),
    ]
    for sel, kind, word, title, file, when in samples:
        rows.append(named((sel, pill(kind, word), title, f'<span class="mono">{file}</span>', when), title))
    table = scan('data-suite-scan="1"', ["Sel", "Status", "Title", "File", "Last"], rows, focus=0)
    body = f"""<div class="split two" data-lep-no-outer-scroll="1">
  {work("Suites", "Sel is multi-select for Run selected. The row click focuses. The filter stays in the toolbar above.", table, "No suites in this level.")}
  {detail("Checkout totals", '''
    <label class="field">File<input class="fake mono" value="checkout.spec.js" readonly /></label>
    <label class="field">Last<input class="fake" value="Fail · 22 Nov 09:12" readonly /></label>
    <p class="hint">Checked Sel does not open this pane. Run selected uses the toolbar once a Sel cell is on.</p>
    <button class="btn primary" type="button">Run this suite</button>
  ''')}
</div>"""
    inner = stage(
        "suites",
        "Suites",
        '''<button class="btn" type="button">Refresh</button>
        <button class="btn primary" type="button">Run selected</button>
        <input class="filter" type="search" placeholder="Filter title" aria-label="Filter suites" data-lep-filter="1" />''',
        body,
    )
    page(
        "01b-themed-suites.html",
        "Suites — enhancement pack",
        "<strong>Phase 1.</strong> No rail. Filter sits in the existing toolbar. Sel lexicon. Empty preview replaces the scan with one line and the detail with Select a row.",
        "",
        inner,
        anno("No rail · one collection", ["Sel"]),
    )


def plans_cases():
    rows = []
    samples = [
        ("ok", "On", "c1", "Happy path login", "smoke", "Pass"),
        ("warn", "Quar", "c2", "Flaky locator", "regression", "Fail"),
        ("ok", "On", "c3", "Guest search", "smoke", "Pass"),
        ("idle", "Off", "c4", "Archived tax", "nightly", "—"),
        ("ok", "On", "c5", "Cart badge", "smoke", "Pass"),
        ("ok", "On", "c6", "Promo code", "regression", "Pass"),
        ("warn", "Fail", "c7", "Pay button", "smoke", "Fail"),
        ("ok", "On", "c8", "Address book", "regression", "Pass"),
    ]
    for kind, word, cid, title, tags, last in samples:
        rows.append(
            named((pill(kind, word), f'<span class="mono">{cid}</span>', title, tags, pill(kind if kind != "idle" else "idle", last)), title)
        )
    table = scan('data-plan-cases-scan="1"', ["Status", "Id", "Name", "Tags", "Last"], rows, focus=0)
    inner_detail = """
    <section class="sec" data-lep-sections="edit"><h4>Edit</h4>
      <label class="field">Name<input class="fake" value="Happy path login" readonly /></label>
      <label class="field">Tags<input class="fake" value="smoke" readonly /></label>
      <div class="bool-row" data-lep-bool="case">
        <label class="compact-check"><input type="checkbox" checked /> Enabled</label>
        <label class="compact-check"><input type="checkbox" /> Archived</label>
      </div>
    </section>
    <section class="sec" data-lep-sections="run"><h4>Run</h4>
      <p class="fake">Last pass · 22 Nov 09:12 · lab-local</p>
      <p class="hint">Run itself is pinned below. This section is the record.</p>
    </section>
    <section class="sec" data-lep-sections="quarantine"><h4>Quarantine</h4>
      <label class="compact-check"><input type="checkbox" /> Quarantined</label>
      <label class="field">Reason<input class="fake" value="" placeholder="Why this case is held" readonly /></label>
    </section>
    <section class="sec" data-lep-sections="known"><h4>Known issue</h4>
      <label class="field">Issue<input class="fake" value="KAN-410" readonly /></label>
      <p class="hint">Label only. Nothing is filed from this mock.</p>
    </section>
    """
    pin = '<button class="btn primary" type="button">Save</button><button class="btn" type="button">Run</button>'
    tabs = """<div class="area-tabs" role="tablist" data-lep-tabs="1">
      <button type="button" data-tab="draft">Draft</button>
      <button type="button" data-tab="cases" aria-selected="true">Cases</button>
      <button type="button" data-tab="coverage">Coverage</button>
      <button type="button" data-tab="trace">Trace</button>
      <button type="button" data-tab="history">History</button>
      <button type="button" data-tab="run">Run</button>
    </div>"""
    notes = "".join(
        f'<div class="panel" data-panel="{pid}" hidden><div class="work"><p class="hint">See 01d-themed-plans-tabs.html for {label}.</p></div></div>'
        for pid, label in (
            ("draft", "Draft"),
            ("coverage", "Coverage"),
            ("trace", "Trace"),
            ("history", "History"),
            ("run", "Run"),
        )
    )
    body = f"""{tabs}
<div class="split two panel" data-panel="cases">
  {work("Cases", "Show archived is a compact check in the toolbar. Enabled and Archived sit in Edit, not a page-width stack.", table, "No cases.")}
  {detail("Happy path login", inner_detail, pin=pin)}
</div>
{notes}"""
    inner = stage(
        "plans-cases",
        "Plans",
        '''<span class="fake">Checkout smoke</span>
        <button class="btn" type="button">Open</button>
        <button class="btn" type="button">Refresh</button>
        <label class="compact-check" data-lep-bool="show-archived"><input type="checkbox" /> Show archived</label>''',
        body,
        tabset=True,
    )
    page(
        "01c-themed-plans-cases.html",
        "Plans · Cases — enhancement pack",
        "<strong>Phase 1.</strong> In-area tabs stay (two-plus jobs, no second rail). Case detail is four sections. Save and Run stay pinned while the detail body scrolls. Booleans are compact.",
        "",
        inner,
        anno("In-area tabs · plan jobs", ["Enabled"], extra='<span class="chip">Archived</span>'),
    )


def plans_tabs():
    coverage = scan(
        'data-plan-coverage-scan="1"',
        ["Story", "Gap", "Summary"],
        [
            named(("KAN-410", pill("warn", "No case"), "Checkout totals"), "KAN-410"),
            named(("KAN-411", pill("idle", "All disabled"), "Guest search"), "KAN-411"),
            named(("KAN-412", pill("ok", "Covered"), "Cart badge"), "KAN-412"),
            named(("KAN-413", pill("warn", "No case"), "Promo code"), "KAN-413"),
        ],
    )
    trace = scan(
        'data-plan-trace-scan="1"',
        ["Story", "Cases", "Last", "Bugs", "Known"],
        [
            named(("KAN-410", "2", pill("warn", "Fail"), "KAN-88", "No"), "KAN-410"),
            named(("KAN-412", "1", pill("ok", "Pass"), "—", "No"), "KAN-412"),
            named(("KAN-414", "3", pill("ok", "Pass"), "—", "Yes"), "KAN-414"),
        ],
    )
    history = scan(
        'data-plan-history-scan="1"',
        ["A", "B", "Time", "Dur", "Pass", "Fail", "Tag"],
        [
            named(("on", "", "22 Nov 09:10", "42s", "8", "1", "smoke"), "22 Nov 09:10"),
            named(("", "on", "21 Nov 18:02", "40s", "9", "0", "smoke"), "21 Nov 18:02"),
            named(("", "", "20 Nov 11:14", "38s", "7", "2", "nightly"), "20 Nov 11:14"),
        ],
        group="hist",
    )
    tabs = """<div class="area-tabs" role="tablist" data-lep-tabs="1">
      <button type="button" data-tab="draft">Draft</button>
      <button type="button" data-tab="cases">Cases · 01c</button>
      <button type="button" data-tab="coverage" aria-selected="true">Coverage</button>
      <button type="button" data-tab="trace">Trace</button>
      <button type="button" data-tab="history">History</button>
      <button type="button" data-tab="run">Run</button>
    </div>"""
    body = f"""{tabs}
<div class="split two panel" data-panel="coverage">
  {work("Coverage gaps", "No checkbox. Row focuses the gap. Creating a case stays on Cases.", coverage, "No gaps.")}
  {detail("KAN-410", "<p class=\"hint\">Checkout totals has no case. This pane does not mint one.</p>")}
</div>
<div class="split two panel" data-panel="trace" hidden>
  {work("Traceability", "Row opens the case. No Sel column.", trace, "No trace rows.")}
  {detail("KAN-410", "<button class=\"btn\" type=\"button\">Open case</button><p class=\"hint\">Lands on Cases (01c). This pack does not add a second editor.</p>")}
</div>
<div class="split two panel" data-panel="history" hidden>
  {work("Suite history", "A and B are radio cells. Row focus is separate from the compare slot.", history, "No runs yet.")}
  {detail("22 Nov 09:10", "<p class=\"fake\">run-synth-14 · 8 pass · 1 fail</p><button class=\"btn primary\" type=\"button\">Compare A and B</button>")}
</div>
<div class="split two panel" data-panel="draft" hidden>
  <div class="work scroll-host">
    <div class="work-head"><h3>Draft &amp; import</h3><p class="hint">Compact form. Not a scan. Import never deletes external Playwright files.</p></div>
    <div class="pane-scroll">
      <div class="stack">
        <label class="field">Issue key<input class="fake" value="KAN-410" readonly /></label>
        <label class="field">Document<input class="fake" value="checkout-spec.md" readonly /></label>
        <button class="btn primary" type="button">Draft from story</button>
      </div>
    </div>
  </div>
  {detail("Draft result", "<p class=\"fake\">3 draft cases · 0 written to Jira</p>")}
</div>
<div class="split two panel" data-panel="run" hidden>
  <div class="work scroll-host">
    <div class="work-head"><h3>Run setup</h3><p class="hint">Pause on fail is a compact check in the row of options, not a page-width label.</p></div>
    <div class="pane-scroll">
      <div class="stack">
        <label class="field">Environment<select class="fake"><option>lab-local</option></select></label>
        <label class="field">Sandbox<select class="fake"><option>Normal browser profile</option></select></label>
        <div class="bool-row" data-lep-bool="pause-on-fail">
          <label class="compact-check"><input type="checkbox" /> Pause on fail</label>
        </div>
        <details class="advanced"><summary>Scheduled local run</summary><p class="hint">Collapsed. Missed slots are not a pass.</p></details>
        <button class="btn primary" type="button">Run by tag</button>
      </div>
    </div>
  </div>
  {detail("Run record", "<p class=\"hint\">Credentials stay in Settings. Environment does not switch security level.</p>")}
</div>
<div class="panel" data-panel="cases" hidden><div class="work"><p class="hint">Cases sections, pinned Save/Run, and Show archived / Enabled / Archived are in 01c-themed-plans-cases.html.</p></div></div>
"""
    inner = stage(
        "plans-tabs",
        "Plans",
        '<span class="fake">Checkout smoke</span><button class="btn" type="button">Refresh</button>',
        body,
        tabset=True,
    )
    page(
        "01d-themed-plans-tabs.html",
        "Plans · other tabs — enhancement pack",
        "<strong>Phase 1.</strong> Coverage, Trace, History, Draft, Run. History uses A/B radio cells. Run keeps Pause on fail compact. Cases itself is 01c. Click the tabs.",
        "",
        inner,
        anno("In-area tabs · plan jobs", ["A", "B"]),
    )


def reports():
    rows = []
    samples = [
        ("22 Nov 09:12", "Checkout smoke", "Run"),
        ("21 Nov 16:40", "Read-only pack", "Pack"),
        ("21 Nov 11:02", "Guest search", "Run"),
        ("20 Nov 18:20", "Nightly pack", "Pack"),
        ("20 Nov 09:14", "Cart badge", "Run"),
        ("19 Nov 15:01", "Promo code", "Run"),
        ("18 Nov 12:44", "Address book", "Run"),
        ("17 Nov 08:05", "Stock lookup", "Run"),
    ]
    for when, title, kind in samples:
        rows.append(named((when, title, "OFFICIAL", kind), title))
    table = scan('data-rpt-scan="1"', ["When", "Title", "Level", "Kind"], rows)
    body = f"""<div class="split two">
  {work("Saved reports", "No section rail. Row opens the markdown. Section include/exclude stays in Settings.", table, "No saved reports.")}
  {detail("Checkout smoke", '''
    <label class="field">Id<input class="fake mono" value="rpt-synth-09" readonly /></label>
    <pre class="diff"># Checkout smoke
Passed 8 · Failed 1
Story KAN-410 covered.</pre>
  ''', evidence=True)}
</div>"""
    inner = stage(
        "reports",
        "Reports",
        '''<button class="btn" type="button">Refresh library</button>
        <button class="btn" type="button">Report settings</button>
        <button class="btn" type="button">Export…</button>
        <input class="filter" type="search" placeholder="Filter title" aria-label="Filter reports" data-lep-filter="1" />''',
        body,
    )
    page(
        "01e-themed-reports.html",
        "Reports — enhancement pack",
        "<strong>Phase 1</strong> filter in the existing toolbar. <strong>Phase 2</strong> evidence hint is dashed in the detail and is not a build target yet.",
        "",
        inner,
        anno("No rail · one collection", [], extra='<span class="chip phase2">Evidence · Phase 2</span>'),
    )


def documents():
    diff = scan(
        'data-doc-diff-scan="1"',
        ["Keep", "Key", "From", "To"],
        [
            named(("on", "target_url", "(empty)", "https://shop.example.test"), "target_url"),
            named(("cb", "jira_project", "KAN", "KAN"), "jira_project"),
            named(("cb", "suite_path", "(empty)", "D:\\samples\\shop-pw"), "suite_path"),
        ],
    )
    uploads = scan(
        'data-doc-uploads-scan="1"',
        ["Name", "Time", "Level", "Consent"],
        [
            named(("checkout-spec.md", "22 Nov 08:01", "OFFICIAL", "Yes"), "checkout-spec.md"),
            named(("notes.txt", "20 Nov 11:14", "OFFICIAL", "Yes"), "notes.txt"),
        ],
    )
    tabs = """<div class="area-tabs" role="tablist" data-lep-tabs="1">
      <button type="button" data-tab="propose" aria-selected="true">Propose</button>
      <button type="button" data-tab="uploads">Uploads</button>
    </div>"""
    body = f"""{tabs}
<div class="split two panel" data-panel="propose">
  <div class="work scroll-host">
    <div class="work-head">
      <h3>Proposal</h3>
      <p class="hint">Keep is the checkbox cell. Confirm writes only checked keys after the existing confirm. Toolbar on this tab is Parse only.</p>
    </div>
    <div class="pane-scroll" data-lep-scroll="scan">
      <p class="empty-line" data-lep-empty>No proposal rows.</p>
      <pre class="diff"># Checkout
Target: https://shop.example.test</pre>
      {diff}
    </div>
  </div>
  {detail("target_url", '''
    <p class="hint">From empty to the sample shop host. Decline writes nothing.</p>
    <div class="btn-row">
      <button class="btn primary" type="button">Confirm selected</button>
      <button class="btn" type="button">Decline</button>
    </div>
  ''')}
</div>
<div class="split two panel" data-panel="uploads" hidden>
  {work("Uploads", "Toolbar on this tab is Refresh only. Delete of stored uploads stays on Security → Privacy.", uploads, "No uploads.")}
  {detail("checkout-spec.md", "<p class=\"hint\">Name, time, level, consent. No document body in the list.</p>")}
</div>"""
    inner = stage(
        "documents",
        "Documents",
        '''<button class="btn primary" type="button" data-show="propose">Parse &amp; propose</button>
        <button class="btn" type="button" data-show="uploads" hidden>Refresh</button>''',
        body,
        tabset=True,
    )
    page(
        "01f-themed-documents.html",
        "Documents — enhancement pack",
        "<strong>Phase 1.</strong> Propose | Uploads. The toolbar follows the tab: Parse on Propose, Refresh on Uploads. Keep cell unchanged. Click Uploads.",
        "",
        inner,
        anno("In-area tabs · 2 jobs", ["Keep"]),
    )


def security():
    privacy = scan(
        'data-sec-privacy-scan="1"',
        ["Include", "Artifact"],
        [
            named(("on", "Reports"), "Reports"),
            named(("on", "Screenshots"), "Screenshots"),
            named(("cb", "Heal audit"), "Heal audit"),
            named(("cb", "Sessions (this level)"), "Sessions (this level)"),
            named(("cb", "Uploaded documents"), "Uploaded documents"),
        ],
    )
    audit = scan(
        'data-sec-audit-scan="1"',
        ["Time", "Action", "Ref"],
        [
            named(("22 Nov 09:02", "plan_edit", "plan-synth"), "plan_edit"),
            named(("21 Nov 18:11", "privacy_wipe", "OFFICIAL"), "privacy_wipe"),
            named(("21 Nov 12:00", "backup_create", "OFFICIAL"), "backup_create"),
            named(("20 Nov 09:40", "level_switch", "propose"), "level_switch"),
        ],
    )
    rails = [
        ("level", "Level"),
        ("privacy", "Privacy"),
        ("audit", "Audit"),
        ("redact", "Redaction"),
        ("backup", "Backup"),
    ]
    buttons = []
    for pid, label in rails:
        cur = ' aria-current="true"' if pid == "privacy" else ""
        buttons.append(f'<button type="button" data-tab="{pid}"{cur}>{label}</button>')
    body = f"""<div class="split">
  <nav class="rail" data-lep-rail="1" aria-label="Security sections">
    <p class="rail-label">Sections</p>
    {"".join(buttons)}
  </nav>
  <div class="work scroll-host">
    <div class="panel pane-fill" data-panel="privacy">
      <div class="work-head"><h3>Local data to wipe</h3>
        <p class="hint">Include is a dedicated cell. The row does not toggle it. One level is shown.</p></div>
      <div class="pane-scroll" data-lep-scroll="scan">
        <p class="empty-line" data-lep-empty>No local artifacts.</p>
        {privacy}
      </div>
    </div>
    <div class="panel pane-fill" data-panel="audit" hidden>
      <div class="work-head"><h3>Local side-effects</h3><p class="hint">Time, action, id. No document bodies.</p></div>
      <div class="pane-scroll" data-lep-scroll="scan">
        <p class="empty-line" data-lep-empty>No audit rows.</p>
        {audit}
      </div>
    </div>
    <div class="panel pane-fill" data-panel="level" hidden>
      <div class="work-head"><h3>Classification</h3><p class="hint">Switch takes effect only after Confirm.</p></div>
      <div class="pane-scroll"><label class="field">Proposed level<select class="fake"><option>SECRET</option></select></label></div>
    </div>
    <div class="panel pane-fill" data-panel="redact" hidden>
      <div class="work-head"><h3>Redaction status</h3></div>
      <div class="pane-scroll">
        <p class="empty-line" data-lep-empty>No redaction runs.</p>
        <p class="fake">Export redaction on · 3 pattern hits · screenshots not OCR-redacted</p>
      </div>
    </div>
    <div class="panel pane-fill" data-panel="backup" hidden>
      <div class="work-head"><h3>Backups for this level</h3></div>
      <div class="pane-scroll">
        <p class="empty-line" data-lep-empty>No backups.</p>
        <p class="fake">22 Nov 07:00 · OFFICIAL · secrets no</p>
      </div>
    </div>
  </div>
  <aside class="detail scroll-host">
    <div class="panel pane-fill" data-panel="privacy">
      <div class="detail-live pane-scroll">
        <h3 data-lep-focus-name>Reports</h3>
        <p class="hint">Credentials and settings are not deleted here.</p>
        <div class="danger-zone">
          <button class="btn danger" type="button">Delete local data…</button>
          <button class="btn" type="button" disabled>Confirm delete</button>
        </div>
      </div>
      <div class="detail-empty" data-lep-unfocused><h3>Detail</h3><p class="empty-line">Select a row</p></div>
    </div>
    <div class="panel pane-fill" data-panel="audit" hidden>
      <div class="detail-live pane-scroll"><h3>plan_edit</h3><p class="fake">plan-synth · OFFICIAL</p></div>
      <div class="detail-empty"><h3>Detail</h3><p class="empty-line">Select a row</p></div>
    </div>
    <div class="panel pane-fill" data-panel="level" hidden>
      <div class="detail-live pane-scroll"><h3>Switch</h3>
        <p class="hint">Profile name only. Stores stay unmixed.</p>
        <button class="btn" type="button">Switch level</button></div>
      <div class="detail-empty"><h3>Detail</h3><p class="empty-line">Select a row</p></div>
    </div>
    <div class="panel pane-fill" data-panel="redact" hidden>
      <div class="detail-live pane-scroll"><h3>Evidence</h3><p class="hint">Hit counts only. Never echo a matched secret.</p></div>
      <div class="detail-empty"><h3>Detail</h3><p class="empty-line">Select a row</p></div>
    </div>
    <div class="panel pane-fill" data-panel="backup" hidden>
      <div class="detail-live pane-scroll"><h3>Restore</h3>
        <label class="compact-check"><input type="checkbox" /> Include settings (no secrets)</label>
        <label class="compact-check"><input type="checkbox" /> Include secrets — off by default</label>
        <div class="danger-zone"><button class="btn danger" type="button">Restore…</button></div>
      </div>
      <div class="detail-empty"><h3>Detail</h3><p class="empty-line">Select a row</p></div>
    </div>
  </aside>
</div>"""
    inner = stage("security", "Security", "<span>Active level OFFICIAL · profile-official-local</span>", body, tabset=True)
    page(
        "01g-themed-security.html",
        "Security — enhancement pack",
        "<strong>Phase 1.</strong> Rail of five sections. Include cell. Masked status. One level. Empty preview is one line, not a privacy dashboard.",
        "",
        inner,
        anno("Rail · ≥3 sections", ["Include"]),
    )


def heal():
    rows = [
        named(("on", pill("warn", "Test defect"), "getByRole button Checkout", "run-synth-14", "22 Nov 09:14"), "Checkout"),
        named(("on", pill("idle", "Unclassified"), "css .pay", "run-synth-11", "21 Nov 16:02"), "css .pay"),
        named(("cb", pill("warn", "Test defect"), "getByLabel Total", "run-synth-14", "22 Nov 09:15"), "Total"),
        named(("cb", pill("ok", "Product bug"), "css .stock", "run-synth-09", "19 Nov 12:11"), "stock"),
    ]
    table = scan('data-heal-scan="1"', ["Sel", "Class", "Locator", "Run", "When"], rows)
    sheet = """<div class="confirm-sheet" data-lep-heal-confirm role="region" aria-label="Approve selected">
      <strong>Approve 2 proposals?</strong>
      <p class="hint">Files are not written. Reject is not part of this step.</p>
      <div class="btn-row">
        <button class="btn primary" type="button">Confirm approve</button>
        <button class="btn" type="button">Cancel</button>
      </div>
    </div>"""
    body = f"""<div class="split two">
  {work("Pending proposals", "Sel selects for the toolbar. It does not approve. The row focuses one proposal.", table, "No pending proposals.")}
  {detail("Checkout", sheet + '''
    <label class="field">Id<input class="fake mono" value="heal-synth-3" readonly /></label>
    <pre class="diff">locator: getByRole button Checkout
proposed: getByRole('button', { name: 'Checkout' })</pre>
    <p class="hint">Reject stays on this focused proposal. There is no Reject selected.</p>
    <div class="btn-row">
      <button class="btn primary" type="button">Approve</button>
      <button class="btn" type="button">Reject</button>
    </div>
  ''', evidence=True)}
</div>"""
    inner = stage(
        "heal",
        "Heal",
        '''<span class="fake">All pending</span>
        <button class="btn" type="button">Refresh</button>
        <button class="btn primary" type="button" data-heal-bulk="1">Approve selected (2)</button>''',
        body,
    )
    page(
        "01h-themed-heal.html",
        "Heal — enhancement pack",
        "<strong>Phase 1.</strong> Bulk confirm names the count and says files are not written. Reject stays in the detail. <strong>Phase 2</strong> evidence hint is dashed.",
        "",
        inner,
        anno("No rail · one collection", ["Sel"], extra='<span class="chip phase2">Evidence · Phase 2</span>'),
    )


def manual():
    rows = [
        named(("22 Nov 10:02", "Explore checkout errors", "KAN-410", "Review"), "Explore checkout errors"),
        named(("21 Nov 15:18", "Guest search empty", "—", "Ended"), "Guest search empty"),
        named(("20 Nov 11:02", "Cart badge drift", "KAN-411", "Ended"), "Cart badge drift"),
        named(("19 Nov 09:40", "Promo copy", "—", "Ended"), "Promo copy"),
    ]
    table = scan(
        'data-manual-session-scan="1"',
        ["When", "Charter", "Link", "Stage"],
        rows,
    )
    start = """<details class="start-fold" data-lep-start-collapse>
      <summary>Start session</summary>
      <div class="stack">
        <label class="field">Charter<textarea class="fake" rows="3">Explore checkout errors on the sample shop.</textarea></label>
        <label class="compact-check"><input type="checkbox" /> Link to Jira</label>
        <label class="compact-check"><input type="checkbox" /> Agent assist (recommended off)</label>
        <label class="compact-check"><input type="checkbox" /> Armed mist (recommended off)</label>
        <button class="btn primary" type="button">Start session</button>
      </div>
    </details>"""
    body = f"""<div class="split two">
  {work("Session library", "A focused session collapses Start. Charter Frame is not in this frame.", table, "No sessions.", extra=start)}
  {detail("Explore checkout errors", '''
    <label class="field">Link<input class="fake" value="KAN-410" readonly /></label>
    <p class="hint">Propose stays a deliberate button. The dock below is one line.</p>
    <div class="btn-row">
      <button class="btn" type="button">Propose bug</button>
      <button class="btn" type="button">Propose comment</button>
    </div>
  ''', evidence=True)}
</div>
<div class="dock" data-lep-dock="1" data-manual-confirm-dock="1">
  <span class="summary">Bug · KAN-410 · Explore checkout errors — writes on Confirm</span>
  <button class="btn primary" type="button">Confirm</button>
  <button class="btn" type="button">Cancel</button>
</div>"""
    inner = stage(
        "manual",
        "Manual",
        '''<button class="btn" type="button">Clear linked context</button>
        <button class="btn" type="button">Open Plans</button>
        <button class="btn" type="button">Refresh library</button>''',
        body,
    )
    page(
        "01i-themed-manual.html",
        "Manual — enhancement pack",
        "<strong>Phase 1.</strong> Focused session: Start is collapsed. Confirm dock is one line. Charter Frame is untouched and not drawn. <strong>Phase 2</strong> evidence hint only. FR-MAN-2 is out.",
        "",
        inner,
        anno("No rail · one collection", [], extra='<span class="chip phase2">Evidence · Phase 2</span>'),
    )


def desktop():
    table = scan(
        'data-desk-scan="1"',
        ["Enabled", "Status", "Path", "Last smoke"],
        [named(("on", pill("ok", "Ready"), '<span class="mono">D:\\samples\\Shop.exe</span>', "Pass · 22 Nov 09:20"), "Shop.exe")],
    )
    extra = """<details class="advanced" data-lep-advanced>
      <summary>Advanced</summary>
      <label class="field">Launch args<input class="fake mono" value="--sample" readonly /></label>
      <label class="field">Window title<input class="fake" value="Shop sample" readonly /></label>
      <p class="hint">Closed by default. This is not TRACK3-LAB density.</p>
    </details>"""
    body = f"""<div class="split two">
  {work("Desktop target", "One target, still a scan row. Enabled is the cell. Advanced stays closed.", table, "No desktop target.", extra=extra)}
  {detail("Shop.exe", '''
    <label class="field">Exe path<input class="fake mono" value="D:\\samples\\Shop.exe" readonly /></label>
    <p class="hint">Separate from Playwright. Save lives here.</p>
    <button class="btn" type="button">Save plugin</button>
  ''')}
</div>"""
    inner = stage(
        "desktop",
        "Desktop",
        '<button class="btn primary" type="button">Run smoke</button><button class="btn" type="button">Run demo steps</button>',
        body,
    )
    page(
        "01j-themed-desktop.html",
        "Desktop Lab — enhancement pack",
        "<strong>Phase 1.</strong> Progressive disclosure: Advanced is a closed details element. Not a lab dashboard. Synthetic exe path.",
        "",
        inner,
        anno("No rail · one collection", ["Enabled"]),
    )


def sandboxes():
    table = scan(
        'data-ms-scan="1"',
        ["Id", "Label", "URL", "Ready"],
        [
            named(("primary", "Sample shop", '<span class="mono">https://shop.example.test</span>', pill("ok", "Prepared")), "primary"),
            named(("guest", "Guest mirror", '<span class="mono">https://guest.example.test</span>', pill("idle", "Planned")), "guest"),
        ],
    )
    extra = """<details class="advanced" data-lep-advanced>
      <summary>Advanced</summary>
      <label class="field">Profile folder<input class="fake mono" value="D:\\samples\\profiles\\primary" readonly /></label>
      <label class="compact-check"><input type="checkbox" /> Headed</label>
      <p class="hint">Closed by default. Local only. No cloud farm panels.</p>
    </details>"""
    body = f"""<div class="split two">
  {work("Sandbox list", "No select column. Row focuses. Remove waits in the detail. Advanced stays closed.", table, "No sandboxes.", extra=extra)}
  {detail("primary", '''
    <label class="field">URL<input class="fake mono" value="https://shop.example.test" readonly /></label>
    <button class="btn" type="button">Save sandbox</button>
    <div class="danger-zone">
      <button class="btn danger" type="button">Remove…</button>
      <button class="btn" type="button" disabled>Confirm remove</button>
    </div>
  ''')}
</div>"""
    inner = stage(
        "sandboxes",
        "Sandboxes",
        '<label class="compact-check"><input type="checkbox" checked /> Enable multi-sandbox</label><button class="btn primary" type="button">Orchestrate</button>',
        body,
    )
    page(
        "01k-themed-sandboxes.html",
        "Sandboxes Lab — enhancement pack",
        "<strong>Phase 1.</strong> Advanced closed. Enable stays a compact toolbar check. Not TRACK3-LAB density. Synthetic hosts only.",
        "",
        inner,
        anno("No rail · one collection", [], extra='<span class="chip muted">Enable · toolbar check</span>'),
    )


def wire():
    empty = """<div class="stage mini force-empty">
      <header class="frozen-bar"><h1 class="area-title">Empty contract</h1><span class="frozen-tag">Static</span></header>
      <div class="split two">
        <div class="work scroll-host">
          <div class="work-head"><h3>Scan</h3></div>
          <div class="pane-scroll" data-lep-scroll="scan">
            <p class="empty-line" data-lep-empty>No rows in this level.</p>
            <table class="scan"><thead><tr><th>Name</th></tr></thead><tbody><tr><td>hidden</td></tr></tbody></table>
          </div>
        </div>
        <aside class="detail scroll-host">
          <div class="detail-live pane-scroll"><h3>Hidden while empty</h3></div>
          <div class="detail-empty" data-lep-unfocused><h3>Detail</h3><p class="empty-line">Select a row</p></div>
        </aside>
      </div>
    </div>"""
    rows = "".join(f"<tr class='row-hit{' is-focus' if i == 2 else ''}'><td>row {i}</td><td>OFFICIAL</td></tr>" for i in range(1, 14))
    scroll = f"""<div class="stage mini">
      <header class="frozen-bar"><h1 class="area-title">One scroll each</h1><span class="frozen-tag">Static</span></header>
      <div class="split two" data-lep-no-outer-scroll="1">
        <div class="work scroll-host">
          <div class="work-head"><h3>Scan scroller</h3><p class="hint">Thead sticks here only. The stage does not scroll.</p></div>
          <div class="pane-scroll" data-lep-scroll="scan">
            <table class="scan" data-lep-sticky="1"><thead><tr><th>Row</th><th>Level</th></tr></thead><tbody>{rows}</tbody></table>
          </div>
        </div>
        <aside class="detail scroll-host">
          <div class="detail-live pane-scroll"><h3>Detail scroller</h3>
            <p class="hint">This pane scrolls on its own. No third scroll on the split.</p>
            <p class="fake">Field</p><p class="fake">Field</p><p class="fake">Field</p><p class="fake">Field</p><p class="fake">Field</p><p class="fake">Field</p>
          </div>
        </aside>
      </div>
    </div>"""
    def token(title, chrome, blurb):
        return f"""<div class="stage mini">
          <header class="frozen-bar"><h1 class="area-title">{title}</h1></header>
          {chrome}
          <div class="work" style="padding:12px"><p class="hint">{blurb}</p></div>
        </div>"""
    rail = token(
        "Settings",
        '<nav class="rail"><p class="rail-label">Sections</p><button type="button" aria-current="true">One</button><button type="button">Two</button><button type="button">Three</button></nav>',
        "Rail when the area has three or more real sections. Settings, Security.",
    )
    # rail token above doesn't use split; the rail will just be a block. Better a tiny split.
    rail = f"""<div class="stage mini">
      <header class="frozen-bar"><h1 class="area-title">Rail</h1><span class="frozen-tag">≥3</span></header>
      <div class="split"><nav class="rail"><p class="rail-label">Sections</p><button type="button" aria-current="true">Privacy</button><button type="button">Audit</button><button type="button">Backup</button></nav>
      <div class="work"><p class="hint">Settings and Security. Do not add a second rail beside tabs.</p></div>
      <aside class="detail"><h3>Detail</h3><p class="empty-line" style="display:block">Select a row</p></aside></div>
    </div>"""
    tabs = """<div class="stage mini">
      <header class="frozen-bar"><h1 class="area-title">Tabs</h1><span class="frozen-tag">2 jobs</span></header>
      <div class="area-tabs"><button type="button" aria-selected="true">Propose</button><button type="button">Uploads</button></div>
      <div class="work" style="padding:12px"><p class="hint">Plans tabs (FR-UI-9) and Documents Propose | Uploads. Not a new App nav item.</p></div>
    </div>"""
    none = """<div class="stage mini">
      <header class="frozen-bar"><h1 class="area-title">No rail</h1><span class="frozen-tag">1 collection</span></header>
      <div class="work" style="padding:12px"><p class="hint">Suites, Reports, Heal, Manual, Desktop, Sandboxes. Scan plus detail only.</p></div>
    </div>"""
    inner = f"""<div class="rule-card">
  <h2>Chrome rule</h2>
  <p>Vertical rail at three or more sections. In-area tabs for two jobs. No rail for one collection. Theme, orb, home/chat, and App nav stay locked.</p>
</div>
<div class="trio">{rail}{tabs}{none}</div>
<div class="rule-card">
  <h2>Checkbox verb lexicon</h2>
  <table class="lex-table" data-lep-lexicon="1">
    <thead><tr><th>Verb</th><th>Means</th><th>Where</th></tr></thead>
    <tbody>
      <tr><td>Sel</td><td>Multi-select for a toolbar action. Never Approve or Reject by itself.</td><td>Suites, Heal</td></tr>
      <tr><td>Keep</td><td>Include this key in a confirm write.</td><td>Documents propose</td></tr>
      <tr><td>Include</td><td>This artifact or block is in the action.</td><td>Settings report blocks, Security wipe</td></tr>
      <tr><td>Enabled</td><td>Plugin or target on.</td><td>Desktop cell; Plans case compact check</td></tr>
      <tr><td>A · B</td><td>Compare slot. Radio, not a toggle of the row.</td><td>Plans History</td></tr>
    </tbody>
  </table>
  <p class="callout">Show archived, Archived, and Pause on fail are compact booleans, not scan-column verbs.</p>
</div>
<div class="pair">{empty}{scroll}</div>
<div class="rule-card">
  <h2>Keyboard</h2>
  <p><span class="kbd">↑</span> <span class="kbd">↓</span> move the focused row inside the scan. <span class="kbd">Enter</span> keeps that row’s detail open. <span class="kbd">Space</span> activates only a focused checkbox or radio cell. Space on the row does nothing.</p>
  <p class="callout">Click Empty preview on any themed file to see the one-line empty scan. The dashed chip row above each themed stage is a Studio note and does not ship.</p>
</div>
"""
    page(
        "00-structure-wire.html",
        "Layout enhancement pack — structure wire",
        "<strong>System rules</strong> for every secondary area. Structure, lexicon, empty, scroll, keyboard. Not a new skin.",
        "wire",
        inner,
        "",
        script=False,
    )


AREAS = [
    ("Settings", "01a-themed-settings.html", "Phase 1", "Rail · ≥3", [
        "Section rail remains the only in-area chrome. No second rail and no new App nav item.",
        "Work pane scrolls on its own; detail pane scrolls on its own; the stage does not scroll.",
        "Scan header sticks inside the scan scroller only.",
        "Empty scan is one line (No report blocks / No environments). Unfocused detail reads Select a row.",
        "Up/Down move row focus. Enter shows detail. Space toggles only the Include cell.",
        "Include does not cover the row hit.",
    ], "Settings section markup and environment / report-block render in ui/desktop/index.html, desktop.js, desktop.css."),
    ("Suites", "01b-themed-suites.html", "Phase 1", "No rail", [
        "No section rail.",
        "Filter is one search input in the existing toolbar, not a bar under it.",
        "Sel cell is the only multi-select hit. Row focus is separate.",
        "Same empty, scroll, sticky header, and keyboard contract as the wire.",
    ], "renderSuiteList and the suites toolbar in ui/desktop/index.html, desktop.js, desktop.css."),
    ("Plans · Cases", "01c-themed-plans-cases.html", "Phase 1", "In-area tabs", [
        "FR-UI-9 tabs stay. No rail beside them.",
        "Show archived is a compact check in the toolbar.",
        "Enabled and Archived are compact checks inside the Edit section, not page-width labels.",
        "Detail groups Edit, Run, Quarantine, and Known issue.",
        "Save and Run stay pinned while the detail body scrolls.",
        "Empty detail reads Select a row and hides the pin.",
    ], "renderPlanCases and #plan-cases editor in ui/desktop/index.html, desktop.js, desktop.css."),
    ("Plans · other tabs", "01d-themed-plans-tabs.html", "Phase 1", "In-area tabs", [
        "Coverage and Trace have no checkbox column. Trace row still opens the case.",
        "History A and B are dedicated radio cells.",
        "Pause on fail is a compact check on Run.",
        "Draft stays a compact form.",
        "Scheduled run stays inside a closed details block.",
    ], "Plan Draft, Coverage, Trace, History, and Run panels; #plan-pause-on-fail."),
    ("Reports", "01e-themed-reports.html", "Phase 1 + hint", "No rail", [
        "No rail. Filter sits in the existing toolbar beside Refresh, Report settings, and Export.",
        "Row opens the saved markdown in the detail.",
        "Dashed evidence region is marked Phase 2 and is not a Phase 1 acceptance target.",
    ], "renderReportLibraryList and #rpt-detail. Evidence slot waits for Phase 2."),
    ("Documents", "01f-themed-documents.html", "Phase 1", "In-area tabs · 2 jobs", [
        "Propose shows Parse & propose and hides Refresh.",
        "Uploads shows Refresh and hides Parse.",
        "Keep remains a dedicated cell on the diff.",
        "Confirm / Decline stay in the detail.",
    ], "Documents toolbar and renderDocProposal; uploads list."),
    ("Security", "01g-themed-security.html", "Phase 1", "Rail · ≥3", [
        "Five-section rail stays: Level, Privacy, Audit, Redaction, Backup.",
        "Include is the wipe checkbox cell.",
        "One level (OFFICIAL) and masked status. No secret values.",
        "Delete and Restore stay propose-then-confirm in the detail.",
        "Empty state is one line, not a dashboard.",
    ], "Security rail panels in ui/desktop/index.html, desktop.js, desktop.css."),
    ("Heal", "01h-themed-heal.html", "Phase 1 + hint", "No rail", [
        "Sel does not approve. The row does not approve.",
        "Approve selected (N) states the count.",
        "Confirm copy includes that files are not written.",
        "Reject exists only on the focused detail. No Reject selected control.",
        "Evidence hint is Phase 2.",
    ], "renderHealProposals, data-heal-bulk, heal confirm copy. Do not add bulk Reject."),
    ("Manual", "01i-themed-manual.html", "Phase 1 + hint", "No rail", [
        "When a session row is focused, Start session is collapsed.",
        "Confirm dock is one line: kind, link, charter summary, Confirm, Cancel.",
        "Charter Frame (#charter-frame-root and related nodes) is not restyled and is not in the mock.",
        "Evidence hint is Phase 2. FR-MAN-2 circles are out.",
    ], "Manual session list, start block, confirm dock. Do not edit charter frame markup for this pack."),
    ("Desktop", "01j-themed-desktop.html", "Phase 1", "No rail", [
        "Single target remains a scan row. Enabled is the cell.",
        "Advanced is a closed details element (launch args, window title).",
        "No extra lab panels, no voice chrome.",
    ], "Desktop target row and Advanced disclosure."),
    ("Sandboxes", "01k-themed-sandboxes.html", "Phase 1", "No rail", [
        "No select column. Enable multi-sandbox stays a compact toolbar check.",
        "Advanced is closed (profile folder, headed).",
        "Remove stays in the detail behind confirm.",
        "No cloud-farm or TRACK3-LAB boards.",
    ], "renderSandboxList and the sandbox detail form."),
]


def annotated():
    chunks = ["""<div class="notes">
  <h2>How to read the markers</h2>
  <p>These attributes live on the mock HTML so a later Build slice can map acceptance checks. They are not a new product API.</p>
  <ul>
    <li><code>data-layout-enhancement-pack</code> stage root</li>
    <li><code>data-lep-area</code> settings, suites, plans-cases, plans-tabs, reports, documents, security, heal, manual, desktop, sandboxes</li>
    <li><code>data-lep-empty</code> one-line empty scan · <code>data-lep-unfocused</code> Select a row</li>
    <li><code>data-lep-kbd</code> keyboard note (Studio bar, do not ship the bar)</li>
    <li><code>data-lep-scroll</code> pane scroller · <code>data-lep-sticky</code> on the wire’s scan · <code>data-lep-no-outer-scroll</code></li>
    <li><code>data-lep-structure</code> rail / tabs / no rail · <code>data-lep-lexicon</code></li>
    <li><code>data-lep-bool</code> Show archived, case Enabled/Archived, Pause on fail</li>
    <li><code>data-lep-sections</code> Edit / Run / Quarantine / Known issue · <code>data-lep-pin</code> Save + Run</li>
    <li><code>data-show</code> Documents toolbar scope · <code>data-lep-heal-confirm</code></li>
    <li><code>data-lep-advanced</code> Desktop and Sandboxes · <code>data-lep-start-collapse</code> · <code>data-lep-dock</code></li>
    <li><code>data-lep-filter</code> Suites and Reports · <code>data-lep-evidence="phase2"</code></li>
  </ul>
  <h2>Phase split</h2>
  <p><strong>Phase 1</strong> is structure craft on the shipped FR-UI-11 grammar: empty, keyboard, one scroll, sticky header, lexicon labels, Plans booleans and sections, Documents toolbar scope, Heal confirm copy, Manual focus chrome, toolbar filters, closed Advanced. <strong>Phase 2</strong> is the evidence hint on Reports, Heal, and Manual only. Do not block Phase 1 on it.</p>
  <p>Suggested epic (draft, not created): Layout enhancement pack — FR-UI-11 craft. One story per cluster below, each with a linked test ticket, after Designer accept and a Council pass on whether the keyboard line and the Phase 2 slot need spec text.</p>
  <h2>Do not edit in Design Studio</h2>
  <p><code>ui/desktop/index.html</code>, <code>ui/desktop/desktop.js</code>, <code>ui/desktop/desktop.css</code>, <code>desktop_app.py</code>. Charter frame nodes stay out of this pack. Orb, home/chat, and App nav stay locked.</p>
"""]
    for title, filename, phase, chrome, acs, files in AREAS:
        items = "".join(f"<li>{a}</li>" for a in acs)
        chunks.append(f"""<h2>{title}</h2>
  <p><code>{filename}</code> · {phase} · {chrome}</p>
  <ul>{items}</ul>
  <p>Later files: {files}</p>""")
    chunks.append("""<h2>Shared keyboard and empty acceptance</h2>
  <ul>
    <li>With focus in the scan, Up and Down move <code>is-focus</code> and do not toggle a checkbox.</li>
    <li>Enter leaves the quiet-empty state and shows the focused detail.</li>
    <li>Space on a row does nothing. Space on a checkbox or radio cell toggles that control only.</li>
    <li>Empty preview: scan body hidden, one dashed line, detail reads Select a row, Plans pin hidden.</li>
  </ul>
</div>""")
    page(
        "02-annotated-build-note.html",
        "Layout enhancement pack — build note",
        "<strong>Build notes.</strong> Markers and acceptance bullets per area. Product UI is not part of this Studio pass.",
        "",
        "".join(chunks),
        "",
        script=False,
    )


def rejected():
    inner = """<div class="reject-grid">
  <article class="reject-card">
    <h2>KPI / hero dashboard</h2>
    <div class="kpi-row"><div class="kpi"><b>12</b><span>Passed</span></div><div class="kpi"><b>3</b><span>Open</span></div><div class="kpi"><b>99%</b><span>Health</span></div></div>
    <p class="why">Pretty-empty. Hides the scan a tester came to read. Rejected again for every secondary area.</p>
  </article>
  <article class="reject-card">
    <h2>Whole-row toggle</h2>
    <div class="soup">
      <label><input type="checkbox" checked /> Checkout totals — the label is the hit</label>
      <label><input type="checkbox" /> Guest search — row and check are the same control</label>
    </div>
    <p class="why">Checkbox and row stay different hits. Space does not toggle from the row.</p>
  </article>
  <article class="reject-card">
    <h2>Bulk Heal Reject</h2>
    <p><span class="btn danger">Reject selected (2)</span></p>
    <p class="why">Reject stays on the focused proposal. Bulk approve may confirm. Bulk reject does not ship in this pack.</p>
  </article>
  <article class="reject-card">
    <h2>TRACK3-LAB, voice, FR-MAN-2</h2>
    <div class="kpi-row"><div class="kpi"><b>Lab</b><span>Density board</span></div><div class="kpi"><b>Voice</b><span>KAN-81</span></div><div class="kpi"><b>Circles</b><span>FR-MAN-2</span></div></div>
    <p class="why">Deferred until Active Build is set. Desktop and Sandboxes only close an Advanced disclosure. Charter Frame is untouched.</p>
  </article>
  <article class="reject-card">
    <h2>Second filter bar</h2>
    <div class="toolbar"><span>Refresh</span></div>
    <div class="toolbar"><input class="filter" placeholder="A bar under the toolbar" /></div>
    <p class="why">Suites and Reports put the optional filter in the toolbar that already exists.</p>
  </article>
  <article class="reject-card">
    <h2>Page-width stack label</h2>
    <div class="soup">
      <label><input type="checkbox" /> Show archived — full width of the page</label>
      <label><input type="checkbox" /> Pause on fail — same pattern</label>
    </div>
    <p class="why">Those booleans are compact checks: toolbar or a horizontal row inside Edit / Run.</p>
  </article>
  <article class="reject-card">
    <h2>Evidence gallery</h2>
    <div class="kpi-row"><div class="kpi"><b>Shot</b><span>Hero</span></div><div class="kpi"><b>Shot</b><span>Hero</span></div><div class="kpi"><b>JSON</b><span>Hero</span></div></div>
    <p class="why">Phase 2 is a single dashed hint in the detail, not a new evidence area or App nav item. It does not block Phase 1.</p>
  </article>
  <article class="reject-card">
    <h2>New App nav item</h2>
    <p class="fake">Home · Suites · Plans · Reports · Evidence · Heal</p>
    <p class="why">App nav is locked. Evidence, if it ever lands, stays inside the detail of Reports, Heal, or Manual.</p>
  </article>
</div>"""
    page(
        "03-rejected.html",
        "Layout enhancement pack — rejected",
        "<strong>Out of this pack.</strong> KPI dashboards, whole-row toggles, bulk Heal Reject, TRACK3-LAB / voice / FR-MAN-2, a second filter bar, page-width booleans, an evidence gallery, a new App nav item.",
        "",
        inner,
        "",
        script=False,
    )


def main():
    wire()
    settings()
    suites()
    plans_cases()
    plans_tabs()
    reports()
    documents()
    security()
    heal()
    manual()
    desktop()
    sandboxes()
    annotated()
    rejected()
    expected = [
        "00-structure-wire.html",
        "01a-themed-settings.html",
        "01b-themed-suites.html",
        "01c-themed-plans-cases.html",
        "01d-themed-plans-tabs.html",
        "01e-themed-reports.html",
        "01f-themed-documents.html",
        "01g-themed-security.html",
        "01h-themed-heal.html",
        "01i-themed-manual.html",
        "01j-themed-desktop.html",
        "01k-themed-sandboxes.html",
        "02-annotated-build-note.html",
        "03-rejected.html",
    ]
    missing = [n for n in expected if not (OUT / n).exists()]
    if missing:
        raise SystemExit("missing " + ", ".join(missing))
    for name in expected:
        text = (OUT / name).read_text(encoding="utf-8")
        if "ui/desktop" in text and name.startswith("01"):
            raise SystemExit(name + " leaked a product path into a themed stage")
        if name.startswith("01") and "data-layout-enhancement-pack" not in text:
            raise SystemExit(name + " missing pack marker")
        if name.startswith("01") and "data-lep-empty" not in text:
            raise SystemExit(name + " missing empty contract")
    print("ok", len(expected))


if __name__ == "__main__":
    main()
