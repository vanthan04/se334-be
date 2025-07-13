# SE334-BE

Đây là backend của dự án SE334 sử dụng Flask.

## Yêu cầu

- Python 3.x
- pip

## Cài đặt

1. Tạo môi trường ảo (venv):
   ```
   python -m venv venv
   ```
2. Kích hoạt môi trường ảo:
   - Trên Windows:
     ```
     venv\Scripts\activate
     ```
   - Trên macOS/Linux:
     ```
     source venv/bin/activate
     ```
3. Cài đặt các thư viện cần thiết:
   ```
   pip install -r requirements.txt
   ```

4. Thiết lập biến môi trường (nếu cần):
   ```
   set FLASK_APP=app.py
   set FLASK_ENV=development
   set DB_URI=postgresql://postgres:1234@localhost:5432/sa_system

   BASE_URL=https://cfcb-104-155-217-159.ngrok-free.app // Lấy từ kaggle hoặc local
   ```

## Chạy ứng dụng

```
flask run
```

Ứng dụng sẽ chạy tại `http://127.0.0.1:5000/` theo mặc định.

## Cấu trúc thư mục

- `app.py`: File chính chạy Flask app.
- `requirements.txt`: Danh sách các thư viện cần thiết.
- `...`: Các file và thư mục khác của dự án.
