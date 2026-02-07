from __future__ import annotations

import csv
import hashlib
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from .sources import BDPM_FILES, OBF_FR_CSV_URL


def _norm_ascii(text: str) -> str:
    return "".join(ch for ch in text.lower().strip() if ch.isalnum() or ch in {" ", "-", "_"})


def _sha12(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_otc_cpd_text(cpd_text: str) -> bool:
    t = _norm_ascii(cpd_text)
    blocked = [
        "usage hospitalier",
        "reserve a lusage hospitalier",
        "prescription",
        "liste i",
        "liste ii",
        "stupefiant",
    ]
    return not any(x in t for x in blocked)


def _pick_category(name: str) -> str:
    t = _norm_ascii(name)
    if any(x in t for x in ("allerg", "rhinit", "antihistamin")):
        return "allergy"
    if any(x in t for x in ("diges", "constipat", "diarr", "ballonn", "reflux")):
        return "digestion"
    if any(x in t for x in ("peau", "derm", "ecz", "creme", "baume")):
        return "dermatology"
    if any(x in t for x in ("douleur", "migraine", "cephale", "headache", "pain")):
        return "pain"
    if any(x in t for x in ("oeil", "eye", "ocul", "conjonctiv")):
        return "eye"
    if any(x in t for x in ("urin", "urolog")):
        return "urology"
    return "other"


def _to_price(value: str) -> float | None:
    raw = value.strip().replace(",", ".")
    if not raw:
        return None
    try:
        v = float(raw)
    except ValueError:
        return None
    if v < 0:
        return None
    return round(v, 2)


@dataclass(frozen=True)
class BuildStats:
    bdpm_rows: int
    obf_rows: int
    merged_rows: int


def download_sources(
    *, out_dir: Path, timeout_sec: int = 60, obf_max_lines: int = 200_000
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_paths: list[Path] = []
    downloaded: list[tuple[str, str, Path]] = []
    for name, url in BDPM_FILES.items():
        path = _download(url, out_dir / name, timeout_sec=timeout_sec)
        out_paths.append(path)
        downloaded.append((name, url, path))
    obf_path = _download_text_lines(
            OBF_FR_CSV_URL,
            out_dir / "fr.openbeautyfacts.org.products.csv",
            max_lines=max(2, obf_max_lines),
            timeout_sec=timeout_sec,
        )
    out_paths.append(obf_path)
    downloaded.append(("fr.openbeautyfacts.org.products.csv", OBF_FR_CSV_URL, obf_path))
    lock_path = _write_sources_lock(out_dir=out_dir, downloaded=downloaded)
    out_paths.append(lock_path)
    return out_paths


def _write_sources_lock(*, out_dir: Path, downloaded: list[tuple[str, str, Path]]) -> Path:
    rows: list[dict[str, Any]] = []
    for filename, url, path in downloaded:
        rows.append(
            {
                "filename": filename,
                "url": url,
                "sha256": _sha256_file(path),
                "bytes": int(path.stat().st_size),
            }
        )
    rows.sort(key=lambda x: str(x["filename"]))
    payload = {
        "schema_version": "0.0.0",
        "sources": rows,
    }
    lock_path = out_dir / "sources.lock.json"
    lock_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return lock_path


def _download(url: str, out_path: Path, *, timeout_sec: int = 60) -> Path:
    resp = requests.get(url, timeout=timeout_sec)
    resp.raise_for_status()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(resp.content)
    return out_path


def _download_text_lines(
    url: str, out_path: Path, *, max_lines: int, timeout_sec: int = 60
) -> Path:
    resp = requests.get(url, timeout=timeout_sec, stream=True)
    resp.raise_for_status()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out_path.open("w", encoding="utf-8") as f:
        for raw in resp.iter_lines(decode_unicode=True):
            if raw is None:
                continue
            f.write(raw + "\n")
            count += 1
            if count >= max_lines:
                break
    return out_path


def build_demo_catalog(
    *,
    raw_dir: Path,
    out_path: Path,
    max_products: int = 500,
    seed: int = 42,
) -> BuildStats:
    cis_path = raw_dir / "CIS_bdpm.txt"
    cip_path = raw_dir / "CIS_CIP_bdpm.txt"
    cpd_path = raw_dir / "CIS_CPD_bdpm.txt"
    obf_path = raw_dir / "fr.openbeautyfacts.org.products.csv"
    for p in (cis_path, cip_path, cpd_path):
        if not p.exists():
            raise FileNotFoundError(f"Missing required source file: {p}")

    cpd_by_cis = _load_cpd(cpd_path)
    bdpm = _load_bdpm_otc(cis_path=cis_path, cip_path=cip_path, cpd_by_cis=cpd_by_cis)
    if obf_path.exists():
        obf = _load_obf(obf_path)
    else:
        obf = _load_obf_from_url(OBF_FR_CSV_URL)
    merged = _merge_products(bdpm=bdpm, obf=obf, max_products=max_products, seed=seed)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return BuildStats(
        bdpm_rows=len(bdpm),
        obf_rows=len(obf),
        merged_rows=len(merged),
    )


def _load_cpd(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    with path.open("r", encoding="latin-1", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if len(row) < 2:
                continue
            cis = row[0].strip()
            text = row[1].strip()
            if cis and text:
                out[cis] = text
    return out


def _load_bdpm_otc(
    *, cis_path: Path, cip_path: Path, cpd_by_cis: dict[str, str]
) -> list[dict[str, Any]]:
    cis_to_name: dict[str, str] = {}
    cis_to_brand: dict[str, str] = {}
    with cis_path.open("r", encoding="latin-1", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if len(row) < 12:
                continue
            cis = row[0].strip()
            name = row[1].strip()
            brand = row[11].strip() if len(row) > 11 else ""
            if cis and name:
                cis_to_name[cis] = name
                cis_to_brand[cis] = brand or "Unknown"

    out: list[dict[str, Any]] = []
    with cip_path.open("r", encoding="latin-1", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if len(row) < 7:
                continue
            cis = row[0].strip()
            cip13 = row[6].strip()
            if not cis or not cip13 or cis not in cis_to_name:
                continue

            cpd_text = cpd_by_cis.get(cis, "")
            if cpd_text and not _is_otc_cpd_text(cpd_text):
                continue

            name = cis_to_name[cis]
            category = _pick_category(name)
            price = _to_price(row[9] if len(row) > 9 else "")
            out.append(
                {
                    "schema_version": "0.0.0",
                    "sku": cip13,
                    "name": name,
                    "brand": cis_to_brand[cis],
                    "category": category,
                    "ingredients": [],
                    "contraindication_tags": [],
                    "price_eur": price if price is not None else 0.0,
                    "in_stock": True,
                    "stock_qty": 10,
                    "_source": "bdpm",
                }
            )
    return out


def _load_obf(path: Path, *, limit: int = 20000) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return _obf_rows_to_products(reader, limit=limit)


def _load_obf_from_url(url: str, *, limit: int = 20000) -> list[dict[str, Any]]:
    resp = requests.get(url, timeout=120, stream=True)
    resp.raise_for_status()
    lines: list[str] = []
    for raw in resp.iter_lines(decode_unicode=True):
        if raw is None:
            continue
        lines.append(raw)
        if len(lines) > (limit + 1):
            break
    if not lines:
        return []

    reader = csv.DictReader(lines, delimiter="\t")
    return _obf_rows_to_products(reader, limit=limit)


def _obf_rows_to_products(
    rows: csv.DictReader[str], *, limit: int
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        if idx >= limit:
            break
        code = (row.get("code") or "").strip()
        name = (row.get("product_name") or "").strip()
        brands = (row.get("brands") or "").strip()
        countries_tags = (row.get("countries_tags") or "").strip().lower()
        ingredients_text = (row.get("ingredients_text") or "").strip()
        categories = (row.get("categories_tags") or "").strip().lower()

        if not code or not name:
            continue
        if "en:france" not in countries_tags:
            continue
        if not categories:
            continue

        category = "dermatology"
        if "supplement" in categories or "vitamin" in categories:
            category = "digestion"
        elif "hygiene" in categories:
            category = "other"

        ingredients = [x.strip() for x in ingredients_text.split(",") if x.strip()][:8]
        out.append(
            {
                "schema_version": "0.0.0",
                "sku": code,
                "name": name,
                "brand": brands or "Unknown",
                "category": category,
                "ingredients": ingredients,
                "contraindication_tags": [],
                "price_eur": 0.0,
                "in_stock": True,
                "stock_qty": 5,
                "_source": "obf",
            }
        )
    return out


def _merge_products(
    *, bdpm: list[dict[str, Any]], obf: list[dict[str, Any]], max_products: int, seed: int
) -> list[dict[str, Any]]:
    by_sku: dict[str, dict[str, Any]] = {}
    for row in bdpm:
        sku = str(row.get("sku") or "").strip()
        if not sku:
            continue
        by_sku[sku] = dict(row)

    for row in obf:
        sku = str(row.get("sku") or "").strip()
        if not sku:
            continue
        if sku in by_sku:
            # Keep BDPM as canonical if collision, but enrich missing ingredients.
            existing = by_sku[sku]
            if not existing.get("ingredients") and row.get("ingredients"):
                existing["ingredients"] = row["ingredients"]
            continue
        by_sku[sku] = dict(row)

    rows = list(by_sku.values())
    rows.sort(key=lambda x: str(x.get("sku") or ""))

    rng = random.Random(seed)
    for r in rows:
        base = int(_sha12(str(r.get("sku") or "0")), 16)
        rng.seed(base ^ seed)
        if not isinstance(r.get("price_eur"), int | float) or r["price_eur"] <= 0:
            r["price_eur"] = round(3.0 + (rng.random() * 17.0), 2)
        r["stock_qty"] = int(1 + rng.random() * 24)
        r["in_stock"] = r["stock_qty"] > 0
        r.pop("_source", None)

    return rows[: max(1, max_products)]
