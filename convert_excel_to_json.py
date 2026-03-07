import pandas as pd
import json
import os

# Nama file Excel
excel_file = "data_siswa.xlsx"  # ganti sesuai nama file Excel kamu
# Folder tujuan JSON
output_folder = "nilai"
output_file = os.path.join(output_folder, "data.json")

# Baca Excel
df = pd.read_excel("nilai/data_siswa.xlsx")

# Buat list of dict
data_list = []

for _, row in df.iterrows():
    siswa = {
        "nisn": str(row["nisn"]).strip(),
        "nama": str(row["nama"]).strip(),
        "tgl_lahir": str(row["tgl_lahir"]).strip(),
        "matematika": row["matematika"],
        "bahasa_indonesia": row["bahasa_indonesia"],
        "ppkn": row["ppkn"],
        "ipa": row["ipas"],
        "pjok": row["pjok"],
        "seni_rupa": row["seni_rupa"]
    }
    data_list.append(siswa)

# Simpan ke JSON
os.makedirs(output_folder, exist_ok=True)
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data_list, f, indent=2, ensure_ascii=False)

print(f"Berhasil membuat JSON di {output_file}")