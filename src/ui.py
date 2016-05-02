import urwid.curses_display
import urwid
import re

from . import util
from . import file_io
from . import file_sys
from .data import Data
from .proxy import Flags
from . import memfog


class InteractionLabel(urwid.Text):
    def __init__(self):
        super(InteractionLabel, self).__init__(
            markup='',
            align='left'
        )


class ViewLabel(urwid.Text):
    def __init__(self):
        super(ViewLabel, self).__init__(
            markup='',
            align='left'
        )


class TitleWidget(urwid.Edit):
    def __init__(self):
        super(TitleWidget, self).__init__(
            edit_text='',
            align='right'
        )


class HeaderWidget(urwid.Columns):
    """ Container to hold ModeLabel and Title widgets """
    def __init__(self):
        palette_id = 'HEADER_BASE'
        self.interaction = InteractionLabel()
        self.view = ViewLabel()
        self.title = TitleWidget()

        super(HeaderWidget, self).__init__(
            widget_list=[
                ('pack',urwid.AttrMap(self.interaction, palette_id)),
                ('pack', urwid.AttrMap(urwid.Text(' / '), palette_id)),
                ('pack',urwid.AttrMap(self.view, palette_id)),
                (urwid.AttrMap(self.title, palette_id))
            ])


class KeywordsWidget(urwid.Edit):
    def __init__(self):
        super(KeywordsWidget, self).__init__(
            caption='Keywords: ',
            edit_text='',
            align='left',
            wrap='clip'
        )


class BodyWidget(urwid.Edit):
    def __init__(self):
        super(BodyWidget, self).__init__(
            edit_text='',
            align='left',
            multiline=True,
            allow_tab=True
        )


class Content(urwid.ListBox):
    """ Container to hold header, keywords, and body widgets """
    def __init__(self):
        self.header = HeaderWidget()
        self.keywords = KeywordsWidget()
        self.record_body = BodyWidget()

        super(Content, self).__init__(
            body=urwid.SimpleFocusListWalker([
                self.header,
                urwid.Divider('-'),
                self.record_body
            ]))

    def keyword_widget_handler(self):
        interaction_mode = self.header.interaction.text
        switch = { 'INSERT':self.show_keywords, 'COMMAND':self.hide_keywords }
        switch[interaction_mode]()

    def show_keywords(self):
        self.base_widget.body.insert(1, self.keywords)

    def hide_keywords(self):
        if len(self.base_widget.body) == 4:
            self.keywords = self.base_widget.body.pop(1)


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
                ('pack', urwid.AttrMap(urwid.Text(' ^X '), palette_id[0])),
                ('pack', urwid.AttrMap(urwid.Text('Exit'), palette_id[1])),
                ('pack', urwid.AttrMap(urwid.Text(' ESC '), palette_id[0])),
                ('pack', urwid.AttrMap(urwid.Text('Toggle Mode'), palette_id[1]))
            ])


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


class ScreenController(urwid.curses_display.Screen):
    def __init__(self):
        super(ScreenController, self).__init__()
        self.palettes = {'INSERT': [('HEADER_BASE', 'white', 'dark magenta'),
                                    ('INSERT_FOOTER_HIGHLIGHT', 'dark gray', 'light gray'),
                                    ('INSERT_FOOTER_BASE', 'white', 'dark magenta')],
                         'COMMAND': [('HEADER_BASE', 'white', 'black'),
                                     ('COMMAND_FOOTER_BASE', 'dark cyan', 'black')]}

        self.scroll_actions = {'up', 'down', 'page up', 'page down', 'scroll wheel up', 'scroll wheel down'}

    def set_palette_mode(self, mode):
        self.register_palette(self.palettes[mode])


class WidgetController(urwid.Frame):
    def __init__(self):
        super(WidgetController, self).__init__(body=Content(), footer=Footer())

    def dump(self):
        return {
            'title':self.body.header.title.edit_text,
            'keywords':self.body.keywords.edit_text,
            'body':self.body.record_body.edit_text
        }

    def set_widget_text(self, args):
        """
        :type args: dict
        :param args: { widget_name1:new_text, widget_name2:new_text, ... }
        Assigns text to widget for key(widget name) value(text) pair in args
        """
        if 'interaction_mode' in args:
            self.body.header.interaction.set_text(args['interaction_mode'])
            self.footer.set_mode(args['interaction_mode'])
        if 'view_mode' in args:
            self.body.header.view.set_text(args['view_mode'])
        if 'title' in args:
            self.body.header.title.set_edit_text(args['title'])
        if 'keywords' in args:
            self.body.keywords.set_edit_text(args['keywords'])
        if 'body' in args:
            self.body.record_body.set_edit_text(args['body'])


class DataController:
    def __init__(self, record):
        self.data = Data(record)
        self.interaction_mode = ''
        self.view_mode = ''

    def dump(self):
        return { 'RAW':self.get_view('RAW'), 'INTERPRETED':self.get_view('INTERPRETED') }

    def get_view(self, view_mode):
        switch = { 'RAW':self.data.raw.dump, 'INTERPRETED':self.data.interpreted.dump }
        return { **switch[view_mode](), **{'interaction_mode':self.interaction_mode, 'view_mode':self.view_mode} }

    def save_view(self, view_data):
        """
        Updates stored data to reflect view_data from Widgets
        If record data is not being interpreted, makes sure data from other views is kept in sync
        """
        if self.view_mode == 'RAW':
            self.data.raw.update_text(view_data)
            if not self.data.is_interpreted:
                self.data.interpreted = self.data.raw

        elif self.view_mode == 'INTERPRETED':
            self.data.interpreted.update_text(view_data)
            if not self.data.is_interpreted:
                self.data.raw = self.data.interpreted


