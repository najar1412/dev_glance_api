f"""
glance web app
"""

__author__ = ""
__version__ = "0.1"
__license__ = "./LICENSE"

import os
import subprocess

import requests
from flask import Flask, render_template, request, session, jsonify

import glance.modules.auth as auth
import glance.modules.file as file
import glance.modules.image as image

from config import settings


'''Flask Config'''
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = settings.tmp_upload
app.secret_key = settings.secret_key

'''API SHORTHAND'''
# TODO: Lazy?
API = settings.api_root
API_ITEM = '{}item'.format(settings.api_root)
API_COLLECTION = '{}collection'.format(settings.api_root)
API_USER = '{}user'.format(settings.api_root)

'''Routes'''
# auth
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form = request.form

        data = {
            'username': form['username'],
            'password': form['password']
        }

        if auth.check_login_details(**data):
            auth.SessionHandler(session).open(form['username'])

        else:
            auth.SessionHandler(session).close()

    elif request.method == 'GET':
        return render_template('index.html')

    return home()


@app.route("/logout")
def logout():

    auth.SessionHandler(session).close()

    return home()


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        payload = {}
        for form_input in request.form:
            payload[form_input] = request.form[form_input]

        r = requests.post('{}'.format(API_USER), params=payload)

        return home()

    elif request.method == 'GET':
        return render_template('signup.html')


# utility
@app.route('/append_fav', methods=['GET','POST'])
def append_fav():

    item_id = request.args['item_id']
    item_thumb = request.args['item_thumb']

    auth.SessionHandler(session).fav(item_id, item_thumb)

    return jsonify(result=len(session['fav']))


