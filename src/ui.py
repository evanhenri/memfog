import npyscreen as np

class MemDisplay:
    class BoxedMultiLineEdit(np.BoxTitle):
        _contained_widget = np.MultiLineEdit

    def __init__(self, title='', keywords='', body=''):
        self.title_text = title
        self.keywords_text = keywords
        self.body_text = body

        np.wrapper_basic(self._run)

    def _run(self, *args):
        F = np.Form()
        title = F.add(np.TitleText, name='Title:', value=self.title_text)
        keywords = F.add(np.TitleText, name='Keywords:', value=self.keywords_text)
        body = F.add(self.BoxedMultiLineEdit, name='Body', value=self.body_text)
        body.entry_widget.scroll_exit = True

        F.edit()

        # update UI member variables in case they have been changed by the user
        self.title_text = title.value
        self.keywords_text = keywords.value
        self.body_text = body.value