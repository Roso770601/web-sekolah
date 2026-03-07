import pandas as pd
import json

df = pd.read_excel("nilai/data_siswa.xlsx")

# ubah NaN menjadi None (akan jadi null di JSON)
df = df.where(pd.notnull(df), None)

data_list = df.to_dict(orient="records")

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data_list, f, indent=2, ensure_ascii=False)

print("JSON berhasil dibuat tanpa NaN")