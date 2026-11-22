"""Emit Studio mock HTML for remaining App areas. Not product runtime."""
from pathlib import Path

OUT = Path(__file__).resolve().parent

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>{title}</title>
<link rel="stylesheet" href="../settings_layout_grammar/grammar.css" />
<link rel="stylesheet" href="rest.css" />
</head>
<body class="{body}">
<p class="page-note">{note}</p>
"""

FOOT = """</body>
</html>
"""

FROZEN = """<header class="frozen-bar">
  <button class="btn ghost" type="button">Back</button>
  <h1 class="area-title">{title}</h1>
  <span class="frozen-tag">Frozen chrome · synthetic</span>
</header>
"""


def scan_table(marker, headers, rows, focus=0):
    ths = "".join(f"<th{' class=\"hit\"' if h in ('Sel', 'Keep', 'A', 'B') else ''}>{h}</th>" for h in headers)
    body = []
    for i, row in enumerate(rows):
        cls = "is-focus" if i == focus else ""
        tds = []
        for h, cell in zip(headers, row):
            if h in ("Sel", "Keep") and cell == "cb":
                tds.append(
                    '<td class="hit"><input type="checkbox" aria-label="Select row" /></td>'
                )
            elif h == "A" and cell == "on":
                tds.append('<td class="hit"><input type="radio" name="hist-a" checked aria-label="Compare A" /></td>')
            elif h == "A":
                tds.append('<td class="hit"><input type="radio" name="hist-a" aria-label="Compare A" /></td>')
            elif h == "B" and cell == "on":
                tds.append('<td class="hit"><input type="radio" name="hist-b" checked aria-label="Compare B" /></td>')
            elif h == "B":
                tds.append('<td class="hit"><input type="radio" name="hist-b" aria-label="Compare B" /></td>')
            else:
                tds.append(f"<td>{cell}</td>")
        body.append(f'<tr class="row-hit {cls}">{"".join(tds)}</tr>')
    return f"""<table class="scan" {marker}>
<thead><tr>{ths}</tr></thead>
<tbody>
{chr(10).join(body)}
</tbody>
</table>"""


def detail(title, inner):
    return f"""<aside class="detail">
  <h3>{title}</h3>
  {inner}
</aside>"""


def page(name, title, note, body_class, inner):
    (OUT / name).write_text(
        HEAD.format(title=title, body=body_class, note=note) + inner + FOOT,
        encoding="utf-8",
    )
    print(name)


def plans():
    tabs = """
<div class="area-tabs" role="tablist" data-plans-tabs-layout-grammar="1">
  <button type="button" role="tab" data-panel="draft">Draft</button>
  <button type="button" role="tab" class="owned" data-panel="cases" title="KAN-329 owns Cases">Cases · KAN-329</button>
  <button type="button" role="tab" data-panel="coverage" aria-selected="true">Coverage</button>
  <button type="button" role="tab" data-panel="trace">Trace</button>
  <button type="button" role="tab" data-panel="history">History</button>
  <button type="button" role="tab" data-panel="run">Run</button>
</div>
"""
    coverage = f"""<div class="split two panel" data-panel="coverage">
  <div class="work">
    <h3>Coverage gaps</h3>
    <p class="hint">Stories with no case, or all cases disabled. Refresh does not create cases.</p>
    {scan_table('data-plan-coverage-scan="1"', ["Story", "Gap", "Summary"], [
      ["KAN-410", '<span class="pill warn">No case</span>', "Checkout totals"],
      ["KAN-411", '<span class="pill idle">All disabled</span>', "Guest search"],
    ])}
  </div>
  {detail("Gap detail", '''
    <label class="field">Story<input class="fake" value="KAN-410" readonly /></label>
    <label class="field">Summary<input class="fake" value="Checkout totals" readonly /></label>
    <p class="hint">Row click focuses this pane. No checkbox. Creating a case stays on Cases (KAN-329).</p>
  ''')}
</div>"""
    trace = f"""<div class="split two panel" data-panel="trace" hidden>
  <div class="work">
    <h3>Traceability</h3>
    {scan_table('data-plan-trace-scan="1"', ["Story", "Cases", "Last", "Bugs", "Known"], [
      ["KAN-410", "2", '<span class="pill warn">Fail</span>', "KAN-88", "No"],
      ["KAN-412", "1", '<span class="pill ok">Pass</span>', "—", "No"],
    ], focus=0)}
  </div>
  {detail("Trace row", '''
    <p class="hint">Row click opens that case in Cases. This story does not redraw the Cases editor (KAN-329).</p>
    <button class="btn" type="button">Open case</button>
  ''')}
