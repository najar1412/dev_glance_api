import sqlite3
import sqlalchemy
import datetime

from sqlalchemy import JSON, ARRAY, Column, DateTime, String, Integer, ForeignKey, func, Table


# TODO: Define globals or config - table names

def connect(user, password, db, host='localhost', port=5432):
    """
    Connects to database using string name
    :param db: name of database, str
    :return: Connection object
    """
    '''Returns a connection and a metadata object'''
    # We connect with the help of the PostgreSQL URL
    # postgresql://federer:grandestslam@localhost:5432/tennis
    url = 'postgresql://{}:{}@{}:{}/{}'
    url = url.format(user, password, host, port, db)

    # The return value of create_engine() is our connection object
    con = sqlalchemy.create_engine(url, client_encoding='utf8')

    # We then bind the connection to MetaData()
    meta = sqlalchemy.MetaData(bind=con, reflect=True)

    return con, meta


def CREATE_asset_table(conn):
    """
    Creates Asset table in database
    :param conn: Connection object
    :return: None
    """
    try:
        c = conn.cursor()
        c.execute(
            '''CREATE TABLE Asset(
                id integer PRIMARY KEY,
                asset_name text,
                asset_image text,
                asset_thumb text,
                tag text,
                attachment text,
                flag text,
                uploadedby text,
                uploaddate text,
                uploadmodified text
            )'''
        )
        c.close()
        return None
    except: pass


def CREATE_collection_table(conn):
    """
    Creates Collection table in database
    :param conn: Connection object
    :return: None
    """
    try:
        c = conn.cursor()
        c.execute(
            '''CREATE TABLE Collection(
                id integer PRIMARY KEY,
                collection_name text,
                collection_cover text,
                collection_assets text,
                tag text,
                flag text,
                uploadedby text,
                uploaddate text,
                uploadmodified text
            )'''
        )
        c.close()
        return None
    except: pass


def POST_asset(con, meta, *asset_info, tablename='dev_asset'):
    """
    Create a new asset in the database
    :param conn: Connection object
    :param list_of_dict: A list containing a dict of new assets
    :return: Boolean
    """
    print('-------------------------------')
    print(asset_info)
    # TODO: Format initdate and moddate
    asset = meta.tables[tablename]
    clause = asset.insert().values(
        name=asset_info[0], image=asset_info[1], attached=asset_info[5],
        tag=asset_info[2], flag=0, author=asset_info[3],
        initdate=datetime.datetime.utcnow(), moddate=datetime.datetime.utcnow(),
        image_thumb=asset_info[4]
        )
    result = con.execute(clause)

    return result


def POST_collection(con, meta, *collection_info, tablename='dev_collection'):
    """
    Craete a new collection in the database
    :param conn: Connection object
    :param list_of_dict: A list containing a dict of new collections
    :return: Boolean
    """
    # TODO: Format initdate and moddate
    collection = meta.tables[tablename]
    clause = collection.insert().values(
        name=collection_info[0], image=collection_info[1], tag=collection_info[2], flag=0,
        author=collection_info[3], initdate=datetime.datetime.utcnow(), moddate=datetime.datetime.utcnow(),
        image_thumb=collection_info[4], assets=collection_info[5]
        )
    result = con.execute(clause)

    return result.inserted_primary_key


def GET_collection(con, meta):
    """
    Query all rows in the Collection table
    :param conn: the Connection object
    :param meta: the MetaData object
    :return: list of collections (as dicts)
    """
    # TODO: Build correct return structure
    collections = {}
    table = meta.tables['dev_collection']
    for row in con.execute(table.select()):
        collections[row[0]] = {
            'name': row[1], 'image': row[2], 'tag': row[3], 'flag': row[4],
            'author': row[5], 'initdate': row[6], 'moddate': row[7],
            'image_thumb': row[8], 'assets': row[9],
            }
    return collections


def GET_collection_id(con, meta, _id):
    """
    Query Collection table for a collection using its id (pk)
    :param conn: the Connection object
    :param meta: the MetaData object
    :param _id: The id of a collection
    :return: collect, dict.
    """
    result = {}
    collection = meta.tables['dev_collection']
    clause = collection.select().where(collection.c.id == _id)

    for row in con.execute(clause):
        result[row[0]] = {
            'name': row[1], 'image': row[2], 'tag': row[3], 'flag': row[4],
            'author': row[5], 'initdate': row[6], 'moddate': row[7],
            'image_thumb': [8]
            }

    print('------')
    print('------')
    print('------')
    print(result)

    return result


