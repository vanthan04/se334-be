import json
import re
import pickle
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from .config import Config

# Prompt template cho Groq
template = """
Bạn là một AI phân tích cảm xúc.

Dưới đây là danh sách các câu, mỗi câu có một ID. Với mỗi câu, bạn cần:
1. Xác định cảm xúc: "positive", "negative" hoặc "neutral".

{{
  "sentenceId": <sentenceId của câu>,
  "sentence": <câu đầu vào>,
  "predict": "<positive|negative|neutral>"
}}

Danh sách câu:

{id_sentence_list}

Trả lời:
"""

prompt = PromptTemplate(
    input_variables=["id_sentence_list"],
    template=template
)

# Khởi tạo model
if Config.use_groq:
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=Config.api_key,
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )
else:
    with open("sentiment_model.pkl", "rb") as f:
        sentiment_model = pickle.load(f)

# Hàm gọi model
def get_model_response(id_sentence_list: str) -> str:
    filled_prompt = prompt.format(id_sentence_list=id_sentence_list)

    if Config.use_groq:
        response = llm.invoke(filled_prompt)
        return response.content
    else:
        # Parse lại câu theo định dạng "<id>: <sentence>"
        lines = id_sentence_list.strip().splitlines()
        ids, sentences = [], []

        for line in lines:
            match = re.match(r"(\d+):\s(.+)", line)
            if match:
                ids.append(int(match.group(1)))
                sentences.append(match.group(2))

        predictions = sentiment_model.predict(sentences)  # ['positive', 'negative', ...]

        results = []
        for i in range(len(predictions)):
            results.append({
                "sentenceId": ids[i],
                "sentence": sentences[i],
                "predict": predictions[i]
            })

        return json.dumps(results, ensure_ascii=False)