</div>"""
    history = f"""<div class="split two panel" data-panel="history" hidden>
  <div class="work">
    <h3>Suite history</h3>
    <p class="hint">A and B are dedicated radio cells. Row click focuses the run. Compare uses the radios.</p>
    {scan_table('data-plan-history-scan="1"', ["A", "B", "Time", "Dur", "Pass", "Fail", "Tag"], [
      ["on", "", "22 Nov 09:10", "42s", "8", "1", "smoke"],
      ["", "on", "21 Nov 18:02", "40s", "9", "0", "smoke"],
    ])}
  </div>
  {detail("Run focus", '''
    <label class="field">Run id<input class="fake mono" value="run-synth-14" readonly /></label>
    <p class="hint">Known issues stay labelled. Nothing uploads.</p>
    <button class="btn primary" type="button">Compare A and B</button>
  ''')}
</div>"""
    draft = """<div class="split two panel" data-panel="draft" hidden data-plan-draft-form="1">
  <div class="work">
    <h3>Draft &amp; import</h3>
    <p class="hint">Compact form. Actions sit here, not on list rows. Import never deletes external Playwright files.</p>
    <div class="stack">
      <label class="field">Issue key<input class="fake" value="KAN-410" readonly /></label>
      <label class="field">Document name<input class="fake" value="checkout-spec.md" readonly /></label>
      <label class="field">Playwright path<input class="fake mono" value="D:\\samples\\shop-pw" readonly /></label>
      <div class="btn-row">
        <button class="btn primary" type="button">Draft from story</button>
        <button class="btn" type="button">Import Playwright</button>
      </div>
    </div>
  </div>
  """ + detail("Draft result", '''
    <p class="hint">New cases land on Cases. This pane shows the last draft summary only.</p>
    <p class="fake">3 draft cases · 0 written to Jira</p>
  ''') + "</div>"
    run = """<div class="split two panel" data-panel="run" hidden data-plan-run-sections="1">
  <div class="work">
    <h3>Run setup</h3>
    <p class="hint">Stacked sections. Pause-on-fail is a compact checkbox, not a page-width row.</p>
    <div class="stack">
      <label class="field">Active environment<select class="fake"><option>lab-local</option></select></label>
      <label class="field">Sandbox<select class="fake"><option>Normal browser profile</option></select></label>
      <label class="field">Parallel<select class="fake"><option>1 — sequential</option></select></label>
      <label class="field">Tag<input class="fake" value="smoke" readonly /></label>
      <label class="compact-check"><input type="checkbox" /> Pause on fail</label>
      <details><summary class="hint">Scheduled local run (collapsed)</summary><p class="hint">Off until saved. Missed slots are not a pass.</p></details>
      <button class="btn primary" type="button">Run by tag</button>
    </div>
  </div>
  """ + detail("Run record", '''
    <p class="hint">Credentials stay in Settings. Switching environment does not switch security level.</p>
    <p class="fake">Environment: lab-local · Sandbox: default</p>
  ''') + "</div>"
    cases = """<div class="panel" data-panel="cases" hidden>
  <div class="work"><p class="owned-note">Cases scan + detail is Active Build KAN-329 / test KAN-330. This mock does not redraw it.</p></div>
</div>"""
    script = """
