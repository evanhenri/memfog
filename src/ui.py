import npyscreen as np
import signal

class UI:
    class BoxedMultiLineEdit(np.BoxTitle):
        _contained_widget = np.MultiLineEdit

    # Any Record objext can be passed to UI constructor and its contents will be used
    # to populate the widget text areas. Any changes made to the Record will be reflected
    # in the database when the UI is closed
    def __init__(self, Rec):
        self.__dict__.update(Rec.dump())
        self.altered = False
        self._forced_close = False
        np.wrapper_basic(self._run)

    def dump(self):
        return {'title':self.title,'keywords':self.keywords,'body':self.body}

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
            self._forced_close = True

            if change_detected() and np.notify_yes_no('Save changes?'):
                # set save = True only if user selected 'yes' button
                self.altered = True

            # break out of npyscreen ui
            F.exit_editing()

        signal.signal(signal.SIGINT, ctrl_c_handler)
        F.edit()

        # altered flag set if user changed record text and exited using OK button
        if not self._forced_close and change_detected():
            self.altered = True

        # altered flag will be set if any change was made regardless
        #  of if ui was closed using the OK button or by using ctrl-c
        if self.altered:
            self.title = title_widget.value
            self.keywords = keywords_widget.value
            self.body = body_widget.value
