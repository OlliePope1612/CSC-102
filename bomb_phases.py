import time
from tkinter import Tk

# --- phase base class ---
class PhaseThread:
    def __init__(self, target):
        self.target = target
        self.defused = False
        self.failed  = False

    def read(self):
        """Override to sample hardware/input; should call self.defuse() or self.fail() as needed."""
        pass

    def display(self):
        """Return the string to show on the LCD for this phase."""
        return "DEFUSED" if self.defused else "????"

    def defuse(self):
        if not self.defused:
            self.defused = True

    def fail(self):
        if not self.failed:
            self.failed = True

# --- concrete phases ---
class TimerPhase(PhaseThread):
    def __init__(self, component, start_secs):
        super().__init__(None)
        self.comp   = component
        self.value  = start_secs
        self.last_t = time.time()

    def read(self):
        now = time.time()
        if now - self.last_t >= 1:
            self.value -= 1
            self.last_t = now
            self.comp.print(f"{self.value//60:02d}:{self.value%60:02d}")
            if self.value < 0:
                self.fail()

    def display(self):
        return f"{self.value//60:02d}:{self.value%60:02d}"

class KeypadPhase(PhaseThread):
    def __init__(self, component, target):
        super().__init__(target)
        self.comp  = component
        self.value = ""

    def read(self):
        if self.comp.pressed_keys:
            k = str(self.comp.pressed_keys[0])
            while self.comp.pressed_keys: pass  # simple debounce
            if k == "*":
                self.value = ""
            elif k == "#":
                (self.defuse if self.value == self.target else self.fail)()
            elif len(self.value) < len(self.target):
                self.value += k

    def display(self):
        return "DEFUSED" if self.defused else self.value

class WiresPhase(PhaseThread):
    def __init__(self, component, target):
        super().__init__(target)
        self.comp = component

    def read(self):
        # nothing to do until user presses “submit” on the button
        pass

    def submit(self):
        bits = "".join("1" if w.is_cut() else "0" for w in self.comp)
        (self.defuse if bits == self.target else self.fail)()

    def display(self):
        return "".join("1" if w.is_cut() else "0" for w in self.comp)

# TogglesPhase is identical to WiresPhase but reads toggle pins
# ButtonPhase you’d implement similarly—either defuse on timing match
# or route “submit” to Wires/Toggles if it’s in that sub-state.

# --- main application ---

class BombApp:
    def __init__(self):
        self.root = Tk()
        # build your GUI here, stash your Label objects as self.lbl_timer, self.lbl_keypad, ...
        # instantiate your five phases in order:
        self.phases = [
            TimerPhase(component_7seg, COUNTDOWN),
            KeypadPhase(component_keypad, str(keypad_target)),
            WiresPhase(component_wires,   bin(wires_target)[2:].zfill(5)),
            TogglesPhase(component_toggles, bin(toggles_target)[2:].zfill(4)),
            ButtonPhase(component_button_state, component_button_RGB, button_target, button_color)
        ]
        self.current = 0
        self.strikes = NUM_STRIKES

        # start the update loop
        self.root.after(100, self.update)

    def update(self):
        # 1) Always tick the timer
        self.phases[0].read()

        # 2) For the current challenge (index 1–4), call .read()
        #    so keypad polls, toggles simply updates display, etc.
        if 1 <= self.current < len(self.phases):
            self.phases[self.current].read()

        # 3) Update all five labels:
        self.lbl_timer .config(text=self.phases[0].display())
        self.lbl_keypad.config(text=self.phases[1].display())
        self.lbl_wires .config(text=self.phases[2].display())
        self.lbl_toggle.config(text=self.phases[3].display())
        self.lbl_button.config(text=self.phases[4].display())
        self.lbl_strike.config(text=f"Strikes: {self.strikes}")

        # 4) Check for any newly‐failed or newly‐defused phase:
        for i, p in enumerate(self.phases):
            if p.failed and i == self.current:
                self.strikes -= 1
                self.stomp()   # reset wires/toggles/keypad for retry
            if p.defused and i == self.current:
                self.current += 1
                # if we’ve finished all phases, show “DEFUSED!” and stop
                if self.current >= len(self.phases):
                    self.show_banner(True)
                    return

        # 5) Boom if timer ran out or strikes ≤ 0
        if self.phases[0].failed or self.strikes <= 0:
            self.show_banner(False)
            return

        # 6) Otherwise keep going
        self.root.after(100, self.update)

    def stomp(self):
        # reset only the current phase’s pins or value
        # e.g. clear keypad buffer, re‐uncut wires, re‐flip toggles
        pass

    def show_banner(self, defused):
        # tear down the five‐label UI and show your “DEFUSED!” or “BOOM!” screen
        pass

    def run(self):
        self.root.mainloop()

# and in bomb.py:
if __name__=="__main__":
    BombApp().run()