<script>
document.querySelectorAll('.area-tabs button').forEach(function (btn) {
  btn.addEventListener('click', function () {
    var id = btn.getAttribute('data-panel');
    document.querySelectorAll('.area-tabs button').forEach(function (b) {
      b.setAttribute('aria-selected', b === btn ? 'true' : 'false');
    });
    document.querySelectorAll('.panel').forEach(function (p) {
      p.hidden = p.getAttribute('data-panel') !== id;
    });
  });
});
</script>
"""
    inner = f"""<div class="stage" data-plans-tabs-layout-grammar="1">
{FROZEN.format(title="Plans")}
<div class="toolbar"><span>Plan</span><span class="fake">Checkout smoke</span><button class="btn" type="button">Open</button><button class="btn" type="button">Refresh</button><span class="status">Ready</span></div>
{tabs}
{coverage}{trace}{history}{draft}{run}{cases}
</div>
{script}"""
    page(
        "01-themed-plans-tabs.html",
        "Plans remaining tabs — themed",
        "<strong>Preferred.</strong> Plans tabs other than Cases. Cases stays KAN-329. Synthetic keys only. Click a tab.",
        "",
        inner,
    )


def reports():
    table = scan_table(
        'data-rpt-scan="1"',
        ["When", "Title", "Level", "Kind"],
        [
            ["22 Nov 09:12", "Checkout smoke", "OFFICIAL", "Run"],
            ["21 Nov 16:40", "Read-only pack", "OFFICIAL", "Pack"],
        ],
    )
    inner = f"""<div class="stage" data-reports-layout-grammar="1">
{FROZEN.format(title="Reports")}
<div class="toolbar">
  <button class="btn" type="button">Refresh library</button>
  <button class="btn" type="button">Report settings</button>
  <button class="btn" type="button">Export…</button>
  <span class="status">2 saved · OFFICIAL</span>
</div>
<div class="split two">
  <div class="work">
    <h3>Saved reports</h3>
    <p class="hint">No section rail. Row opens detail. Section include/exclude stays in Settings.</p>
    {table}
  </div>
  {detail("Report", '''
    <label class="field">Id<input class="fake mono" value="rpt-synth-09" readonly /></label>
    <pre class="diff"># Checkout smoke
Passed 8 · Failed 1
Story KAN-410 covered.</pre>
    <p class="hint">Screenshot and raw JSON stay in this pane. No secrets.</p>
  ''')}
</div>
</div>"""
    page(
        "01b-themed-reports.html",
        "Reports library — themed",
        "<strong>Preferred.</strong> Suites-like scan + detail. No section rail. Synthetic report ids.",
        "",
        inner,
    )


def documents():
    diff = scan_table(
        'data-doc-diff-scan="1"',
        ["Keep", "Key", "From", "To"],
        [
            ["cb", "target_url", "(empty)", "https://shop.example.test"],
            ["cb", "jira_project", "KAN", "KAN"],
        ],
    )
    uploads = scan_table(
        'data-doc-uploads-scan="1"',
        ["Name", "Time", "Level", "Consent"],
        [
            ["checkout-spec.md", "22 Nov 08:01", "OFFICIAL", "Yes"],
            ["notes.txt", "20 Nov 11:14", "OFFICIAL", "Yes"],
        ],
        focus=0,
    )
    inner = f"""<div class="stage" data-documents-layout-grammar="1">
{FROZEN.format(title="Documents")}
<div class="toolbar">
  <button class="btn primary" type="button">Parse &amp; propose</button>
  <button class="btn" type="button">Refresh uploads</button>
  <span class="status">OFFICIAL</span>
</div>
<div class="area-tabs" role="tablist">
  <button type="button" data-panel="propose" aria-selected="true">Propose</button>
  <button type="button" data-panel="uploads">Uploads</button>
</div>
<div class="split two panel" data-panel="propose">
  <div class="work">
    <h3>Spec text</h3>
    <pre class="diff"># Checkout
Target: https://shop.example.test
Jira project: KAN</pre>
    <h3>Proposal</h3>
    <p class="hint">Keep is a dedicated checkbox cell. Row click focuses the change. Confirm / Decline are not the row.</p>
    {diff}
  </div>
  {detail("Change", '''
    <label class="field">Key<input class="fake mono" value="target_url" readonly /></label>
    <p class="hint">Confirm writes only checked keys after the existing confirm step. Decline writes nothing.</p>
    <div class="btn-row">
      <button class="btn primary" type="button">Confirm selected</button>
      <button class="btn" type="button">Decline</button>
    </div>
  ''')}
</div>
<div class="split two panel" data-panel="uploads" hidden>
  <div class="work">
    <h3>Uploads</h3>
    {uploads}
  </div>
  {detail("Upload", '''
    <label class="field">File<input class="fake" value="checkout-spec.md" readonly /></label>
    <p class="hint">Name, time, level, consent only. No document body in the list. Delete stays on Security → Privacy.</p>
  ''')}
