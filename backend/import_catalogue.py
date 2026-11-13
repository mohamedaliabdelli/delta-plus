import re
import random
from datetime import datetime, timezone

import pdfplumber
from pymongo import MongoClient

from config import settings

CATS = [(1, 50, "Consommables & Injections"), (51, 100, "Stérilisation & Pansements"),
        (101, 150, "Diagnostic & Monitoring"), (151, 200, "Laboratoire"),
        (201, 250, "Mobilier hospitalier & Réanimation")]


def clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("\n", " ")).strip()


rows = {}
with pdfplumber.open("catalogue.pdf") as pdf:
    for page in pdf.pages:
        for table in page.extract_tables():
            for r in table:
                ref = clean(r[0]).replace(" ", "")
                if re.fullmatch(r"ART-2026-\d{3}", ref):
                    price = float(re.sub(r"[^\d.]", "", clean(r[4]).replace("DT", "")))
                    rows[ref] = (clean(r[1]), clean(r[2]), int(clean(r[3]).replace(" ", "")), price)

print(len(rows), "articles lus dans le PDF")
rng = random.Random(42)
col = MongoClient(settings.mongo_url)["delta_sav"]["equipments"]
added = 0
for ref in sorted(rows):
    name, cond, mn, price = rows[ref]
    n = int(ref[-3:])
    if rng.random() < 0.10:
        q = max(0, round(mn * rng.uniform(0.4, 0.9)))
    else:
        q = max(mn + 1, round(mn * rng.uniform(1.2, 3.0)))
    doc = {"name": name, "reference": ref, "serial_number": None, "lot": None,
           "quantity": q, "min_stock": mn, "expiry_date": None, "statut": "en_stock",
           "categorie": next(c for a, b, c in CATS if a <= n <= b),
           "conditionnement": cond, "prix_tnd": price,
           "created_at": datetime.now(timezone.utc).replace(tzinfo=None)}
    res = col.update_one({"reference": ref}, {"$setOnInsert": doc}, upsert=True)
    added += 1 if res.upserted_id else 0

print(added, "articles ajoutés")
print("Total équipements en base :", col.count_documents({}))
