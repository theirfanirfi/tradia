#!/usr/bin/env python3
"""
scripts/generate_models.py

Reads B650_Field_Mapping_Fully_Numbered_N10.csv and
generates a Pydantic BaseModel class with proper types and
Optional[...] for non-required fields.
"""

import pandas as pd
import re

# 1) Load the mapping CSV
df = pd.read_csv("/home/abdulwahab-bhai/personal/tradia_ai_backend/backend/docs/B957_Voice_Interaction_Mapping.json")

# 2) Helpers to sanitize names and map types
def to_snake(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[ /&(),-]+", "_", s)
    s = re.sub(r"__+", "_", s)
    s = s.strip("_")
    if s and s[0].isdigit():
        s = "_" + s
    return s

def map_type(dt: str, required: bool) -> str:
    dt = dt.lower()
    if dt in ("numeric",):
        base = "float"
    else:
        # cover code/identifier, string, code
        base = "str"
    if not required:
        return f"Optional[{base}] = None"
    else:
        return base

# 3) Build fields
fields = []
for _, row in df.iterrows():
    field_name = row["Field Name"]
    required   = bool(row["Required"])
    data_type  = row["Data Type"]
    py_name    = to_snake(field_name)
    annotation = map_type(data_type, required)
    fields.append((py_name, annotation))

# 4) Emit the model code
model_lines = [
    "from typing import Optional",
    "from pydantic import BaseModel\n",
    "class B650Model(BaseModel):"
]
for name, ann in fields:
    model_lines.append(f"    {name}: {ann}")

# 5) Write it out
output = "\n".join(model_lines) + "\n"
with open("b650_schema.py", "w") as f:
    f.write(output)

print("Wrote app/utils/schema_definitions.py with B650Model!")
