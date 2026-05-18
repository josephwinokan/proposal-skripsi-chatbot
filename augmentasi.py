import pandas as pd
import random

# Load dataset asli
df = pd.read_csv("faq.csv")

# Kamus sinonim
sinonim = {
    "bagaimana": ["gimana", "cara", "bagaimana cara"],
    "dimana": ["di mana", "lokasi", "tempat"],
    "apa": ["apakah", "apa itu"],
    "kapan": ["kapan sih", "waktu"],
    "mengisi": ["isi", "input"],
    "melihat": ["cek", "lihat"],
    "membayar": ["bayar", "melakukan pembayaran"],
}

def augment_text(text):
    words = str(text).lower().split()
    new_words = []

    for w in words:
        if w in sinonim and random.random() > 0.5:
            new_words.append(random.choice(sinonim[w]))
        else:
            new_words.append(w)

    return " ".join(new_words)

# Hindari error NaN
df["pertanyaan"] = df["pertanyaan"].fillna("")

# Buat data augmentasi
augmented_rows = []

for _, row in df.iterrows():
    for i in range(3):  # 3 variasi tiap pertanyaan
        new_question = augment_text(row["pertanyaan"])

        augmented_rows.append({
            "id": f"{row['id']}_aug{i}",
            "pertanyaan": new_question,
            "jawaban": row["jawaban"],
            "kategori": row["kategori"],
            "semester_berlaku": row["semester_berlaku"],
            "sumber": row["sumber"]
        })

# Gabungkan
df_aug = pd.concat([df, pd.DataFrame(augmented_rows)], ignore_index=True)

# Simpan hasil
df_aug.to_csv("faq_augmented.csv", index=False)

print("✅ Augmentasi selesai!")
print("Total data:", len(df_aug))