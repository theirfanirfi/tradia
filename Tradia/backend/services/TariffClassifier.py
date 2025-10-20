# """
# HS/Tariff classifier (no fine-tuning)
# -------------------------------------

# Drop-in module that implements a hierarchical HS code matcher using a
# hybrid retrieval approach (BM25 + embeddings) and structure-aware logic.

# Dependencies (install in your environment):
#     pip install sentence-transformers rank-bm25 numpy tqdm

# Recommended base model (multilingual & strong):
#     BAAI/bge-m3   (supports short queries well)
# Alternative (English-focused):
#     intfloat/e5-large-v2

# How it works
# ------------
# 1) Build a canonical catalog from your tariff rows (at the leaf level you
#    intend to return, e.g., subheading). Each doc text concatenates the full
#    path (Section→Chapter→Heading→Subheading) plus synonyms you provide.
# 2) Hybrid retrieval at inference:
#    - BM25 lexical search returns top-K candidates fast.
#    - Bi-encoder embeddings re-rank those candidates semantically.
#    - Scores are fused (weighted sum). No fine-tuning needed.
# 3) Hierarchical guardrails: the returned subheading carries its heading,
#    chapter, and section—so the structure is always consistent.

# You can use this as a library or run the demo at the bottom.
# """
# from __future__ import annotations

# from dataclasses import dataclass
# from typing import List, Dict, Optional, Tuple
# import re
# import json
# import math
# import numpy as np
# from tqdm import tqdm
# import os, hashlib


# # BM25
# from rank_bm25 import BM25Okapi

# # Embeddings
# from sentence_transformers import SentenceTransformer, util

# # ------------------------------
# # Data model
# # ------------------------------

# @dataclass
# class TariffEntry:
#     section_code: str  # e.g., "I"
#     chapter_number: str  # e.g., "01"
#     chapter_title: str   # e.g., "Live animals"
#     heading_code: str    # e.g., "0101" (derived from reference_number)
#     code: str            # leaf code, e.g., "0101.21.00"
#     title: str           # the subheading text (e.g., "-- Pure-bred breeding animals")
#     doc_text: str        # concatenated path and description for retrieval
#     extra: dict          # any additional fields you want to carry around


# # ------------------------------
# # Text normalization / tokenization
# # ------------------------------

# def _strip_punct(text: str) -> str:
#     return re.sub(r"[^\w\s]", " ", text)


# try:
#     # regex is optional; if unavailable, fall back
#     import regex as _regex
#     _HAS_REGEX = True
# except Exception:
#     _HAS_REGEX = False


# def _strip_punct(text: str) -> str:
#     if _HAS_REGEX:
#         return _regex.sub(r"\p{P}+[\s\n]*", " ", text)
#     return re.sub(r"[^\w\s]", " ", text)


# def normalize(text: str) -> str:
#     text = text.lower().strip()
#     text = _strip_punct(text)
#     text = re.sub(r"\s+", " ", text)
#     return text


# def tokenize(text: str) -> List[str]:
#     return normalize(text).split()


# # ------------------------------
# # Catalog builder
# # ------------------------------

# class Catalog:
#     def __init__(self, index_dir: Optional[str] = None):
#         self.entries: List[TariffEntry] = []
#         self.doc_texts: List[str] = []
#         self.doc_titles: List[str] = []
#         self.codes: List[str] = []
#         self._bm25 = None
#         self._emb_model = None
#         self._doc_embs: Optional[np.ndarray] = None

#         self.index_dir = index_dir
#         if self.index_dir:
#             os.makedirs(self.index_dir, exist_ok=True)
#         self._saved_model_name: Optional[str] = None


#     @staticmethod
#     def build_doc_text(section_code: str,
#                        chapter_number: str,
#                        chapter_title: str,
#                        heading_code: str,
#                        leaf_code: str,
#                        subheading: str,
#                        synonyms: Optional[List[str]] = None) -> str:
#         path = (
#             f"Section {section_code}; "
#             f"Chapter {chapter_number} {chapter_title}; "
#             f"Heading {heading_code}; "
#             f"Subheading {leaf_code} {subheading}"
#         )
#         syn = f" Synonyms: {', '.join(synonyms)}" if synonyms else ""
#         return (path + "." + syn).strip()

