import os
import requests

from flask import Flask, flash, redirect, render_template, request, session, abort

from packages.function import LoggedIn, CheckLoginDetails, upload_handler, process_raw_files


APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/tmp')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# TODO: make a dev and production config, dont use secret_key in prob.
app.secret_key = os.urandom(12)

API = 'http://127.0.0.1:5050/glance/api'
API_ASSET = 'http://127.0.0.1:5050/glance/api/asset'

@app.route('/')
def home():
    if LoggedIn(session):
        r = requests.get('{}'.format(API_ASSET))

        return render_template('home.html', items=r.json())
    else:
        return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        form = request.form

        data = {
            'username': form['username'],
            'password': form['password']
        }

        if CheckLoginDetails(**data):
            session['logged_in'] = True
            session['user'] = data['username']
        else:
            # TODO: Something here?
            pass

    return home()


@app.route("/logout")
def logout():
    session['logged_in'] = False

    return home()


@app.route('/upload')
def upload():
    if LoggedIn(session):
        return render_template('upload.html')
    else:
        return home()


@app.route('/uploading', methods=['POST'])
def uploading():
    if LoggedIn(session):
        if request.method == 'POST':
            # Init dict and append user data
            upload_data = {}

            for form_input in request.form:
                upload_data[form_input] = request.form[form_input]

            # process all uploaded files.
            processed_files = process_raw_files(request.files.getlist('file'))

            # build payload for api
            for items in processed_files:
                payload = {}
                payload['name'] = items
                payload['author'] = session['user']
                payload['tag'] = upload_data['tag']
                payload['collection'] = upload_data['collection']

                for item in processed_files[items]:
                    if item.filename.endswith('.jpg'):
                        uploaded_file = upload_handler(item, app.config['UPLOAD_FOLDER'])

                        payload['image'] = uploaded_file
                        payload['image_thumb'] = uploaded_file
                    else:
                        uploaded_file = upload_handler(item, app.config['UPLOAD_FOLDER'])
                        payload['attached'] = uploaded_file

                # post payload to api
                r = requests.post('{}'.format(API_ASSET), params=payload)

            return render_template('uploadcomplete.html')
    else:
        return home()


@app.route('/item/<id>')
def item(id):

    r = requests.get('{}/{}'.format(API_ASSET, id))

    return render_template('item.html', item=r.json())


@app.route('/search')
def search():
    search_data = {}
    search_term = request.args['search']
    search_data['search_term'] = str(search_term)

    return render_template('search.html', data=search_data)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)