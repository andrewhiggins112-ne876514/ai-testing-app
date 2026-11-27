# Operate Demo Catalog — User Guide (synthetic)

<!-- OPERATE_DOCS_DEMO=1 KAN-381 — fictional walkthrough; not employer/customer content -->

## Getting started

1. Start the local demo AUT (same home-PC stack as OPERATE golden path).
2. Open Documents in the desktop app and confirm this guide is listed under Uploads.
3. Draft cases from this guide into a plan, then review before any run.

## Walkthrough — happy path

- The tester **must** land on the catalog home without a login wall for this demo.
- The tester **should** locate SKU `DEMO-100` in the product list.
- Given the list is visible, When the tester clicks `DEMO-100`, Then the detail pane shows "Demo Widget".
- Given detail is open, When the tester clicks Back, Then the list is visible again.

## Walkthrough — edge cases

- Searching for `ZZZ-NONE` **must** show "No matching products" (honest empty).
- Clearing the search box **should** repopulate the previous full list.
- Given detail is open for `DEMO-100`, When stock shows `0`, Then a "Out of stock" note is visible.
- Keyboard focus on Search **must** accept Enter to run the same filter as the Search button.
- Given an intentional fail scenario is selected, When the run asserts missing banner text, Then the case fails with evidence (not a silent pass).

## Tips for document-driven planning

- Prefer Given / When / Then lines and "must" / "should" bullets — the draft extractor looks for those.
- Keep cases editable after draft; never treat draft as auto-run.
- Do not paste real customer or employer documents into this OFFICIAL demo pack.