class UI:
    def __init__(self, context, msg_queue):
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

    def update_context(self):
        self.DataC.save_view(self.WigetC.dump())
        return self.DataC.data.update_record_context(self.context)

    def save(self, context):
        """ Update database entry for current record using most recent record data """
        self.msg_queue.put(context)

        if self.DataC.data.is_interpreted:
            self.DataC.data.update_interpreted_sources()

        # Block until context put into queue is fully processed.
        # Race condition occurs when adding new records if not present
        self.msg_queue.join()

    def export(self, fp, payload):
        """ Creates json file at filepath fp containing data for currently displayed record """
        default_dp = memfog.config.project_dp
        default_fn = (payload['title']).replace(' ', '_')
        fp = file_sys.fix_path(fp, default_dp, default_fn)
        return file_io.json_to_file(fp, self.WigetC.dump())

    def evaluate_command(self, cmd_text):
        if len(cmd_text) > 0:
            self.WigetC.footer.base_widget.cmd_history.append(cmd_text)

            # extract :command pattern from cmd input field
            cmd = self.WigetC.footer.base_widget.cmd_pattern.search(cmd_text)

            if cmd is not None:
                cmd = cmd.group(0)
                args = cmd_text.split(' ', 1)[-1].strip()

                if cmd == ':e' or cmd == ':export':
                    # If no filename/path was given, clear string to trigger default to be set in _export()
                    if args.startswith(cmd): args = ''
                    result = self.export(args, self.WigetC.dump())
                    self.WigetC.footer.base_widget.set_edit_text(result)

                elif cmd == ':h' or cmd == ':help':
                    self.WigetC.footer.base_widget.set_edit_text(':export <path>, :insert, :quit, :refresh, :save, :view <mode>')

                elif cmd == ':i' or cmd == ':insert':
                    self.WigetC.footer.base_widget.set_edit_text('')
                    self.set_interaction_mode('INSERT')

                elif cmd == ':q' or cmd == ':quit':
                    self.exit_flag = True

                elif cmd == ':s' or cmd == ':save':
                    context = self.update_context()
                    self.save(context)
                    self.WigetC.footer.base_widget.set_edit_text('Record Saved')

                elif cmd == ':r' or cmd == ':refresh':
                    self.DataC.save_view(self.WigetC.dump())
                    self.DataC.data.refresh_interpretation()
                    self.WigetC.set_widget_text(self.DataC.get_view(self.DataC.view_mode))

                elif cmd == ':v' or cmd == ':view':
                    try:
                        self.set_view_mode(args.upper())
                    except KeyError:
                        self.WigetC.footer.base_widget.set_edit_text('Valid views = \'raw\',\'interpreted\''.format(args))
                else:
                    self.WigetC.footer.base_widget.set_edit_text('Invalid command')
            else:
                self.WigetC.footer.base_widget.set_edit_text('Invalid command')

    def evaluate_keypress(self, k):
        if k == 'ctrl l':
            self.WigetC.footer.base_widget.clear_text()
        elif k == 'enter':
            cmd_text = self.WigetC.footer.base_widget.get_edit_text()
            self.WigetC.footer.base_widget.clear_text()
            self.evaluate_command(cmd_text)
            # if error results from entered command, clear error message before next keystroke appears
            self.WigetC.footer.base_widget.clear_before_keypress = True
        elif k == 'shift up':
            self.WigetC.footer.base_widget.scroll_history_up()
        elif k == 'shift down':
            self.WigetC.footer.base_widget.scroll_history_down()
        elif k == 'left':
            self.WigetC.footer.base_widget.cursor_left()
        elif k == 'right':
            self.WigetC.footer.base_widget.cursor_right()
        elif k == 'home':
            self.WigetC.footer.base_widget.cursor_home()
        elif k == 'end':
            self.WigetC.footer.base_widget.cursor_end()
        else:
            self.WigetC.footer.base_widget.keypress((1,), k)

    def refresh_screen(self, size):
        canvas = self.WigetC.render(size, focus=True)
        self.ScreenC.draw_screen(size, canvas)

    def run(self):
        size = self.ScreenC.get_cols_rows()

        while not self.exit_flag:
            self.refresh_screen(size)
            keys = None

            while not keys:
                try:
                    keys = self.ScreenC.get_input()
                except KeyboardInterrupt:
                    return

            for k in keys:
                if k == 'window resize':
                    size = self.ScreenC.get_cols_rows()

                elif k == 'ctrl x':
                    self.exit_flag = True

                elif k in self.ScreenC.scroll_actions and self.WigetC.focus_position == 'body':
                    self.WigetC.keypress(size, k)

                elif self.DataC.interaction_mode == 'INSERT':
                    if k == 'esc':
                        self.set_interaction_mode('COMMAND')
                    else:
                        self.WigetC.keypress(size, k)

                elif self.DataC.interaction_mode == 'COMMAND':
                    self.evaluate_keypress(k)

        # Force switch to COMMAND mode so command line footer can prompt user if unsaved changes exist
        self.set_interaction_mode('COMMAND')
        context = self.update_context()

        if len(context.altered_fields) > 0:
            self.WigetC.footer.base_widget.set_edit_text('Save change? y/n')

            # refresh so message prompt is drawn to canvas
            self.refresh_screen(size)
            k = self.ScreenC.get_input()
            if k[0].lower() == 'y':
                self.save(context)
