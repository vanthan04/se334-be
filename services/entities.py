from .connect_db import db

class Files(db.Model):
    __tablename__ = "files"

    fileId = db.Column(db.Integer, primary_key=True)
    fileName = db.Column(db.Text, nullable=False)

    # Quan hệ 1-nhiều với Sentences
    sentences = db.relationship("Sentences", backref="file", cascade="all, delete", lazy=True)

    def to_dict(self):
         return {
            "fileId": self.fileId,
            "fileName": self.fileName,
         }
    

    def __repr__(self):
        return f"<File {self.fileId} {self.fileName}>"
    

class Sentences(db.Model):
    __tablename__ = "sentences"

    sentenceId = db.Column(db.Integer)
    fileId = db.Column(db.Integer, db.ForeignKey("files.fileId", ondelete="CASCADE"))
    sentence = db.Column(db.Text)
    sentence_time = db.Column(db.DateTime)
    label = db.Column(db.Text)

    __table_args__ = (
        db.PrimaryKeyConstraint("sentenceId", "fileId"),
    )

    def __repr__(self):
        return f"<Sentence {self.sentenceId} from File {self.fileId}>"

