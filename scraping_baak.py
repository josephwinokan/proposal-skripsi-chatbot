import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

BASE_URL = "https://baak.universitasmulia.ac.id/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

# 🔥 Ambil link (lebih aman)
def get_links():
    res = requests.get(BASE_URL, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]

        # ambil link internal saja
        if "universitasmulia.ac.id" in href:
            if href.startswith("http"):
                links.append(href)
            else:
                links.append(BASE_URL + href)

    links = list(set(links))
    print("Total link ditemukan:", len(links))

    return links


# 🔥 Ambil isi halaman (ANTI GAGAL)
def scrape_detail(url):
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        # ambil semua teks (pasti ada)
        text = soup.get_text(separator=" ")
        text = " ".join(text.split())

        # ambil sebagian saja biar tidak terlalu panjang
        content = text[:500]

        # ambil title
        title = soup.title.string if soup.title else "Informasi Akademik"

        return title, content

    except Exception as e:
        print("Error:", e)
        return None, None


# 🔥 MAIN
def main():
    links = get_links()

    data = []

    for link in links[:50]:  # batasi biar aman
        print("Scraping:", link)

        title, content = scrape_detail(link)

        if title and content:
            data.append({
                "pertanyaan": title,
                "jawaban": content,
                "kategori": "BAAK",
                "semester_berlaku": "Umum",
                "sumber": link
            })

        time.sleep(1)

    print("Jumlah data berhasil:", len(data))
    print("Preview data:", data[:2])

    if len(data) == 0:
        print("❌ Data kosong! Scraping gagal.")
        return

    df = pd.DataFrame(data)

    # 🔥 PAKSA SIMPAN KE DOCKER MOUNT
    output_path = "/app/faq_baak_scraping.csv"
    df.to_csv(output_path, index=False)

    print("✅ File berhasil dibuat di:", output_path)
    print("Isi folder /app:", os.listdir("/app"))


if __name__ == "__main__":
    main()