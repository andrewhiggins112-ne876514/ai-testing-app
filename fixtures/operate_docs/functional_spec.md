# Operate Demo Catalog — Functional Spec (synthetic)

<!-- OPERATE_DOCS_DEMO=1 KAN-381 — fictional product only; not employer/customer content -->

**Product:** Operate Demo Catalog (local lab AUT companion)  
**Audience:** Designer POC / home-PC walkthrough  
**Security level target:** OFFICIAL demo data only

## Purpose

Describe expected behaviour for a tiny catalog web app so Documents → draft plan
can extract editable test ideas without real company documents.

## Happy path

- The catalog home page **must** show the title "Operate Demo Catalog".
- A signed-in tester **must** see a product list with at least one demo SKU.
- Searching by SKU **should** filter the list to matching items only.
- Given a tester opens the catalog home, When the page finishes loading, Then the welcome banner is visible.
- Given a demo SKU is listed, When the tester opens that SKU, Then the detail pane shows name, price, and stock.

## Edge notes

- Empty search **must** restore the full product list (not leave a blank table).
- An unknown SKU search **should** show an honest empty state, not a fake green pass.
- Given the network is offline, When the tester retries search, Then the UI shows a recoverable error message.
- Stock of zero **must** still allow opening the detail pane (read-only).
- Rapid double-click on Search **should** not create duplicate result rows.

## Out of scope for this demo pack

- Real payment, employer VPN, customer PII, or live production catalogs.
- Silent writes to Jira or Settings (drafts stay reviewable in Plans).
