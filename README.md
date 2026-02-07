# pharmassist-catalog-fr

Open-data ingestion tool for a realistic French OTC/parapharmacy demo catalog.

Sources:
- BDPM (ANSM): [telechargement](https://base-donnees-publique.medicaments.gouv.fr/telechargement)
- Open Beauty Facts FR dump: [csv](https://fr.openbeautyfacts.org/data/fr.openbeautyfacts.org.products.csv)

Outputs:
- `products.demo.json`: compact deterministic subset for Kaggle/demo runtime
- `products.full.jsonl`: optional larger export from the same normalized pipeline

## Quick start

```bash
make setup

# 1) download source files into data/raw
.venv/bin/pharmassist-catalog-fr download-sources --out data/raw --obf-max-lines 200000

# 2) build deterministic demo subset
.venv/bin/pharmassist-catalog-fr build-demo --raw-dir data/raw --out products.demo.json --max-products 500
```

`download-sources` also writes `data/raw/sources.lock.json` with per-file SHA-256 hashes. Keep this lockfile with your artifact release so the build can be reproduced from the exact same snapshots.

## Attribution and licenses

- BDPM data: Licence Ouverte v2.0 (Etalab), attribution required.
- Open Beauty Facts data: ODbL; attribution + share-alike obligations for redistributed databases.

If you redistribute `products.demo.json` / `products.full.jsonl` with OBF-derived rows:
- include `ATTRIBUTION.md` in the release artifact,
- include ODbL terms and identify the output as a Derived Database,
- provide the corresponding source snapshot hashes (`sources.lock.json`) and fulfill ODbL share-alike obligations.

See:
- `ATTRIBUTION.md`
- `LICENSES.md`
