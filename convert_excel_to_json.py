import pandas as pd
import json

print("Membaca Excel...")

df = pd.read_excel("nilai/data_siswa.xlsx")

# ubah semua NaN menjadi string kosong
df = df.fillna("")

# ubah ke list JSON
data_list = df.to_dict(orient="records")

print("Menyimpan JSON...")

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data_list, f, indent=2, ensure_ascii=False)

print("JSON berhasil dibuat tanpa NaN")