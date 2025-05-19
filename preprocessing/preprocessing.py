import pandas as pd
import numpy as np

load_df = pd.read_csv("./data/sentimentdataset.csv")

load_df = load_df.rename(columns={"Unnamed: 0": "sentenceId", "Text": "sentence", "Timestamp": "sentence_time"})

df = load_df[["sentenceId", "sentence", "sentence_time"]]

# Trộn ngẫu nhiên dữ liệu
df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)

# Chia thành 5 phần gần bằng nhau
split_dfs = np.array_split(df_shuffled, 5)

# Ghi từng phần vào file, và reset sentenceId cho mỗi file
for i, split_df in enumerate(split_dfs, start=1):
    split_df = split_df.reset_index(drop=True)
    split_df["sentenceId"] = range(1, len(split_df) + 1)
    split_df.to_csv(f"./data/sentiment_part_{i}.csv", index=False)

