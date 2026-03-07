import pandas as pd
import json
import math

df = pd.read_excel("nilai/data_siswa.xlsx")

data_list = []

for _, row in df.iterrows():
    siswa = {}

    for kolom in df.columns:
        nilai = row[kolom]

        # Jika nilai NaN ubah menjadi string kosong
        if pd.isna(nilai) or (isinstance(nilai, float) and math.isnan(nilai)):
            nilai = ""

        siswa[kolom] = nilai

    data_list.append(siswa)

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data_list, f, indent=2, ensure_ascii=False)

print("Excel berhasil diubah menjadi JSON tanpa NaN")