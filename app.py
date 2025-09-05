from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

app = Flask(__name__)
app.secret_key = "rahasia_super_aman"  # ganti sesuai kebutuhan

CSV_FILE = "faq.csv"

# --- Fungsi load data ---
def load_faqs():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    else:
        return pd.DataFrame(columns=["id","pertanyaan","jawaban","kategori","semester_berlaku","sumber"])

def save_faqs(df):
    df.to_csv(CSV_FILE, index=False)

# --- Load dataset FAQ awal ---
data = load_faqs()
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(data["pertanyaan"]) if not data.empty else None


@app.route("/")
def home():
    return render_template("index.html")


# ---------- LOGIN ADMIN ----------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "admin" and password == "admin":
            session["admin"] = True
            return redirect("/admin/dashboard")
        else:
            return render_template("login.html", error="Username atau password salah")
    return render_template("login.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/admin")
    rows = load_faqs().to_dict(orient="records")
    return render_template("admin.html", rows=rows)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin")


# ---------- API TAMBAH FAQ ----------
@app.route("/add_faq", methods=["POST"])
def add_faq():
    pertanyaan = request.form.get("pertanyaan")
    jawaban = request.form.get("jawaban")
    kategori = request.form.get("kategori")
    semester = request.form.get("semester")
    sumber = request.form.get("sumber")

    df = load_faqs()
    new_id = len(df) + 1
    new_row = pd.DataFrame([{
        "id": new_id,
        "pertanyaan": pertanyaan,
        "jawaban": jawaban,
        "kategori": kategori,
        "semester_berlaku": semester,
        "sumber": sumber
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_faqs(df)

    global data, vectorizer, X
    data = df
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(data["pertanyaan"])

    return jsonify({"status": "success", "message": "FAQ berhasil ditambahkan!"})


# ---------- API CHATBOT ----------
@app.route("/get", methods=["POST"])
def get_bot_response():
    data_json = request.get_json()
    user_msg = data_json.get("msg", "")

    if not user_msg.strip() or X is None:
        return jsonify({"response": "Maaf, saya tidak punya data untuk menjawab."})

    user_vec = vectorizer.transform([user_msg])
    similarity = cosine_similarity(user_vec, X)

    idx = similarity.argmax()
    score = similarity[0][idx]

    if score < 0.3:
        reply = "Maaf, saya belum punya jawaban pasti. Silakan hubungi admin akademik."
    else:
        row = data.iloc[idx]
        reply = f"{row['jawaban']} \n\n📌 Kategori: {row['kategori']} | Semester: {row['semester_berlaku']} | Sumber: {row['sumber']}"

    return jsonify({"response": reply})


if __name__ == "__main__":
    app.run(debug=True, port=8000)