</div>
</div>
<script>
document.querySelectorAll('.area-tabs button').forEach(function (btn) {{
  btn.addEventListener('click', function () {{
    var id = btn.getAttribute('data-panel');
    document.querySelectorAll('.area-tabs button').forEach(function (b) {{
      b.setAttribute('aria-selected', b === btn ? 'true' : 'false');
    }});
    document.querySelectorAll('.panel').forEach(function (p) {{
      p.hidden = p.getAttribute('data-panel') !== id;
    }});
  }});
}});
</script>"""
    page(
        "01c-themed-documents.html",
        "Documents — themed",
        "<strong>Preferred.</strong> In-area Propose | Uploads. Dedicated Keep cell. Synthetic spec only.",
        "",
        inner,
    )


def security():
    privacy = scan_table(
        'data-sec-privacy-scan="1"',
        ["Include", "Artifact"],
        [["cb", "Reports"], ["cb", "Screenshots"], ["cb", "Heal audit"], ["cb", "Sessions (this level)"]],
    )
    audit = scan_table(
        'data-sec-audit-scan="1"',
        ["Time", "Action", "Ref"],
        [["22 Nov 09:02", "plan_edit", "plan-synth"], ["21 Nov 18:11", "privacy_wipe", "OFFICIAL"]],
    )
    backups = scan_table(
        'data-sec-backup-scan="1"',
        ["When", "Level", "Secrets"],
        [["22 Nov 07:00", "OFFICIAL", "No"]],
    )
    inner = f"""<div class="stage" data-security-layout-grammar="1">
{FROZEN.format(title="Security")}
<div class="toolbar"><span class="status">Active level OFFICIAL · profile-official-local</span></div>
<div class="split">
  <nav class="rail" aria-label="Security sections" data-sec-rail="1">
    <p class="rail-label">Sections</p>
    <button type="button" data-panel="level">Level</button>
    <button type="button" data-panel="privacy" aria-current="true">Privacy</button>
    <button type="button" data-panel="audit">Audit</button>
    <button type="button" data-panel="redact">Redaction</button>
    <button type="button" data-panel="backup">Backup</button>
  </nav>
  <div class="work">
    <div class="panel" data-panel="level" hidden>
      <h3>Classification</h3>
      <p class="hint">One level at a time. Switch takes effect only after Confirm.</p>
      <label class="field">Proposed level<select class="fake"><option>SECRET</option></select></label>
    </div>
    <div class="panel" data-panel="privacy">
      <h3>Local data to wipe</h3>
      <p class="hint">Include is a 28px checkbox cell. The row does not toggle it.</p>
      {privacy}
    </div>
    <div class="panel" data-panel="audit" hidden>
      <h3>Local side-effects</h3>
      {audit}
    </div>
    <div class="panel" data-panel="redact" hidden>
      <h3>Redaction status</h3>
      <p class="fake">Export redaction on · 3 pattern hits · screenshots not OCR-redacted</p>
      <p class="hint">No secret values, tokens, or settings.json contents on this surface.</p>
    </div>
    <div class="panel" data-panel="backup" hidden>
      <h3>Backups for this level</h3>
      {backups}
    </div>
  </div>
  <aside class="detail">
    <div class="panel" data-panel="level" hidden>
      <h3>Switch</h3>
      <p class="hint">Browser profile name only. Stores stay unmixed.</p>
      <div class="btn-row">
        <button class="btn" type="button">Switch level</button>
        <button class="btn" type="button" disabled>Confirm switch</button>
      </div>
    </div>
    <div class="panel" data-panel="privacy">
      <h3>Delete</h3>
      <p class="hint">Credentials and settings are not deleted here.</p>
      <div class="danger-zone">
        <button class="btn danger" type="button">Delete local data…</button>
        <button class="btn" type="button" disabled>Confirm delete</button>
      </div>
    </div>
    <div class="panel" data-panel="audit" hidden>
      <h3>Entry</h3>
      <p class="fake">plan_edit · plan-synth · OFFICIAL</p>
      <p class="hint">Time, action, id, level. No document bodies.</p>
    </div>
    <div class="panel" data-panel="redact" hidden>
      <h3>Evidence</h3>
      <p class="hint">Hit counts only. Never echo a matched secret.</p>
    </div>
    <div class="panel" data-panel="backup" hidden>
      <h3>Restore</h3>
      <label class="compact-check"><input type="checkbox" /> Include settings (no secrets)</label>
      <label class="compact-check"><input type="checkbox" /> Include secrets — off by default</label>
      <div class="danger-zone">
        <button class="btn" type="button">Create backup</button>
        <button class="btn danger" type="button">Restore…</button>
        <button class="btn" type="button" disabled>Confirm restore</button>
      </div>
    </div>
  </aside>
