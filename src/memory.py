import npyscreen as np

from . import data

class Memory:
    def __init__(self, db_key=0, title='', keywords='', body=''):
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

    def diff(self, Mem_UI):
        memory_changes = {}

        if Mem_UI.title != self.title: memory_changes['title'] = Mem_UI.title
        if Mem_UI.keywords != self.keywords: memory_changes['keywords'] = Mem_UI.keywords
        if Mem_UI.body != self.body: memory_changes['body'] = Mem_UI.body

        return memory_changes


class UI:
    class BoxedMultiLineEdit(np.BoxTitle):
        _contained_widget = np.MultiLineEdit

    def __init__(self, Mem):
        self.title = Mem.title
        self.keywords = Mem.keywords
        self.body = Mem.body
        np.wrapper_basic(self._run)

    def _run(self, *args):
        F = np.Form()
        title_widget = F.add(np.TitleText, name='Title:', value=self.title)
        keywords_widget = F.add(np.TitleText, name='Keywords:', value=self.keywords)
        body_widget = F.add(self.BoxedMultiLineEdit, name='Body', value=self.body)
        body_widget.entry_widget.scroll_exit = True

        F.edit()

        # update UI member variables in case they have been changed by the user
        self.title = title_widget.value
        self.keywords = keywords_widget.value
        self.body = body_widget.value