@app.route('/uploading', methods=['POST'])
def uploading():
    #TODO:  refactor.
    if auth.logged_in(session):
        if request.method == 'POST':
            # Init dict and append user data
            upload_data = {}
            upload_data['items_for_collection'] = []
            items_for_collection = []

            for form_input in request.form:
                upload_data[form_input] = request.form[form_input]

            # process all uploaded files.
            processed_files = file.process_raw_files(request.files.getlist('file'))

            # process remaining item data
            if upload_data['itemradio'] == 'image':
                for items in processed_files:

                    for item in processed_files[items]:
                        if item.filename.endswith('.jpg'):
                            uploaded_file = file.upload_handler(item, app.config['UPLOAD_FOLDER'])
                            payload = {}
                            payload['name'] = items
                            payload['author'] = session['user']
                            payload['tags'] = upload_data['tags']
                            payload['item_type'] = upload_data['itemradio']
                            payload['item_loc'] = uploaded_file[0]
                            payload['item_thumb'] = uploaded_file[1]

                            # AWS REKOGNITION
                            for tag in image.generate_tags(uploaded_file[0]):
                                payload['tags'] +=  ' ' + tag.lower()

                        else:
                            uploaded_file = file.upload_handler(item, app.config['UPLOAD_FOLDER'])
                            payload['attached'] = uploaded_file

                    # post payload to api
                    r = requests.post('{}'.format(API_ITEM), params=payload)
                    # collect uploaded item ids from respoce object in a list
                    # incase its this also a collection...
                    # TODO: above comment makes no sence... can i check if its a
                    # collection at the beginning? does it matter? Its not dry.
                    # TODO: Make this a helper
                    res = r.json()

                    # append Item ids for Collection
                    for x in res:
                        item_id = res['POST: /item'][0]['id']
                        upload_data['items_for_collection'].append(item_id)

            elif upload_data['itemradio'] == 'footage':
                # build payload for api
                for items in processed_files:
                    payload['name'] = items

                    for item in processed_files[items]:
                        if item.filename.endswith('.mp4'):
                            uploaded_file = file.upload_handler(item, app.config['UPLOAD_FOLDER'])
                            item_thumb_filename, item_thumb_ext = os.path.splitext(uploaded_file[0])

                            payload = {}
                            payload['name'] = items
                            payload['author'] = session['user']
                            payload['tags'] = upload_data['tags']
                            payload['item_type'] = upload_data['itemradio']
                            payload['item_loc'] = uploaded_file[0]
                            payload['item_thumb'] = uploaded_file[1]

                            # AWS REKOGNITION
                            # TODO: currently running `generate_tags` on the
                            # thumbnail. Needs to be run on the extracted image.
                            for tag in image.generate_tags(uploaded_file[1]):
                                payload['tags'] +=  ' ' + tag.lower()


                        else:
                            # Use to validate wether item is a valid format
                            pass
                            """
                            uploaded_file = file.upload_handler(item, app.config['UPLOAD_FOLDER'])
                            payload['attached'] = uploaded_file
                            """

                    # post payload to api
                    r = requests.post('{}'.format(API_ITEM), params=payload)
                    payload['tags'] = ''

                    # append Item ids for Collection
                    res = r.json()
                    for x in res:
                        item_id = res['POST: /item'][0]['id']
                        upload_data['items_for_collection'].append(item_id)

            elif upload_data['itemradio'] == 'geometry':
                # build payload for api

                for items in processed_files:
                    # payload['name'] = items

                    for item in processed_files[items]:
                        if item.filename.endswith('.jpg'):
                            uploaded_file = file.upload_handler(item, app.config['UPLOAD_FOLDER'])

                            payload = {}
                            payload['name'] = items
                            payload['author'] = session['user']
                            payload['tags'] = upload_data['tags']
                            payload['item_type'] = upload_data['itemradio']
                            payload['item_loc'] = uploaded_file[0]
                            payload['item_thumb'] = uploaded_file[1]

                            # AWS REKOGNITION
                            for tag in image.generate_tags(uploaded_file[0]):
                                payload['tags'] +=  ' ' + tag.lower()

                        else:
                            uploaded_file = file.upload_handler(item, app.config['UPLOAD_FOLDER'])
                            payload['attached'] = uploaded_file

                    # post payload to api
                    r = requests.post('{}'.format(API_ITEM), params=payload)
                    # collect uploaded item ids from respoce object.
                    # payload['tags'] = ''
                    res = r.json()
                    # append Item ids for Collection
                    for x in res:
                        item_id = res['POST: /item'][0]['id']
                        upload_data['items_for_collection'].append(item_id)

            elif upload_data['itemradio'] == 'people':
                # build payload for api

                for items in processed_files:

                    for item in processed_files[items]:
                        if item.filename.endswith('.jpg'):
                            uploaded_file = file.upload_handler(item, app.config['UPLOAD_FOLDER'])

                            payload = {}
                            payload['name'] = items
                            payload['author'] = session['user']
                            payload['tags'] = upload_data['tags']
                            payload['item_type'] = upload_data['itemradio']
                            payload['item_loc'] = uploaded_file[0]
                            payload['item_thumb'] = uploaded_file[1]

                            # AWS REKOGNITION
                            for tag in image.generate_tags(uploaded_file[0]):
                                payload['tags'] +=  ' ' + tag.lower()

                        else:
                            uploaded_file = file.upload_handler(item, app.config['UPLOAD_FOLDER'])
                            payload['attached'] = uploaded_file

                    # post payload to api
                    r = requests.post('{}'.format(API_ITEM), params=payload)
                    # collect uploaded item ids from respoce object.
                    # TODO: Make this a helper
                    # append Item ids for Collection
                    res = r.json()
                    for x in res:
                        item_id = res['POST: /item'][0]['id']
                        upload_data['items_for_collection'].append(item_id)

            # Runs if collection has been requested aswell as the uploading of files.
            if 'collection' in upload_data:
                if upload_data['collection'] != '':

                    payload = {
                        'name': upload_data['collection'],
                        'item_type': 'collection',
                        'item_loc': 'site/default_cover.jpg',
                        'item_thumb': 'site/default_cover.jpg',
                        'tags': upload_data['tags'],
                        'items': ' '.join(upload_data['items_for_collection']),
                        'author': session['user']
                    }

                    r = requests.post('{}'.format(API_ITEM), params=payload)
                    # print()

                    # return home()
                    return render_template('collection.html', item=r.json()['POST: /item'])

            return render_template('uploadcomplete.html')
    else:
        return home()


@app.route('/patch', methods=['POST'])
def patch_item():

    data = {}
    if request.method == 'POST':
        form = request.form
        for k in form:
            print('JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ')
            print(k)
            if k == 'append_collection':
                data['items'] = form[k]

            elif k == 'append_tags':
                data['tags'] = form[k]

            elif k == 'change_cover':
                pass

            elif k == 'people_tags':

                tags = ' '.join(form.getlist('people_tags'))
                print('pppppppppppppppppppppp')
                print(tags)
                data['people_tags'] = tags

            else:
                data[k] = form[k]

    r = requests.patch('{}/patch'.format(API_ITEM), params=data)

    return home()


