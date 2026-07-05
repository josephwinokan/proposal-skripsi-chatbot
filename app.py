from flask import Flask, render_template, request, redirect, session, jsonify, send_file
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "rahasia_super_aman"

CSV_FILE = "faq_final.csv"
CHAT_HISTORY_FILE = "chat_history.csv"

# ================================
# 🔥 TEXT CLEANING
# ================================
def preprocess_text(text):

    text = str(text).lower()

    # hapus simbol
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)

    slang = {
        "elu": "kamu",
        "loe": "kamu",
        "gue": "saya",
        "gw": "saya",
        "gk": "tidak",
        "ga": "tidak",
        "nggak": "tidak",
        "krsan": "krs",
        "maba": "mahasiswa baru"
    }

    words = text.split()

    words = [
        slang[w] if w in slang else w
        for w in words
    ]

    return " ".join(words)

# ================================
# 🔥 INTENT DETECTION
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
# 🔥 LOAD FAQ
# ================================
def load_faqs():

    if os.path.exists(CSV_FILE):

        df = pd.read_csv(CSV_FILE)

        # pastikan kolom ada
        needed = [
            "id",
            "pertanyaan",
            "jawaban",
            "kategori",
            "semester_berlaku",
            "sumber"
        ]

        for col in needed:
            if col not in df.columns:
                df[col] = ""

        df = df.fillna("")

        # cleaning hasil scraping
        df["jawaban"] = df["jawaban"].apply(
            lambda x: re.sub(
                r'menu.*',
                '',
                str(x).lower()
            )
        )

        return df

    return pd.DataFrame(
        columns=[
            "id",
            "pertanyaan",
            "jawaban",
            "kategori",
            "semester_berlaku",
            "sumber"
        ]
    )

# ================================
# 💾 SAVE FAQ
# ================================
def save_faqs(df):
    df.to_csv(CSV_FILE, index=False)

# ================================
# 💾 SAVE CHAT HISTORY
# ================================
def save_chat_history(question, answer, score):

    file_exists = os.path.isfile(CHAT_HISTORY_FILE)

    history = pd.DataFrame([{
        "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pertanyaan": question,
        "jawaban": answer,
        "score": round(float(score), 4)
    }])

    history.to_csv(
        CHAT_HISTORY_FILE,
        mode="a",
        header=not file_exists,
        index=False
    )

# ================================
# 🔥 INIT MODEL
# ================================
data = load_faqs()

vectorizer = TfidfVectorizer(
    ngram_range=(1,3)
)

X = None

# ================================
# 🔥 RETRAIN MODEL
# ================================
def retrain_model():

    global data
    global vectorizer
    global X

    data = load_faqs()

    if not data.empty:

        vectorizer = TfidfVectorizer(
            ngram_range=(1,3)
        )

        X = vectorizer.fit_transform(
            data["pertanyaan"].apply(preprocess_text)
        )

    else:
        X = None

# train awal
retrain_model()

# ================================
# 🏠 HOME
# ================================
@app.route("/")
def home():
    return render_template("index.html")