</div>
</div>
<script>
document.querySelectorAll('.rail button').forEach(function (btn) {{
  btn.addEventListener('click', function () {{
    var id = btn.getAttribute('data-panel');
    document.querySelectorAll('.rail button').forEach(function (b) {{
      if (b === btn) b.setAttribute('aria-current', 'true');
      else b.removeAttribute('aria-current');
    }});
    document.querySelectorAll('.panel').forEach(function (p) {{
      p.hidden = p.getAttribute('data-panel') !== id;
    }});
  }});
}});
</script>"""
    page(
        "01d-themed-security.html",
        "Security — themed",
        "<strong>Preferred.</strong> In-area rail. Masked status only. One level (OFFICIAL) shown. No live secrets.",
        "",
        inner,
    )


def heal():
    table = scan_table(
        'data-heal-scan="1"',
        ["Sel", "Class", "Locator", "Run", "When"],
        [
            ["cb", '<span class="pill warn">Test defect</span>', "getByRole button Checkout", "run-synth-14", "22 Nov 09:14"],
            ["cb", '<span class="pill idle">Unclassified</span>', "css .pay", "run-synth-11", "21 Nov 16:02"],
        ],
    )
    # Prefer hand-authored 01e (checked Sel + bulk toolbar script). Keep generator aligned for regen.
    inner = f"""<div class="stage" data-heal-layout-grammar="1">
{FROZEN.format(title="Heal review")}
<div class="toolbar">
  <span>Run</span><span class="fake">All pending</span>
  <button class="btn" type="button">Refresh</button>
  <span class="status">2 pending</span>
  <span class="toolbar-bulk" data-heal-bulk="1" hidden>
    <button class="btn primary" type="button" id="heal-bulk-approve">Approve selected (0)</button>
  </span>
</div>
<div class="split two">
  <div class="work">
    <h3>Pending proposals</h3>
    <p class="hint">Sel = multi-select only (stopPropagation). Row click focuses. Approve is never the checkbox and never the row.</p>
    {table}
  </div>
  <aside class="detail" data-heal-detail="1">
  <h3>Proposal</h3>
    <label class="field">Id<input class="fake mono" value="heal-synth-3" readonly /></label>
    <pre class="diff">locator: css .pay
proposed: getByRole('button', {{ name: 'Pay' }})
assertion: unchanged</pre>
    <p class="hint">Approve / Reject act on the focused proposal only. Bulk Approve selected lives in the toolbar and requires confirm. Suite files are not auto-committed.</p>
    <div class="btn-row" data-heal-actions="1">
      <button class="btn primary" type="button" id="heal-approve">Approve</button>
      <button class="btn" type="button" id="heal-reject">Reject</button>
    </div>
</aside>
</div>
</div>
<script>
(function () {{
  var bulk = document.querySelector('[data-heal-bulk]');
  var btn = document.getElementById('heal-bulk-approve');
  function sync() {{
    var n = document.querySelectorAll('[data-heal-scan] tbody input[type=checkbox]:checked').length;
    if (!bulk || !btn) return;
    bulk.hidden = n < 1;
    btn.textContent = 'Approve selected (' + n + ')';
  }}
  document.querySelectorAll('[data-heal-scan] tbody input[type=checkbox]').forEach(function (cb) {{
    cb.addEventListener('click', function (e) {{ e.stopPropagation(); sync(); }});
  }});
  sync();
}})();
</script>"""
    page(
        "01e-themed-heal.html",
        "Heal review — themed",
        "<strong>Preferred (Designer CR 2026-11-22).</strong> Scan + detail. Detail Approve/Reject + toolbar bulk approve on Sel cells. Synthetic locator.",
        "",
        inner,
    )


def manual():
    table = scan_table(
        'data-manual-session-scan="1"',
        ["When", "Charter", "Link", "Stage"],
        [
            ["22 Nov 10:02", "Explore checkout errors", "KAN-410", "Review"],
            ["21 Nov 15:18", "Guest search empty", "—", "Ended"],
        ],
    )
    inner = f"""<div class="stage" data-manual-layout-grammar="1">
{FROZEN.format(title="Manual")}
<div class="toolbar">
  <button class="btn" type="button">Clear linked context</button>
  <button class="btn" type="button">Open Plans</button>
  <button class="btn" type="button">Refresh library</button>
  <span class="status">Loop: idle</span>
