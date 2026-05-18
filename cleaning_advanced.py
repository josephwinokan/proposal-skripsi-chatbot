import pandas as pd
import re

def clean_text(text):
    text = str(text).lower()

    # hapus html / simbol aneh
    text = re.sub(r'<.*?>', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)

    # hapus kata tidak penting (stopwords sederhana)
    stopwords = [
        "yang", "dan", "di", "ke", "dari", "untuk",
        "pada", "dengan", "adalah", "itu", "ini"
    ]

    words = text.split()
    words = [w for w in words if w not in stopwords]

    return " ".join(words)


def main():
    df = pd.read_csv("faq_final.csv")

    df["pertanyaan"] = df["pertanyaan"].apply(clean_text)
    df["jawaban"] = df["jawaban"].apply(clean_text)

    # hapus data kosong
    df = df[df["pertanyaan"].str.len() > 5]
    df = df[df["jawaban"].str.len() > 20]

    # hapus duplikat
    df = df.drop_duplicates(subset=["pertanyaan"])

    df.to_csv("faq_clean.csv", index=False)

    print("✅ Cleaning selesai!")
    print("Total data:", len(df))


if __name__ == "__main__":
    main()