import pandas as pd
import re

df = pd.read_csv("faq_baak_scraping.csv")

def clean_text(text):
    text = str(text)

    # hapus menu navigasi umum
    patterns = [
        "Menu Profil.*",
        "Skip to content",
        "BAAK Menu.*",
    ]

    for p in patterns:
        text = re.sub(p, "", text, flags=re.IGNORECASE)

    # hapus karakter aneh
    text = re.sub(r'\s+', ' ', text)

    # ambil kalimat penting saja (max 2 kalimat)
    sentences = text.split(".")
    text = ". ".join(sentences[:2])

    return text.strip()


def clean_title(title):
    title = str(title)

    # hapus "- BAAK"
    title = re.sub(r'- BAAK.*', '', title)

    return title.strip()


# cleaning
df["pertanyaan"] = df["pertanyaan"].apply(clean_title)
df["jawaban"] = df["jawaban"].apply(clean_text)

# hapus data yang terlalu pendek / tidak valid
df = df[df["jawaban"].str.len() > 30]

# hapus duplikat
df = df.drop_duplicates(subset=["pertanyaan"])

# simpan
df.to_csv("faq_clean.csv", index=False)

print("✅ Cleaning selesai!")
print("Jumlah data:", len(df))