import pandas as pd
import json

df = pd.read_excel("nilai/data_siswa.xlsx")

# GANTI SEMUA NaN MENJADI STRING KOSONG
df = df.fillna("")

data_list = []

for _, row in df.iterrows():
    siswa = {
        "nisn": str(row["nisn"]).strip(),
        "nama": str(row["nama"]).strip(),
        "tgl_lahir": str(row["tgl_lahir"]).strip(),
        "matematika": row["matematika"],
        "bahasa_indonesia": row["bahasa_indonesia"],
        "ppkn": row["ppkn"],
        "ipas": row["ipas"],
        "pjok": row["pjok"],
        "seni_rupa": row["seni_rupa"]
    }

    data_list.append(siswa)

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data_list, f, indent=2, ensure_ascii=False)

print("Excel berhasil diubah menjadi JSON")