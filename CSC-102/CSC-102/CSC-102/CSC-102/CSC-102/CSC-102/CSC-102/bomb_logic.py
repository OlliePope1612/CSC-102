# bomb_logic.py

from bomb_configs import toggles_target, wires_target, keypad_target, button_target, NUM_STRIKES

class BombDefusalGame:
    def __init__(self):
        self.questions = [
            {"correct": toggles_target},
            {"correct": wires_target},
            {"correct": keypad_target},
            {"correct": button_target},
        ]
        self.MAX_PHASES = len(self.questions)
        self.MAX_STRIKES = NUM_STRIKES
        self.strikes = 0
        self._current_phase = 0

    def answer(self, response):
        correct = self.questions[self._current_phase]["correct"]
        if response == correct:
            if self._current_phase == self.MAX_PHASES - 1:
                self._current_phase += 1
                return "Defused"
            else:
                self._current_phase += 1
                return "Correct"
        else:
            self.strikes += 1
            if self.strikes >= self.MAX_STRIKES:
                return "Game Over"
            return "Incorrect"
