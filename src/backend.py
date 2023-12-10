# backend.py
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

from gi.repository import GObject
from gi.repository import Gst, GLib

from .question import Question

import requests
import json
import html
import random
import threading

class OpenTriviaDB(GObject.GObject):
    __gsignals__ = {
        'error': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'questions-finished': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'questions-retrieved': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'categories-retrieved': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.questions = []
        self.token = None

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

    def get_new_trivia_questions(self, amount=10, category=None, difficulty=None, question_type=None, token=None):
        print(f"amount: {amount}")
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

            print(f"responce: {response_code}")

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
                print("added question")

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
                    # self.categories_string_list.append(category_name)

        except json.JSONDecodeError as e:
            print("Error decoding JSON:", e)

        return category_names
