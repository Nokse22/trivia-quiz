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
from gi.repository import GLib

from .question import Question

import requests
import json
import html
import random
import threading
import time

class OpenTriviaDB(GObject.GObject):
    __gsignals__ = {
        'connection-error': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'no-results': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'invalid-parameter': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'token-empty': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'questions-finished': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'questions-retrieved': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'categories-retrieved': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'token-reset': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'rate-limit': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.questions = []
        self.token = "123"

    def get_open_trivia_token(self):
        token_url = "https://opentdb.com/api_token.php?command=request"

        try:
            response = requests.get(token_url)
        except Exception as e:
            self.emit("connection-error")
            return 0

        json_data = response.json()

        if json_data.get("response_code") == 0:
            self.token = json_data.get("token")

    def reset_open_trivia_token(self):
        token_url = "https://opentdb.com/api_token.php?command=reset&token="

        try:
            response = requests.get(token_url + self.token)
        except Exception as e:
            self.emit("connection-error")
            return 0

        self.emit('token-reset')

    def get_new_trivia_questions_with_delay(self, amount=1, category=None, difficulty=None, question_type=None, token=None):
        time.sleep(5.1)
        self.get_new_trivia_questions(amount, category, difficulty, question_type, token)

    def get_new_trivia_questions(self, amount=1, category=None, difficulty=None, question_type=None, token=None):
        base_url = "https://opentdb.com/api.php"

        if token == None:
            token = self.token

        params = {}

        params["amount"] = amount

        if category is not None:
            params["category"] = category
        if difficulty is not None:
            params["difficulty"] = difficulty
        if question_type is not None:
            params["type"] = question_type
        params["token"] = token

        try:
            response = requests.get(base_url, params=params)
        except Exception as e:
            self.emit("connection-error")
            return

        data = response.json()

        try:
            results = data.get("results", [])
            response_code = data.get("response_code")

            print(f"response: {response_code}, {token}")

            # Success: Returned results successfully.
            if response_code == 0:
                pass
            # No Results: Could not return results. The API doesn't have enough
            # questions for your query. (Ex. Asking for 50 Questions in a Category that only has 20.)
            elif response_code == 1:
                self.emit("no-results")
                self.is_empty = True
                return
            # Invalid Parameter: Contains an invalid parameter.
            # Arguments passed in are not valid. (Ex. Amount = Five)
            elif response_code == 2:
                self.emit("invalid-parameter")
                return
            # Token Not Found: Session Token does not exist.
            elif response_code == 3:
                self.get_open_trivia_token()
                time.sleep(5.1)
                self.get_new_trivia_questions(amount, category, difficulty, question_type)
                return
            # Token Empty: Session Token has returned all possible questions
            # for the specified query. Resetting the Token is necessary.
            elif response_code == 4:
                self.emit("token-empty")
                return
            # Rate Limit: Too many requests have occurred.
            # Each IP can only access the API once every 5 seconds.
            elif response_code == 5:
                self.emit('rate-limit')
                return

            for result in results:
                question_text = html.unescape(result.get("question"))
                category = html.unescape(result.get("category"))
                difficulty = html.unescape(result.get("difficulty"))
                question_type = result.get("type")
                correct_answer = html.unescape(result.get("correct_answer"))
                incorrect_answers = []
                for incorrect_answer in result.get("incorrect_answers", []):
                    incorrect_answers.append(html.unescape(incorrect_answer))

                question = Question(question_text, category, difficulty, question_type, correct_answer, incorrect_answers)
                self.questions.append(question)

        except json.JSONDecodeError as e:
            print("Error decoding JSON:", e)

        self.emit("questions-retrieved")

    def get_categories(self):
        print("get categories")
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

    def reset_questions(self):
        self.questions = []
