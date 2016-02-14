from . import data, user

class Memory:
    def __init__(self, db_key=None, title='', keywords='', body=''):
        self.db_key = db_key
        self.title = title
        self.keywords = keywords
        self.body = body
        self.search_score = 0

    def __gt__(self, other_memory):
        return self.search_score > other_memory.search_score

    def __repr__(self):
        return 'Memory {}: {}'.format(self.db_key, self.title)

    def get_backup(self):
        return {k:v for k,v in self.__dict__.items() if k != 'search_score'}

    def make_set(self):
        # body text is not include in string match
        m_data = ' '.join([self.title, self.keywords])
        return set(data.standardize(m_data))

    def update_title(self):
        self.title = user.prefilled_input('Title: ', self.title)

    def update_keywords(self):
        self.keywords = user.prefilled_input('Keywords: ', self.keywords)

    def update_body(self):
        self.body = user.prefilled_input('Body: ', self.body)