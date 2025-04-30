import unittest
from bomb_logic import BombDefusalGame

class TestBombDefusalGame(unittest.TestCase):

    def test_correct_answers_progress(self):
        game = BombDefusalGame()
        for i in range(game.MAX_PHASES - 1):
            result = game.answer(game.questions[i]["correct"])
            self.assertEqual(result, "Correct")
            self.assertEqual(game.strikes, 0)

    def test_final_correct_answer_wins(self):
        game = BombDefusalGame()
        for i in range(game.MAX_PHASES - 1):
            game.answer(game.questions[i]["correct"])
        result = game.answer(game.questions[-1]["correct"])
        self.assertEqual(result, "Defused")

    def test_incorrect_answer_adds_strike(self):
        game = BombDefusalGame()
        result = game.answer("Wrong Answer")
        self.assertEqual(result, "Incorrect")
        self.assertEqual(game.strikes, 1)

    def test_mega_button_gives_strike(self):
        game = BombDefusalGame()
        result = game.answer("Meg")
        self.assertEqual(result, "Incorrect")
        self.assertEqual(game.strikes, 1)

    def test_game_over_after_5_strikes(self):
        game = BombDefusalGame()
        for _ in range(4):
            game.answer("Wrong")
        result = game.answer("Wrong")
        self.assertEqual(result, "Game Over")

if __name__ == '__main__':
    unittest.main()
