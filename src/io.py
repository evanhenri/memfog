import os
import json
import sqlite3

class DB:
    def __init__(self, file_path):
        self.filename = file_path
        self.connection = sqlite3.connect(file_path)
        self.cursor = self.connection.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS records
                            (key INTEGER, title TEXT, keywords TEXT,
                            body TEXT, PRIMARY KEY (key))""")
    def dump(self):
        sql = """SELECT * FROM records"""
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    def insert(self, title, keywords, body):
        sql = """INSERT INTO records(title, keywords, body) VALUES(?,?,?)"""
        self.cursor.execute(sql, (title, keywords, body))
        self.connection.commit()
    def update(self, mem_obj, mem_ui):
        """
        :type mem_obj: memory.Memory
        :type mem_ui: memory.UI
        Updates to database on done if mem_obj has different values compared to mem_ui
        """
        sql = """UPDATE records SET"""
        if mem_obj.title != mem_ui.title_text:
            sql += """ title="{}",""".format(mem_ui.title_text)
        if mem_obj.keywords != mem_ui.keywords_text:
            sql += """ keywords="{}",""".format(mem_ui.keywords_text)
        if mem_obj.body != mem_ui.body_text:
            sql += """ body="{}",""".format(mem_ui.body_text)

        # sql string will only change from default value if change has been detected
        if sql != """UPDATE records SET""":
            if sql.endswith(','):
                sql = sql.rsplit(',',1)[0]
            sql += """ WHERE key={}""".format(mem_obj.db_key)
            self.cursor.executescript(sql)
            self.connection.commit()
    def remove(self, key):
        sql = """DELETE FROM records WHERE key={}""".format(key)
        self.cursor.execute(sql)
        self.connection.commit()

def file_exists(filepath):
    if os.path.isfile(filepath):
        return True
    print('Invalid file path {}'.format(filepath))
    return False

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

def mkfile(filepath):
    """
    :type filepath: str
    """
    try:
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