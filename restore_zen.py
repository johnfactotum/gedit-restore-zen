from gi.repository import GObject, Gedit, Gdk, Pango, Gtk, PeasGtk, Gio
import os

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
SCHEMAS_PATH = os.path.join(BASE_PATH, 'schemas')

try:
    schema_source = Gio.SettingsSchemaSource.new_from_directory(
        SCHEMAS_PATH,
        Gio.SettingsSchemaSource.get_default(),
        False)
    schema = schema_source.lookup(
        'org.gnome.gedit.plugins.restore_zen',
        False)
    settings = Gio.Settings.new_full(
        schema,
        None,
        '/org/gnome/gedit/plugins/restore_zen/')
except:
    settings = None

class RestoreZenPlugin(GObject.Object, Gedit.WindowActivatable, PeasGtk.Configurable):

    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_create_configure_widget(self):
        if not settings:
            return Gtk.Label(label='Error: could not load settings schema')

        check = Gtk.CheckButton.new_with_label('Wrap text at right margin')
        flag = Gio.SettingsBindFlags.DEFAULT
        settings.bind('wrap-right', check, 'active', flag)
        return check

    def get_wrap_right(self):
        if not settings: return False
        return settings.get_boolean('wrap-right')

    def get_views(self):
        views = self.window.get_views()
        if not isinstance(views, list): views = [views]
        return views

    def center_views(self):
        window_width = self.window.get_size().width
        for view in self.get_views():
            right_margin_pos = view.get_right_margin_position()
            context = view.get_pango_context()
            layout = Pango.Layout(context)
            layout.set_text('_' * right_margin_pos)
            text_width = layout.get_pixel_size().width

            gutter_window = view.get_window(Gtk.TextWindowType.LEFT)
            gutter_width = gutter_window.get_width() if gutter_window else 0

            margin = (window_width - text_width - gutter_width) / 2
            view.set_margin_left(margin)
            if self.get_wrap_right():
                view.set_margin_right(margin)
            else:
                view.set_margin_right(0)

    def uncenter_views(self):
        for view in self.get_views():
            view.set_margin_left(0)
            view.set_margin_right(0)

    def on_window_state_event(self, _, event):
        state = event.get_window().get_state()
        self.is_fullscreen = bool(state & Gdk.WindowState.FULLSCREEN)
        self.update()

    def update(self, *args):
        if self.is_fullscreen: self.center_views()
        else: self.uncenter_views()

    def do_activate(self):
        self.is_fullscreen = False
        self.handlers = [
            self.window.connect('window-state-event', self.on_window_state_event),
            self.window.connect('tab-added', self.update),
            self.window.connect('size-allocate', self.update)
        ]
        if settings is not None:
            self.settings_handler = settings.connect(
                'changed::wrap-right', self.update)

    def do_deactivate(self):
        self.uncenter_views()
        for handler in self.handlers: self.window.disconnect(handler)
        if settings is not None:
            settings.disconnect(self.settings_handler)
