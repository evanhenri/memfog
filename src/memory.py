import npyscreen as np
import signal

from . import util

class Memory:
    # Constructor only called with params when initially retrieving memories from database
    #   which does not store body.text so no param for body is needed.
    # body.text is only set prior to being displayed in the terminal UI, but must be
    #   initialized to empty string or an exception will get thrown for populating the
    #   body_widget with a NoneType object
    def __init__(self, db_key=None, title='', keywords=''):
        self.db_key = db_key
        self.title = title
        self.keywords = keywords
        self.body = ''
        self.search_score = 0

    def __gt__(self, other_memory):
        return self.search_score > other_memory.search_score

    def __repr__(self):
        return 'Memory {}: {}'.format(self.__dict__.items())

    def get_backup(self):
        return {k:v for k,v in self.__dict__.items() if k != 'search_score'}

    def make_set(self):
        # body text is not include in string match
        m_data = ' '.join([self.title, self.keywords])
        return set(util.standardize(m_data))

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
        self.altered = False
        np.wrapper_basic(self._run)

    def _run(self, *args):
        F = np.Form()
        title_widget = F.add(np.TitleText, name='Title:', value=self.title)
        keywords_widget = F.add(np.TitleText, name='Keywords:', value=self.keywords)
        body_widget = F.add(self.BoxedMultiLineEdit, name='Body', value=self.body)
        body_widget.entry_widget.scroll_exit = True

        def change_detected():
            return any([self.title != title_widget.value,
                        self.keywords != keywords_widget.value,
                        self.body != body_widget.value])

        def ctrl_c_handler(signal, frame):
            self.__dict__['_save'] = False

            if change_detected() and np.notify_yes_no('Save changes?'):
                # set save = True only if user selected 'yes' button
                self.__dict__['_save'] = True

            # break out of npyscreen ui
            F.exit_editing()

        signal.signal(signal.SIGINT, ctrl_c_handler)
        F.edit()

        # if ctrl-c was used, save_trigger gets set from result of np.notify_yes_no popup selection
        #   otherwise save_trigger only == True if a text field has been changed
        save_trigger = self.__dict__.setdefault('_save', True) and change_detected()

        if save_trigger:
            self.title = title_widget.value
            self.keywords = keywords_widget.value
            self.body = body_widget.value
            self.altered = True