@app.route('/fav_to_collection', methods=['GET', 'POST'])
def fav_to_collection():
    if 'fav' in session:
        items = []
        for x in session['fav']:
            items.append(list(x.keys())[0])

    payload = {
        'name': "upload_data['collection']",
        'item_type': 'collection',
        'item_loc': 'site/default_cover.jpg',
        'item_thumb': 'site/default_cover.jpg',
        'tags': "upload_data['tags']",
        'items': ' '.join(items),
        'author': session['user']
    }

    r = requests.post('{}'.format(API_ITEM), params=payload)


    res = r.json()['POST: /item']
    for x in res:
        if x == 'responce':
            if res['responce'] == 'successful':
                collection_id = res['location'].split('/')[-1:][0]

                session['fav'] = []
                return item(collection_id)
        else:
            print('empty else')
            pass



    return home()


@app.route('/item/delete/<int:id>')
def delete(id):
    g = requests.get('{}/{}'.format(API_ITEM, id))
    resp = g.json()['item'][0]
    r = requests.delete('{}/delete/{}'.format(API_ITEM, id))
    data = []
    if 'item_loc' in resp:
        data.append(resp['item_loc'])
    if 'item_thumb' in resp:
        data.append(resp['item_thumb'])
    if 'attached' in resp:
        data.append(resp['attached'])

    # delete from s3 and database
    # TODO: IMP something safer.
    auth.delete_from_s3(data)
    r = requests.delete('{}/delete/{}'.format(API_ITEM, id))


    return home()


# display
@app.route('/')
def home():
    """Serves front page
    :return: dict. Each item tyoe.
    """
    print(session)
    # process and reverse data so the latest uploaded items are first.
    # Currently using the items `id`, but upload date would be better.
    reversed_list = []

    payload = {}
    payload['filter'] = 'all'
    auth.SessionHandler(session).filter(payload['filter'])

    g = requests.get('{}'.format(API_ITEM))
    res = g.json()

    if 'GET assets' in res and res['GET assets']['Message'] == 'No assets in database':
        return render_template('home.html')

    else:

        # latest ten collections
        collections = [x for x in res if x['item_type'] == 'collection'][0:9]

        # latest ten image
        images = [x for x in res if x['item_type'] == 'image'][0:9]

        # latest ten collections
        footage = [x for x in res if x['item_type'] == 'footage'][0:9]

        # latest ten people
        people = [x for x in res if x['item_type'] == 'people'][0:9]

        # latest ten geometry
        geometry = [x for x in res if x['item_type'] == 'geometry'][0:10]



        return render_template(
            'home.html', collections=collections, images=images, footage=footage,
            people=people, geometry=geometry
            )


@app.route('/favorite')
def favorite():
    # TODO: API needs to be able to serve, `item by author`.
    if auth.logged_in(session):
        # data to send... collections made by user
        r = requests.get(
            '{}collection/author/{}'.format(API, session['user'])
        )

        data = ['test', 'test2']

        return render_template('favorite.html', collection=r.json(), items=data)
    else:
        return home()


@app.route('/upload')
def upload():
    if auth.logged_in(session):
        return render_template('upload.html')
    else:
        return home()


@app.route('/item/<id>/')
def item(id):

    r = requests.get('{}/{}'.format(API_ITEM, id))

    if r.json()['item'][0]['item_type'] == 'image':
        return render_template('image.html', item=r.json()['item'])

    elif r.json()['item'][0]['item_type'] == 'collection':
        return render_template('collection.html', item=r.json()['item'])

    elif r.json()['item'][0]['item_type'] == 'footage':
        return render_template('footage.html', item=r.json()['item'])

    elif r.json()['item'][0]['item_type'] == 'geometry':
        return render_template('geometry.html', item=r.json()['item'])

    elif r.json()['item'][0]['item_type'] == 'people':
        tags_from_api = r.json()['item'][0]['tags']
        people_tags = image.get_people_tags(tags_from_api)
        #print(people_tags)

        return render_template('people.html', item=r.json()['item'], people_tags=people_tags)


    else:
        return home()


@app.route('/search')
def search():
    search_data = {}
    search_term = request.args['search']
    search_data['query'] = str(search_term)
    search_data['filter_people'] = []

    if 'filter' in request.args:
        search_data['filter'] = request.args['filter']
        auth.SessionHandler(session).filter(request.args['filter'])
    else:
        pass

    # adds people filter to session.
    if 'filter_people' in request.args:
        auth.SessionHandler(session).filter_people(request.args['filter_people'])

    # get all people filters == 1, and append to searfh_data
    for x in session['filter_people']:
        for j in session['filter_people'][x]:
            if session['filter_people'][x][j] == 1:
                search_data['filter_people'].append(j)

    r = requests.get('{}query'.format(API), params=search_data)

    return render_template('search.html', data=search_data, items=r.json()['result'])


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
