import urwid
import urwid.curses_display
import itertools
import signal

class Content(urwid.ListBox):
    def __init__(self, Rec):
        self.widgets = urwid.SimpleFocusListWalker([
            (urwid.AttrMap(urwid.Edit(edit_text=Rec.title, align='center'), 'HDR')),
            urwid.Divider('-'),
            urwid.Edit( caption='Keywords: ', edit_text=Rec.keywords, align='left', wrap='clip'),
            urwid.Divider(' '),
            urwid.Edit( edit_text=Rec.body, align='left', multiline=True, allow_tab=True),
        ])
        super(Content, self).__init__(self.widgets)

    def __getitem__(self, item):
        accessible = {
            'title':self.widgets[0].base_widget,
            'keywords':self.widgets[2],
            'body':self.widgets[4],
        }
        return accessible[item]

class Footer(urwid.Pile):
    def __init__(self):
        self.widgets = [
            urwid.Columns(
                [
                    ('pack', urwid.AttrMap(urwid.Text('^X'), 'FTR_CMD')),
                    ('pack', urwid.AttrMap(urwid.Text(' Exit  '), 'FTR')),
                    ('pack', urwid.AttrMap(urwid.Text('i / ESC'), 'FTR_CMD')),
                    ('pack', urwid.AttrMap(urwid.Text(' Toggle Mode  '), 'FTR')),
                    (urwid.Padding(urwid.AttrMap(urwid.Text(''), 'HDR'), align='right', width=('relative', 15)))
                ]
            ),
            urwid.Edit(caption='>', edit_text='', align='left', wrap='clip'),
        ]
        super(Footer, self).__init__(self.widgets)

    def __getitem__(self, item):
        accessible = {
            'label_widget_mirror':self.widgets[0][-1].base_widget,
            'cmd':self.widgets[-1]
        }
        return accessible[item]

    def mode_label_callback(self, widget, signal, label_text):
        """ Called when Mode.label_widget emits 'change' signal in response to its edit_text being changed """
        self.widgets[0][-1].base_widget.set_text(label_text)

    def cmd_input(self, k):
        """ Handles keypresses entered when COMMAND is current mode to display then in the command entry field widget """
        if k == 'ctrl l':
            self.widgets[-1].set_edit_text('')
        else:
            self.widgets[-1].keypress((1,), k)

class Display(urwid.Frame):
    """ Contains container widgets that hold individual widgets for each section """
    def __init__(self, Rec):
        self._content = urwid.AttrMap(Content(Rec), attr_map='BODY')
        self._footer = urwid.AttrMap(Footer(), attr_map='FTR')
        super(Display, self).__init__(body=self._content, footer=self._footer)

    def __getitem__(self, item):
        accessible = {
            'content':self._content,
            'footer':self._footer
        }
        return accessible[item].base_widget

class Mode:
    """ Contains data that differs between interface modes and objects to trigger mode switching """
    def __init__(self):
        # label_widget_mirror mirrors the text in label_widget and updates in response to 'change' signal
        #  emitted by label_widget to label_widget_mirror whenever label_widget is changed
        self.label_widget = urwid.Edit(caption='Mode: ')
        self.identifiers = ['COMMAND','INSERT']
        self.palettes = [
            [
                # normal mode
                ('HDR', 'white', 'black', 'bold'),
                ('FTR', 'white', 'black', 'bold'),
                ('FTR_CMD', 'dark gray', 'light gray', 'bold'),
                ('MODE', 'white', 'black', 'bold')
            ],
            [
                # insert mode
                ('HDR','white',      'dark magenta', 'bold'),
                ('FTR','white',      'dark magenta', 'bold'),
                ('FTR_CMD', 'dark gray', 'light gray', 'bold'),
                ('NORMAL_MODE', 'dark gray', 'light gray', 'bold'),
            ]
        ]
        self.settings = zip(self.identifiers, self.palettes)

    def __getitem__(self, item):
        accessible = {
            'caption':self.label_widget.caption,
            'label':self.label_widget.edit_text,
            'text':self.label_widget.caption + self.label_widget.edit_text
        }
        return accessible[item]

class Screen(urwid.curses_display.Screen):
    """ Contains functionality to change appearence and behavior of terminal interface """
    def __init__(self):
        super(Screen, self).__init__()
        self.mode = Mode()
        self._switcher = self._swith_generator()

    def switch_mode(self):
        """ Helper function so next() does not need to be used directly when switching modes """
        next(self._switcher)

    def _swith_generator(self):
        """ Infitite circular iterator used to flip back and forth between modes """
        for identifier, palette in itertools.cycle(self.mode.settings):
            self.register_palette( palette )
            self.mode.label_widget.set_edit_text(identifier)
            yield

class UI:
    def __init__(self, Rec):
        signal.signal(signal.SIGINT, self.ctrl_c_handler)
        self._force_exit = False

        self.screen = Screen()
        self.display = Display(Rec)
        self.starting_values = Rec.dump()

        # Establish connection between Mode.widget and in Footer mode widget.
        # Footer mode widget mirrors the contents of Mode.widget and is a label indicator of current input mode
        urwid.connect_signal(self.screen.mode.label_widget, 'change',
                             self.display['footer'].mode_label_callback,
                             user_args=[self.screen.mode['text']])

        self.screen.run_wrapper( self._run )

    def altered(self):
        """ Returns True if any values in Rec have been changed """
        return self.starting_values != self.dump()

    def ctrl_c_handler(self, sig, frame):
        self._force_exit = True

    def dump(self):
        return { 'title':self.display['content']['title'].edit_text,
                 'keywords':self.display['content']['keywords'].edit_text,
                 'body':self.display['content']['body'].edit_text }

    def _run(self):
        size = self.screen.get_cols_rows()

        # set initial mode values for terminal interface
        self.screen.switch_mode()

        while True:
            canvas = self.display.render( size, focus=True )
            self.screen.draw_screen( size, canvas )
            keys = None

            while not keys:
                keys = self.screen.get_input()

                if self._force_exit:
                    [setattr(self, key, value) for key, value in self.dump().items()]
                    return

            for k in keys:
                if k == 'window resize':
                    size = self.screen.get_cols_rows()

                elif k == 'ctrl x':
                    [setattr(self, key, value) for key, value in self.dump().items()]
                    return

                elif self.screen.mode['label'] == 'INSERT':
                    if k == 'esc':
                        self.screen.switch_mode()
                    else:
                        self.display.keypress( size, k )

                elif self.screen.mode['label'] == 'COMMAND':
                    if k in ['a','A','i','I','o','O']:
                        self.screen.switch_mode()
                    else:
                        self.display['footer'].cmd_input(k)
