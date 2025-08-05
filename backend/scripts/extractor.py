# scripts/extractor.py
import re

def extract_ids(text: str) -> dict:
    ids = {
        "po_id": None,
        "asn_id": None,
        "pallet_id": None
    }

    po_match = re.search(r"\b(2\d{9})\b", text)
    if po_match:
        po_id = po_match.group(1)
        if len(po_id) == 10:
            ids["po_id"] = po_id

    asn_match = re.search(r"\b(0\d{4})\b", text)
    if asn_match:
        asn_id = asn_match.group(1)
        if len(asn_id) == 5:
            ids["asn_id"] = asn_id

    pallet_match = re.search(r"\b(5\d{14})\b", text)
    if pallet_match:
        pallet_id = pallet_match.group(1)
        if len(pallet_id) == 15:
            ids["pallet_id"] = pallet_id

    return ids

def validate_ids(ids: dict) -> list:
    issues = []

    if ids["po_id"] is not None and not re.fullmatch(r"2\d{9}", ids["po_id"]):
        issues.append("PO ID must be 10 digits and start with 2.")

    if ids["asn_id"] is not None and not re.fullmatch(r"0\d{4}", ids["asn_id"]):
        issues.append("ASN must be 5 digits and start with 0.")

    if ids["pallet_id"] is not None and not re.fullmatch(r"5\d{14}", ids["pallet_id"]):
        issues.append("Pallet ID must be 15 digits and start with 5.")

    return issues