</div>
<div class="split two">
  <div class="work">
    <h3>Session library</h3>
    {table}
    <h3>Start session</h3>
    <label class="field">Charter<textarea class="fake" rows="3">Explore checkout errors on the sample shop.</textarea></label>
    <label class="compact-check" data-manual-compact-check="1"><input type="checkbox" /> Link to Jira</label>
    <label class="compact-check" data-manual-compact-check="1"><input type="checkbox" /> Agent assist (recommended off)</label>
    <label class="compact-check" data-manual-compact-check="1"><input type="checkbox" /> Armed mist (recommended off)</label>
    <button class="btn primary" type="button">Start session</button>
    <p class="hint">Charter Frame overlay is unchanged and is not drawn here. Home stays locked. FR-MAN-2 circles are out.</p>
  </div>
  {detail("Focused session", '''
    <label class="field">Charter<input class="fake" value="Explore checkout errors" readonly /></label>
    <p class="hint">Row click opens review for that session. Propose buttons stay deliberate. Confirm dock is below the work, outside the scroll.</p>
    <div class="btn-row">
      <button class="btn" type="button">Propose bug</button>
      <button class="btn" type="button">Propose comment</button>
    </div>
  ''')}
</div>
<div class="dock" data-manual-confirm-dock="1">
  <span class="hint">Proposal ready — Confirm writes; Cancel writes nothing</span>
  <button class="btn primary" type="button">Confirm</button>
  <button class="btn" type="button">Cancel proposal</button>
</div>
</div>"""
    page(
        "01f-themed-manual.html",
        "Manual area — themed",
        "<strong>Preferred.</strong> Library scan + compact checks. Confirm dock pinned. Charter Frame and home not redesigned.",
        "",
        inner,
    )


def desktop():
    table = scan_table(
        'data-desk-scan="1"',
        ["Enabled", "Status", "Path", "Last smoke"],
        [["cb", '<span class="pill ok">Ready</span>', "D:\\samples\\Shop.exe", "Pass · 22 Nov 09:20"]],
    )
    inner = f"""<div class="stage" data-desktop-layout-grammar="1">
{FROZEN.format(title="Desktop")}
<div class="toolbar">
  <button class="btn primary" type="button">Run smoke</button>
  <button class="btn" type="button">Run demo steps</button>
  <span class="status">Plugin ready</span>
</div>
<div class="split two">
  <div class="work">
    <h3>Desktop target</h3>
    <p class="hint">One target, still a scan row — not a hero card. Enabled is the checkbox cell only.</p>
    {table}
    <p class="owned-note">TRACK3-LAB density stays deferred. This mock changes hierarchy and hit targets only.</p>
  </div>
  {detail("Plugin", '''
    <label class="field">Exe path<input class="fake mono" value="D:\\samples\\Shop.exe" readonly /></label>
    <p class="hint">Separate from Playwright. Save and path override live here.</p>
    <button class="btn" type="button">Save plugin</button>
  ''')}
</div>
</div>"""
    page(
        "01g-themed-desktop.html",
        "Desktop Lab — themed",
        "<strong>Preferred.</strong> Single-target scan. Synthetic exe path. Lab density deferred.",
        "",
        inner,
    )


def sandboxes():
    table = scan_table(
        'data-ms-scan="1"',
        ["Id", "Label", "URL", "Ready"],
        [
            ["primary", "Sample shop", "https://shop.example.test", '<span class="pill ok">Prepared</span>'],
            ["guest", "Guest mirror", "https://guest.example.test", '<span class="pill idle">Planned</span>'],
        ],
    )
    inner = f"""<div class="stage" data-sandboxes-layout-grammar="1">
{FROZEN.format(title="Sandboxes")}
<div class="toolbar">
  <label class="compact-check"><input type="checkbox" checked /> Enable multi-sandbox</label>
  <span>Action</span><span class="fake">list</span>
  <button class="btn primary" type="button">Orchestrate</button>
  <span class="status">2 / 4</span>
