import os
import json
import sqlite3

from . import fs

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

    def update(self, record_key, memory_updates={}):
        def _construct_str(dictionary):
            """
            returns str of key="value" for each key value pair in dictionary
             individual key="value" pairs delimited by commas
            """
            s = ''
            for i, (k, v) in enumerate(dictionary.items()):
                s += '{}="{}"'.format(k, v)
                if i < len(dictionary)-1: s += ', '
            return s

        values = _construct_str(memory_updates)
        sql = """UPDATE records SET {} WHERE key={}""".format(values, record_key)
        self.cursor.executescript(sql)
        self.connection.commit()

def delete_file(file_path):
    """
    :type file_path: str
    """
    try:
        if fs.file_exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print('Error occured while deleting {}\n{}'.format(file_path, e.args))

def json_from_file(file_path):
    """
    :type file_path: str
    """
    try:
        if fs.file_exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return dict()
    except Exception as e:
        print('Error occured while reading {} as json\n{}'.format(file_path, e.args))

def json_to_file(file_path, payload):
    """
    :type file_path: str
    :type payload: json encodable obj
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(payload, f, indent=4)
        print('Saved {}'.format(file_path))
    except Exception as e:
        print('Error occured while writing json to {}\n{}'.format(file_path, e.args))

def set_from_file(file_path):
    """
    :type file_path: str
    :returns: contents of file at file_path where each line is an element in returned set
    """
    try:
        if fs.file_exists(file_path):
            with open(file_path, 'r') as f:
                return set([line.strip() for line in f.readlines()])
        return set()
    except Exception as e:
        print('Error occured while reading {} as set\n{}'.format(file_path, e.args))

def str_from_file(file_path):
    """
    :type file_path: str
    :returns: contents of file at file_path as string
    """
    try:
        if fs.file_exists(file_path):
            with open(file_path, 'r') as f:
                return f.read()
        return str()
    except Exception as e:
        print('Error occured while reading {} as string\n{}'.format(file_path, e.args))

def str_to_file(file_path, payload):
    """
    :type file_path: str
    :type payload: str
    """
    try:
        with open(file_path, 'w') as f:
            f.write(payload)
    except Exception as e:
        print('Error occured while reading {} as set\n{}'.format(file_path, e.args))