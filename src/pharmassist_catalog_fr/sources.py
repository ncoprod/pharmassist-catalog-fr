from __future__ import annotations

BDPM_BASE = "https://base-donnees-publique.medicaments.gouv.fr/download/file"

BDPM_FILES: dict[str, str] = {
    "CIS_bdpm.txt": f"{BDPM_BASE}/CIS_bdpm.txt",
    "CIS_CIP_bdpm.txt": f"{BDPM_BASE}/CIS_CIP_bdpm.txt",
    "CIS_CPD_bdpm.txt": f"{BDPM_BASE}/CIS_CPD_bdpm.txt",
}

OBF_FR_CSV_URL = "https://fr.openbeautyfacts.org/data/fr.openbeautyfacts.org.products.csv"

