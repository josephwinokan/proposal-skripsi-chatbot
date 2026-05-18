from flask import Flask, render_template, request, redirect, session, jsonify
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

app = Flask(__name__)
app.secret_key = "rahasia_super_aman"

CSV_FILE = "faq_final.csv"

# ================================
# 🔥 TEXT PREPROCESSING
# ================================
def preprocess_text(text):
    text = str(text).lower()

    # hapus karakter aneh
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)

    slang = {
        "elu": "kamu",
        "loe": "kamu",
        "gue": "saya",
        "gw": "saya",
        "gk": "tidak",
        "ga": "tidak",
        "nggak": "tidak",
        "krsan": "krs"
    }

    words = text.split()
    words = [slang[w] if w in slang else w for w in words]

    return " ".join(words)


# ================================
# 🔥 INTENT FILTER
# ================================
def detect_intent(msg):
    msg = msg.lower()

    if any(x in msg for x in ["kamu siapa", "siapa kamu"]):
        return "Saya adalah chatbot akademik kampus."

    if any(x in msg for x in ["halo", "hai", "hi"]):
        return "Halo! Ada yang bisa saya bantu?"

    if "terima kasih" in msg:
        return "Sama-sama 🙌"

    if len(msg.split()) < 2:
        return "Pertanyaan terlalu singkat, coba lebih jelas ya."

    return None


# ================================
# 🔥 CLEANING DATA SCRAPING
# ================================
def clean_scraping(text):
    text = str(text).lower()

    # hapus bagian menu panjang
    text = re.sub(r'menu.*', '', text)

    # hapus noise umum
    noise = [
        "profil", "panduan", "login", "email",
        "mahasiswa", "akademik"
    ]

    for n in noise:
        text = text.replace(n, "")

    text = re.sub(r"\s+", " ", text).strip()
    return text


# ================================
# 🔥 LOAD DATA
# ================================
def load_faqs():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)

        df["pertanyaan"] = df["pertanyaan"].fillna("")
        df["jawaban"] = df["jawaban"].fillna("")

        df["jawaban"] = df["jawaban"].apply(clean_scraping)

        return df

    return pd.DataFrame(columns=["id","pertanyaan","jawaban","kategori","semester_berlaku","sumber"])


def save_faqs(df):
    df.to_csv(CSV_FILE, index=False)


# ================================
# 🔥 INIT MODEL
# ================================
def train_model(df):
    if df.empty:
        return None, None

    vectorizer = TfidfVectorizer(ngram_range=(1,2))
    X = vectorizer.fit_transform(df["pertanyaan"].apply(preprocess_text))

    return vectorizer, X


data = load_faqs()
vectorizer, X = train_model(data)


# ================================
# 🔥 ROUTES
# ================================
@app.route("/")
def home():
    return render_template("index.html")


# ================================
# 🔐 ADMIN
# ================================
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin":
            session["admin"] = True
            return redirect("/admin/dashboard")
        return render_template("login.html", error="Login gagal")

    return render_template("login.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/admin")

    rows = load_faqs().to_dict(orient="records")
    return render_template("admin.html", rows=rows)


# ================================
# ➕ TAMBAH FAQ
# ================================
@app.route("/add_faq", methods=["POST"])
def add_faq():
    df = load_faqs()

    new_row = {
        "id": len(df) + 1,
        "pertanyaan": request.form.get("pertanyaan"),
        "jawaban": request.form.get("jawaban"),
        "kategori": request.form.get("kategori"),
        "semester_berlaku": request.form.get("semester"),
        "sumber": request.form.get("sumber")
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_faqs(df)

    # retrain model
    global data, vectorizer, X
    data = df
    vectorizer, X = train_model(data)

    return jsonify({"status": "success"})


# ================================
# 🤖 CHATBOT
# ================================
@app.route("/get", methods=["POST"])
def chatbot():
    user_msg = request.get_json().get("msg", "")

    if not user_msg.strip():
        return jsonify({"response": "Tolong masukkan pertanyaan."})

    # intent
    intent = detect_intent(user_msg)
    if intent:
        return jsonify({"response": intent})

    if X is None:
        return jsonify({"response": "Data belum tersedia."})

    user_clean = preprocess_text(user_msg)

    user_vec = vectorizer.transform([user_clean])
    similarity = cosine_similarity(user_vec, X)

    idx = similarity.argmax()
    score = similarity[0][idx]

    # DEBUG
    print("USER:", user_msg)
    print("CLEAN:", user_clean)
    print("SCORE:", score)

    if score < 0.45:
        return jsonify({
            "response": "Maaf, pertanyaan tidak ditemukan. Coba gunakan kata kunci lain."
        })

    row = data.iloc[idx]

    return jsonify({
        "response": f"{row['jawaban']}\n\n📌 {row['kategori']} | {row['semester_berlaku']}\n🔗 {row['sumber']}"
    })


# ================================
# 🚀 RUN
# ================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)