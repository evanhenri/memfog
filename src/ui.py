import urwid.curses_display
import urwid
import os
import re

from . import link
from .util import BidirectionScrollList


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
            caption='',
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
        self.cmd_history = BidirectionScrollList()

    def clear_text(self):
        self.set_edit_text('')

    def scroll_history_up(self):
        past_command = self.cmd_history.prev()
        if past_command is not None:
            self.set_edit_text(past_command)

    def scroll_history_down(self):
        past_command = self.cmd_history.next()
        if past_command is not None:
            self.set_edit_text(past_command)

    def keypress(self, size, key):
        if self.clear_before_keypress:
            self.clear_before_keypress = False
            self.set_edit_text('')

        super(CommandFooter, self).keypress(size, key)


class InsertFooter(urwid.Columns):
    def __init__(self):
        self.palette_id = 'INSERT_FOOTER_BASE'
        palette_id = [self.palette_id, 'INSERT_FOOTER_HIGHLIGHT']
        super(InsertFooter, self).__init__(
            widget_list=[
                ('pack', urwid.AttrMap(urwid.Text('^X'), palette_id[0])),
                ('pack', urwid.AttrMap(urwid.Text(' Exit  '), palette_id[1])),
                ('pack', urwid.AttrMap(urwid.Text('ESC'), palette_id[0])),
                ('pack', urwid.AttrMap(urwid.Text(' Toggle Mode  '), palette_id[1]))
            ])


class Content(urwid.ListBox):
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

    def show_keywords(self):
        self.base_widget.body.insert(1, self.keyword_widget)
    def hide_keywords(self):
        self.keyword_widget = self.base_widget.body.pop(1)


class Footer(urwid.WidgetPlaceholder):
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
    def __init__(self, mode):
        super(ScreenController, self).__init__()
        self.attributes = ScreenAttributes()
        self.register_palette( self.attributes.palette[mode] )


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
            'mode':self['header']['label'].text,
            'title':self['header']['title'].text,
            'keywords':self['keywords'].text,
            'body':self['body'].text
        }

    def update(self, data={}):
        self['header']['label'].set_text(data['interaction_mode'])
        self['header']['title'].set_edit_text(data['title'])
        self['keywords'].set_edit_text(data['keywords'])
        self['body'].set_edit_text(data['body'])
        self.footer.set_mode(data['interaction_mode'])


class DataController:
    def __init__(self, record, interaction_mode, view_mode):
        self.modes = ['COMMAND', 'INSERT', 'RAW', 'INTERPRET']
        self.interaction_mode = interaction_mode
        self.view_mode = view_mode

        self.data = {
            'RAW':{
                'title':record.title,
                'keywords':record.keywords,
                'body':record.body
            },
            'INTERPRET':{
                'title':link.expand(record.title),
                'keywords':link.expand(record.keywords),
                'body':link.expand(record.body)
            }
        }

        self.interpretted = self.data['RAW'] != self.data['INTERPRET']


    def dump(self, data_type=None):
        if data_type is None:
            return self.data
        return { **self.data[self.view_mode], 'interaction_mode':self.interaction_mode }


class UI:
    def __init__(self, record, interaction_mode='COMMAND', view_mode='INTERPRET'):
        self.Screen = ScreenController(interaction_mode)
        self.Data = DataController(record, interaction_mode, view_mode)
        self.Wigets = WidgetController()
        self.Wigets.update(self.Data.dump(view_mode))

        urwid.register_signal(DataController, self.Data.modes)
        urwid.connect_signal(self.Data, 'COMMAND', self._set_interaction_mode, 'COMMAND')
        urwid.connect_signal(self.Data, 'INSERT', self._set_interaction_mode, 'INSERT')

        self.altered = False
        self._quit_flag = False
        self.Screen.run_wrapper(self._run)

    def _set_interaction_mode(self, mode_id):
        self.Data.interaction_mode = mode_id
        self.Screen.set_palette_mode(mode_id)
        self.Wigets.footer.set_mode(mode_id)

    def _set_view_mode(self, mode_id):
        self.Data.view_mode = mode_id
        self.Wigets.update(self.Data.dump(mode_id))

    #def _safe_exit(self):

    def _evaluate_command(self, cmd_text):
        if len(cmd_text) > 0:
            self.Wigets['footer'].cmd_history.append(cmd_text)

            # extract :command pattern from cmd input field
            cmd = self.Wigets['footer'].cmd_pattern.search(cmd_text)

            if cmd is not None:
                cmd = cmd.group(0)
                args = cmd_text.split(' ', 1)[-1].strip()

                if cmd == ':e' or cmd == ':export':
                    # Use current working directory if no export argument was provided as argument
                    if args.startswith(cmd):
                        args = os.getcwd()
                    self.Wigets['footer'].set_edit_text('Exported to {}'.format(args))

                elif cmd == ':h' or cmd == ':help':
                    self.Wigets['footer'].set_edit_text('(:i)nsert, (:q)uit')

                elif cmd == ':i' or cmd == ':insert':
                    self.Wigets['footer'].set_edit_text('')
                    urwid.emit_signal(self.Data, 'INSERT')

                elif cmd == ':q' or cmd == ':quit':
                    self._quit_flag = True

                elif cmd == ':v' or cmd == ':view':
                    try:
                        self._set_view_mode(args.upper())
                    except KeyError:
                        self.Wigets['footer'].set_edit_text('Invalid view mode \'{}\''.format(args))
            else:
                self.Wigets['footer'].set_edit_text('Invalid command')

    def _run(self):
        size = self.Screen.get_cols_rows()

        while True:
            if self._quit_flag:
                return

            canvas = self.Wigets.render(size, focus=True)
            self.Screen.draw_screen(size, canvas)
            keys = None

            while not keys:
                keys = self.Screen.get_input()

            for k in keys:
                if k == 'window resize':
                    size = self.Screen.get_cols_rows()

                elif k == 'ctrl x':
                    return

                elif k == 'ctrl l':
                    self.Wigets['footer'].clear_text()

                elif self.Data.interaction_mode == 'INSERT':
                    if k == 'esc':
                        urwid.emit_signal(self.Data, 'COMMAND')
                    else:
                        self.Wigets.keypress(size, k)
                        self.altered = True

                elif self.Data.interaction_mode == 'COMMAND':
                    if k == 'enter':
                        cmd_text = self.Wigets['footer'].get_edit_text()
                        self.Wigets['footer'].clear_text()

                        self._evaluate_command(cmd_text)
                        # if error results from entered command, clear error message before next keystroke appears
                        self.Wigets['footer'].clear_before_keypress = True

                    elif k == 'shift up':
                        self.Wigets['footer'].scroll_history_up()
                    elif k == 'shift down':
                        self.Wigets['footer'].scroll_history_down()

                #     elif k in scroll_actions and self.tty.focus_position == 'body':
                #         self.tty.keypress(size, k)
                    else:
                        self.Wigets['footer'].keypress((1,), k)
