import json
import sqlite3

class DB:
    def __init__(self, file_path):
        self.filename = file_path
        self.connection = sqlite3.connect(file_path)
        self.cursor = self.connection.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS records (key INTEGER, title TEXT, keywords TEXT, body TEXT, PRIMARY KEY (key))')
    def dump(self):
        sql = 'SELECT * FROM records'
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    def insert(self, title, keywords, body):
        sql = 'INSERT INTO records(title, keywords, body) VALUES(\'{}\',\'{}\',\'{}\')'.format(title, keywords, body)
        self.cursor.execute(sql)
        self.connection.commit()
    def update(self, mem_obj, mem_ui):
        """
        :type mem_obj: memory.Memory
        :type mem_ui: memory.UI
        Updates any changes made to mem_obj using single SQL statement
        """
        sql = 'UPDATE records SET'
        if mem_obj.title != mem_ui.title_text:
            sql += ' title=\'{}\','.format(mem_ui.title_text)
        if mem_obj.keywords != mem_ui.keywords_text:
            sql += ' keywords=\'{}\','.format(mem_ui.keywords_text)
        if mem_obj.body != mem_ui.body_text:
            sql += ' body=\'{}\','.format(mem_ui.body_text)

        # sql string will only change from default value if change has been detected
        if sql != 'UPDATE records SET':
            if sql.endswith(','):
                sql = sql.rsplit(',',1)[0]
            sql += ' WHERE key={}'.format(mem_obj.db_key)
            self.cursor.executescript(sql)
            self.connection.commit()
    def remove(self, key):
        sql = 'DELETE FROM records WHERE key={}'.format(key)
        self.cursor.execute(sql)
        self.connection.commit()

def json_from_file(file_path):
    """
    :type file_path: str
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
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

def mkfile(file_path):
    """
    :type file_path: str
    """
    try:
        open(file_path, 'w').close()
    except Exception as e:
        print('Error occured while making file {}\n{}'.format(file_path, e.args))

def set_from_file(file_path):
    """
    :type file_path: str
    :returns: contents of file at file_path where each line is an element in returned set
    """
    try:
        with open(file_path, 'r') as f:
            return set([line.strip() for line in f.readlines()])
    except Exception as e:
        print('Error occured while reading {} as set\n{}'.format(file_path, e.args))
