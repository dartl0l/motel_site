# -*- coding: utf-8 -*-

from shutil import rmtree
from os import listdir, makedirs
from os.path import join, dirname, realpath, isfile, exists
from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, UserMixin, login_required, \
    login_user, current_user, logout_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from base64 import b64encode
import motel_db as mdb
import uuid


UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'static/img/upload/')
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'bmp'])

app = Flask(__name__, static_url_path='/static')
app.config['APPLICATION_ROOT'] = '/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'shikaka'

login_manager = LoginManager()
login_manager.init_app(app)

users = {"admin": {"pw_hash": generate_password_hash("motel-admin")}}


class User(UserMixin):
    pass


@login_manager.user_loader
def user_loader(username):
    if username not in users:
        return

    user = User()
    user.id = username
    return user


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    if username not in users:
        return

    user = User()
    user.id = username
    user.is_authenticated = check_password_hash(users[username]['pw_hash'],
                                                request.form['pw'])

    return user


@app.route('/logout')
def logout():
    logout_user()
    return redirect("/admin")


@login_manager.unauthorized_handler
def unauthorized_handler():
    # return 'Unauthorized'
    return render_template("admin.html")


@app.route("/")
def main():
    events_db = mdb.Events.query.all()
    last_event = {}
    if len(events_db) != 0:
        last_event["image"] = b64encode(events_db[-1].image)
    return render_template("index.html", last_event=last_event)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/press")
def press():
    return render_template("press.html")


@app.route("/music")
def music():
    return render_template("music.html")


@app.route("/contact")
def contacts():
    return render_template("contact.html")


@app.route("/admin", methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        if username not in users:
            return redirect("admin")
        if check_password_hash(users[username]['pw_hash'],
                               request.form['pw']):
            user = User()
            user.id = username
            login_user(user)
            return redirect("list_events")
    if current_user.is_authenticated:
        return redirect("list_events")
    return render_template("admin.html")


@app.route("/delete_event", methods=['GET', 'POST'])
@login_required
def delete_event():
    if request.method == 'POST':
        for key in request.form:
            if key.startswith('to_delete'):
                value = request.form[key]
                event_id = int(value)
                event = mdb.Events.query.get(event_id)
                mdb.db.session.delete(event)
                mdb.db.session.commit()
    return redirect("/events")


@app.route("/list_events")
@login_required
def list_events():
    events_db = mdb.Events.query.all()
    list_events = []
    for i, event in enumerate(events_db, 1):
        list_events.append({
                            "id": event.id,
                            "name": event.name,
                            "description": event.description,
                            "date": event.date,
                            })
    return render_template("list_events.html", events=list_events)


# @app.route("/events")
# def events():
#     events_db = mdb.Events.query.all()
#     list_events = []
#     for i, event in enumerate(events_db, 1):
#         list_events.append({
#                             "id": event.id,
#                             "name": event.name,
#                             "description": event.description,
#                             "date": event.date,
#                             "image_url": event.image_name,
#                             "image": b64encode(event.image)
#                             })
#     return render_template("events.html", events=list_events)


@app.route("/events")
def events():
    return render_template("insta.html",)


@app.route("/new_event", methods=['GET', 'POST'])
@login_required
def new_event():
    if request.method == 'POST':
        new_event = mdb.Events()
        new_event.name = request.form['event_name']
        new_event.date = datetime.strptime(str(request.form['event_date']),
                                           '%Y-%m-%d')
        new_event.description = request.form['event_description']
        new_event.image_name = request.files['event_image'].filename
        new_event.image = request.files['event_image'].read()

        mdb.db.session.add(new_event)
        mdb.db.session.commit()
        print "saved"

        return redirect("/events")
    else:
        return render_template("new_event.html")


@app.route("/delete_album", methods=['GET', 'POST'])
@login_required
def delete_album():
    if request.method == 'POST':
        for key in request.form:
            if key.startswith('to_delete'):
                value = request.form[key]
                album_id = int(value)
                album = mdb.Albums.query.get(album_id)
                rmtree(join(app.config['UPLOAD_FOLDER'],
                            album.folder_uuid))
                mdb.db.session.delete(album)
                mdb.db.session.commit()
    return redirect("/gallery")


@app.route("/list_albums")
@login_required
def list_albums():
    albums_db = mdb.Albums.query.all()
    list_albums = []
    for i, album in enumerate(albums_db, 1):
        list_albums.append({
                            "id": album.id,
                            "name": album.name,
                            })
    return render_template("list_albums.html", albums=list_albums)


@app.route("/new_album", methods=['GET', 'POST'])
@login_required
def new_album():
    if request.method == 'POST':
        new_album = mdb.Albums()
        new_album.name = request.form['album_name']
        new_album.cover = request.files['album_cover'].read()
        new_album.folder_uuid = str(uuid.uuid4())

        album_path = join(join(app.config['UPLOAD_FOLDER'],
                          new_album.folder_uuid))
        print album_path
        if not exists(album_path):
            makedirs(album_path)

        for media_file in request.files.getlist('album_data'):
            save_image(media_file, album_path)

        mdb.db.session.add(new_album)
        mdb.db.session.commit()

        return redirect("/gallery")
    else:
        return render_template("new_album.html")


@app.route("/gallery")
@app.route("/gallery-<folder>")
def gallery(folder=""):
    if folder == "":
        print "1"
        albums_db = mdb.Albums.query.all()
        list_albums = []
        for i, album in enumerate(albums_db, 1):
            list_albums.append({
                                "id": album.id,
                                "name": album.name,
                                "cover": b64encode(album.cover),
                                "folder_uuid": album.folder_uuid
                                })
        print list_albums
        return render_template("gallery.html", albums=list_albums)
    else:
        path = join(app.config['UPLOAD_FOLDER'], folder)
        list_photos = [join("static/img/upload/" + folder, file)
                       for file in listdir(path)
                       if isfile(join(path, file))]
        return render_template("album.html", album=list_photos)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def save_image(image, path=app.config['UPLOAD_FOLDER']):
    # image = request.files['event_image']
    print image
    print type(image)
    # uuid.uuid4()
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image.save(join(path, filename))


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
