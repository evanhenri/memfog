import urwid
import urwid.curses_display
import itertools
import signal
from collections import deque

class Header(urwid.Columns):
    def __init__(self, Rec, mode_label):
        self.widgets = [
            (urwid.AttrMap(urwid.Edit(edit_text=Rec.title, align='center'), 'HDR')),
            (urwid.Padding(urwid.AttrMap(urwid.Text(mode_label), 'HDR'), align='right', width=('relative', 15)))
        ]
        super(Header, self).__init__(self.widgets)

    def __getitem__(self, item):
        accessible = {
            'title':self.widgets[0].base_widget,
            'mode_label':self.widgets[-1].base_widget,
        }
        return accessible[item]

class Content(urwid.ListBox):
    def __init__(self, Rec, mode_label):
        self.widgets = urwid.SimpleFocusListWalker([
            Header(Rec, mode_label),
            urwid.Divider('-'),
            urwid.Edit( caption='Keywords: ', edit_text=Rec.keywords, align='left', wrap='clip'),
            urwid.Divider('-'),
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

class InfoText(urwid.Columns):
    def __init__(self):
        self.widgets = [
            ('pack', urwid.AttrMap(urwid.Text('^X'), 'FTR_CMD')),
            ('pack', urwid.AttrMap(urwid.Text(' Exit  '), 'INFO')),
            ('pack', urwid.AttrMap(urwid.Text('i / ESC'), 'FTR_CMD')),
            ('pack', urwid.AttrMap(urwid.Text(' Toggle Mode  '), 'INFO')),
        ]
        super(InfoText, self).__init__(self.widgets)

class CmdEdit(urwid.Edit):
    def __init__(self):
        super(CmdEdit, self).__init__(caption='> ')
        pass

    def __getitem__(self, item):
        accessible = {
            'cmd':self.edit_text
        }
        return accessible.setdefault(item, None)

class Mode:
    """ Contains data that differs between interface modes and objects to trigger mode switching """
    def __init__(self, starting_label):
        # label_widget_mirror mirrors the text in label_widget and updates in response to 'change' signal
        #  emitted by label_widget to label_widget_mirror whenever label_widget is changed
        self.label_widget = urwid.Edit(caption='Mode: ', edit_text=starting_label)
        self.identifiers = ['COMMAND','INSERT']
        self.palettes = [
            [
                # normal mode
                ('HDR', 'white', 'black', 'bold'),
                ('INFO', 'white', 'black', 'bold'),
                ('FTR_CMD', 'dark gray', 'light gray', 'bold'),
                ('MODE', 'white', 'black', 'bold'),
                ('CMD', 'yellow', 'light green', 'bold')
            ],
            [
                # insert mode
                ('HDR','white',      'dark magenta', 'bold'),
                ('INFO','white',      'dark magenta', 'bold'),
                ('FTR_CMD', 'dark gray', 'light gray', 'bold'),
                ('NORMAL_MODE', 'dark gray', 'light gray', 'bold'),
                ('CMD', 'yellow', 'light green', 'bold'),
            ]
        ]
        self.settings = deque(zip(self.identifiers, self.palettes))

        if starting_label in self.identifiers:
            while self.settings[0][0] != starting_label:
                self.settings.rotate(1)

    def __getitem__(self, item):
        accessible = {
            'caption':self.label_widget.caption,
            'label':self.label_widget.edit_text,
            'text':self.label_widget.caption + self.label_widget.edit_text
        }
        return accessible[item]

class TTY(urwid.Frame, urwid.curses_display.Screen):
    def __init__(self, Rec, starting_label):
        self._content = Content(Rec, starting_label)
        self._footer = urwid.Text('')
        super(TTY, self).__init__(body=self._content, footer=self._footer)

        self.mode = Mode(starting_label)
        self._switcher = self._switch_generator()
        self.switch_mode()

    def __getitem__(self, item):
        accessible = {
            'content':self._content.base_widget,
            'footer':self._footer
        }
        return accessible[item]

    def switch_mode(self):
        """ Helper function so next() does not need to be used directly when switching modes """
        next(self._switcher)

    def _switch_generator(self):
        """ Infinite circular iterator used to flip back and forth between modes """
        for label, palette in itertools.cycle(self.mode.settings):
            self.register_palette( palette )
            self.mode.label_widget.set_edit_text( label )
            self.body['title']['mode_label'].set_text(label)

            if label == 'COMMAND':
                self.footer = urwid.AttrMap(CmdEdit(), attr_map='CMD')
            elif label == 'INSERT':
                self.footer = urwid.AttrMap(InfoText(), attr_map='INFO')

            yield

class UI:
    def __init__(self, Rec):
        signal.signal(signal.SIGINT, self.ctrl_c_handler)
        self._force_exit = False

        self.tty = TTY(Rec, 'COMMAND')
        self.starting_values = Rec.dump()

        self.tty.run_wrapper( self._run )

    def altered(self):
        """ Returns True if any values in Rec have been changed """
        return self.starting_values != self.dump()

    def ctrl_c_handler(self, sig, frame):
        self._force_exit = True

    def dump(self):
        return { 'title':self.tty['content']['title']['title'].edit_text, ## RENAME ACCESS PATHS TO HEADER TEXT
                 'keywords':self.tty['content']['keywords'].edit_text,
                 'body':self.tty['content']['body'].edit_text }

    def _run(self):
        size = self.tty.get_cols_rows()

        while True:
            canvas = self.tty.render( size, focus=True )
            self.tty.draw_screen( size, canvas )
            keys = None

            while not keys:
                keys = self.tty.get_input()

                if self._force_exit:
                    [setattr(self, key, value) for key, value in self.dump().items()]
                    return

            for k in keys:
                if k == 'window resize':
                    size = self.tty.get_cols_rows()

                elif k == 'ctrl x':
                    [setattr(self, key, value) for key, value in self.dump().items()]
                    return

                elif self.tty.mode['label'] == 'INSERT':
                    if k == 'esc':
                        self.tty.switch_mode()
                    else:
                        self.tty.keypress( size, k )

                elif self.tty.mode['label'] == 'COMMAND':
                    if k in ['a','A','i','I','o','O']:
                        self.tty.switch_mode()
                    # if user tries to scroll when focus is on command widget, change focus
                    #   to the body and send up / down keypress. Focus immediately returned
                    #   to command widget when awaiting next keypress
                    elif k in ['up', 'down']:
                        self.tty.set_focus('body')
                        self.tty.keypress(size, k)
                    else:
                        self.tty['footer'].keypress((1, ), k)

# TODO see if possible to assign header to Frame.header and still move between it and the body sections
# TODO make braced access calls [] consistent
# TODO necessary to have header/footer color change if mode label and bottom status already changing ?
# TODO fix header so mode label is right aligned. no need to fix coloring if i remove color changes
# TODO disable body Edit widgets and see if still able to copy/paste when in command mode
# TODO make COMMAND entry default to highlight search body text