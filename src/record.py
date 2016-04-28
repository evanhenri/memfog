from . import database
from . import util

class Record(database.RecordMap):
    def __init__(self, row_id=None, title='', keywords='', body=''):
        super(Record, self).__init__(row_id, title, keywords, body)
        self.search_score = 0

    def __gt__(self, other_record):
        return self.search_score > other_record.search_score

    def __repr__(self):
        return 'Memory {}: {}'.format(self.__dict__.items())

    def dump(self):
        return { 'title':self.title,'keywords':self.keywords,'body':self.body }

    def make_set(self):
        # body text is not include in string match
        m_data = ' '.join([self.title, self.keywords])
        return set(util.standardize(m_data))

class RecordGroup:
    def __init__(self, db_stream):
        self._records = { record.title:record for record in db_stream }

    def __len__(self):
        return len(self._records)

    def __iter__(self):
        return iter(self._records.values())

    def __contains__(self, item):
        return item in self._records

    def __delitem__(self, key):
        del self._records[key]