import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings

# ẩn cảnh báo không quan trọng
warnings.filterwarnings("ignore", category=FutureWarning)

# 1. Đọc file gốc
load_df = pd.read_excel(
    "./data/data_se334/train_nor_811.xlsx",
    engine='openpyxl'
)
print("Số lượng câu gốc:", len(load_df))
print("Các cột trong DataFrame:", load_df.columns)

# 2. Đổi tên cột
load_df = load_df.rename(columns={
    "Unnamed: 0": "sentenceId",
    "Sentence": "sentence"
})

# 3. Chỉ giữ các cột cần thiết
df = load_df[["sentenceId", "sentence"]]

# 4. Tạo ngẫu nhiên sentence_time trong 1 năm trở lại
today = datetime.now()
one_year_ago = today - timedelta(days=4*365)

# random timestamp trong khoảng [one_year_ago, today]
random_timestamps = np.random.uniform(
    one_year_ago.timestamp(),
    today.timestamp(),
    size=len(df)
)

# convert thành Series dạng datetime ISO 8601
df["sentence_time"] = pd.to_datetime(random_timestamps, unit="s").strftime("%Y-%m-%d %H:%M:%S")

# 5. Trộn ngẫu nhiên
df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)

# 6. Chia thành 5 phần gần bằng nhau
split_dfs = np.array_split(df_shuffled, 5)

# 7. Ghi từng phần ra file CSV, và reset sentenceId
for i, split_df in enumerate(split_dfs, start=1):
    split_df = split_df.reset_index(drop=True)
    split_df["sentenceId"] = range(1, len(split_df) + 1)
    split_df.to_csv(f"./data/data_vn/vn_part_{i}.csv", index=False)

print("✅ Hoàn thành chia file vn.")
