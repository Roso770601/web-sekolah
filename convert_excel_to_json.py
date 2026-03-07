import pandas as pd
import json
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

# Baca Excel semua kolom sebagai string
excel_path = os.path.join(base_dir, "nilai", "data_siswa.xlsx")
df = pd.read_excel(excel_path, dtype=str)

# Paksa PIN dari 4 digit terakhir NISN
df['pin'] = df['nisn'].apply(lambda x: str(x)[-4:])

# Pastikan NISN & PIN benar-benar string
df['nisn'] = df['nisn'].apply(str)
df['pin'] = df['pin'].apply(str)
df['kelas'] = df['kelas'].apply(str)
df['nama'] = df['nama'].apply(str)
df['tgl_lahir'] = df['tgl_lahir'].apply(str)

# Hanya ganti NaN di kolom nilai optional jadi ""
nilai_cols = ['matematika','bahasa_indonesia','ppkn','ipas','pjok','seni_rupa']
for col in nilai_cols:
    if col in df.columns:
        df[col] = df[col].fillna("")

# Convert ke dict, paksa NISN & PIN tetap string
data_list = []
for _, row in df.iterrows():
    data_list.append({k: str(v) if k in ['nisn','pin'] else v for k, v in row.items()})

# Simpan JSON di folder nilai
json_path = os.path.join(base_dir, "nilai", "data.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(data_list, f, ensure_ascii=False, indent=2)

print(f"✅ data.json berhasil dibuat, NISN & PIN pakai \"\", kolom nilai kosong aman, nama tetap ada!")