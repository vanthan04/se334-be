from flask import request
from flask import request, jsonify
from werkzeug.utils import secure_Filesname
import os 
import pandas as pd
from .connect_db import db
from datetime import datetime
from .entities import Sentences, Files
from ..ai.predict import handle_predict
from sqlalchemy import select, func, and_


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
    if 'Files' not in request.Files:
        return jsonify({"message": "Không tìm thấy Files."}), 400

    Files = request.Files['Files']
    if Files.Filesname == '':
        return jsonify({"message": "Tên Files trống."}), 400

    Filesname = secure_Filesname(Files.Filesname)
    Files_ext = os.path.splitext(Filesname)[1].lower()

    try:
        # 1. Lưu tên Files vào bảng Files
        new_Files = Files(FilesName=Filesname)
        db.session.add(new_Files)
        db.session.flush()
        Files_id = new_Files.FilesId

        # 2. Đọc trực tiếp từ Files trong bộ nhớ (không lưu ra ổ đĩa)
        if Files_ext == ".csv":
            df = pd.read_csv(Files)
        elif Files_ext in [".xls", ".xlsx"]:
            df = pd.read_excel(Files)
        else:
            raise ValueError("Định dạng Files không được hỗ trợ.")

        if df.empty:
            raise ValueError("Files không có nội dung.")
        
        data_handle = handle_predict(df)

        # 3. Lưu từng dòng vào bảng Sentences
        for row in data_handle:
            SentencesId = row.get("textId")
            Sentences = row.get("Sentences")
            predict = row.get("sentiment")
            Sentences_time = row.get("Sentences_time")
            #  Thực hiện dự đoán ở đây
   
            if SentencesId is not None and Sentences and Sentences_time and predict:
               new_Sentences = Sentences(
                     FilesId=Files_id,
                     SentencesId=SentencesId,
                     Sentences=Sentences,
                     predict=predict,
                     Sentences_time=Sentences_time
               )
               db.session.add(new_Sentences)

        db.session.commit()
        return jsonify({"message": "Lưu và xử lý thành công!"}), 200

    except Exception as e:
        db.session.rollback()
        print("Lỗi xử lý:", str(e))
        return jsonify({"message": "Lỗi xử lý Files.", "error": str(e)}), 500


def handle_statistic():
    data = request.get_json()
    print(data)

    start_time_str = data.get("startTime")
    end_time_str = data.get("endTime")
    type_statistic = data.get("typeStatistic", "alltime")
    selected_file_names = data.get("selectedFilesNames", [])

    try:
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d")
        end_time = datetime.strptime(end_time_str, "%Y-%m-%d")
    except Exception:
        return jsonify({"error": "Invalid date format"}), 400

    # ================================
    # THỐNG KÊ THEO NGÀY
    # ================================
    if type_statistic == "day":
        query = db.session.query(
            func.date(Sentences.sentence_time).label("period"),
            Sentences.predict,
            func.count(Sentences.sentenceId).label("count")
        ).join(Files, Sentences.fileId == Files.fileId)

        query = query.filter(
            Sentences.sentence_time >= start_time,
            Sentences.sentence_time <= end_time
        )

        if selected_file_names:
            query = query.filter(Files.fileName.in_(selected_file_names))

        query = query.group_by(func.date(Sentences.sentence_time), Sentences.predict)
        results = query.all()

        stats = {}
        for period, label, count in results:
            date_str = period.strftime("%Y-%m-%d")
            if date_str not in stats:
                stats[date_str] = {"pos": 0, "neg": 0, "neu": 0}
            stats[date_str][label] = count

    # ================================
    # THỐNG KÊ THEO THÁNG
    # ================================
    elif type_statistic == "month":
        query = db.session.query(
            func.date_trunc('month', Sentences.sentence_time).label("period"),
            Sentences.predict,
            func.count(Sentences.sentenceId).label("count")
        ).join(Files, Sentences.fileId == Files.fileId)

        query = query.filter(
            Sentences.sentence_time >= start_time,
            Sentences.sentence_time <= end_time
        )

        if selected_file_names:
            query = query.filter(Files.fileName.in_(selected_file_names))

        query = query.group_by(func.date_trunc('month', Sentences.sentence_time), Sentences.predict)
        results = query.all()

        stats = {}
        for period, label, count in results:
            month_str = period.strftime("%Y-%m")
            if month_str not in stats:
                stats[month_str] = {"pos": 0, "neg": 0, "neu": 0}
            stats[month_str][label] = count

    # ================================
    # TỔNG HỢP THEO FILE + LABEL
    # ================================
    else:
        query = db.session.query(
            Sentences.fileId,
            Files.fileName.label("file_name"),
            Sentences.predict,
            func.count(Sentences.sentenceId).label("count")
        ).join(Files, Sentences.fileId == Files.fileId)

        query = query.filter(
            Sentences.sentence_time >= start_time,
            Sentences.sentence_time <= end_time
        )

        if selected_file_names:
            query = query.filter(Files.fileName.in_(selected_file_names))

        query = query.group_by(Sentences.fileId, Files.fileName, Sentences.predict)
        results = query.all()

        stats = {}
        for file_id, file_name, label, count in results:
            if file_name not in stats:
                stats[file_name] = {"pos": 0, "neg": 0, "neu": 0}
            stats[file_name][label] = count

    return jsonify(stats)




def handle_start_and_end_time():
    try:
        listFiles = request.get_json()
        if not listFiles or not isinstance(listFiles, list):
            return jsonify({"message": "Dữ liệu gửi lên không hợp lệ."}), 400
        
        stmt = select(
            func.min(Sentences.Sentences_time).label("start_time"),
            func.max(Sentences.Sentences_time).label("end_time")
        ).where(Sentences.FilesId.in_(listFiles))

        result = db.session.execute(stmt).first()

        if result.start_time is None or result.end_time is None:
            return jsonify({"message": "Không có dữ liệu thời gian."}), 404

        return jsonify({
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat()
        })

    except Exception as e:
        print("Lỗi khi xử lý:", e)
        return jsonify({"message": "Lỗi server", "error": str(e)}), 500



def handle_delete_files():
    data = request.get_json()
    file_ids = data.get("selectedFilesNames", [])  # Ví dụ: [1, 2, 3]

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