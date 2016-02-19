import os
import json
import sqlite3

class DB:
    def __init__(self, file_path):
        self.filename = file_path
        self.connection = sqlite3.connect(file_path)
        self.cursor = self.connection.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS records
                            (key INTEGER, title TEXT, keywords TEXT, PRIMARY KEY (key))""")

    def dump(self):
        sql = """SELECT * FROM records"""
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def insert(self, Mem):
        sql = """INSERT INTO records(title, keywords) VALUES(?,?)"""
        self.cursor.execute(sql, (Mem.title, Mem.keywords))
        self.connection.commit()
        return self.cursor.lastrowid

    def remove(self, key):
        sql = """DELETE FROM records WHERE key={}""".format(key)
        self.cursor.execute(sql)
        self.connection.commit()

    def update_many(self, record_key, record_changes={}):
        cols_vals = ''.join(['{}="{}", '.format(col,val) for col,val in record_changes.items()])
        sql = """UPDATE records SET {} WHERE key={key)""".format(cols_vals, key=record_key)
        self.cursor.executescript(sql)
        self.connection.commit()

def file_exists(filepath):
    if os.path.isfile(filepath):
        return True
    print('Invalid file path {}'.format(filepath))
    return False

def delete_file(filepath):
    """
    :type filepath: str
    """
    try:
        if file_exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print('Error occured while deleting {}\n{}'.format(filepath, e.args))

def json_from_file(filepath):
    """
    :type filepath: str
    """
    try:
        if file_exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return dict()
    except Exception as e:
        print('Error occured while reading {} as json\n{}'.format(filepath, e.args))

def json_to_file(filepath, payload):
    """
    :type filepath: str
    :type payload: json encodable obj
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(payload, f, indent=4)
        print('Saved {}'.format(filepath))
    except Exception as e:
        print('Error occured while writing json to {}\n{}'.format(filepath, e.args))

def init_dir(dirpath):
    """
    :type dirpath: str
    """
    try:
        if not os.path.isdir(dirpath):
            os.mkdir(dirpath)
    except Exception as e:
        print('Error occured while creating directory at {}\n{}'.format(dirpath, e.args))

def init_file(filepath):
    """
    :type filepath: str
    """
    try:
        if not os.path.isfile(filepath):
            open(filepath, 'w').close()
    except Exception as e:
        print('Error occured while making file {}\n{}'.format(filepath, e.args))

def set_from_file(filepath):
    """
    :type filepath: str
    :returns: contents of file at file_path where each line is an element in returned set
    """
    try:
        if file_exists(filepath):
            with open(filepath, 'r') as f:
                return set([line.strip() for line in f.readlines()])
        return set()
    except Exception as e:
        print('Error occured while reading {} as set\n{}'.format(filepath, e.args))

def str_from_file(filepath):
    """
    :type filepath: str
    :returns: contents of file at file_path as string
    """
    try:
        if file_exists(filepath):
            with open(filepath, 'r') as f:
                return f.read()
        return str()
    except Exception as e:
        print('Error occured while reading {} as string\n{}'.format(filepath, e.args))

def str_to_file(filepath, payload):
    """
    :type filepath: str
    :type payload: str
    """
    try:
        with open(filepath, 'w') as f:
            f.write(payload)
    except Exception as e:
        print('Error occured while reading {} as set\n{}'.format(filepath, e.args))