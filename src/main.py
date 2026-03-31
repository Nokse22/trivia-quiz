# main.py
#
# Copyright 2023 Nokse
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk, Gio, Adw, Gdk
from .window import TriviaWindow

import sys
import webbrowser


class TriviaApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='io.github.nokse22.trivia-quiz',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action(
            'contribute-to-otdb', self.on_contribute_to_otdb_action)

        self.settings = Gio.Settings.new('io.github.nokse22.trivia-quiz')
        colorblind_action = self.settings.create_action('colorblind-mode')
        self.add_action(colorblind_action)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        provider = Gtk.CssProvider()
        provider.load_from_resource('/io/github/nokse22/trivia-quiz/style.css')
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.win = self.props.active_window
        if not self.win:
            self.win = TriviaWindow(application=self)
        self.win.present()

    def on_about_action(self, widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(
            application_name='Trivia Quiz',
            application_icon='io.github.nokse22.trivia-quiz',
            developer_name='Nokse',
            version='1.1.0',
            website='https://github.com/grahamthetvi/trivia-quiz',
            issue_url='https://github.com/grahamthetvi/trivia-quiz/issues',
            developers=['Nokse'],
            license_type=Gtk.License.GPL_3_0,
            copyright='© 2023 Nokse')
        about.present(self.win)

    def on_contribute_to_otdb_action(self, *args):
        webbrowser.open("https://opentdb.com/")

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = TriviaApplication()
    return app.run(sys.argv)