</div>
<div class="split two">
  <div class="work">
    <h3>Sandbox list</h3>
    <p class="hint">No checkbox column. Row click focuses. Remove sits in the detail behind confirm.</p>
    {table}
    <p class="owned-note">TRACK3-LAB density stays deferred. Local only. No cloud farms.</p>
  </div>
  {detail("primary", '''
    <label class="field">Label<input class="fake" value="Sample shop" readonly /></label>
    <label class="field">URL<input class="fake mono" value="https://shop.example.test" readonly /></label>
    <div class="btn-row"><button class="btn" type="button">Save sandbox</button></div>
    <div class="danger-zone">
      <button class="btn danger" type="button">Remove…</button>
      <button class="btn" type="button" disabled>Confirm remove</button>
    </div>
  ''')}
</div>
</div>"""
    page(
        "01h-themed-sandboxes.html",
        "Sandboxes — themed",
        "<strong>Preferred.</strong> Scan + detail. Synthetic hosts only. Enable is a compact toolbar checkbox.",
        "",
        inner,
    )


def wire():
    def mini(title, cols, marker):
        return f"""<div class="stage auto">
{FROZEN.format(title=title)}
<div class="split two">
  <div class="work"><h3>Scan</h3>
    <table class="scan" {marker}><thead><tr>{''.join(f'<th>{c}</th>' for c in cols)}</tr></thead>
    <tbody><tr class="row-hit is-focus"><td>sample</td><td>sample</td><td>sample</td></tr></tbody></table>
  </div>
  <aside class="detail"><h3>Detail</h3><p class="hint">Row focuses. Checkbox only where labelled in the themed mock.</p></aside>
</div>
</div>"""
    # wire uses 3-col tables for speed; themed files are authoritative for columns
    parts = [
        mini("Plans · Coverage", ["Story", "Gap", "Summary"], 'data-plan-coverage-scan="1"'),
        mini("Plans · Trace", ["Story", "Cases", "Last"], 'data-plan-trace-scan="1"'),
        mini("Plans · History", ["A/B", "Time", "Tag"], 'data-plan-history-scan="1"'),
        mini("Reports", ["When", "Title", "Kind"], 'data-rpt-scan="1"'),
        mini("Documents · diff", ["Keep", "Key", "To"], 'data-doc-diff-scan="1"'),
        mini("Security · privacy", ["Include", "Artifact", "—"], 'data-sec-privacy-scan="1"'),
        mini("Heal", ["Class", "Locator", "Run"], 'data-heal-scan="1"'),
        mini("Manual library", ["When", "Charter", "Stage"], 'data-manual-session-scan="1"'),
        mini("Desktop", ["Enabled", "Path", "Smoke"], 'data-desk-scan="1"'),
        mini("Sandboxes", ["Id", "Label", "URL"], 'data-ms-scan="1"'),
    ]
    page(
        "00-structure-wire.html",
        "Secondary areas — structure wire",
        "<strong>Wire.</strong> Hierarchy only. Themed files name the real columns, checkbox cells, and contrasts. Not product UI.",
        "wire",
        "\n".join(parts),
    )


def annotated():
    legend = """
<div class="legend">
<p><span class="mark">1</span>Plans remaining tabs — Coverage/Trace scan, no checkbox; History A/B radios in .hit; Draft/Run are forms. Cases untouched (KAN-329). Marker data-plans-tabs-layout-grammar.</p>
<p><span class="mark">2</span>Reports — scan data-rpt-scan + detail. No section rail. Report settings button deep-links to Settings. No section-include editor here.</p>
<p><span class="mark">3</span>Documents — Keep cell on data-doc-diff-scan; uploads data-doc-uploads-scan. Confirm/Decline outside the row.</p>
<p><span class="mark">4</span>Security — rail data-sec-rail. Privacy Include cell. Confirm stays disabled until propose. No secret strings.</p>
<p><span class="mark">5</span>Heal — Sel cell for multi-select; toolbar data-heal-bulk Approve selected (confirm). data-heal-actions Approve/Reject in detail. Checkbox never approves.</p>
<p><span class="mark">6</span>Manual — session scan + data-manual-compact-check. Confirm dock outside work. Do not edit #charter-frame-root.</p>
<p><span class="mark">7</span>Desktop — one scan row; Enabled is .hit. TRACK3-LAB geometry deferred.</p>
<p><span class="mark">8</span>Sandboxes — scan without a select column. Remove behind confirm in detail. Enable is a compact toolbar checkbox.</p>
<p><span class="mark">9</span>Frozen: theme tokens, orb, home/chat, ▦ App menu, Screen drawer. Code: ui/desktop/index.html + desktop.js + desktop.css only, per area ids in README.</p>
<p><span class="mark">0</span>Selection grammar: checkbox/radio cell stops at the control; row click focuses or opens; ban whole-row toggle.</p>
</div>
"""
    page(
        "02-annotated-build-note.html",
        "Annotated build note — remaining areas",
        "<strong>Build note.</strong> Open the themed file named on each mark. Product code stays in the Build lane.",
        "",
        legend
        + """
