"""
This module contains functions for Authentication & Authorization
"""

__author__ = ""
__version__ = ""
__license__ = ""

import os
import requests
import boto3
from requests.auth import HTTPBasicAuth

import glance.config.settings as settings
import glance.modules.struct as struct


# basic unencrypted user auth using the api and flasks `session`.
def logged_in(session):
    """Check if user is currently logged in.

    :param session: -- Sqlalchemy session object.

    :return type: Bool
    """
    if session.get('logged_in'):

        return True
    else:
        session['logged_in'] = False
        session.pop('filter', None)
        session.pop('user', None)

        return False


def check_login_details(**data):
    """Check if user details are correct.

    :param data: -- lst. User data.

    :return type: Bool
    """
    # r = requests.get('{}user'.format(settings.api_root), params=data)

    r = requests.get(
            '{}accounts'.format(settings.api_root),
            auth=HTTPBasicAuth(data['username'], data['password'])
            )
    response = r.status_code

    if 'user details' in r.json():
        if r.json()['user details']:
            result = True
        else:
            result = False
    else:
        result = False

    return result


# user session data
class SessionHandler():
    """ Handles all interaction with flask.session object.

    :methods:
      * open(data)
      * filter(data)
      * fav(id, item_type)
      * close()
    """

    allowed_params = {'filter': '', 'user': '', 'logged_in': '', 'fav': '', 'filter_people': ''}
    allowed_filters = ['all', 'image', 'footage', 'geometry', 'collection', 'people']

    def __init__(self, session):
        self.session = session


    def open(self, username, password, data=None):
        r = requests.get('{}accounts'.format(settings.api_root), auth=HTTPBasicAuth(username, password))
        if r.status_code == 200:
            self.session['logged_in'] = True
            self.session['username'] = username
            self.session['password'] = password
            self.session['filter'] = 'all'
            self.session['fav'] = {}
            self.session['filter_people'] = struct.structure_people_tags()

            return True

        elif r.status_code != 200:
            return False

    def get(self):
        result = {}
        for k in self.session:
            result[k] = self.session[k]
        return result


    def filter(self, data):
        if isinstance(data, str):
            if data in self.allowed_filters:
                self.session['filter'] = data
        else:
            self.session['filter'] = 'all'

        return self.session

    def filter_people(self, data):
        for x in self.session['filter_people']:
            for j in self.session['filter_people'][x]:
                if data == j:
                    if self.session['filter_people'][x][data] == 0:
                        self.session['filter_people'][x][data] = 1
                        self.session.modified = True
                    else:
                        self.session['filter_people'][x][data] = 0
                        self.session.modified = True

        return self.session

    def fav(self, id, item_thumb=None):
        if id not in self.session['fav']:
            self.session['fav'][id] = item_thumb
            self.session.modified = True
        else:
            del self.session['fav'][id]
            self.session.modified = True

        return self.session


    def close(self):
        self.session['logged_in'] = False
        self.session.pop('filter', None)
        self.session.pop('username', None)
        self.session.pop('fav', None)
        self.session.pop('filter_people', None)

        return self.session

    def __repr__(self):
        return '<SessionHandler>'


# aws access
def boto3_res_s3():
    """Create Amazon s3 Resource..

    :return type: boto3 resource
    """
    boto3_session = boto3.session.Session(
        aws_access_key_id=settings.config_type['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=settings.config_type['AWS_SECRET_ACCESS_KEY'],
    )

    s3 = boto3_session.resource('s3')

    return s3


def boto3_res_rek():
    """Create Amazon rekognition Client.

    :return type: boto3 client
    """
    boto3_session = boto3.session.Session(
        aws_access_key_id=settings.config_type['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=settings.config_type['AWS_SECRET_ACCESS_KEY'],
    )

    # init client
    client = boto3_session.client('rekognition', region_name='us-east-1')

    return client


def boto3_rek_tag(client, data, confidence=60):
    """Run Rekognition on Image.

    :param client: -- Rekognition Object
    :param data: -- ???
    :param confidence: -- Controls label ammount.

    :return type: JSON.
    """
    result = client.detect_labels(
        Image={
            'S3Object': {
                'Bucket': settings.config_type['AWS_BUCKET'],
                'Name': data,
            },
        },
        MaxLabels=100,
        MinConfidence=confidence,
    )

    return result


def boto3_s3_upload(s3, dst, file):
    """Upload Item to s3.

    :param s3: -- Sqlalchemy session object.
    :param dst: -- str. Location to storage ???
    :param file: -- ???. File object.

    Return Type: Bool
    """
    s3.Object(settings.config_type['AWS_BUCKET'], file).put(Body=open(os.path.join(dst, file), 'rb'))

    return file


def delete_from_s3(data):
    """delete physical assets from s3

    :param data: -- ???

    :return type: ???
    """
    # refactor below
    # get s3 resource
    s3 = boto3_res_s3()

    bucket = s3.Bucket(settings.config_type['AWS_BUCKET'])

    objects_to_delete = []
    for obj in data:
        if obj == 'site/default_cover.jpg':
            return True
        else:
            objects_to_delete.append({'Key': obj})


    bucket.delete_objects(
        Delete={
            'Objects': objects_to_delete
        }
    )
