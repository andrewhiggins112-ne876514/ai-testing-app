# Track 3 — Area wires pack (Primary)

**FR:** FR-UI-10 · **Roadmap:** TRACK3-UX  
**Status:** Draft for Slice-0 — **awaiting Designer accept** before any HTML/CSS geometry Build.  
**Density source:** `docs/design/ENTERPRISE_LAYOUT_NOTE.md` (accepted; tokens shipped KAN-297 — geometry still open).

## Designer decisions (Council 2026-11-18)

1. Hard accept gate on this pack before geometry code — **yes**.
2. Track 3 scope = **Primary** areas only; Lab density = follow-on epic — **yes**.
3. Verify density in **all** layout modes A–E — **yes**.

## In scope (Primary)

| Area | Wire depth for Slice-0 |
|------|------------------------|
| Plans · Cases | Full (extend ENTERPRISE_LAYOUT_NOTE §6) |
| Manual (idle / review + Confirm dock) | Full |
| Reports (library) | Full |
| Documents | Full |
| Settings (App category hub) | Full |
| Security (level + credentials chrome) | Full outline (ships with Settings alignment story) |

## Out of scope (follow-on Lab epic)

Heal review, Desktop plugin area, Suites, Sandboxes — outline only here; no geometry stories in Track 3 Primary.

## Out of scope (forever for Track 3)

Orb home rewrite; tall App rail; top app tab bar; purple SaaS; CDN fonts; Gradio-first; voice; FR-MAN-2; token-only “layout Done”.

## Chrome budget (all Primary wires)

| Band | Max |
|------|-----|
| Surface bar | ~40px |
| One toolbar (picker / search / filter / status) | ~56px |
| Optional section tabs | ~36px |
| Confirm dock (Manual, when shown) | ~48px below work |
| **Stack above work** | ≤ **~120px** common case |

No second filter strip. No `*-sticky-*` naming after scaffold story. Chrome outside `.area-work`.

## Wires to complete in Slice-0 Build (docs)

Placeholder — Slice-0 story fills ASCII wires for each Primary area (and notes A–E verify points). Until then, Plans Cases wire in `ENTERPRISE_LAYOUT_NOTE.md` §6 is the reference.

### Accept checklist

- [ ] Plans · Cases wire signed  
- [ ] Manual idle + review/Confirm wire signed  
- [ ] Reports library wire signed  
- [ ] Documents wire signed  
- [ ] Settings + Security chrome outline signed  
- [ ] A–E verify contract acknowledged  

**Accept reply in Council/Build:** `Accept Track 3 wires` (or Amend with specifics).
