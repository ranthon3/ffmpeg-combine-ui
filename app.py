#!/usr/bin/env python3
"""A simple GNOME / GTK 3 file-combining demonstration."""

import threading

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk

from combine import combine_files


class CombineWindow(Gtk.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application, title='Combine files')
        self.set_default_size(600, 360)
        layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        layout.set_border_width(16)
        self.add(layout)
        self.entries = []
        for number in range(1, 4):
            row = Gtk.Box(spacing=8)
            label = 'File 3 (optional)' if number == 3 else f'File {number}'
            row.pack_start(Gtk.Label(label=label), False, False, 0)
            entry = Gtk.Entry()
            entry.set_placeholder_text('Optional' if number == 3 else 'Choose a file')
            self.entries.append(entry)
            row.pack_start(entry, True, True, 0)
            browse = Gtk.Button(label='Browse…')
            browse.connect('clicked', self.choose_file, entry)
            row.pack_start(browse, False, False, 0)
            layout.pack_start(row, False, False, 0)

        self.output = Gtk.TextView()
        self.output.set_editable(False)
        self.output.set_monospace(True)
        self.output.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.output)
        layout.pack_start(scroll, True, True, 0)
        self.button = Gtk.Button(label='Combine')
        self.button.connect('clicked', self.on_combine)
        layout.pack_start(self.button, False, False, 0)

    def choose_file(self, _button, entry):
        dialog = Gtk.FileChooserDialog(
            title='Choose a file', transient_for=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons('Cancel', Gtk.ResponseType.CANCEL,
                           'Open', Gtk.ResponseType.OK)
        if dialog.run() == Gtk.ResponseType.OK:
            entry.set_text(dialog.get_filename())
        dialog.destroy()

    def on_combine(self, _button):
        paths = [entry.get_text().strip() for entry in self.entries]
        self.button.set_sensitive(False)
        self.output.get_buffer().set_text('Running…')
        threading.Thread(target=self.run_combine, args=(paths,), daemon=True).start()

    def run_combine(self, paths):
        try:
            output, status = combine_files(paths)
            message = f'{output}\nExit status: {status}'
        except Exception as error:
            message = f'Error: {error}'
        GLib.idle_add(self.finished, message)

    def finished(self, message):
        self.output.get_buffer().set_text(message)
        self.button.set_sensitive(True)
        return GLib.SOURCE_REMOVE


class CombineApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='org.example.FfmpegCombineUI')

    def do_activate(self):
        window = self.get_active_window()
        if window is None:
            window = CombineWindow(self)
        window.show_all()
        window.present()


if __name__ == '__main__':
    raise SystemExit(CombineApplication().run(None))
