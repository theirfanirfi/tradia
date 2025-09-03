"""
General document-agnostic trade document extractor
Pipeline: OCR/Layout → NER+Regex → Candidate Graph → LLM Normalizer → Validators
"""

import re, json
import pdfplumber
import spacy
from spacy.pipeline import EntityRuler
from rapidfuzz import fuzz, process

# ---------------------------
# 1. Define canonical schema
# ---------------------------
CANONICAL_SCHEMA = {
    "bl_number": None,
    "doc_number": None,
    "vessel": None,
    "voyage": None,
    "port_loading": None,
    "port_discharge": None,
    "place_delivery": None,
    "shipper_exporter": {"name": None, "address": None},
    "consignee": {"name": None, "address": None},
    "notify_party": {"name": None, "address": None},
    "delivery_agent": {"name": None, "address": None},
    "packages": {"count": None, "kind": None},
    "gross_weight_kg": None,
    "volume_cbm": None,
    "invoice": {
        "number": None,
        "date": None,
        "currency": None,
        "total_amount": None,
        "line_items": []
    },
    "owner": {"name": None, "address": None},
    "provenance": {}
}

# -----------------------------------
# 2. NLP setup: NER + gazetteer rules
# -----------------------------------
nlp = spacy.load("en_core_web_sm")
ruler = nlp.add_pipe("entity_ruler", before="ner")

# Ports, Incoterms, common parties
patterns = [
    {"label": "PORT", "pattern": "Brisbane"},
    {"label": "PORT", "pattern": "Shanghai"},
    {"label": "INCOTERM", "pattern": "CIF"},
    {"label": "INCOTERM", "pattern": "FOB"}
]
ruler.add_patterns(patterns)

# Regex extractors
REGEX_PATTERNS = {
    "bl_number": re.compile(r"\b(B\/L(?: No)?|Bill of Lading)\s*[:#]?\s*([A-Z0-9\-]+)", re.I),
    "doc_number": re.compile(r"\bDOC(?:UMENT)?\s*NO\.?\s*[:#]?\s*([A-Z0-9\-]+)", re.I),
    "container": re.compile(r"\b([A-Z]{4}\d{7})\b"),
    "gross_weight": re.compile(r"(\d+(?:\.\d+)?)\s*KGS?\b", re.I),
    "volume": re.compile(r"(\d+(?:\.\d+)?)\s*CBM\b", re.I),
}

# -------------------------------------------------
# 3. Candidate generation: NER + regex + headers
# -------------------------------------------------
def extract_candidates(text, page=1):
    candidates = []
    doc = nlp(text)

    # Named entity candidates
    for ent in doc.ents:
        if ent.label_ in {"ORG", "PERSON", "GPE", "PORT", "INCOTERM"}:
            candidates.append({
                "field": ent.label_.lower(),
                "value": ent.text.strip(),
                "page": page,
                "method": "ner",
                "confidence": 0.7
            })

    # Regex candidates
    for name, rx in REGEX_PATTERNS.items():
        for m in rx.finditer(text):
            candidates.append({
                "field": name,
                "value": m.group(2) if m.lastindex else m.group(1),
                "page": page,
                "method": "regex",
                "confidence": 0.9
            })
    return candidates

# ----------------------------------------------
# 4. Owner derivation logic (deterministic rule)
# ----------------------------------------------
def derive_owner(normalized):
    au_candidates = []
    for key in ["consignee", "invoice", "delivery_agent"]:
        party = normalized.get(key)
        if isinstance(party, dict) and party.get("address") and "australia" in party["address"].lower():
            au_candidates.append(party)

    if au_candidates:
        normalized["owner"] = au_candidates[0]
    else:
        normalized["owner"] = {"name": None, "address": None}
        normalized["owner_conflict"] = True
    return normalized

# -----------------------------------
# 5. LLM normalizer placeholder
# -----------------------------------
def llm_normalize(candidates):
    """
    In practice: send 'candidates' + schema to your LLM with function calling.
    Here: trivial reducer picking the highest-confidence candidate per field.
    """
    result = dict(CANONICAL_SCHEMA)  # shallow copy
    prov = {}

    for cand in candidates:
        f = cand["field"]
        # simple: pick max confidence
        if f not in result or not result[f]:
            result[f] = cand["value"]
            prov[f] = {"page": cand["page"], "method": cand["method"], "confidence": cand["confidence"]}
        else:
            # if numeric, keep max confidence
            if prov[f]["confidence"] < cand["confidence"]:
                result[f] = cand["value"]
                prov[f] = {"page": cand["page"], "method": cand["method"], "confidence": cand["confidence"]}
    result["provenance"] = prov
    return result

# -----------------------------------
# 6. End-to-end processor
# -----------------------------------
def process_pdf(path):
    all_candidates = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            all_candidates.extend(extract_candidates(text, page=i))

    normalized = llm_normalize(all_candidates)
    normalized = derive_owner(normalized)
    return normalized

# ----------------------------
# Example usage
# ----------------------------
if __name__ == "__main__":
    doc = process_pdf("document.pdf")
    print(json.dumps(doc, indent=2))
