# Reproducible Build

1. Download raw sources and lock their hashes:

```bash
pharmassist-catalog-fr download-sources --out data/raw
```

This writes `data/raw/sources.lock.json` with source URLs, file sizes, and SHA-256.

2. Verify the local raw snapshots match the lockfile:

```bash
python - <<'PY'
import hashlib, json
from pathlib import Path

raw = Path("data/raw")
lock = json.loads((raw / "sources.lock.json").read_text(encoding="utf-8"))
for src in lock["sources"]:
    blob = (raw / src["filename"]).read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if digest != src["sha256"]:
        raise SystemExit(f"MISMATCH {src['filename']}: {digest} != {src['sha256']}")
print("LOCK_OK")
PY
```

3. Build deterministic demo subset from that exact snapshot:

```bash
pharmassist-catalog-fr build-demo \
  --raw-dir data/raw \
  --out products.demo.json \
  --max-products 500 \
  --seed 42
```

4. Hash output:

```bash
shasum -a 256 products.demo.json
```

5. Release checklist:
- include `products.demo.json`,
- include `data/raw/sources.lock.json`,
- include `ATTRIBUTION.md` + `LICENSES.md`,
- if OBF-derived rows are included, apply ODbL share-alike requirements to the redistributed database.
