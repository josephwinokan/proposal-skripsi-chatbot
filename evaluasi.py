import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import precision_score, recall_score, f1_score

# Load dataset FAQ
faq = pd.read_csv("faq_augmented.csv")

# Load data uji
test = pd.read_csv("data_uji.csv")

# Bersihkan data
faq["pertanyaan"] = faq["pertanyaan"].fillna("")
test["pertanyaan"] = test["pertanyaan"].fillna("")

# TF-IDF
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(faq["pertanyaan"])

y_true = []
y_pred = []

for i, row in test.iterrows():
    user_q = row["pertanyaan"]
    true_ans = row["jawaban_benar"]

    # Transform pertanyaan user
    user_vec = vectorizer.transform([user_q])

    # Hitung similarity
    sim = cosine_similarity(user_vec, X)

    idx = sim.argmax()
    pred_ans = faq.iloc[idx]["jawaban"]

    # Label benar / salah
    if pred_ans.strip() == true_ans.strip():
        y_pred.append(1)
    else:
        y_pred.append(0)

    y_true.append(1)  # semua pertanyaan punya jawaban benar

# Hitung metrik
precision = precision_score(y_true, y_pred)
recall = recall_score(y_true, y_pred)
f1 = f1_score(y_true, y_pred)

print("=== HASIL EVALUASI ===")
print("Precision:", precision)
print("Recall:", recall)
print("F1-score:", f1)