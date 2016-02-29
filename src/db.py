from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from . import util

Base = declarative_base()

class Database:
    def __init__(self, db_fp):
        # Create an engine that stores data in db found at db_path
        engine = create_engine('sqlite:///{}'.format(db_fp))

        # Create all tables in the engine
        Base.metadata.create_all(engine)

        DBSession = sessionmaker(bind=engine)
        self.session = DBSession()

    def bulk_insert(self, Recs=[]):
        self.session.bulk_save_objects(Recs)
        self.session.commit()

    def insert(self, Rec):
        self.session.add(Rec)
        self.session.commit()

    def remove(self, Rec):
        self.session.query(Record).filter_by(row=Rec.row).delete()
        self.session.commit()

    def update(self, Rec, keys={}):
        updated_fields = { k:v for k,v in Rec.dump().items() if k in keys }
        self.session.query(Record).filter_by(row=Rec.row).update(updated_fields)
        self.session.commit()

class Record(Base):
    __tablename__ = 'record'
    row = Column('row', Integer, primary_key=True)
    title = Column('title', String, nullable=False)
    keywords = Column('keywords', String)
    body = Column('body', Text)

    def __init__(self, row=None, title='', keywords='', body=''):
        self.row = row
        self.title = title
        self.keywords = keywords
        self.body = body
        self.search_score = 0

    def __gt__(self, other_memory):
        return self.search_score > other_memory.search_score

    def __repr__(self):
        return 'Memory {}: {}'.format(self.__dict__.items())

    def dump(self):
        return { 'row':self.row, 'title':self.title,'keywords':self.keywords,'body':self.body }

    def make_set(self):
        # body text is not include in string match
        m_data = ' '.join([self.title, self.keywords])
        return set(util.standardize(m_data))

