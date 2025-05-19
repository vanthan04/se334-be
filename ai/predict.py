import json
import re
from ai.ai_model import get_model_response

def extract_json_objects(text):
    """
    Trích xuất tất cả các object JSON có chứa trường "textId" trong chuỗi text.
    """
    pattern = r"\{[^{}]*\"sentenceId\"[^{}]*\}"
    matches = re.findall(pattern, text, re.DOTALL)

    parsed = []
    for match in matches:
        try:
            parsed.append(json.loads(match))
        except json.JSONDecodeError:
            # Bỏ qua nếu không parse được
            continue
    return parsed

def predict_sentiment(list_sen):
    """
    Nhận đầu vào là list dict: [{"sentenceId": int, "sentence": str}, ...]
    Trả về list kết quả JSON phân tích cảm xúc.
    """
    # Chuyển danh sách câu thành chuỗi định dạng <id>: <sentence>
    rows = [f"{item['sentenceId']}: {item['sentence']}" for item in list_sen]
    id_sentence_list = "\n".join(rows)

    try:
        response_text = get_model_response(id_sentence_list)
    except Exception as e:
        print(f"Error calling model: {e}")
        return []

    return extract_json_objects(response_text)


def handle_predict(df):
    """
    Nhận DataFrame có ít nhất 3 cột: 'sentenceId', 'sentence', 'sentence_time'
    Trả về list kết quả phân tích cảm xúc, giữ nguyên 'sentence_time' cho từng câu.
    Xử lý theo batch để giảm tải.
    """
    all_results = []
    batch_size = 10
    total_rows = len(df)

    for i in range(0, total_rows, batch_size):
        batch_df = df.iloc[i:i+batch_size]
        rows = [f"{row['sentenceId']}: {row['sentence']}" for _, row in batch_df.iterrows()]
        id_sentence_list = "\n".join(rows)

        try:
            response_text = get_model_response(id_sentence_list)
        except Exception as e:
            print(f"Error calling model in batch {i}-{i+batch_size}: {e}")
            continue

        batch_result = extract_json_objects(response_text)

        for res in batch_result:
            try:
                matching_row = batch_df[batch_df['sentenceId'] == int(res['sentenceId'])]
                if not matching_row.empty and 'sentence_time' in matching_row.columns:
                    res['sentence_time'] = matching_row.iloc[0]['sentence_time']
            except Exception:
                # Nếu lỗi gì thì bỏ qua
                continue

        all_results.extend(batch_result)

    return all_results


if __name__ == "__main__":
    # Test nhanh với ví dụ câu
    list_sen = [
        {"sentenceId": 1, "sentence": "Tôi rất vui hôm nay."},
        {"sentenceId": 2, "sentence": "Tôi cảm thấy mệt mỏi."},
        {"sentenceId": 3, "sentence": "Thời tiết hôm nay bình thường."},
        {"sentenceId": 4, "sentence": "Tôi không ổn."},
    ]

    result = predict_sentiment(list_sen)
    print(json.dumps(result, indent=2, ensure_ascii=False))