#     def add_entry(self, entry: TariffEntry):
#         self.entries.append(entry)
#         self.doc_texts.append(entry.doc_text)
#         self.doc_titles.append(entry.title)
#         self.codes.append(entry.code)

#     def build_from_rows(self,
#                     rows: List[Dict],
#                     section_title_lookup: Optional[Dict[str, str]] = None,
#                     synonyms_index: Optional[Dict[str, List[str]]] = None) -> None:
#         """Build catalog from raw tariff rows (robust to None / bad types)."""

#         def _s(val) -> str:
#             # safe string: None -> "", numbers -> str(n), strings -> stripped
#             if val is None:
#                 return ""
#             if isinstance(val, str):
#                 return val.strip()
#             return str(val).strip()

#         def _to_int(val, default=0) -> int:
#             try:
#                 if val is None or _s(val) == "":
#                     return default
#                 return int(_s(val))
#             except Exception:
#                 return default

#         added = 0
#         skipped_missing_code = 0
#         skipped_non_leaf = 0

#         for r in rows:
#             code = _s(r.get("reference_number"))
#             subheading = _s(r.get("subheading"))
#             section_code = _s(r.get("section"))
#             chapter_number = _s(r.get("chapter_number"))
#             chapter_title = _s(r.get("chapter_title"))
#             indent_level = _to_int(r.get("indent_level"), 0)

#             # Only index leaf rows (adjust this if your schema differs)
#             if not code:
#                 skipped_missing_code += 1
#                 continue
#             if indent_level == 0:
#                 skipped_non_leaf += 1
#                 continue

#             # Derive heading_code from first 4 digits if not provided
#             heading_code = _s(r.get("heading_code"))
#             if not heading_code:
#                 m = re.search(r"(\d{4})", code)
#                 heading_code = m.group(1) if m else ""

#             # Synonyms (optional)
#             syns = None
#             if synonyms_index is not None:
#                 syns = synonyms_index.get(code) or synonyms_index.get(heading_code)

#             doc_text = self.build_doc_text(
#                 section_code=section_code,
#                 chapter_number=chapter_number,
#                 chapter_title=chapter_title,
#                 heading_code=heading_code,
#                 leaf_code=code,
#                 subheading=subheading,
#                 synonyms=syns,
#             )

#             entry = TariffEntry(
#                 section_code=section_code,
#                 chapter_number=chapter_number,
#                 chapter_title=chapter_title,
#                 heading_code=heading_code,
#                 code=code,
#                 title=subheading,
#                 doc_text=doc_text,
#                 extra={k: v for k, v in r.items() if k not in {
#                     "section", "chapter_number", "chapter_title", "reference_number",
#                     "subheading", "indent_level", "heading_code"
#                 }},
#             )
#             self.add_entry(entry)
#             added += 1

#         # quick summary to help you validate
#         print(f"Catalog build: added={added}, skipped_missing_code={skipped_missing_code}, skipped_non_leaf={skipped_non_leaf}")

#     # ------------------------------
#     # Indexers
#     # ------------------------------

#     def build_bm25(self) -> None:
#         tokenized = [tokenize(t) for t in self.doc_texts]
#         self._bm25 = BM25Okapi(tokenized)

#     def build_embeddings(self,
#                         model_name: str = "BAAI/bge-m3",
#                         batch_size: int = 128,
#                         normalize: bool = True,
#                         use_cache: bool = True) -> None:
#         """
#         Build or load cached embeddings for doc_texts.

#         Cache layout when index_dir is provided:
#         - texts.json
#         - entries.json
#         - embeddings.npy
#         - meta.json {"model_name": "...", "fingerprint": "..."}
#         """
#         if self.index_dir:
#             texts_path = os.path.join(self.index_dir, "texts.json")
#             embs_path  = os.path.join(self.index_dir, "embeddings.npy")
#             meta_path  = os.path.join(self.index_dir, "meta.json")

#             fp = hashlib.md5("\n".join(self.doc_texts).encode("utf-8")).hexdigest()

#             if use_cache and os.path.exists(embs_path) and os.path.exists(meta_path) and os.path.exists(texts_path):
#                 try:
#                     with open(meta_path, "r", encoding="utf-8") as f:
#                         meta = json.load(f)
#                     if meta.get("model_name") == model_name and meta.get("fingerprint") == fp:
#                         self._doc_embs = np.load(embs_path)
#                         self._saved_model_name = model_name
#                         with open(texts_path, "r", encoding="utf-8") as f:
#                             disk_texts = json.load(f)
#                         if disk_texts == self.doc_texts:
#                             self._emb_model = SentenceTransformer(model_name)
#                             return
#                 except Exception:
#                     pass

