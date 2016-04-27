from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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
        self.session.query(RecordMap).filter_by(row_id=Rec.row_id).delete()
        self.session.commit()

    def update(self, rec_id, updated_fields):
        self.session.query(RecordMap).filter_by(row_id=rec_id).update(updated_fields)
        self.session.commit()

class RecordMap(Base):
    __tablename__ = 'record'
    row_id = Column('row_id', Integer, primary_key=True)
    title = Column('title', String, nullable=False)
    keywords = Column('keywords', String)
    body = Column('body', Text)

    def __init__(self, row_id=None, title='', keywords='', body=''):
        self.row_id = row_id
        self.title = title
        self.keywords = keywords
        self.body = body

