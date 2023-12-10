# question.py
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