#         # compute fresh
#         self._emb_model = SentenceTransformer(model_name)
#         embs = self._emb_model.encode(self.doc_texts,
#                                     batch_size=batch_size,
#                                     convert_to_tensor=True,
#                                     normalize_embeddings=normalize,
#                                     show_progress_bar=True)
#         self._doc_embs = embs.detach().cpu().numpy().astype("float32")

#         # save cache
#         if self.index_dir:
#             texts_path   = os.path.join(self.index_dir, "texts.json")
#             entries_path = os.path.join(self.index_dir, "entries.json")
#             embs_path    = os.path.join(self.index_dir, "embeddings.npy")
#             meta_path    = os.path.join(self.index_dir, "meta.json")
#             with open(texts_path, "w", encoding="utf-8") as f:
#                 json.dump(self.doc_texts, f)
#             with open(entries_path, "w", encoding="utf-8") as f:
#                 json.dump([e.__dict__ for e in self.entries], f)
#             np.save(embs_path, self._doc_embs)
#             with open(meta_path, "w", encoding="utf-8") as f:
#                 json.dump({"model_name": model_name,
#                         "fingerprint": hashlib.md5("\n".join(self.doc_texts).encode("utf-8")).hexdigest()}, f)

#         # ------------------------------
#         # Search / predict
#         # ------------------------------

#     def save_index_only(self):
#         if not self.index_dir: return
#         with open(os.path.join(self.index_dir, "texts.json"), "w", encoding="utf-8") as f:
#             json.dump(self.doc_texts, f)
#         with open(os.path.join(self.index_dir, "entries.json"), "w", encoding="utf-8") as f:
#             json.dump([e.__dict__ for e in self.entries], f)

#     def load_index(self) -> bool:
#         if not self.index_dir: return False
#         texts_path   = os.path.join(self.index_dir, "texts.json")
#         entries_path = os.path.join(self.index_dir, "entries.json")
#         embs_path    = os.path.join(self.index_dir, "embeddings.npy")
#         meta_path    = os.path.join(self.index_dir, "meta.json")
#         if not (os.path.exists(texts_path) and os.path.exists(entries_path)):
#             return False
#         with open(texts_path, "r", encoding="utf-8") as f:
#             self.doc_texts = json.load(f)
#         with open(entries_path, "r", encoding="utf-8") as f:
#             raw = json.load(f)
#         self.entries    = [TariffEntry(**e) for e in raw]
#         self.doc_titles = [e.title for e in self.entries]
#         self.codes      = [e.code for e in self.entries]
#         self.build_bm25()
#         if os.path.exists(embs_path) and os.path.exists(meta_path):
#             self._doc_embs = np.load(embs_path)
#             with open(meta_path, "r", encoding="utf-8") as f:
#                 meta = json.load(f)
#             self._saved_model_name = meta.get("model_name")
#         return True

#     def search(self,
#             query: str,
#             k_lex: int = 200,
#             k_dense: int = 50,
#             alpha_dense: float = 0.65,
#             return_topn: int = 5,
#             normalize_query: bool = True,
#             stagewise_filter: bool = False) -> List[Tuple[TariffEntry, float]]:
#         """Hybrid retrieval.

#         Args:
#             query: user title
#             k_lex: how many BM25 candidates to take into dense stage
#             k_dense: final pool size for fusion / ranking
#             alpha_dense: weight for dense scores in linear fusion (0..1)
#             return_topn: how many results to return
#             normalize_query: apply normalization to query
#             stagewise_filter: if True, do a weak chapter-level filter using
#                 the top lexical candidate's chapter as a soft constraint.
#         """
#         assert self._bm25 is not None, "Call build_bm25() first"
#         assert self._emb_model is not None and self._doc_embs is not None, "Call build_embeddings() first"

#         q = normalize(query) if normalize_query else query

#         # 1) Lexical stage
#         bm25_scores = self._bm25.get_scores(tokenize(q))
#         # Pick top k_lex indices
#         lex_top_idx = np.argpartition(-bm25_scores, kth=min(k_lex, len(bm25_scores)-1))[:k_lex]

