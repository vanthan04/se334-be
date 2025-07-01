from flask import request
from flask import request, jsonify
from werkzeug.utils import secure_filename
import os 
import pandas as pd
from .connect_db import db
from datetime import datetime
from .entities import Sentences, Files
from sqlalchemy import select, func
import asyncio
from api.call_api import async_predict, sync_predict

def handle_get_list_files():
    try:
        stmt = select(Files)
        result = db.session.execute(stmt)
        listFiles = result.scalars().all()
        return jsonify({"dataResponse": [f.to_dict() for f in listFiles]}), 200
    except Exception as e:
        print("Lỗi:", e)
        return jsonify({"message": "Lấy danh sách Files thất bại"}), 400



def handle_predict_and_save():
    if 'file' not in request.files:
        return jsonify({"message": "Không tìm thấy file."}), 400

    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return jsonify({"message": "Tên file trống."}), 400

    fileName = secure_filename(uploaded_file.filename)
    file_ext = os.path.splitext(fileName)[1].lower()

    try:
        # 1. Lưu metadata file
        new_file = Files(fileName=fileName)
        db.session.add(new_file)
        db.session.flush()
        file_id = new_file.fileId

        # 2. Đọc file
        if file_ext == ".csv":
            df = pd.read_csv(uploaded_file)
        elif file_ext in [".xls", ".xlsx"]:
            df = pd.read_excel(uploaded_file)
        else:
            raise ValueError("Định dạng file không hỗ trợ.")

        if df.empty:
            raise ValueError("File không có nội dung.")

        # kiểm tra cột sentence
        if "sentence" not in df.columns:
            raise ValueError("File thiếu cột 'sentence'.")

        sentences = df["sentence"].tolist()
        if len(sentences) == 0:
            db.session.rollback()
            print("Lỗi xử lý:", str(e))
            return jsonify({"message": "Lỗi xử lý file.", "error": str(e)}), 500

        
        # 3. Gọi async_predict
        predictions = asyncio.run(async_predict(sentences))
         #3.1. Gọi API để dự đoán
      #   predictions = sync_predict(sentences)  # Sử dụng hàm đồng bộ nếu không cần async

        # 4. Ghi dữ liệu Sentences tuần tự
        for idx, pred in enumerate(predictions):
            sentence_text = sentences[idx]
            sentence_id = idx + 1
            predict_label = pred.get("label")
            sentence_time = df["sentence_time"][idx] if "sentence_time" in df.columns else None

            if isinstance(sentence_time, str):
                sentence_time = datetime.strptime(sentence_time, "%Y-%m-%d %H:%M:%S")

            new_sentence = Sentences(
                fileId=file_id,
                sentenceId=sentence_id,
                sentence=sentence_text,
                label=predict_label,
                sentence_time=sentence_time if sentence_time else datetime.now()
            )
            db.session.add(new_sentence)

        db.session.commit()

        return jsonify({
            "message": "Lưu và xử lý thành công!",
            "fileId": file_id,
            "fileName": fileName
        }), 200

    except Exception as e:
        db.session.rollback()
        print("Lỗi xử lý:", str(e))
        return jsonify({"message": "Lỗi xử lý file.", "error": str(e)}), 500


