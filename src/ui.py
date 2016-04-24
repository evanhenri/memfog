import urwid.curses_display
import urwid
import signal
import os
import re

from . import link
from . import util
from . import file_io
from . import file_sys

class ModeLabel(urwid.Text):
    def __init__(self):
        super(ModeLabel, self).__init__(
            markup='',
            align='left'
        )


class Title(urwid.Edit):
    def __init__(self):
        super(Title, self).__init__(
            edit_text='',
            align='right'
        )


class Header(urwid.Columns):
    """ Container to hold ModeLabel and Title widgets """
    def __init__(self):
        palette_id = 'HEADER_BASE'
        super(Header, self).__init__(
            widget_list=[
                (urwid.AttrMap(ModeLabel(), palette_id)),
                (urwid.AttrMap(Title(), palette_id))
            ])

        self._attributes = {
            'label': self.widget_list[0].base_widget,
            'title': self.widget_list[-1].base_widget
        }
    def __getitem__(self, item):
        return self._attributes[item]


class Keywords(urwid.Edit):
    def __init__(self):
        super(Keywords, self).__init__(
            caption='Keywords: ',
            edit_text='',
            align='left',
            wrap='clip'
        )


class Body(urwid.Edit):
    def __init__(self):
        super(Body, self).__init__(
            edit_text='',
            align='left',
            multiline=True,
            allow_tab=True
        )
        self._attributes = {
            'text': self.edit_text
        }
    def __getitem__(self, item):
        return self._attributes[item]
    def __setitem__(self, key, value):
        self._attributes[key] = value


class CommandFooter(urwid.Edit):
    def __init__(self):
        super(CommandFooter, self).__init__(
            caption='> ',
            edit_text=''
        )
        self.palette_id = 'COMMAND_FOOTER_BASE'
        self.cmd_pattern = re.compile('(:.\S*)')
        self.clear_before_keypress = False
        self.cmd_history = util.BidirectionScrollList()

    def clear_text(self):
        self.set_edit_text('')
        self.cmd_history.reset()

    def cursor_left(self):
        self.set_edit_pos(self.edit_pos-1)

    def cursor_right(self):
        self.set_edit_pos(self.edit_pos+1)

    def cursor_home(self):
        self.set_edit_pos(0)

    def cursor_end(self):
        self.set_edit_pos(len(self.edit_text))

    def scroll_history_up(self):
        # Set to false so entered keypresses get appended to end of old command
        self.clear_before_keypress = False
        past_command = self.cmd_history.prev()
        if past_command is not None:
            self.set_edit_text(past_command)
        # Ensure new keypresses get appended to existing command footer text
        self.cursor_end()

    def scroll_history_down(self):
        # Set to false so entered keypresses get appended to end of old command
        self.clear_before_keypress = False
        past_command = self.cmd_history.next()
        if past_command is not None:
            self.set_edit_text(past_command)
        # Ensure new keypresses get appended to existing command footer text
        self.cursor_end()

    def keypress(self, size, key):
        if self.clear_before_keypress:
            self.clear_text()
            self.clear_before_keypress = False
        super(CommandFooter, self).keypress(size, key)


class InsertFooter(urwid.Columns):
    def __init__(self):
        self.palette_id = 'INSERT_FOOTER_BASE'
        palette_id = [self.palette_id, 'INSERT_FOOTER_HIGHLIGHT']
        super(InsertFooter, self).__init__(
            widget_list=[
                ('pack', urwid.AttrMap(urwid.Text(' ^C '), palette_id[0])),
                ('pack', urwid.AttrMap(urwid.Text('Exit'), palette_id[1])),
                ('pack', urwid.AttrMap(urwid.Text(' ESC '), palette_id[0])),
                ('pack', urwid.AttrMap(urwid.Text('Toggle Mode'), palette_id[1]))
            ])


class Content(urwid.ListBox):
    """ Container to hold header, keywords, and body widgets """
    def __init__(self):
        self.keyword_widget = Keywords()
        super(Content, self).__init__(
            body=urwid.SimpleFocusListWalker([
                Header(),
                urwid.Divider('-'),
                Body()
            ]))

        self._attributes = {
            'header': self.base_widget.body[0],
            'body':self.base_widget.body[-1],
        }

    def __getitem__(self, item):
        if item == 'keywords':
            # keyword widget would not be in ListBox if len(ListBox) == 3
            if len(self.base_widget.body) == 3:
                return self.keyword_widget
            # keyword widget is only present at index one (1) in INSERT mode
            return self.base_widget.body[1]
        return self._attributes[item]

    def keyword_widget_handler(self):
        interaction_mode = self['header']['label'].text
        switch = { 'INSERT':self._show_keywords, 'COMMAND':self._hide_keywords }
        switch[interaction_mode]()

    def _show_keywords(self):
        self.base_widget.body.insert(1, self.keyword_widget)
    def _hide_keywords(self):
        if len(self.base_widget.body) == 4:
            self.keyword_widget = self.base_widget.body.pop(1)


