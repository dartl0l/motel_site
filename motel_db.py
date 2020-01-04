# -*- coding: utf-8 -*-

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/motel.db'
db = SQLAlchemy(app)


class Events(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    date = db.Column(db.DateTime)
    image_name = db.Column(db.String)
    image = db.Column(db.LargeBinary)

    def __init__(self, name="", description="", date=""):
        self.name = name
        self.description = description
        self.date = date


class Albums(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    cover = db.Column(db.LargeBinary)
    folder_uuid = db.Column(db.String)
    # album_photos =

    def __init__(self, album_name="", album_cover=""):
        self.album_name = album_name
        self.album_cover = album_cover


class Music(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    cover = db.Column(db.LargeBinary)
    folder_uuid = db.Column(db.String)
    # album_photos =

    def __init__(self, album_name="", album_cover=""):
        self.album_name = album_name
        self.album_cover = album_cover


if __name__ == '__main__':
    db.drop_all()
    db.create_all()

    db.session.commit()
    print "good"
