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

from .question import Question
from .backend import OpenTriviaDB

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
    retry_button_stack = Gtk.Template.Child()

    category_label = Gtk.Template.Child()
    difficulty_label = Gtk.Template.Child()
    question_label = Gtk.Template.Child()

    answers_stack = Gtk.Template.Child()

    answer_1 =  Gtk.Template.Child()
    answer_2 =  Gtk.Template.Child()
    answer_3 =  Gtk.Template.Child()
    answer_4 =  Gtk.Template.Child()

    true_button =  Gtk.Template.Child()
    false_button =  Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.difficulties = {"Any Difficulty": None, "Easy": "easy", "Medium": "medium", "Hard": "hard"}

        self.types = {"Any Type": None, "Multiple Choice": "multiple", "True or False": "boolean"}

        self.categories = {'Any Category': None, 'General Knowledge': 9, 'Entertainment: Books': 10,
                'Entertainment: Film': 11, 'Entertainment: Music': 12, 'Entertainment: Musicals & Theatres': 13,
                'Entertainment: Television': 14, 'Entertainment: Video Games': 15, 'Entertainment: Board Games': 16,
                'Science & Nature': 17, 'Science: Computers': 18, 'Science: Mathematics': 19, 'Mythology': 20,
                'Sports': 21, 'Geography': 22, 'History': 23, 'Politics': 24, 'Art': 25, 'Celebrities': 26, 'Animals': 27,
                'Vehicles': 28, 'Entertainment: Comics': 29, 'Science: Gadgets': 30,
                'Entertainment: Japanese Anime & Manga': 31, 'Entertainment: Cartoon & Animations': 32}

        self.multiple_buttons = [self.answer_1, self.answer_2, self.answer_3, self.answer_4]
        self.true_false_buttons = [self.true_button, self.false_button]

        self.correct_button = None

        self.selected_difficulty = None
        self.selected_category = None
        self.selected_type = None
        self.amount = 5

        self.open_trivia_db = OpenTriviaDB()
        self.open_trivia_db.connect("connection-error", self.on_backend_connection_error)
        self.open_trivia_db.connect("results-error", self.on_backend_results_error)
        self.open_trivia_db.connect("questions-retrieved", self.on_got_questions)

        self.has_responded = False

    def on_backend_connection_error(self, *args):
        self.retry_button_stack.set_visible_child_name("retry_label")
        if self.open_trivia_db.questions == []:
            self.stack.set_visible_child_name("error_page")
            self.start_button_stack.set_visible_child_name("label")
            self.home_button.set_sensitive(True)

    def on_backend_results_error(self, *args):
        self.retry_button_stack.set_visible_child_name("retry_label")
        if self.open_trivia_db.questions == []:
            self.stack.set_visible_child_name("results_error_page")
            self.start_button_stack.set_visible_child_name("label")
            self.home_button.set_sensitive(True)

    def show_question(self):
        for button in self.multiple_buttons:
            button.set_css_classes([])
        for button in self.true_false_buttons:
            button.set_css_classes([])

        try:
            question = self.open_trivia_db.questions[0]
        except:
            return

        self.category_label.set_label(question.category.capitalize())
        self.difficulty_label.set_label(question.difficulty.capitalize())

        self.question_label.set_label(question.question_text)

        possible_answers = question.incorrect_answers + [question.correct_answer]
        random.shuffle(possible_answers)

        if question.question_type == "multiple":
            self.answers_stack.set_visible_child_name("multiple_choice_answers")

            for index, answer in enumerate(possible_answers):
                self.multiple_buttons[index].get_child().set_label(answer)
                if answer == question.correct_answer:
                    self.correct_button = self.multiple_buttons[index]

        else:
            self.answers_stack.set_visible_child_name("true_false_answers")

            for index, answer in enumerate(possible_answers):
                self.true_false_buttons[index].set_label(answer)
                if answer == question.correct_answer:
                    self.correct_button = self.true_false_buttons[index]

    def first_question(self):
        self.stack.set_visible_child_name("question_page")
        self.start_button_stack.set_visible_child_name("label")
        self.home_button.set_sensitive(True)
        self.show_question()

    def load_next_question(self):
        self.has_responded = False
        self.open_trivia_db.questions.pop(0)
        if len(self.open_trivia_db.questions) == 0:
            self.open_trivia_db.get_new_trivia_questions(self.amount, self.selected_category, self.selected_difficulty, self.selected_type)
        elif len(self.open_trivia_db.questions) < 2:
            th = threading.Thread(target=self.open_trivia_db.get_new_trivia_questions, args=(self.amount, self.selected_category, self.selected_difficulty, self.selected_type, self.on_got_questions))
            th.start()

        self.show_question()

    def on_got_questions(self, *args):
        self.start_button_stack.set_visible_child_name("label")
        self.retry_button_stack.set_visible_child_name("retry_label")
        self.first_question()

    @Gtk.Template.Callback("on_start_button_clicked")
    def on_start_button_clicked(self, btn):
        self.selected_difficulty = self.difficulties[self.difficulty_row.get_selected_item().get_string()]
        self.selected_category = self.categories[self.category_row.get_selected_item().get_string()]
        self.selected_type = self.types[self.type_row.get_selected_item().get_string()]

        self.start_button_stack.set_visible_child_name("spinner")

        th = threading.Thread(target=self.open_trivia_db.get_new_trivia_questions, args=(self.amount, self.selected_category, self.selected_difficulty, self.selected_type))
        th.start()

    @Gtk.Template.Callback("on_answer_button_clicked")
    def on_answer_button_clicked(self, btn):
        if self.has_responded:
            return
        self.has_responded = True

        try:
            question = self.open_trivia_db.questions[0]
        except:
            return
        answer = btn.get_child().get_label()

        if answer == question.correct_answer:
            btn.add_css_class("success")
            GLib.timeout_add(800, self.load_next_question)
        else:
            btn.add_css_class("error")
            self.correct_button.add_css_class("success")
            GLib.timeout_add(800, self.load_next_question)

    @Gtk.Template.Callback("on_retry_button_clicked")
    def on_retry_button_clicked(self, btn):
        self.retry_button_stack.set_visible_child_name("retry_spinner")

        th = threading.Thread(target=self.open_trivia_db.get_new_trivia_questions, args=(self.amount, self.selected_category, self.selected_difficulty, self.selected_type))
        th.start()

    @Gtk.Template.Callback("on_home_button_clicked")
    def on_home_button_clicked(self, btn):
        self.open_trivia_db.reset_questions()
        self.stack.set_visible_child_name("home_page")
        self.home_button.set_sensitive(False)
