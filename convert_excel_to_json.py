import pandas as pd
import json
import os

# Folder dasar
base_dir = os.path.dirname(os.path.abspath(__file__))

# Baca Excel semua kolom sebagai string
excel_path = os.path.join(base_dir, "nilai", "data_siswa.xlsx")
df = pd.read_excel(excel_path, dtype=str)

# Paksa PIN dari 4 digit terakhir NISN
df['pin'] = df['nisn'].apply(lambda x: str(x)[-4:])

# Pastikan info utama string
info_cols = ['kelas','nisn','nama','tgl_lahir','pin']
for col in info_cols:
    df[col] = df[col].apply(str)

# Ambil semua kolom nilai (otomatis kolom selain info utama)
nilai_cols = [c for c in df.columns if c not in info_cols]

# Ganti NaN semua kolom nilai dengan ""
for col in nilai_cols:
    df[col] = df[col].fillna("")

# Buat list dictionary
data_list = []
for _, row in df.iterrows():
    data_list.append({k: str(v) if k in ['nisn','pin'] else v for k, v in row.items()})

# Simpan JSON
json_path = os.path.join(base_dir, "nilai", "data.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(data_list, f, ensure_ascii=False, indent=2)

print(f"✅ data.json berhasil dibuat, semua mapel baru otomatis, nilai kosong aman, NISN & PIN pakai string!")