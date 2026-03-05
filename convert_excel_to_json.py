import pandas as pd
import json

# baca excel
df = pd.read_excel("nilai.xlsx")

# ubah ke list
data = df.to_dict(orient="records")

# simpan ke json di folder nilai
with open("nilai/data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Berhasil membuat nilai/data.json")