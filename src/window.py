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

@Gtk.Template(resource_path='/io/github/nokse22/trivia-quiz/window.ui')
class TriviaWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'TriviaQuizWindow'

    difficulty_row = Gtk.Template.Child()
    category_row = Gtk.Template.Child()
    type_row = Gtk.Template.Child()
    home_button = Gtk.Template.Child()

    categories_string_list = Gtk.Template.Child()
    stack = Gtk.Template.Child()

    start_button = Gtk.Template.Child()
    start_button_stack = Gtk.Template.Child()

    category_label = Gtk.Template.Child()
    difficulty_label = Gtk.Template.Child()
    question_label = Gtk.Template.Child()

    answers_stack = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.categories = [["Any category", None]]
        self.difficulties = [["Any difficulty", None], ["Easy", "easy"], ["Medium", "medium"], ["Hard", "hard"]]
        self.types = [["Any type", None], ["Multiple Choice", "multiple"], ["True or False", "boolean"]]

        self.selected_difficulty = ""
        self.selected_category = ""
        self.selected_type = ""
        self.selected_mode = ""
        self.amount = 20

        self.questions = []

        self.token = self.get_open_trivia_token()

        self.has_responded = False

        self.get_categories()

    def on_retry_button_clicked(self, btn):
        code = self.set_start_page()
        if code == 0:
            toast = Adw.Toast(title="Still No Connection")
            # self.toast_overlay.add_toast(toast)

    @Gtk.Template.Callback("on_home_button_clicked")
    def on_home_button_clicked(self, btn):
        self.questions = []
        self.stack.set_visible_child_name("home_page")
        self.home_button.set_sensitive(False)

    def set_start_page(self):
        # self.clamp.set_child(self.start_page)
        pass

    def get_start_page(self):
        new_categories = self.get_categories()
        if new_categories == 0:
            self.stack.set_visible_child_name("error_page")
            return 0
        self.categories += new_categories

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

        self.category_label.set_label(question.category.capitalize())
        self.difficulty_label.set_label(question.difficulty.capitalize())

        self.question_label.set_label(question.question_text)

        if question.question_type == "multiple":
            self.answers_stack.set_visible_child_name("multiple_choice_answers")
            question.correct_answer

            # correct_button1.connect("clicked", self.answer_selected, correct_button1)

            # for answer in question.incorrect_answers:
            #     html.unescape(answer)
            #     button1 = Gtk.Button(margin_top=10, margin_bottom=10)
            #     button1.set_child(label)
            #     buttons.append(button1)
            #     button1.connect("clicked", self.answer_selected, correct_button1)
        else:
            self.answers_stack.set_visible_child_name("true_false_answers")
            # correct_button1 = Gtk.Button(label=question.correct_answer, vexpand=True, margin_top=10, margin_bottom=10)
            # buttons.append(correct_button1)
            # correct_button1.connect("clicked", self.answer_selected, correct_button1)
            # button1 = Gtk.Button(label=question.incorrect_answers[0], vexpand=True, margin_top=10, margin_bottom=10)
            # buttons.append(button1)
            # button1.connect("clicked", self.answer_selected, correct_button1)

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
                self.stack.set_visible_child_name("error_page")
                return
            thread = threading.Thread(target=self.get_new_trivia_questions, args=(self.amount, self.selected_category, self.selected_difficulty, self.selected_type))
            thread.start()
        elif len(self.questions) < 2:
            thread = threading.Thread(target=self.get_new_trivia_questions, args=(self.amount, self.selected_category, self.selected_difficulty, self.selected_type))
            thread.start()
        question_page = self.new_question_page()

    @Gtk.Template.Callback("on_start_button_clicked")
    def on_start_button_clicked(self, btn):
        self.home_button.set_sensitive(True)
        self.selected_difficulty = self.get_identification(self.difficulty_row.get_selected_item(), self.difficulties)
        self.selected_category = self.get_identification(self.category_row.get_selected_item(), self.categories)
        self.selected_type = self.get_identification(self.type_row.get_selected_item(), self.types)

        thread = threading.Thread(target=self.get_new_trivia_questions, args=(self.amount, self.selected_category, self.selected_difficulty, self.selected_type))
        thread.start()

        self.start_button_stack.set_visible_child_name("spinner")

        if len(self.questions) == 0:
            self.get_new_trivia_questions(1, self.selected_category, self.selected_difficulty, self.selected_type, self.token)
            self.start_button_stack.set_visible_child_name("label")

        self.first_question()

    def get_identification(self, interface_name, lookup_array):
        for couple in lookup_array:
            if couple[0] == interface_name:
                return couple[1]
        return None

    def first_question(self):
        self.stack.set_visible_child_name("question_page")
        code = question_page = self.new_question_page()
        if code == 0:
            toast = Adw.Toast(title="There is no connection")
            # self.toast_overlay.add_toast(toast)
            self.stack.set_visible_child_name("error_page")
            return



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
                    # self.toast_overlay.add_toast(toast)
                self.amount = 5
                return
            if response_code == 2:
                toast = Adw.Toast(title="There was en error retrieving more questions")
                # self.toast_overlay.add_toast(toast)
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
                    self.categories_string_list.append(category_name)

        except json.JSONDecodeError as e:
            print("Error decoding JSON:", e)

        return category_names
