from flask import Flask
from .connect_db import db
from sqlalchemy.exc import OperationalError
from .config import Config
from flask import request
from .service import handle_predict_and_save, handle_statistic, handle_start_and_end_time, handle_get_list_files, handle_delete_files
from flask_cors import CORS
def create_app():
    app = Flask(__name__)
    CORS(app, origins=["http://localhost:5173"], supports_credentials=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = Config.DB_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    try:
        db.init_app(app)
        print("✅ Database connected successfully.")

        with app.app_context():
            db.create_all()
            print("✅ Tables created.")
    except OperationalError as e:
        print("❌ Failed to connect to the database:")
        print(e)

    @app.route("/api/predict-and-save", methods=["POST"])
    def predict_and_save():
      return handle_predict_and_save()
    
    @app.route("/api/get-files", methods=["GET"])
    def get_list_file():
        return handle_get_list_files()
    
    @app.route("/api/statistic", methods=["POST"])
    def statistic():
        return handle_statistic()

    @app.route("/api/start-end-time", methods=["POST"])
    def select_start_and_end_time():
        return handle_start_and_end_time()
    
    @app.route("/api/delete-list-file", methods=["DELETE"])
    def delete_list_file():
        return handle_delete_files()
    return app
