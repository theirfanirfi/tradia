import requests, numpy as np
from functools import lru_cache

OLLAMA_URL = "http://localhost:11434"
MODEL = "mxbai-embed-large:latest"

SECTION_MAP = {
  "Animals": "I", "Vegetables": "II", "Oils/Fats": "III", "Food/Drink": "IV",
  "Minerals": "V", "Chemicals": "VI", "Plastics/Rubber": "VII", "Leather/Furs": "VIII",
  "Woodwork": "IX", "Paper": "X", "Textiles": "XI", "Footwear/Wearables": "XII",
  "Stone/Ceramics": "XIII", "Jewellery": "XIV", "Metals": "XV",
  "Machinery/Electronics": "XVI", "Transport": "XVII", "Instruments": "XVIII",
  "Arms": "XIX", "Misc. Goods": "XX", "Art/Antiques": "XXI",
}

SYNONYMS = {
  "Animals": "livestock, meat, dairy, fish, poultry",
  "Vegetables": "vegetables, fruits, nuts, cereals, grains, seeds, produce",
  "Oils/Fats": "oils, fats, butter, margarine, wax",
  "Food/Drink": "food, beverage, alcohol, tobacco, snacks, nicotine",
  "Minerals": "minerals, ore, salt, coal, fuel",
  "Chemicals": "chemicals, fertilizers, pharmaceuticals, paint, dyes, acids",
  "Plastics/Rubber": "plastics, rubber, latex, polymer",
  "Leather/Furs": "leather, hides, skins, fur, bags, luggage, handbags",
  "Woodwork": "wood, timber, cork, straw, bamboo, basketware",
  "Paper": "paper, pulp, paperboard, cardboard, cartons",
  "Textiles": "textiles, fabric, clothing, apparel, garments, yarn",
  "Footwear/Wearables": "footwear, shoes, hats, caps, umbrellas, wigs, feathers",
  "Stone/Ceramics": "stone, cement, plaster, bricks, tiles, pottery, glass",
  "Jewellery": "jewelry, gems, diamonds, gold, silver, coins, pearls",
  "Metals": "metals, steel, iron, copper, aluminium, alloys, metalwork",
  "Machinery/Electronics": "machinery, tools, engines, appliances, electronics, devices, computers, tv",
  "Transport": "vehicles, cars, trucks, motorcycles, ships, boats, aircraft",
  "Instruments": "optical, medical, surgical, watches, clocks, cameras, musical, measuring",
  "Arms": "weapons, guns, firearms, ammunition",
  "Misc. Goods": "miscellaneous, toys, furniture, lamps, sports equipment, stationery",
  "Art/Antiques": "art, paintings, sculptures, collectibles, antiques",
}

def _embed_one(text: str) -> np.ndarray:
    text = (text or "").strip()
    if not text:
        raise ValueError("Tried to embed an empty string.")
    r = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": MODEL, "prompt": text},  # single-input path is most reliable
        timeout=60,
    )
    try:
        data = r.json()
    except Exception:
        raise RuntimeError(f"Non-JSON response from Ollama: {r.status_code} {r.text[:400]}")
    if "error" in data:
        raise RuntimeError(f"Ollama error: {data['error']}")
    if "embedding" not in data or not isinstance(data["embedding"], list) or len(data["embedding"]) == 0:
        raise RuntimeError(f"Unexpected/empty embedding payload: {data}")
    vec = np.asarray(data["embedding"], dtype=np.float32)
    return vec

def _embed_many(texts):
    # robust multi: call single endpoint per text, avoid batch incompatibilities
    return [ _embed_one(t) for t in texts ]

@lru_cache(maxsize=1)
def _label_matrix():
    keys = list(SECTION_MAP.keys())
    label_texts = [(f"{k}. {SYNONYMS.get(k,'')}".strip()) for k in keys]
    vecs = _embed_many(label_texts)
    dims = [v.shape[0] for v in vecs]
    if len(set(dims)) != 1:
        raise RuntimeError(f"Label embeddings have inconsistent dims: {dims}")
    mat = np.vstack(vecs)  # (N_labels, D)
    return keys, mat

def _safe_cosine_matrix(mat: np.ndarray, q: np.ndarray) -> np.ndarray:
    if q.ndim != 1:
        raise ValueError(f"Query embedding must be 1-D; got shape {q.shape}")
    if mat.shape[1] != q.shape[0]:
        raise ValueError(f"Dim mismatch: mat {mat.shape}, q {q.shape}")
    mat_norms = np.linalg.norm(mat, axis=1)
    q_norm = np.linalg.norm(q)
    if q_norm == 0 or np.any(mat_norms == 0):
        raise ValueError("Zero-norm embedding encountered.")
    # cosine similarity = (mat @ q) / (||mat_i|| * ||q||)
    return (mat @ q) / (mat_norms * q_norm)

def classify_to_section(text: str, top_k: int = 3, threshold: float = 0.0):
    keys, label_mat = _label_matrix()
    q = _embed_one(text)
    sims = _safe_cosine_matrix(label_mat, q)
    order = np.argsort(-sims)
    ranked = [{"label": keys[i], "section": SECTION_MAP[keys[i]], "score": float(sims[i])}
              for i in order[:max(1, top_k)]]
    best = ranked[0]
    if threshold and best["score"] < threshold:
        return {"input": text, "best": None, "top_k": ranked, "note": "below threshold"}
    return {"input": text, "best": best, "top_k": ranked}

# --- demo ---
if __name__ == "__main__":
    for item in ["Grapple"]:
        print(classify_to_section(item, top_k=3, threshold=0.28))
