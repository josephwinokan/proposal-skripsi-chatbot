import pandas as pd

df1 = pd.read_csv("faq.csv")
df2 = pd.read_csv("faq_augmented.csv")
df3 = pd.read_csv("faq_clean.csv")

df = pd.concat([df1, df2, df3], ignore_index=True)

df.drop_duplicates(subset=["pertanyaan"], inplace=True)

df.to_csv("faq_final.csv", index=False)

print("✅ Data digabung")
print("Total:", len(df))