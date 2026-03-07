import pandas as pd
import json

# baca file excel
df = pd.read_excel("nilai/data_siswa.xlsx")

data_list = []

for _, row in df.iterrows():
    siswa = {}

    for kolom in df.columns:
        nilai = row[kolom]

        if pd.isna(nilai):
            nilai = ""

        siswa[kolom] = str(nilai).strip()

    data_list.append(siswa)

# simpan ke json
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data_list, f, indent=2, ensure_ascii=False)

print("✅ Excel berhasil diubah menjadi JSON!")