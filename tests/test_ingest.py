from __future__ import annotations

import json
from pathlib import Path

from pharmassist_catalog_fr.ingest import build_demo_catalog


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _tsv_line(cols: list[str]) -> str:
    return "\t".join(cols)


def _write_sample_sources(raw: Path) -> None:
    _write(
        raw / "CIS_bdpm.txt",
        "\n".join(
            [
                _tsv_line(
                    [
                        "60000001",
                        "Loratadine 10 mg, comprime",
                        "comprime",
                        "orale",
                        "Autorisation active",
                        "Proc nationale",
                        "Commercialisee",
                        "01/01/2020",
                        "",
                        "",
                        "",
                        "LABX",
                        "Non",
                    ]
                ),
                _tsv_line(
                    [
                        "60000002",
                        "Produit hospitalier test",
                        "comprime",
                        "orale",
                        "Autorisation active",
                        "Proc nationale",
                        "Commercialisee",
                        "01/01/2020",
                        "",
                        "",
                        "",
                        "LABY",
                        "Non",
                    ]
                ),
            ]
        )
        + "\n",
    )
    _write(
        raw / "CIS_CIP_bdpm.txt",
        "\n".join(
            [
                _tsv_line(
                    [
                        "60000001",
                        "111",
                        "boite",
                        "Presentation active",
                        "Decl",
                        "01/01/2020",
                        "3400000000011",
                        "oui",
                        "",
                        "4,20",
                        "",
                        "",
                    ]
                ),
                _tsv_line(
                    [
                        "60000002",
                        "222",
                        "boite",
                        "Presentation active",
                        "Decl",
                        "01/01/2020",
                        "3400000000028",
                        "oui",
                        "",
                        "5,10",
                        "",
                        "",
                    ]
                ),
            ]
        )
        + "\n",
    )
    _write(
        raw / "CIS_CPD_bdpm.txt",
        "\n".join(
            [
                "60000001\tdelivrance en pharmacie",
                "60000002\treserve a l'usage hospitalier",
            ]
        )
        + "\n",
    )
    _write(
        raw / "fr.openbeautyfacts.org.products.csv",
        "\t".join(
            [
                "code",
                "product_name",
                "brands",
                "countries_tags",
                "ingredients_text",
                "categories_tags",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "1234567890123",
                "Creme hydratante",
                "DermaBrand",
                "en:france",
                "aqua, glycerin",
                "en:beauty-products,en:skin-care",
            ]
        )
        + "\n",
    )


def test_build_demo_catalog_with_sample_sources(tmp_path: Path):
    raw = tmp_path / "raw"
    _write_sample_sources(raw)

    out_path = tmp_path / "products.demo.json"
    stats = build_demo_catalog(raw_dir=raw, out_path=out_path, max_products=50, seed=42)
    assert stats.bdpm_rows >= 1
    assert stats.obf_rows >= 1
    assert stats.merged_rows >= 2

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert len(payload) >= 2
    for row in payload:
        assert row["schema_version"] == "0.0.0"
        assert isinstance(row["sku"], str) and row["sku"]
        assert isinstance(row["name"], str) and row["name"]
        assert isinstance(row["price_eur"], float | int)
        assert isinstance(row["stock_qty"], int)


def test_build_demo_catalog_is_deterministic_for_same_seed(tmp_path: Path):
    raw = tmp_path / "raw"
    _write_sample_sources(raw)

    out_a = tmp_path / "a.json"
    out_b = tmp_path / "b.json"
    build_demo_catalog(raw_dir=raw, out_path=out_a, max_products=50, seed=42)
    build_demo_catalog(raw_dir=raw, out_path=out_b, max_products=50, seed=42)

    assert out_a.read_text(encoding="utf-8") == out_b.read_text(encoding="utf-8")


def test_build_demo_catalog_seed_changes_generated_values(tmp_path: Path):
    raw = tmp_path / "raw"
    _write_sample_sources(raw)

    out_a = tmp_path / "seed_42.json"
    out_b = tmp_path / "seed_43.json"
    build_demo_catalog(raw_dir=raw, out_path=out_a, max_products=50, seed=42)
    build_demo_catalog(raw_dir=raw, out_path=out_b, max_products=50, seed=43)

    payload_a = json.loads(out_a.read_text(encoding="utf-8"))
    payload_b = json.loads(out_b.read_text(encoding="utf-8"))
    by_sku_a = {str(row["sku"]): row for row in payload_a}
    by_sku_b = {str(row["sku"]): row for row in payload_b}
    assert set(by_sku_a.keys()) == set(by_sku_b.keys())
    assert any(
        (by_sku_a[sku]["stock_qty"] != by_sku_b[sku]["stock_qty"])
        or (by_sku_a[sku]["price_eur"] != by_sku_b[sku]["price_eur"])
        for sku in by_sku_a
    )
