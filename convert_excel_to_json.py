import pandas as pd
import json
import os

df = pd.read_excel("nilai/data_siswa.xlsx")

# Ubah kolom 'nisn' jadi string
df = df.rename(columns=lambda x: x.strip())
df['nisn'] = df['nisn'].astype(str)

data_list = df.to_dict(orient="records")

if not os.path.exists("nilai"):
    os.makedirs("nilai")

with open("nilai/data.json", "w", encoding="utf-8") as f:
    json.dump(data_list, f, indent=2, ensure_ascii=False)

print("data.json berhasil diperbarui di folder 'nilai'")