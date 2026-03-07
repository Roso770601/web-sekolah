import pandas as pd
import json
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
excel_path = os.path.join(base_dir, "nilai", "data_siswa.xlsx")
df = pd.read_excel(excel_path, dtype=str)

# Paksa PIN dari 4 digit terakhir NISN
df['pin'] = df['nisn'].apply(lambda x: str(x)[-4:])

# Pastikan kolom string
for col in ['nisn','pin','kelas','nama','tgl_lahir']:
    df[col] = df[col].astype(str)

# Isi NaN di semua kolom nilai dengan "-"
nilai_cols = [c for c in df.columns if c not in ['nisn','pin','kelas','nama','tgl_lahir']]
for col in nilai_cols:
    df[col] = df[col].fillna("-")

# Convert ke dict
data_list = df.to_dict(orient='records')

# Simpan JSON
json_path = os.path.join(base_dir, "nilai", "data.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(data_list, f, ensure_ascii=False, indent=2)

print("✅ data.json berhasil dibuat dengan semua kolom nilai!")