# ================================
# 🔐 LOGIN ADMIN
# ================================
@app.route("/admin", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin":

            session["admin"] = True

            return redirect("/admin/dashboard")

        return render_template(
            "login.html",
            error="Login gagal"
        )

    return render_template("login.html")

# ================================
# 🚪 LOGOUT
# ================================
@app.route("/admin/logout")
def admin_logout():

    session.pop("admin", None)

    return redirect("/admin")

# ================================
# 📋 DASHBOARD ADMIN
# ================================
@app.route("/admin/dashboard")
def admin_dashboard():

    if not session.get("admin"):
        return redirect("/admin")

    rows = load_faqs().to_dict(orient="records")

    return render_template(
        "admin.html",
        rows=rows
    )

# ================================
# ➕ ADD FAQ
# ================================
@app.route("/add_faq", methods=["POST"])
def add_faq():

    if not session.get("admin"):
        return jsonify({"status": "unauthorized"})

    df = load_faqs()

    # id auto increment aman
    new_id = 1

    if not df.empty:
        new_id = int(df["id"].max()) + 1

    new_row = {
        "id": new_id,
        "pertanyaan": request.form.get("pertanyaan"),
        "jawaban": request.form.get("jawaban"),
        "kategori": request.form.get("kategori"),
        "semester_berlaku": request.form.get("semester"),
        "sumber": request.form.get("sumber")
    }

    df = pd.concat(
        [df, pd.DataFrame([new_row])],
        ignore_index=True
    )

    save_faqs(df)

    retrain_model()

    return jsonify({
        "status": "success",
        "message": "FAQ berhasil ditambahkan"
    })

# ================================
# ✏ EDIT FAQ
# ================================
@app.route("/edit_faq/<int:id>", methods=["POST"])
def edit_faq(id):

    if not session.get("admin"):
        return redirect("/admin")

    df = load_faqs()

    idx = df[df["id"] == id].index

    if len(idx) == 0:
        return "FAQ tidak ditemukan"

    idx = idx[0]

    df.at[idx, "pertanyaan"] = request.form.get("pertanyaan")
    df.at[idx, "jawaban"] = request.form.get("jawaban")
    df.at[idx, "kategori"] = request.form.get("kategori")
    df.at[idx, "semester_berlaku"] = request.form.get("semester")
    df.at[idx, "sumber"] = request.form.get("sumber")

    save_faqs(df)

    retrain_model()

    return redirect("/admin/dashboard")

# ================================
# ❌ DELETE FAQ
# ================================
@app.route("/delete_faq/<int:id>")
def delete_faq(id):

    if not session.get("admin"):
        return redirect("/admin")

    df = load_faqs()

    df = df[df["id"] != id]

    save_faqs(df)

    retrain_model()

    return redirect("/admin/dashboard")

# ================================
# 📊 ANALYTICS
# ================================
@app.route("/admin/analytics")
def analytics():

    if not session.get("admin"):
        return redirect("/admin")

    if os.path.exists(CHAT_HISTORY_FILE):

        history = pd.read_csv(CHAT_HISTORY_FILE)

        rows = history.to_dict(orient="records")

    else:
        rows = []

    return render_template(
        "analytics.html",
        rows=rows
    )

# ================================
# 📥 DOWNLOAD ANALYTICS
# ================================
@app.route("/download/analytics")
def download_analytics():

    if not session.get("admin"):
        return redirect("/admin")

    if not os.path.exists(CHAT_HISTORY_FILE):
        return "Data analytics belum tersedia"

    return send_file(
        CHAT_HISTORY_FILE,
        as_attachment=True
    )

# ================================
# 🤖 CHATBOT
# ================================
@app.route("/get", methods=["POST"])
def chatbot():

    user_msg = request.get_json().get("msg", "")

    if not user_msg.strip():

        return jsonify({
            "response": "Tolong masukkan pertanyaan."
        })

    # intent
    intent = detect_intent(user_msg)

    if intent:

        save_chat_history(
            user_msg,
            intent,
            1
        )

        return jsonify({
            "response": intent
        })

    # preprocessing
    user_msg_clean = preprocess_text(user_msg)

    if X is None:

        return jsonify({
            "response": "Data FAQ belum tersedia."
        })

    # similarity
    user_vec = vectorizer.transform([user_msg_clean])

    similarity = cosine_similarity(user_vec, X)

    idx = similarity.argmax()

    score = similarity[0][idx]

    print("DEBUG SCORE:", score)

    # threshold
    if score < 0.4:

        save_chat_history(
            user_msg,
            "Tidak ditemukan",
            score
        )

        return jsonify({
            "response": "Maaf, pertanyaan tidak ditemukan. Coba gunakan kata kunci lain."
        })

    row = data.iloc[idx]

    answer = f"""
{row['jawaban']}

📌 Kategori: {row['kategori']}
📅 Semester: {row['semester_berlaku']}
🔗 Sumber: {row['sumber']}
"""

    # save history
    save_chat_history(
        user_msg,
        row['jawaban'],
        score
    )

    return jsonify({
        "response": answer
    })

# ================================
# 🚀 RUN APP
# ================================
if __name__ == "__main__":

    app.run(
        debug=True
    )