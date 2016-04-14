from urwid import AttrMap, Columns, Divider, Edit, Frame, ListBox, Text, SimpleFocusListWalker, WidgetPlaceholder
import urwid.curses_display
from collections import deque
from enum import Enum
import itertools
import signal
import os
import re

from . import file_io, file_sys
from .util import BidirectionScrollList


class Header(Columns):
    """ Contains widgets for header elements (used in Content class) which include
        the title of the record and the label displaying the current ui mode """
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
    """ Contains widgets containing mutable record data elements which include
        the header, keywords, and body widgets. Widgets are stored in ListBox
        at the following indicies: 0:header 1: horizontal divider 2:body. Note - body is
        at index 1 when mode=COMMAND and 2 when mode=INSERT as keyword widget
        is inserted at and removed from index 1 to simulate showing/hiding when
        switching between modes """
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
        """ Removes keywords widget from Content ListBox which is at index 1 """
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
    """ Footer class used when ui is in INSERT mode - displays keyboard shortcuts """
    def __init__(self):
        self.widgets = [
            ('pack', AttrMap(Text('^X'), 'FOOTER_INFO_A')),
            ('pack', AttrMap(Text(' Exit  '), 'FOOTER_INFO_B')),
            ('pack', AttrMap(Text('ESC'), 'FOOTER_INFO_A')),
            ('pack', AttrMap(Text(' Toggle Mode  '), 'FOOTER_INFO_B')),
        ]
        super(InfoFooter, self).__init__(self.widgets)


class CmdAction(Enum):
    """ Contains enumerated meanings to outcomes certain cmd input entries whose action
     cannot be called from the CmdFooter class """
    QUIT = 0
    SWITCHMODE = 1
    EXPORT = 2

class CmdFooter(Edit):
    """ Footer class used when ui is in COMMAND mode - provides a command entry field """
    def __init__(self):
        super(CmdFooter, self).__init__(caption='> ')
        self.clear_before_keypress = False
        # extract :<command> substring from cmd field
        self._pattern = re.compile('(:.\S*)')
        self._history = BidirectionScrollList()

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

    def cmd_eval(self, size):
        """
        :returns a tuple as (flag to trigger call to action, field to hold text entry widget text)
        :returns None if the text in cmd footer does not match any available command
        Evaluates cmd footer text entries.
        """
        # cmd input field should be cleared before next user key stroke gets displayed
        self.clear_before_keypress = True
        valid_cmd = {':i', ':insert', ':e', ':export', ':h', ':help', ':q', ':quit'}

        if len(self.edit_text) > 0:
            self._history.append(self.edit_text)

        # extract :command pattern from cmd input field
        cmd = self._pattern.search(self.edit_text)

        if cmd is None or cmd.group(0) not in valid_cmd:
            if len(self.edit_text) > 0:
                self.set_edit_text('Invalid command')
            return

        cmd = cmd.group(0)
        args = self.edit_text.split(' ', 1)[-1].strip()

        if cmd == ':i' or cmd == ':insert':
            return CmdAction.SWITCHMODE, 1
        elif cmd == ':e' or cmd == ':export':
            # if no export path follows export command - no space to split on
            if args.startswith(cmd): args = os.getcwd()
            self.set_edit_text('Exported to {}'.format(args))
            return CmdAction.EXPORT, args
        elif cmd == ':h' or cmd == ':help':
            self.set_edit_text('(:i)nsert, (:q)uit')
        elif cmd == ':q' or cmd == ':quit':
            return CmdAction.QUIT, 0

    def empty(self):
        return len(self.edit_text) == 0

    def scroll_history_up(self):
        historic_cmd_entry = self._history.prev()
        if historic_cmd_entry is not None:
            self.set_edit_text(historic_cmd_entry)

    def scroll_history_down(self):
        historic_cmd_entry = self._history.next()
        if historic_cmd_entry is not None:
            self.set_edit_text(historic_cmd_entry)


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
    """ Facilitates core UI functionality by serving as base screen that all other widgets are placed """
    def __init__(self, Rec, starting_label):
        super(TTY, self).__init__(body=Content(Rec, starting_label), footer=WidgetPlaceholder(Edit('')))

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
    """ User facing class to launch command line interface. Initialization
        defaults to COMMAND mode unless a new record is being created in which UI is set to
        INSERT mode """
    def __init__(self, Rec, start_mode='COMMAND'):
        signal.signal(signal.SIGINT, self.ctrl_c_handler)
        self._force_exit = False
        self.tty = TTY(Rec, start_mode)
        self.starting_values = Rec.dump()
        self.tty.run_wrapper( self._run )

    def altered(self):
        """ Returns True if any values in Rec have been changed """
        return self.starting_values != self.dump()

    def ctrl_c_handler(self, sig, frame):
        """ Callback to set flag when ctrl-c is entered. When flag is set, current record is updated before
            exiting out of the ui """
        self._force_exit = True

    def dump(self):
        """ Used to retrieve record elements relevant to record data members """
        return { 'title':self.tty['content']['header']['title'].edit_text,
                 'keywords':self.tty['content']['keywords'].edit_text,
                 'body':self.tty['content']['body'].edit_text }

    def _export_to_file(self, export_path):
        [setattr(self, key, value) for key, value in self.dump().items()]
        default_filename = getattr(self, 'title').replace(' ', '_')
        target_path = os.getcwd() + '/' + default_filename

        # check if path to file pending export has been included in export_path
        if file_sys.check_path('w', export_path):
            target_path = export_path

        # check if path to directory to export into has been included in export_path
        else:
            if not export_path.endswith('/'):
                export_path += '/'
            if file_sys.check_path('w', export_path, default_filename):
                target_path = export_path + default_filename

        file_io.json_to_file(target_path, self.dump())
        self.tty.footer.base_widget.set_edit_text('Exported to ' + target_path)

    def _run(self):
        size = self.tty.get_cols_rows()
        scroll_actions = {'up', 'down', 'page up', 'page down', 'scroll wheel up', 'scroll wheel down'}

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
                    if k == 'enter' and not self.tty.footer.base_widget.empty():
                        eval_res = self.tty.footer.base_widget.cmd_eval(size)

                        # if valid cmd entry was entered
                        if  eval_res is not None:
                            if eval_res[0] == CmdAction.QUIT:
                                [setattr(self, key, value) for key, value in self.dump().items()]
                                return

                            elif eval_res[0] == CmdAction.SWITCHMODE:
                                self.tty.switch_mode()

                            elif eval_res[0] == CmdAction.EXPORT:
                                self._export_to_file(eval_res[1])

                    elif k == 'shift up':
                        self.tty.footer.base_widget.scroll_history_up()
                    elif k == 'shift down':
                        self.tty.footer.base_widget.scroll_history_down()
                    elif k in scroll_actions and self.tty.focus_position == 'body':
                        self.tty.keypress(size, k)
                    else:
                        # send keypress to footer cmd input
                        self.tty.footer.base_widget.kpi((1, ), k)
