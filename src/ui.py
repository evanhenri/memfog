import urwid.curses_display
import urwid
import signal
import os
import re


from . import util
from . import file_io
from . import file_sys
from .data import Data

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
        self.cmd_history = util.UniqueNeighborScrollList()

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
        switch = { 'INSERT':self.show_keywords, 'COMMAND':self.hide_keywords }
        switch[interaction_mode]()

    def show_keywords(self):
        self.base_widget.body.insert(1, self.keyword_widget)
    def hide_keywords(self):
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

    def set_widget_text(self, data={}):
        if 'interaction_mode' in data:
            self['header']['label'].set_text(data['interaction_mode'])
            self.footer.set_mode(data['interaction_mode'])
        if 'title' in data:
            self['header']['title'].set_edit_text(data['title'])
        if 'keywords' in data:
            self['keywords'].set_edit_text(data['keywords'])
        if 'body' in data:
            self['body'].set_edit_text(data['body'])


class DataController:
    def __init__(self, record):
        self.data = Data(record)
        self.interaction_mode = ''
        self.view_mode = ''

    def dump(self):
        return { 'RAW':self.get_view('RAW'), 'INTERPRETED':self.get_view('INTERPRETED') }

    def get_view(self, view_mode):
        switch = { 'RAW':self.data.raw.dump, 'INTERPRETED':self.data.interpreted.dump }
        return { **switch[view_mode](), **{'interaction_mode':self.interaction_mode} }

    def save_view(self, view_data):
        """
        Updates stored data to reflect view_data from Widgets
        If record data is not being interpreted, makes sure data from other views is kept in sync
        """
        if self.view_mode == 'RAW':
            self.data.raw.update_fields(view_data)
            if not self.data.is_interpreted:
                self.data.interpreted = self.data.raw

        elif self.view_mode == 'INTERPRETED':
            self.data.interpreted.update_fields(view_data)
            if not self.data.is_interpreted:
                self.data.raw = self.data.interpreted


class UI:
    def __init__(self, context, msg_queue):
        signal.signal(signal.SIGINT, self.ctrl_c_callback)
        self.exit_flag = False

        self.context = context
        self.msg_queue = msg_queue

        self.ScreenC = ScreenController()
        self.DataC = DataController(context.record)
        self.WigetC = WidgetController()

        self.set_interaction_mode(context.interaction_mode)
        self.set_view_mode(context.view_mode)

        self.ScreenC.run_wrapper(self.run)

    def set_interaction_mode(self, mode_id):
        self.DataC.interaction_mode = mode_id
        self.ScreenC.set_palette_mode(mode_id)
        self.WigetC.set_widget_text({'interaction_mode':mode_id})
        self.WigetC.body.keyword_widget_handler()

    def set_view_mode(self, mode_id):
        # Save text from current view before changing widget text
        self.DataC.save_view(self.WigetC.dump())
        self.DataC.view_mode = mode_id
        self.WigetC.set_widget_text(self.DataC.get_view(mode_id))

    def safe_exit(self):
        self.exit_flag = True
        self.DataC.save_view(self.WigetC.dump())

        if self.DataC.data.is_interpreted:
            self.DataC.data.update_interpreted_sources()

        context = self.DataC.data.update_record_context(self.context)
        self.msg_queue.put(context)

        # Block until context put into queue is fully processed.
        # Race condition occurs when adding new records if not present
        self.msg_queue.join()

    def ctrl_c_callback(self, sig, frame):
        self.safe_exit()

    def export(self, fp, content):
        default_dp = os.getcwd()
        default_fn = (content['title']).replace(' ', '_')
        fp = file_sys.fix_path(fp, default_dp, default_fn)

        if not file_sys.check_path('w', fp):
            return 'Unable to export to \'{}\''.format(fp)
        file_io.json_to_file(fp, self.WigetC.dump())
        return 'Exported to \'{}\''.format(fp)

    def evaluate_command(self, cmd_text):
        if len(cmd_text) > 0:
            self.WigetC['footer'].cmd_history.append(cmd_text)

            # extract :command pattern from cmd input field
            cmd = self.WigetC['footer'].cmd_pattern.search(cmd_text)

            if cmd is not None:
                cmd = cmd.group(0)
                args = cmd_text.split(' ', 1)[-1].strip()

                if cmd == ':e' or cmd == ':export':
                    # If no filename/path was given, clear string to trigger default to be set in _export()
                    if args.startswith(cmd): args = ''
                    result = self.export(args, self.WigetC.dump())
                    self.WigetC['footer'].set_edit_text(result)

                elif cmd == ':h' or cmd == ':help':
                    self.WigetC['footer'].set_edit_text('[:e]xport <path>, [:i]nsert, [:q]uit, [:v]iew <mode>')

                elif cmd == ':i' or cmd == ':insert':
                    self.WigetC['footer'].set_edit_text('')
                    self.set_interaction_mode('INSERT')

                elif cmd == ':q' or cmd == ':quit':
                    self.safe_exit()

                elif cmd == ':v' or cmd == ':view':
                    try:
                        self.set_view_mode(args.upper())
                    except KeyError:
                        self.WigetC['footer'].set_edit_text('Valid views = \'raw\',\'interpreted\''.format(args))
                else:
                    self.WigetC['footer'].set_edit_text('Invalid command')
            else:
                self.WigetC['footer'].set_edit_text('Invalid command')


    def run(self):
        size = self.ScreenC.get_cols_rows()

        while not self.exit_flag:
            canvas = self.WigetC.render(size, focus=True)
            self.ScreenC.draw_screen(size, canvas)
            keys = None

            while not keys:
                keys = self.ScreenC.get_input()

            for k in keys:
                if k == 'window resize':
                    size = self.ScreenC.get_cols_rows()

                elif k == 'ctrl c':
                    self.safe_exit()

                elif k in self.ScreenC.scroll_actions and self.WigetC.focus_position == 'body':
                    self.WigetC.keypress(size, k)

                elif self.DataC.interaction_mode == 'INSERT':
                    if k == 'esc':
                        self.set_interaction_mode('COMMAND')
                    else:
                        self.WigetC.keypress(size, k)

                elif self.DataC.interaction_mode == 'COMMAND':
                    if k == 'ctrl l':
                        self.WigetC['footer'].clear_text()
                    elif k == 'enter':
                        cmd_text = self.WigetC['footer'].get_edit_text()
                        self.WigetC['footer'].clear_text()
                        self.evaluate_command(cmd_text)
                        # if error results from entered command, clear error message before next keystroke appears
                        self.WigetC['footer'].clear_before_keypress = True
                    elif k == 'shift up':
                        self.WigetC['footer'].scroll_history_up()
                    elif k == 'shift down':
                        self.WigetC['footer'].scroll_history_down()
                    elif k == 'left':
                        self.WigetC['footer'].cursor_left()
                    elif k == 'right':
                        self.WigetC['footer'].cursor_right()
                    elif k == 'home':
                        self.WigetC['footer'].cursor_home()
                    elif k == 'end':
                        self.WigetC['footer'].cursor_end()
                    else:
                        self.WigetC['footer'].keypress((1,), k)