<div class="stage auto">
<header class="frozen-bar"><h1 class="area-title"><span class="mark">0</span>Click map</h1><span class="frozen-tag">Synthetic</span></header>
<div class="work">
<table class="scan">
<thead><tr><th class="hit">Sel</th><th>Name</th><th>Result</th></tr></thead>
<tbody><tr class="row-hit is-focus"><td class="hit"><input type="checkbox" aria-label="Select" /></td><td>Row opens detail</td><td><span class="pill ok">Focus</span></td></tr></tbody>
</table>
<p class="hint"><span class="mark">0</span>The 28px cell is the only select hit. Destructive and single Approve/Reject are never this cell. Heal bulk approve uses selection + toolbar.</p>
</div>
</div>
""",
    )


def rejected():
    inner = """
<div class="reject-grid">
  <article class="reject-card">
    <h2>KPI library</h2>
    <div class="kpi-row"><div class="kpi"><b>12</b><span>Reports</span></div><div class="kpi"><b>98%</b><span>Pass</span></div><div class="kpi"><b>3</b><span>Heals</span></div></div>
    <p class="why">Rejected. Pretty-empty. Hides the scan a tester opens the area to read.</p>
  </article>
  <article class="reject-card">
    <h2>Whole-card Approve</h2>
    <div class="soup">
      <label><input type="checkbox" checked /> Approve heal · css .pay → getByRole Pay</label>
      <label><input type="checkbox" /> Approve heal · button Checkout</label>
    </div>
    <p class="why">Rejected for Heal: checkbox-as-approve and whole-row/card approve. Preferred: detail Approve/Reject + toolbar bulk approve on Sel (Designer CR 2026-11-22).</p>
  </article>
  <article class="reject-card">
    <h2>Page-width check-row</h2>
    <div class="soup">
      <label><input type="checkbox" checked /> Reports — entire label toggles</label>
      <label><input type="checkbox" checked /> Screenshots — entire label toggles</label>
      <label><input type="checkbox" /> Include secrets</label>
    </div>
    <p class="why">Rejected for Security, Documents diffs, Manual start, Desktop enable. Dedicated cell or compact checkbox.</p>
  </article>
  <article class="reject-card">
    <h2>Text dumps</h2>
    <pre class="diff">KAN-410 no case Checkout totals
KAN-411 all disabled Guest search
22 Nov pass 8 fail 1 smoke</pre>
    <p class="why">Rejected for Coverage, Trace, History, report library, uploads, audit, sandboxes. That is the current row-soup.</p>
  </article>
  <article class="reject-card">
    <h2>Redesign Charter Frame / home</h2>
    <p class="why">Rejected. Manual area layout may change. #charter-frame-root, orb home, and clarify-before-act stay. FR-MAN-2 circles stay parked.</p>
  </article>
  <article class="reject-card">
    <h2>New App nav items per tab</h2>
    <div class="soup"><label>App → Coverage</label><label>App → Privacy</label><label>App → Uploads</label></div>
    <p class="why">Rejected. Rails and tabs stay inside the area. ▦ menu model is frozen.</p>
  </article>
</div>
"""
    page(
        "03-rejected-options.html",
        "Rejected options — remaining areas",
        "<strong>Rejected.</strong> Do not build these. Preferred files are 01 through 01h.",
        "",
        inner,
    )


def main():
    wire()
    plans()
    reports()
    documents()
    security()
    heal()
    manual()
    desktop()
    sandboxes()
    annotated()
    rejected()


if __name__ == "__main__":
    main()