def handle_statistic():
    data = request.get_json()

    start_time_str = data.get("startTime")
    end_time_str = data.get("endTime")
    type_statistic = data.get("typeStatistic", "alltime")
    selected_file_names = data.get("selectedFileNames", [])

    try:
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return jsonify({"error": "Invalid date format"}), 400

    valid_labels = ["positive", "negative", "neutral"]
    stats_by_time = {}

    # ========================
    # THỐNG KÊ THEO THỜI GIAN
    # ========================
    if type_statistic in ["day", "month", "year"]:
        if type_statistic == "day":
            time_label = func.date(Sentences.sentence_time)
        elif type_statistic == "month":
            time_label = func.date_trunc('month', Sentences.sentence_time)
        elif type_statistic == "year":
            time_label = func.date_trunc('year', Sentences.sentence_time)

        query_time = db.session.query(
            time_label.label("period"),
            Sentences.label,
            func.count(Sentences.sentenceId).label("count")
        ).join(Files, Sentences.fileId == Files.fileId)

        query_time = query_time.filter(
            Sentences.sentence_time >= start_time,
            Sentences.sentence_time <= end_time,
        )

        if selected_file_names:
            query_time = query_time.filter(Files.fileId.in_(selected_file_names))
         
        query_time = query_time.group_by("period", Sentences.label).order_by("period")
        results_time = query_time.all()

        for period, label, count in results_time:
            if label not in valid_labels:
                continue

            if type_statistic == "day":
                period_str = period.strftime("%Y-%m-%d")
            elif type_statistic == "month":
                period_str = period.strftime("%Y-%m")
            elif type_statistic == "year":
                period_str = period.strftime("%Y")

            if period_str not in stats_by_time:
                stats_by_time[period_str] = {lbl: 0 for lbl in valid_labels}
            stats_by_time[period_str][label] = count

    # ========================
    # THỐNG KÊ THEO FILE
    # ========================
    query_file = db.session.query(
        Files.fileName.label("file_name"),
        Sentences.label,
        func.count(Sentences.sentenceId).label("count")
    ).join(Files, Sentences.fileId == Files.fileId)

    if selected_file_names:
        query_file = query_file.filter(Files.fileId.in_(selected_file_names))

    query_file = query_file.group_by(Files.fileName, Sentences.label)
    results_file = query_file.all()

    stats_by_file = {}
    for file_name, label, count in results_file:
        if label not in valid_labels:
            continue
        if file_name not in stats_by_file:
            stats_by_file[file_name] = {lbl: 0 for lbl in valid_labels}
        stats_by_file[file_name][label] = count

    return jsonify({
        "stats_by_time": stats_by_time,
        "stats_by_file": stats_by_file
    })



def handle_start_and_end_time():
    try:
        # Lấy danh sách fileId từ request body
        list_files = request.get_json()

        # Validate đầu vào
        if not list_files or not isinstance(list_files, list) or not all(isinstance(f, int) for f in list_files):
            return jsonify({
                "message": "Dữ liệu gửi lên không hợp lệ. Vui lòng cung cấp danh sách các số nguyên fileId."
            }), 400

        # Truy vấn database để lấy thời gian sớm nhất và muộn nhất
        stmt = select(
            func.min(Sentences.sentence_time).label("start_time"),
            func.max(Sentences.sentence_time).label("end_time")
        ).where(Sentences.fileId.in_(list_files))

        result = db.session.execute(stmt).first()

        # Kiểm tra dữ liệu có tồn tại không
        if not result or not result.start_time or not result.end_time:
            return jsonify({
                "message": "Không tìm thấy dữ liệu thời gian cho các file đã chọn."
            }), 404

        # Trả về định dạng ISO 8601
        return jsonify({
            "start_time": result.start_time.isoformat(),  # ví dụ: "2025-05-18T14:30:00"
            "end_time": result.end_time.isoformat()
        }), 200

    except Exception as e:
        print("❌ Lỗi khi xử lý thời gian start/end:", str(e))
        return jsonify({
            "message": "Lỗi server.",
            "error": str(e)
        }), 500


def handle_delete_files():
    data = request.get_json()
    file_ids = data.get("selectedFilesNames", [])  

    if not file_ids or not isinstance(file_ids, list):
        return jsonify({"error": "fileIds must be a list of IDs"}), 400

    try:
        # Tìm các file tồn tại trong DB
        files_to_delete = Files.query.filter(Files.fileId.in_(file_ids)).all()

        if not files_to_delete:
            return jsonify({"message": "No matching files found"}), 404

        for file in files_to_delete:
            db.session.delete(file)  # Xóa file, sẽ cascade xóa Sentences

        db.session.commit()
        return jsonify({"message": f"Deleted {len(files_to_delete)} files"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500