class Footer(urwid.WidgetPlaceholder):
    """ Container to hold whichever footer should be shown for current mode """
    def __init__(self):
        self._attributes = { 'COMMAND': CommandFooter(), 'INSERT': InsertFooter() }
        super(Footer, self).__init__(
            original_widget=urwid.Widget()
        )

    def set_mode(self, mode):
        footer_widget = self._attributes[mode]
        self.original_widget = urwid.AttrMap(footer_widget, attr_map=footer_widget.palette_id)


class ScreenAttributes:
    def __init__(self):
        self.palette = { 'INSERT':[ ('HEADER_BASE', 'white', 'dark magenta'),
                                    ('INSERT_FOOTER_HIGHLIGHT', 'dark gray', 'light gray'),
                                    ('INSERT_FOOTER_BASE', 'white', 'dark magenta') ],

                         'COMMAND':[ ('HEADER_BASE', 'white', 'black'),
                                     ('COMMAND_FOOTER_BASE', 'dark cyan', 'black') ] }


class ScreenController(urwid.curses_display.Screen):
    def __init__(self):
        super(ScreenController, self).__init__()
        self.attributes = ScreenAttributes()
        self.scroll_actions = {'up', 'down', 'page up', 'page down', 'scroll wheel up', 'scroll wheel down'}

    def set_palette_mode(self, mode):
        palette = self.attributes.palette.get(mode)
        if palette is not None:
            self.register_palette(palette)


class WidgetController(urwid.Frame):
    def __init__(self):
        super(WidgetController, self).__init__(body=Content(), footer=Footer())

    def __getitem__(self, item):
        if item == 'footer':
            return self.footer.base_widget
        return self.body[item]

    def dump(self):
        return {
            'title':self['header']['title'].edit_text,
            'keywords':self['keywords'].edit_text,
            'body':self['body'].edit_text
        }

    def update(self, data={}):
        if 'interaction_mode' in data:
            self['header']['label'].set_text(data['interaction_mode'])
            self.footer.set_mode(data['interaction_mode'])
        if 'title' in data:
            self['header']['title'].set_edit_text(data['title'])
        if 'keywords' in data:
            self['keywords'].set_edit_text(data['keywords'])
        if 'body' in data:
            self['body'].set_edit_text(data['body'])


class ViewData:
    def __init__(self, record):
        self.title = record.title
        self.keywords = record.keywords
        self.body = record.body
        self.starting_content_hash = self.content_hash()

    def content_hash(self):
        return hash(self.title + self.keywords + self.body)

    def dump(self):
        exclusions = { 'starting_content_hash' }
        return { k:v for k,v in self.__dict__.items() if k not in exclusions }

    def is_altered(self):
        return self.starting_content_hash != self.content_hash()

    def update(self, args):
        self.__dict__.update(args)


class DataController:
    def __init__(self, record):
        self.modes = ['COMMAND', 'INSERT', 'RAW', 'INTERPRETED']

        self.interaction_mode = ''
        self.view_mode = ''

        self.raw_view = ViewData(record)
        self.interpreted_view = ViewData(record)

        for k,v in self.interpreted_view.dump().items():
            setattr(self.interpreted_view, k, link.expand(v))

        self.is_interpreted = self.get('RAW') != self.get('INTERPRETED')

    def dump(self):
        return { 'RAW':self.get('RAW'), 'INTERPRETED':self.get('INTERPRETED') }

    def get(self, view_mode):
        switch = { 'RAW':self.raw_view.dump, 'INTERPRETED':self.interpreted_view.dump }
        return { **switch[view_mode](), **{'interaction_mode':self.interaction_mode} }

    def update(self, view_data):
        """
        Updates stored data to reflect view_data from Widgets
        If record data is not being interpreted, makes sure data from other views is kept in sync
        """
        if self.view_mode == 'RAW':
            self.raw_view.update(view_data)
            if not self.is_interpreted:
                self.interpreted_view = self.raw_view

        elif self.view_mode == 'INTERPRETED':
            self.interpreted_view.update(view_data)
            if not self.is_interpreted:
                self.raw_view = self.interpreted_view


