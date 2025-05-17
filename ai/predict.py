import pandas as pd
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
import os
import re
import json
from .config import Config


# Định nghĩa prompt (bổ sung {output_format_instructions} để nhắc định dạng JSON)
template = """
Bạn là một AI phân tích cảm xúc.

Dưới đây là danh sách các câu, mỗi câu có một ID. Với mỗi câu, bạn cần:
1. Xác định cảm xúc: "positive", "negative" hoặc "neutral".

{{
  "textId": <textId của câu>,
  "sentence": <câu đầu vào>,
  "sentiment": "<positive|negative|neutral>"
}}

Danh sách câu:

{id_sentence_list}

Trả lời:
"""

prompt = PromptTemplate(
    input_variables=["id_sentence_list"],
    template=template
)

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=Config.api_key,
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

def handle_predict(df):
    all_results = []
    batch_size = 10
    total_rows = len(df)

    for i in range(0, total_rows, batch_size):
        batch_df = df.iloc[i:i+batch_size]
        rows = [f"{row['textId']}: {row['sentence']}" for _, row in batch_df.iterrows()]
        id_sentence_list = "\n".join(rows)

        filled_prompt = prompt.format(id_sentence_list=id_sentence_list)
        response = llm.invoke(filled_prompt)

        batch_result = extract_json_objects(response.content)

        for res in batch_result:
            matching_row = batch_df[batch_df['textId'] == int(res['textId'])]
            if not matching_row.empty:
                res['sentence_time'] = matching_row.iloc[0]['sentence_time']

        all_results.extend(batch_result)

    return all_results




def extract_json_objects(text):
    """
    Trích xuất các object JSON từ chuỗi chứa văn bản hỗn hợp (có cả mô tả, đánh số, ghi chú...).
    Trả về danh sách dict JSON.
    """
    # Regex tìm đoạn JSON bắt đầu bằng "textId"
    pattern = r"\{\s*\"textId\"\s*:\s*\d+.*?\}"
    matches = re.findall(pattern, text, re.DOTALL)

    parsed = []
    for match in matches:
        try:
            parsed.append(json.loads(match))
        except json.JSONDecodeError:
            continue
    return parsed

def predict_sentiment(list_sen):
    rows = [f"{item['textId']}: {item['sentence']}" for item in list_sen]
    id_sentence_list = "\n".join(rows)

    filled_prompt = prompt.format(id_sentence_list=id_sentence_list)
    response = llm.invoke(filled_prompt)
    return extract_json_objects(response.content)



# Test nhanh
if __name__ == "__main__":
    list_sen = [
        {"textId": 1, "sentence": "Tôi rất vui hôm nay."},
        {"textId": 2, "sentence": "Tôi cảm thấy mệt mỏi."},
        {"textId": 3, "sentence": "Thời tiết hôm nay bình thường."},
         {"textId": 4, "sentence": "Tôi không ổn."},

    ]

    result = predict_sentiment(list_sen)
    print(result)
