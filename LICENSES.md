# Source Licenses

This code repository is MIT-licensed, but data licensing for generated catalogs depends on source datasets.

## BDPM
- Licence Ouverte v2.0
- Commercial reuse allowed
- Attribution required

## Open Beauty Facts
- ODbL
- Attribution required
- Share-alike obligations for redistributed derived databases

## Redistribution Checklist (Required)

When publishing `products.demo.json` / `products.full.jsonl` that include OBF-derived data:
- Treat the output as a derived database and comply with ODbL share-alike terms.
- Ship attribution for both sources (`ATTRIBUTION.md`).
- Ship source snapshot hashes (`data/raw/sources.lock.json`) so recipients can trace provenance.
- Provide ODbL terms and indicate that downstream redistributions must preserve attribution/share-alike obligations.

If a build excludes OBF data, ODbL obligations may differ; verify the legal posture before distribution.