class UI:
    def __init__(self, record, interaction_mode='COMMAND', view_mode='INTERPRETED'):
        signal.signal(signal.SIGINT, self._ctrl_c_callback)
        self.Screen = ScreenController()
        self.Data = DataController(record)
        self.Wigets = WidgetController()

        self._set_interaction_mode(interaction_mode)
        self._set_view_mode(view_mode)

        self._exit_flag = False
        self.db_update_required = False
        self.Screen.run_wrapper(self._run)

    def _set_interaction_mode(self, mode_id):
        self.Data.interaction_mode = mode_id
        self.Screen.set_palette_mode(mode_id)
        self.Wigets.update({'interaction_mode':mode_id})
        self.Wigets.body.keyword_widget_handler()

    def _set_view_mode(self, mode_id):
        # Save text from current view before changing widget text
        self.Data.update(self.Wigets.dump())
        self.Data.view_mode = mode_id
        self.Wigets.update(self.Data.get(mode_id))

    def _safe_exit(self):
        self._exit_flag = True
        self.Data.update(self.Wigets.dump())

        if self.Data.is_interpreted:
            if self.Data.interpreted_view.is_altered():
                tag, value = link.extract(self.Data.raw_view.body)
                if tag == 'PATH':
                    # Write changes to linked file
                    file_io.str_to_file(value, self.Data.interpreted_view.body)
        # If uninterpreted, all view data has been kept in sync.
        # If interpreted, changes to the raw record have been made.
        # Both circumstances require an update to be made in the record database
        self.db_update_required = self.Data.raw_view.is_altered()

    def _ctrl_c_callback(self, sig, frame):
        self._safe_exit()

    def _export(self, fp, content):
        default_dp = os.getcwd()
        default_fn = (content['title']).replace(' ', '_')
        fp = file_sys.fix_path(fp, default_dp, default_fn)

        if not file_sys.check_path('w', fp):
            return 'Unable to export to \'{}\''.format(fp)
        file_io.json_to_file(fp, self.Wigets.dump())
        return 'Exported to \'{}\''.format(fp)

    def _evaluate_command(self, cmd_text):
        if len(cmd_text) > 0:
            self.Wigets['footer'].cmd_history.append(cmd_text)

            # extract :command pattern from cmd input field
            cmd = self.Wigets['footer'].cmd_pattern.search(cmd_text)

            if cmd is not None:
                cmd = cmd.group(0)
                args = cmd_text.split(' ', 1)[-1].strip()

                if cmd == ':e' or cmd == ':export':
                    # If no filename/path was given, clear string to trigger default to be set in _export()
                    if args.startswith(cmd): args = ''
                    result = self._export(args, self.Wigets.dump())
                    self.Wigets['footer'].set_edit_text(result)

                elif cmd == ':h' or cmd == ':help':
                    self.Wigets['footer'].set_edit_text('[:e]xport <path>, [:i]nsert, [:q]uit, [:v]iew <mode>')

                elif cmd == ':i' or cmd == ':insert':
                    self.Wigets['footer'].set_edit_text('')
                    self._set_interaction_mode('INSERT')

                elif cmd == ':q' or cmd == ':quit':
                    self._safe_exit()

                elif cmd == ':v' or cmd == ':view':
                    try:
                        self._set_view_mode(args.upper())
                    except KeyError:
                        self.Wigets['footer'].set_edit_text('Valid views = \'raw\',\'interpreted\''.format(args))
            else:
                self.Wigets['footer'].set_edit_text('Invalid command')

    def _run(self):
        size = self.Screen.get_cols_rows()

        while not self._exit_flag:
            canvas = self.Wigets.render(size, focus=True)
            self.Screen.draw_screen(size, canvas)
            keys = None

            while not keys:
                keys = self.Screen.get_input()

            for k in keys:
                if k == 'window resize':
                    size = self.Screen.get_cols_rows()

                elif k == 'ctrl c':
                    self._safe_exit()

                elif k in self.Screen.scroll_actions and self.Wigets.focus_position == 'body':
                    self.Wigets.keypress(size, k)

                elif self.Data.interaction_mode == 'INSERT':
                    if k == 'esc':
                        self._set_interaction_mode('COMMAND')
                    else:
                        self.Wigets.keypress(size, k)

                elif self.Data.interaction_mode == 'COMMAND':
                    if k == 'ctrl l':
                        self.Wigets['footer'].clear_text()
                    elif k == 'enter':
                        cmd_text = self.Wigets['footer'].get_edit_text()
                        self.Wigets['footer'].clear_text()
                        self._evaluate_command(cmd_text)
                        # if error results from entered command, clear error message before next keystroke appears
                        self.Wigets['footer'].clear_before_keypress = True
                    elif k == 'shift up':
                        self.Wigets['footer'].scroll_history_up()
                    elif k == 'shift down':
                        self.Wigets['footer'].scroll_history_down()
                    elif k == 'left':
                        self.Wigets['footer'].cursor_left()
                    elif k == 'right':
                        self.Wigets['footer'].cursor_right()
                    elif k == 'home':
                        self.Wigets['footer'].cursor_home()
                    elif k == 'end':
                        self.Wigets['footer'].cursor_end()
                    else:
                        self.Wigets['footer'].keypress((1,), k)
