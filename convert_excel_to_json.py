import pandas as pd
import json

# baca file excel
df = pd.read_excel("data_siswa.xlsx")

# ubah ke format list
data = df.to_dict(orient="records")

# simpan ke json
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Berhasil membuat data.json")