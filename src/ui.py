import urwid.curses_display
import urwid
import os
import re

from . import link

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
        self.cmd_history = []

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

############################3

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
            if len(self.base_widget.body) == 3:
                return self.keyword_widget
            return self.base_widget.body[1]
        else:
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

############################3

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

############################3

class WidgetController(urwid.Frame):
    def __init__(self, data={}):
        super(WidgetController, self).__init__(body=Content(), footer=Footer())
        self['header']['label'].set_text(data['mode'])
        self['header']['title'].set_edit_text(data['title'])
        self['keywords'].set_edit_text(data['keywords'])
        self['body'].set_edit_text(data['body'])
        self.footer.set_mode(data['mode'])

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

############################3

class DataController:
    def __init__(self, record, mode):
        self.mode = mode

        self.raw_data = { 'title':record.title,
                          'keywords':record.keywords,
                          'body':record.body }

        self.interpretted_data = { 'title':link.expand(record.title),
                                   'keywords':link.expand(record.keywords),
                                   'body':link.expand(record.body) }

    def dump(self, data_type='INTERPRETTED'):
        if data_type == 'RAW':
            return {**self.raw_data, 'mode':self.mode}
        return {**self.interpretted_data, 'mode': self.mode}

############################3

class UI:
    def __init__(self, record, mode='COMMAND'):
        self.Data = DataController(record, mode)
        self.Screen = ScreenController(mode)
        self.Wigets = WidgetController( self.Data.dump() )

        urwid.register_signal(DataController, ['COMMAND MODE', 'INSERT MODE'])
        urwid.connect_signal(self.Data, 'COMMAND MODE', self._set_mode, 'COMMAND')
        urwid.connect_signal(self.Data, 'INSERT MODE', self._set_mode, 'INSERT')

        self.Screen.run_wrapper(self._run)

    def _set_mode(self, mode):
        self.Data.mode = mode
        self.Screen.set_palette_mode(mode)
        self.Wigets.footer.set_mode(mode)

    def _evaluate_command(self):
        cmd_text = self.Wigets['footer'].get_edit_text()

        if len(cmd_text) > 0:
            self.Wigets['footer'].cmd_history.append(cmd_text)

        # extract :command pattern from cmd input field
        cmd = self.Wigets['footer'].cmd_pattern.search(cmd_text)

        if cmd is None:
            if len(cmd_text) > 0:
                self.Wigets['footer'].set_edit_text('Invalid command')
            return

        cmd = cmd.group(0)
        args = cmd_text.split(' ', 1)[-1].strip()

        if cmd == ':e' or cmd == ':export':
            # if no export path follows export command - no space to split on
            if args.startswith(cmd):
                args = os.getcwd()
            self.Wigets['footer'].set_edit_text('Exported to {}'.format(args))

        elif cmd == ':h' or cmd == ':help':
            self.Wigets['footer'].set_edit_text('(:i)nsert, (:q)uit')

        elif cmd == ':i' or cmd == ':insert':
            self.Wigets['footer'].set_edit_text('')
            urwid.emit_signal(self.Data, 'INSERT MODE')

        # elif cmd == ':q' or cmd == ':quit':
        #     return CmdAction.QUIT, 0
        # elif cmd == ':v' or cmd == ':view':
        #     if not self.state.change_display(args.upper()):
        #         self.footer_widget.set_edit_text('Invalid display state \'{}\''.format(args))


    def _run(self):
        size = self.Screen.get_cols_rows()

        while True:
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
                    self.Wigets['footer'].set_edit_text('')

                elif self.Data.mode == 'INSERT':
                    if k == 'esc':
                        urwid.emit_signal(self.Data, 'COMMAND MODE')
                    else:
                        self.Wigets.keypress(size, k)

                elif self.Data.mode == 'COMMAND':
                    if k == 'enter':
                        self._evaluate_command()
                        self.Wigets['footer'].clear_before_keypress = True

                #         # if valid cmd entry was entered
                #         if eval_res is not None:
                #             if eval_res[0] == CmdAction.QUIT:
                #                 [setattr(self, key, value) for key, value in self.dump().items()]
                #                 return
                #
                #             elif eval_res[0] == CmdAction.EXPORT:
                #                 self._export_to_file(eval_res[1])
                #
                #             elif eval_res[0] == CmdAction.VIEW:
                #                 self.tty.switch_view(eval_res[1])
                #
                #     elif k == 'shift up':
                #         self.tty.footer.base_widget.scroll_history_up()
                #     elif k == 'shift down':
                #         self.tty.footer.base_widget.scroll_history_down()
                #     elif k in scroll_actions and self.tty.focus_position == 'body':
                #         self.tty.keypress(size, k)
                    else:
                        self.Wigets['footer'].keypress((1,), k)
