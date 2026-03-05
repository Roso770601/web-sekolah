import pandas as pd
import json
import os

# ======================
# File Excel & JSON
# ======================
excel_file = 'data_siswa.xlsx'      # Nama file Excel
json_file = os.path.join('nilai', 'data.json')  # Hasil JSON akan di folder 'nilai'

# Pastikan folder 'nilai' ada
if not os.path.exists('nilai'):
    os.makedirs('nilai')

# ======================
# Baca Excel
# ======================
df = pd.read_excel(excel_file)

# ======================
# Convert ke list of dict
# ======================
data_list = []

for _, row in df.iterrows():
    # Ambil tgl_lahir tanpa strip
    tgl = row['tgl_lahir']
    if not pd.isna(tgl):
        # Jika Excel berupa angka (20160512) langsung string
        try:
            tgl = str(int(tgl))
        except:
            # Jika Excel format datetime
            tgl = tgl.strftime('%Y%m%d')
    else:
        tgl = ''

    data_dict = {
        'nis': str(row['nis']),
        'nama': row['nama'],
        'tgl_lahir': tgl,
        'matematika': row['matematika'],
        'bahasa_indonesia': row['bahasa_indonesia'],
        'ppkn': row['ppkn'],
        'ipa': row['ipa'],
        'ips': row['ips']
    }

    data_list.append(data_dict)

# ======================
# Simpan ke JSON
# ======================
with open(json_file, 'w', encoding='utf-8') as f:
    json.dump(data_list, f, ensure_ascii=False, indent=2)

print(f"✅ Konversi selesai! File JSON tersimpan di '{json_file}'")