#         # Optional stage-wise soft filter by chapter of the #1 lexical hit
#         if stagewise_filter and len(lex_top_idx) > 0:
#             best_lex = int(np.argmax(bm25_scores))
#             best_ch = self.entries[best_lex].chapter_number
#             # Keep lexical candidates with same chapter, but fall back to all if too few
#             same_ch = [i for i in lex_top_idx if self.entries[i].chapter_number == best_ch]
#             if len(same_ch) >= max(20, k_dense):
#                 lex_top_idx = np.array(same_ch, dtype=int)

#         # 2) Dense re-score of lexical candidates
#         q_emb = self._emb_model.encode([q], convert_to_tensor=True, normalize_embeddings=True)
#         cand_embs = self._doc_embs[lex_top_idx]
#         # cosine similarity (q_emb already normalized)
#         dense_scores = util.cos_sim(q_emb, cand_embs).cpu().numpy().ravel()

#         # 3) Score fusion (min-max normalize each to [0,1])
#         def _minmax(x: np.ndarray) -> np.ndarray:
#             if len(x) == 0:
#                 return x
#             mn, mx = float(np.min(x)), float(np.max(x))
#             if mx <= mn + 1e-9:
#                 return np.zeros_like(x)
#             return (x - mn) / (mx - mn)

#         lex_scores = bm25_scores[lex_top_idx]
#         lex_norm = _minmax(lex_scores)
#         dense_norm = _minmax(dense_scores)
#         fused = (1.0 - alpha_dense) * lex_norm + alpha_dense * dense_norm

#         # 4) Select top k_dense → final sort
#         take = min(k_dense, len(fused))
#         topk_local = np.argpartition(-fused, kth=take-1)[:take]
#         # final ordering by fused score desc, tie break by exact token overlap length
#         def overlap_bonus(i_idx: int) -> int:
#             q_tokens = set(tokenize(q))
#             d_tokens = set(tokenize(self.doc_texts[lex_top_idx[i_idx]]))
#             return len(q_tokens & d_tokens)

#         order = sorted(topk_local.tolist(), key=lambda i: (fused[i], overlap_bonus(i)), reverse=True)

#         results: List[Tuple[TariffEntry, float]] = []
#         for i in order[:return_topn]:
#             entry = self.entries[lex_top_idx[i]]
#             results.append((entry, float(fused[i])))
#         return results

#     def predict_best(self, query: str, **kwargs) -> Tuple[TariffEntry, float]:
#         res = self.search(query, return_topn=1, **kwargs)
#         if not res:
#             raise ValueError("No results. Is the catalog empty?")
#         return res[0]


# # ------------------------------
# # Simple demo / CLI
# # ------------------------------

# _DEMO_SECTION_MAP = {
#     "Animals": "I",
#     "Vegetables": "II",
#     "Oils/Fats": "III",
#     "Food/Drink": "IV",
#     "Minerals": "V",
#     "Chemicals": "VI",
#     "Plastics/Rubber": "VII",
#     "Leather/Furs": "VIII",
#     "Woodwork": "IX",
#     "Paper": "X",
#     "Textiles": "XI",
#     "Footwear/Wearables": "XII",
#     "Stone/Ceramics": "XIII",
#     "Jewellery": "XIV",
#     "Metals": "XV",
#     "Machinery/Electronics": "XVI",
#     "Transport": "XVII",
#     "Instruments": "XVIII",
#     "Arms": "XIX",
#     "Misc. Goods": "XX",
#     "Art/Antiques": "XXI",
# }


# # if __name__ == "__main__":

#     #read jsonl file for the rows list
#     # with open("abf_tariff_schedule3.jsonl", "r") as f:
#     #     rows_list = [json.loads(line) for line in f]

#     # print(len(rows_list), "rows loaded.")

#     # catalog = Catalog(index_dir="tradia_tariff_index")
#     # catalog.build_from_rows(rows_list)
#     # catalog.build_bm25()
#     # catalog.build_embeddings(model_name="BAAI/bge-m3", use_cache=True)  # or "intfloat/e5-large-v2"
# catalog = Catalog(index_dir="tradia_tariff_index")
# catalog.load_index()
# catalog.build_embeddings(use_cache=True)

#     # best_entry, score = catalog.predict_best("GRAPPLE")
#     # print(best_entry.code, best_entry.chapter_number, best_entry.heading_code, best_entry.title)
