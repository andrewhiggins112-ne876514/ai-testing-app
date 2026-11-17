# Test-all backlog (CR 2026-11-16)

**Machine catalogue:** [`test_all_catalogue.json`](test_all_catalogue.json)  
**Seed script:** `python scripts/jira_kan_seed_test_all.py` (`--dry-run` first)

## Vision (short)

Downloadable local **test-all** app. Connect once. **One home** = orb + chat; role needs = **HUD widgets**. Primary artifacts = **in-app plan + suite**. Import Playwright repos as input. Pipelines later (separate section). Manual recording = future design. Cut nothing — later = plugin/phase.

## Jira map (seeded)

| Epic | Key | Band |
|------|-----|------|
| A Usable lab (alpha) | **KAN-117** | MUST alpha A1–A9 |
| B Failures for developers | **KAN-118** | GROWTH |
| C Plan the whole project | **KAN-119** | GROWTH |
| D Run policy | **KAN-120** | GROWTH |
| E Privacy / audit / recovery | **KAN-121** | GROWTH |
| F Role widget packs on orb home | **KAN-122** | GROWTH |
| G Widen as plugins | **KAN-123** | later (G10=voice↔KAN-81) |
| H Future workplace (design) | **KAN-124** | FUTURE |

**Active Build story:** **KAN-197** (E3 redact secrets in evidence/exports) · test **KAN-198**  
**Next after E3:** **KAN-260** Lab tools in App menu (Designer priority), then E4…  
**Deferred:** **KAN-81** / **KAN-82** voice until mic (G10 **KAN-235**)  
**Shipped:** A1–A9 (**KAN-125…KAN-141**); B1–B7; C1–C11; D1–D7; E1–E2 (**KAN-193**, **KAN-195**); UI-NAV-IA + App menu (**KAN-247…249**, **KAN-253**, **KAN-257**)  
Stories/tests continue through **KAN-245** / **KAN-246** (H3).

## Sequence

A1→A9 (alpha stop) → B → C → D → E → F → G → H (design only).
