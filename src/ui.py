from urwid import AttrMap, Columns, Divider, Edit, Frame, ListBox, Text, SimpleFocusListWalker, WidgetPlaceholder
import urwid.curses_display
from collections import deque
import itertools
import signal

class Header(Columns):
    def __init__(self, Rec, mode_label):
        self.widgets = [
            (AttrMap(Text(mode_label, align='left'), 'HEADER')),
            (AttrMap(Edit(edit_text=Rec.title, align='right'), 'HEADER'))
        ]
        super(Header, self).__init__(self.widgets)

    def __getitem__(self, item):
        accessible = {
            'mode':self.widgets[0].base_widget,
            'title':self.widgets[-1].base_widget
        }
        return accessible[item]

class Content(ListBox):
    def __init__(self, Rec, mode_label):
        self._keywords = Edit(caption='Keywords: ', edit_text=Rec.keywords, align='left', wrap='clip')
        self._widgets = SimpleFocusListWalker([
            Header(Rec, mode_label),
            Divider('-'),
            Edit( edit_text=Rec.body, align='left', multiline=True, allow_tab=True)
        ])
        super(Content, self).__init__(self._widgets)

    def show_keywords(self):
        if len(self._widgets) == 3:
            # insert keywords widget so it is above divider
            self._widgets.insert(1, self._keywords)

    def hide_keywords(self):
        if len(self._widgets) > 3:
            # update stored keywords before removing them from view
            self._keywords = self._widgets.pop(1)

    def __getitem__(self, item):
        if item == 'keywords' and len(self._widgets) > 3:
            # ensure that the _keywords returned reflect the most recent changes
            self._keywords = self._widgets[1]

        accessible = {
            'header':self._widgets[0].base_widget,
            'keywords':self._keywords,
            'body':self._widgets[-1]
        }
        return accessible[item]

class InfoFooter(Columns):
    def __init__(self):
        self.widgets = [
            ('pack', AttrMap(Text('^X'), 'FOOTER_INFO_A')),
            ('pack', AttrMap(Text(' Exit  '), 'FOOTER_INFO_B')),
            ('pack', AttrMap(Text('ESC'), 'FOOTER_INFO_A')),
            ('pack', AttrMap(Text(' Toggle Mode  '), 'FOOTER_INFO_B')),
        ]
        super(InfoFooter, self).__init__(self.widgets)

class CmdFooter(Edit):
    def __init__(self):
        super(CmdFooter, self).__init__(caption='> ')
        self.clear_before_keypress = False

    def __getitem__(self, item):
        accessible = {
            'cmd':self.edit_text
        }
        return accessible[item]

    def kpi(self, size, key):
        """
        keypress intermediary
        If an invalid entry was made, clear_before_keypress will be set to True
          and 'Invalid entry' notification will be current edit_text. Clear
          notification and reset flag before sending keys to keypress
        """
        if self.clear_before_keypress:
            self.set_edit_text('')
            self.clear_before_keypress = False
        self.keypress(size, key)

class Mode:
    """ Contains data that differs between interface modes and objects to trigger mode switching """
    def __init__(self, starting_label):
        self.label = starting_label
        self.identifiers = ['COMMAND','INSERT']
        self.palettes = [
            [
                # COMMAND mode
                ('HEADER',     'white',     'black'),
                ('FOOTER_CMD', 'dark cyan', 'black')
            ],
            [
                # INSERT mode
                ('HEADER',        'white',     'dark magenta'),
                ('FOOTER_INFO_A', 'dark gray', 'light gray'),
                ('FOOTER_INFO_B', 'white',     'dark magenta'),
            ]
        ]
        self.settings = deque(zip(self.identifiers, self.palettes))

        if starting_label in self.identifiers:
            # rotate settings deque so ui initializes using mode specified by starting_label
            while self.settings[0][0] != starting_label:
                self.settings.rotate(1)

class TTY(Frame, urwid.curses_display.Screen):
    def __init__(self, Rec, starting_label):
        super(TTY, self).__init__(body=Content(Rec, starting_label),
                                  footer=WidgetPlaceholder(Edit('')))

        self.mode = Mode(starting_label)
        self._switcher = self._switch_generator()
        self.switch_mode()

    def __getitem__(self, item):
        accessible = {
            'content':self.body.base_widget,
            'footer':self.footer
        }
        return accessible[item]

    def switch_mode(self):
        """ Helper function so next() does not need to be used directly when switching modes """
        next(self._switcher)

    def _switch_generator(self):
        """ Infinite circular iterator used to flip back and forth between modes """
        # swap same objects in and out of footer so their values are preserved between swaps
        cmd_footer, info_footer = CmdFooter(), InfoFooter()

        for label, palette in itertools.cycle(self.mode.settings):
            self.mode.label = label
            self.register_palette( palette )
            self.body['header']['mode'].set_text(label)

            if label == 'COMMAND':
                self.body.base_widget.hide_keywords()
                self.footer.original_widget = AttrMap(cmd_footer, attr_map='FOOTER_CMD')
            elif label == 'INSERT':
                self.body.base_widget.show_keywords()
                self.footer.original_widget = AttrMap(info_footer, attr_map='FOOTER_INFO_B')
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

    def cmd_eval(self, size):
        """ Evaluates entries in cmd_footer """
        cmd = self.tty.footer.base_widget.edit_text
        self.tty.footer.base_widget.set_edit_text('')

        if cmd == ':q' or cmd == ':quit':
            [setattr(self, key, value) for key, value in self.dump().items()]
            return 0
        elif cmd == ':i' or cmd == ':insert':
            self.tty.switch_mode()
        elif cmd == ':n':
            self.tty.body.base_widget.goto_str(size, cmd[2:])
        else:
            if cmd == ':help':
                self.tty.footer.base_widget.set_edit_text('(:i)nsert, (:q)uit')
            else:
                self.tty.footer.base_widget.set_edit_text('Invalid command')
            self.tty.footer.base_widget.clear_before_keypress = True

    def ctrl_c_handler(self, sig, frame):
        self._force_exit = True

    def dump(self):
        return { 'title':self.tty['content']['header']['title'].edit_text,
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

                elif k == 'ctrl l':
                    self.tty.footer.base_widget.set_edit_text('')

                elif self.tty.mode.label == 'INSERT':
                    if k == 'esc':
                        self.tty.switch_mode()
                    else:
                        self.tty.keypress( size, k )

                elif self.tty.mode.label == 'COMMAND':
                    if k == 'enter':
                        eval_res = self.cmd_eval(size)
                        if  eval_res is None:
                            continue
                        elif eval_res == 0:
                            return

                    # allow scrolling of body text when not in INSERT mode
                    elif k == 'up' or k == 'down' and self.tty.focus_position == 'body':
                        self.tty.keypress(size, k)
                    else:
                        # send keypress to footer cmd input
                        self.tty.footer.base_widget.kpi((1, ), k)
