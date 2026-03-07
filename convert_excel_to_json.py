import pandas as pd
import json
import os

# Folder root tempat script ini berada
base_dir = os.path.dirname(os.path.abspath(__file__))

# Path Excel
excel_path = os.path.join(base_dir, "nilai", "data_siswa.xlsx")

# Baca Excel semua kolom sebagai string
df = pd.read_excel(excel_path, dtype=str)

# Paksa PIN dari 4 digit terakhir NISN (jika kolom PIN kosong)
if 'pin' not in df.columns:
    df['pin'] = df['nisn'].apply(lambda x: str(x)[-4:])

# Pastikan NISN, PIN, nama, kelas, tgl_lahir tetap string
for col in ['nisn', 'pin', 'nama', 'kelas', 'tgl_lahir']:
    if col in df.columns:
        df[col] = df[col].apply(str)

# Semua kolom selain nisn, pin, nama, kelas, tgl_lahir dianggap kolom nilai
nilai_cols = [col for col in df.columns if col not in ['nisn','pin','nama','kelas','tgl_lahir']]

# Ganti NaN di semua kolom nilai jadi string kosong
for col in nilai_cols:
    df[col] = df[col].fillna("")

# Convert ke list of dict
data_list = []
for _, row in df.iterrows():
    data_list.append({k: str(v) if k in ['nisn','pin'] else v for k, v in row.items()})

# Simpan JSON
json_path = os.path.join(base_dir, "nilai", "data.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(data_list, f, ensure_ascii=False, indent=2)

print(f"✅ data.json berhasil dibuat di {json_path} dengan semua kolom nilai otomatis")
