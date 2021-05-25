from flask import Flask, request, jsonify, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_heroku import Heroku
import io
from base64 import b64encode

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://tzbiujkeqzptcp:aa63a41e6b75d21e9eebb9af79fbf454cc03364f09af7b4b59b97b1e520e0cec@ec2-3-215-83-17.compute-1.amazonaws.com:5432/d4anqt3d492ci1"

db = SQLAlchemy(app)
ma = Marshmallow(app)

heroku = Heroku(app)
CORS(app)


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.LargeBinary, nullable=False)
    name = db.Column(db.String(), nullable=False)
    file_type = db.Column(db.String(), nullable=False)
    file_data = db.relationship("FileData", cascade="all,delete", backref="file", lazy=True)

    def __init__(self, data, name, file_type):
        self.data = data
        self.name = name
        self.file_type = file_type

class FileData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    file_type = db.Column(db.String(), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)

    def __init__(self, name, file_type, file_id):
        self.name = name
        self.file_type = file_type
        self.file_id = file_id

class FileSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "file_type", "file_id")

file_schema = FileSchema()
files_schema = FileSchema(many=True)


@app.route("/file/add", methods=["POST"])
def add_file():
    data = request.files.get("data")
    name = request.form.get("name")
    file_type = request.form.get("type")

    new_file = File(data.read(), name, file_type)
    db.session.add(new_file)
    db.session.commit()

    file_data = FileData(name, file_type, new_file.id)
    db.session.add(file_data)
    db.session.commit()

    return jsonify("Data added")

@app.route("/file/get/<id>", methods=["GET"])
def get_file(id):
    returned_file = db.session.query(File).filter(File.id == id).first()
    return send_file(io.BytesIO(returned_file.data), 
                    attachment_filename=returned_file.name,
                    mimetype=returned_file.file_type)

@app.route("/file/delete/<id>", methods=["DELETE"])
def delete_file(id):
    returned_file = db.session.query(File).filter(File.id == id).first()
    db.session.delete(returned_file)
    db.session.commit()
    return jsonify("Data deleted")

@app.route("/filedata/get", methods=["GET"])
def get_file_data():
    all_file_data = db.session.query(FileData).all()
    return jsonify(files_schema.dump(all_file_data))

if __name__ == "__main__":
    app.run(debug=True)