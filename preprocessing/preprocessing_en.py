import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings

# ẩn cảnh báo không quan trọng
warnings.filterwarnings("ignore", category=FutureWarning)

# 1. Đọc file gốc
load_df = pd.read_csv("./data/data_se334/sentimentdataset.csv")

# 2. Đổi tên cột
load_df = load_df.rename(columns={
    "Unnamed: 0": "sentenceId",
    "Text": "sentence",
    "Timestamp": "sentence_time"
})

# 3. Chỉ giữ cột cần
df = load_df[["sentenceId", "sentence"]]

# 4. Tạo random datetime trong 5 năm trở lại
today = datetime.now()
five_years_ago = today - timedelta(days=5*365)

random_timestamps = np.random.uniform(
    five_years_ago.timestamp(),
    today.timestamp(),
    size=len(df)
)

# gán lại vào cột sentence_time
df["sentence_time"] = pd.to_datetime(random_timestamps, unit="s").strftime("%Y-%m-%d %H:%M:%S")

# 5. Trộn ngẫu nhiên
df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)

# 6. Chia 5 phần gần bằng nhau
split_dfs = np.array_split(df_shuffled, 2)

# 7. Ghi file
for i, split_df in enumerate(split_dfs, start=1):
    split_df = split_df.reset_index(drop=True)
    split_df["sentenceId"] = range(1, len(split_df)+1)
    split_df.to_csv(f"./data/data_en/en_part_{i}.csv", index=False)

print("✅ Hoàn thành chia file en.")
