import pandas as pd
import json

df = pd.read_excel("nilai/data_siswa.xlsx")

# ganti semua NaN dengan kosong
df = df.fillna("")

# ubah ke list json
data_list = df.to_dict(orient="records")

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data_list, f, indent=2, ensure_ascii=False, allow_nan=False)

print("Excel berhasil diubah menjadi JSON tanpa NaN")