def GET_asset(con, meta):
    """
    Query all rows in the Asset table
    :param conn: the Connection object
    :param meta: the MetaData object
    :return: list of assets, dicts.
    """
    assets = {}
    table = meta.tables['dev_asset']
    for row in con.execute(table.select()):
        assets[row[0]] = {
        'name': row[1], 'image': row[2], 'attached': row[3], 'tag': row[4],
        'flag': row[5], 'author': row[6], 'initdate': row[7], 'moddate': row[8],
        'image_thumb': row[9]
        }
    return assets


def GET_asset_id(con, meta, _id):
    """
    Query Asset table for a asset using its id (pk)
    :param conn: the Connection object
    :param meta: the MetaData object
    :param _id: The id (pk) of Asset
    :return: asset, dict.
    """
    result = {}
    asset = meta.tables['dev_asset']
    clause = asset.select().where(asset.c.id == _id)

    for row in con.execute(clause):
        result[row[0]] = {
        'name': row[1], 'image': row[2], 'attached': row[3], 'tag': row[4],
        'flag': row[5], 'author': row[6], 'initdate': row[7], 'moddate': row[8],
        'image_thumb': row[9]
        }

    return result


def PUT_asset_tag(
    con, meta, asset_id, asset_n=None, asset_i=None, asset_a=None, image_thumb=None, *tags):
    # TODO: Figure out arrays in postgrest, retriving and appending
    # TODO: ump updating all asset attributes and rename function
    print(image_thumb)
    result = {}
    asset = meta.tables['dev_asset']
    clause = asset.select().where(asset.c.id == asset_id)
    if asset_n != None:
        # IMP name rename
        u = asset.update().where(asset.c.id == asset_id).values(name=asset_n)
        con.execute(u)

    if asset_i != None:
        u = asset.update().where(asset.c.id == asset_id).values(image=asset_i)
        con.execute(u)

    if asset_a != None:
        u = asset.update().where(asset.c.id == asset_id).values(author=asset_a)
        con.execute(u)

    if image_thumb != None:
        u = asset.update().where(asset.c.id == image_thumb).values(image_thumb=image_thumb)
        con.execute(u)

    if len(tags[0]) != 0:
        taglist = []
        # Get and append to current asset tags.
        for row in con.execute(clause):
            taglist = list(row[4])
            for tag in tags[0]:
                taglist.append(tag)
        # remove dups and append all tags to field.
        u = asset.update().where(asset.c.id == asset_id).values(tag=list(set(taglist)))
        con.execute(u)

    for row in con.execute(clause):
        # Build asset dict to return
        result[row[0]] = {
        'name': row[1], 'image': row[2], 'attached': row[3], 'tag': row[4],
        'flag': row[5], 'author': row[6], 'initdate': row[7], 'moddate': row[8],
        'image_thumb': row[9]
        }

    return result


def PUT_collection_tag(con, meta, asset_id, *tags):
    # TODO: Figure out arrays in postgrest, retriving and appending
    # TODO:
    result = {}
    asset = meta.tables['dev_asset']
    clause = asset.select().where(asset.c.id == asset_id)

    if tags:
        # Get and append to current asset tags.
        for row in con.execute(clause):
            taglist = list(row[4])
            for tag in tags[0]:
                taglist.append(tag)
        # remove dups and append all tags to field.
        u = asset.update().where(asset.c.id == asset_id).values(tag=list(set(taglist)))
        con.execute(u)

    for row in con.execute(clause):
        # Build asset dict to return
        result[row[0]] = {
        'name': row[1], 'image': row[2], 'attached': row[3], 'tag': row[4],
        'flag': row[5], 'author': row[6], 'initdate': row[7], 'moddate': row[8],
        'image_thumb': row[9]
        }

    return result


def DELETE_collection(meta, collection_id):
    """
    Delete a collection from the table
    :param conn: the Connection object
    :param _id: The id of collection
    :return: Boolean
    """
    # TODO: Return something useful. Success or not, etc.
    collection = meta.tables['dev_collection']
    delete_collection = collection.delete().where(collection.c.id == collection_id)
    delete_collection.execute()


def DELETE_asset(meta, asset_id):
    """
    Delete an asset from the table
    :param conn: the Connection object
    :param _id: The id of asset
    :return: Boolean
    """
    # TODO: Return something useful. Success or not, etc.
    asset = meta.tables['dev_asset']
    delete_asset = asset.delete().where(asset.c.id == asset_id)
    delete_asset.execute()
