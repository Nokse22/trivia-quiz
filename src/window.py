# window.py
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

from gi.repository import Adw
from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import Gio
from gi.repository import GLib

import requests
import json
import html
import random
import threading

class ListString(GObject.Object):
    __gtype_name__ = 'ListString'

    def __init__(self, name, identification):
        super().__init__()
        self._name = name
        self._identification = identification

    @GObject.Property(type=str)
    def name(self):
        return self._name

    @GObject.Property(type=str)
    def identification(self):
        return self._identification

class Question:
    def __init__(self, question_text, category, difficulty, question_type, correct_answer, incorrect_answers):
        self.question_text = question_text
        self.category = category
        self.difficulty = difficulty
        self.question_type = question_type
        self.correct_answer = correct_answer
        self.incorrect_answers = incorrect_answers

    def __repr__(self):
        return f"Question: {self.question_text}\nCategory: {self.category}\nDifficulty: {self.difficulty}\n" \
               f"Type: {self.question_type}\nCorrect Answer: {self.correct_answer}\n" \
               f"Incorrect Answers: {', '.join(self.incorrect_answers)}"

class TriviaWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'TriviaWindow'

    label = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.first_box = Gtk.Box(orientation=1)
        self.headerbar = Adw.HeaderBar(css_classes=["flat"])

        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu = Gio.Menu()
        # menu.append(_("Preferences"), "app.preferences")
        menu.append(_("Keyboard shortcuts"), "win.show-help-overlay")
        menu.append(_("About Trivia Quiz"), "app.about")
        menu_button.set_menu_model(menu)
        self.headerbar.pack_end(menu_button)

        self.back_button = Gtk.Button(icon_name="go-previous-symbolic")
        self.back_button.connect("clicked", self.on_back_button_clicked)
        self.back_button.set_sensitive(False)
        self.headerbar.pack_start(self.back_button)

        self.set_title("")
        self.set_default_size(600, 800)
        self.set_size_request(400, 650)
        self.first_box.append(self.headerbar)
        self.clamp = Adw.Clamp(margin_start=20, margin_end=20, tightening_threshold=600, maximum_size=800)
        self.handle = Gtk.WindowHandle(margin_bottom=10, vexpand=True)
        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.set_child(self.clamp)
        self.handle.set_child(self.toast_overlay)
        self.first_box.append(self.handle)

        self.categories = [["Any category", None]]

        self.selected_difficulty = ""
        self.selected_category = ""
        self.selected_type = ""
        self.selected_mode = ""
        self.amount = 20

        self.set_content(self.first_box)

        self.start_page = self.get_start_page()
        self.set_start_page()

        self.questions = []

        self.token = self.get_open_trivia_token()

        self.has_responded = False

    def set_no_connection_page(self):
        self.back_button.set_sensitive(False)
        self.no_connectio_page = Gtk.Box(orientation=1, vexpand=True)

        self.no_connectio_page.append(Gtk.Label(label="Trivia Quiz", css_classes=["large-title"], valign=Gtk.Align.CENTER, vexpand=True))

        status_page = Adw.StatusPage(title="No Connection", description="There is no internet connection or the Open Trivia database is not responding",
                icon_name="network-wireless-offline-symbolic", vexpand=True)
        self.no_connectio_page.append(status_page)
        self.retry_button = Gtk.Button(label="Retry", css_classes=["pill", "suggested-action"],
                halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, vexpand=True, margin_bottom=65)
        self.retry_button.connect("clicked", self.on_retry_button_clicked)
        self.no_connectio_page.append(self.retry_button)

        self.clamp.set_child(self.no_connectio_page)
        # self.set_content(self.first_box)

    def on_retry_button_clicked(self, btn):
        code = self.set_start_page()
        if code == 0:
            toast = Adw.Toast(title="Still No Connection")
            self.toast_overlay.add_toast(toast)

    def on_back_button_clicked(self, btn):
        self.questions = []
        self.set_start_page()
        self.back_button.set_sensitive(False)

    def set_start_page(self):
        self.clamp.set_child(self.start_page)

    def get_start_page(self):
        new_categories = self.get_categories()
        if new_categories == 0:
            self.set_no_connection_page()
            return 0
        self.categories += new_categories

        start_page = Gtk.Box(orientation=1, vexpand=True)

        start_page.append(Gtk.Label(label="Trivia Quiz", css_classes=["large-title"], valign=Gtk.Align.CENTER, vexpand=True))

        difficuties = [["Any difficulty", None], ["Easy", "easy"], ["Medium", "medium"], ["Hard", "hard"]]
        difficulty_row = self.new_combo_row_from_strings("Difficulty", difficuties)
        # for index, difficulty in enumerate(difficuties):
        #     if self.selected_difficulty == difficulty[1]:
        #         difficulty_row.set_selected(index)

        category_row = self.new_combo_row_from_strings("Category", self.categories)
        # for index, category in enumerate(self.categories):
        #     if self.selected_category == category[1]:
        #         category_row.set_selected(index)

        types = [["Any type", None], ["Multiple Choice", "multiple"], ["True or False", "boolean"]]
        type_row = self.new_combo_row_from_strings("Type", types)
        # for index, q_type in enumerate(types):
        #     if self.selected_difficulty == q_type[1]:
        #         type_row.set_selected(index)

        modes = [["Endless", "ENDLESS"], ["Time", "TIME"], ["No error", "NO-ERROR"]]
        gamemode_row = self.new_combo_row_from_strings("Game mode", modes)
        # for index, mode in enumerate(modes):
        #     if self.selected_mode == mode[1]:
        #         gamemode_row.set_selected(index)

        settings_list = Gtk.ListBox(selection_mode=0, css_classes=["navigation-sidebar"], valign=Gtk.Align.CENTER, vexpand=True)

        start_page.append(settings_list)

        settings_list.append(difficulty_row)
        settings_list.append(category_row)
        settings_list.append(type_row)
        # settings_list.append(gamemode_row)

        start_button = Gtk.Button(label="Start", css_classes=["pill", "suggested-action"],
                halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, vexpand=True, margin_bottom=40)
        start_button.connect("clicked", self.on_start_button_clicked, difficulty_row, category_row, type_row, gamemode_row)
        start_page.append(start_button)

        return start_page
        # self.set_content(self.first_box)

    def get_open_trivia_token(self):
        token_url = "https://opentdb.com/api_token.php?command=request"

        try:
            response = requests.get(token_url)
        except Exception as e:
            print(e)
            return 0

        json_data = response.json()

        if json_data.get("response_code") == 0:
            return json_data.get("token")
        else:
            return None

    def reset_open_trivia_token(self):
        token_url = "https://opentdb.com/api_token.php?command=reset&token="

        try:
            response = requests.get(token_url + self.token)
        except Exception as e:
            print(e)
            return 0


    def new_question_page(self):
        try:
            question = self.questions[0]
        except:
            return 0

        question_page = Gtk.Box(orientation=1, vexpand=True, homogeneous=True)
        question_box = Gtk.Box(orientation=1, vexpand=True)
        details_box = Gtk.Box()
        if self.selected_category == None:
            details_box.append(Gtk.Label(label=question.category.capitalize(), hexpand=True, ellipsize=3))
        if self.selected_difficulty == None:
            details_box.append(Gtk.Label(label=question.difficulty.capitalize(), hexpand=True))
        question_box.append(details_box)
        question_box.append(Gtk.Label(label=question.question_text, css_classes=["large-title"], wrap=True, margin_bottom=10, vexpand=True))
        question_page.append(question_box)

        answer_box = Gtk.Box(orientation=1, vexpand=True)
        question_page.append(answer_box)
        buttons = []

        if question.question_type == "multiple":
            label = Gtk.Label(label=question.correct_answer, vexpand=True, wrap=True)
            correct_button1 = Gtk.Button(margin_top=10, margin_bottom=10)
            correct_button1.set_child(label)
            buttons.append(correct_button1)
            correct_button1.connect("clicked", self.answer_selected, correct_button1)

            for answer in question.incorrect_answers:
                label = Gtk.Label(label=html.unescape(answer), vexpand=True, wrap=True)
                button1 = Gtk.Button(margin_top=10, margin_bottom=10)
                button1.set_child(label)
                buttons.append(button1)
                button1.connect("clicked", self.answer_selected, correct_button1)
        else:
            correct_button1 = Gtk.Button(label=question.correct_answer, vexpand=True, margin_top=10, margin_bottom=10)
            buttons.append(correct_button1)
            correct_button1.connect("clicked", self.answer_selected, correct_button1)
            button1 = Gtk.Button(label=question.incorrect_answers[0], vexpand=True, margin_top=10, margin_bottom=10)
            buttons.append(button1)
            button1.connect("clicked", self.answer_selected, correct_button1)

        random.shuffle(buttons)
        for button in buttons:
            answer_box.append(button)

        return question_page

    def answer_selected(self, btn, correct_button):
        if self.has_responded:
            return
        self.has_responded = True
        try:
            question = self.questions[0]
        except:
            return
        answer = btn.get_label()

        if btn == correct_button:
            btn.add_css_class("success")
            GLib.timeout_add(800, self.next_question_page)
        else:
            btn.add_css_class("error")
            correct_button.add_css_class("success")
            GLib.timeout_add(800, self.next_question_page)

    def next_question_page(self):
        self.has_responded = False
        self.questions.pop(0)
        print(len(self.questions))
        if len(self.questions) == 0:
            code = self.get_new_trivia_questions(1, self.selected_category, self.selected_difficulty, self.selected_type, self.token)
            if code == 0:
                self.set_no_connection_page()
                return
            thread = threading.Thread(target=self.get_new_trivia_questions, args=(self.amount, self.selected_category, self.selected_difficulty, self.selected_type))
            thread.start()
        elif len(self.questions) < 2:
            thread = threading.Thread(target=self.get_new_trivia_questions, args=(self.amount, self.selected_category, self.selected_difficulty, self.selected_type))
            thread.start()
        question_page = self.new_question_page()
        self.clamp.set_child(question_page)

    def on_start_button_clicked(self, btn, difficulty_row, category_row, type_row, gamemode_row):
        self.back_button.set_sensitive(True)
        self.selected_difficulty = difficulty_row.get_selected_item().identification
        self.selected_category = category_row.get_selected_item().identification
        self.selected_type = type_row.get_selected_item().identification
        self.selected_mode = type_row.get_selected_item().identification

        thread = threading.Thread(target=self.get_new_trivia_questions, args=(self.amount, self.selected_category, self.selected_difficulty, self.selected_type))
        thread.start()

        if len(self.questions) == 0:
            self.get_new_trivia_questions(1, self.selected_category, self.selected_difficulty, self.selected_type, self.token)

        self.first_question()

    def first_question(self):
        code = question_page = self.new_question_page()
        if code == 0:
            toast = Adw.Toast(title="There is no connection")
            self.toast_overlay.add_toast(toast)
            self.set_no_connection_page()
            return
        self.clamp.set_child(question_page)

    def get_new_trivia_questions(self, amount=10, category=None, difficulty=None, question_type=None, token=None):
        base_url = "https://opentdb.com/api.php"

        params = {}

        params["amount"] = amount

        if category is not None:
            params["category"] = category
        if difficulty is not None:
            params["difficulty"] = difficulty
        if question_type is not None:
            params["type"] = question_type
        if question_type is not None:
            params["token"] = token

        try:
            response = requests.get(base_url, params=params)
        except Exception as e:
            print(e)
            return 0

        data = response.json()

        try:
            results = data.get("results", [])
            response_code = data.get("response_code")

            if response_code == 1:
                if self.amount == 5:
                    toast = Adw.Toast(title="The API returned no results")
                    self.toast_overlay.add_toast(toast)
                self.amount = 5
                return
            if response_code == 2:
                toast = Adw.Toast(title="There was en error retrieving more questions")
                self.toast_overlay.add_toast(toast)
                return
            if response_code == 3:
                self.token = self.get_open_trivia_token()
            elif response_code == 4:
                self.token = self.reset_open_trivia_token()

            for result in results:
                question_text = html.unescape(result.get("question"))
                category = result.get("category")
                difficulty = result.get("difficulty")
                question_type = result.get("type")
                correct_answer = html.unescape(result.get("correct_answer"))
                incorrect_answers = result.get("incorrect_answers", [])

                question = Question(question_text, category, difficulty, question_type, correct_answer, incorrect_answers)
                self.questions.append(question)

        except json.JSONDecodeError as e:
            print("Error decoding JSON:", e)

    def get_categories(self):
        base_url = "https://opentdb.com/api_category.php"

        try:
            response = requests.get(base_url)
        except Exception as e:
            print(e)
            return 0

        json_data = response.json()

        category_names = []

        try:
            categories = json_data.get("trivia_categories", [])

            for category in categories:
                category_name = category.get("name")
                category_id = category.get("id")
                if category_name:
                    category_names.append([category_name, category_id])

        except json.JSONDecodeError as e:
            print("Error decoding JSON:", e)

        return category_names

    def new_combo_row_from_strings(self, name, strings):
        model_widget = Gio.ListStore(item_type=ListString)
        sort_model_widget  = Gtk.SortListModel(model=model_widget)
        filter_model_widget = Gtk.FilterListModel(model=sort_model_widget)
        custom_filter_model = Gtk.CustomFilter.new() #self._do_filter_widget_view, filter_model_widget
        filter_model_widget.set_filter(custom_filter_model)

        for string in strings:
            model_widget.append(ListString(string[0], string[1]))

        factory_widget = Gtk.SignalListItemFactory()
        factory_widget.connect("setup", self._on_factory_widget_setup)
        factory_widget.connect("bind", self._on_factory_widget_bind)

        ddwdg = Adw.ComboRow(title=name, model=filter_model_widget, factory=factory_widget, margin_top=6)
        # ddwdg.set_enable_search(True)

        # search_entry_widget = self._get_search_entry_widget(ddwdg)
        # custom_filter_model.set_filter_func(self._do_filter_drop_down, filter_model_widget, search_entry_widget)
        # search_entry_widget.connect('search-changed', self._on_search_drop_down_changed, custom_filter_model)

        return ddwdg

    def _get_search_entry_widget(self, dropdown):
        popover = dropdown.get_last_child()
        box = popover.get_child()
        box2 = box.get_first_child()
        search_entry = box2.get_first_child() # Gtk.SearchEntry
        return search_entry

    def _on_factory_widget_setup(self, factory, list_item):
        box = Gtk.Box(spacing=6, orientation=Gtk.Orientation.HORIZONTAL)
        label = Gtk.Label(ellipsize=3)
        box.append(label)
        list_item.set_child(box)

    def _on_factory_widget_bind(self, factory, list_item):
        box = list_item.get_child()
        label = box.get_first_child()
        widget = list_item.get_item()
        label.set_text(widget.name)

    def _on_selected_widget(self, dropdown, data):
        widget = dropdown.get_selected_item()

        name = widget.name
        obj = eval(name)
        a = set(dir(obj))
        b = set(dir(Gtk.Widget))
        c = a - b
        for item in sorted(list(c)):
            self.model_method.append(Method(name=item))

    def _on_search_drop_down_changed(self, search_entry, filter_model):
        filter_model.changed(Gtk.FilterChange.DIFFERENT)

    def _do_filter_drop_down(self, item, filter_list_model, search_entry):
        return search_entry.get_text().upper() in item.name.upper()
