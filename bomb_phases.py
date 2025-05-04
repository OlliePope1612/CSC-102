import time
from tkinter import Tk

# --- phase base class ---
class Phase:
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
class TimerPhase(Phase):
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

class KeypadPhase(Phase):
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

class WiresPhase(Phase):
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

import time

class TogglesPhase(Phase):
    def __init__(self, component, target):
        """
        component: list of GPIO-toggle pins (with .read() → 0/1 or .value)
        target:    bitstring, e.g. "1010"
        """
        super().__init__(target)
        self.comp = component

    def read(self):
        # nothing automatic—defusal only on explicit submit via ButtonPhase
        pass

    def submit(self):
        # build current bitstring
        bits = "".join(
            "1"
            if (pin.read() if hasattr(pin, "read") else pin.value)
            else "0"
            for pin in self.comp
        )
        if bits == self.target:
            self.defuse()
        else:
            self.fail()

    def display(self):
        # always show live switch positions
        return "".join(
            "1"
            if (pin.read() if hasattr(pin, "read") else pin.value)
            else "0"
            for pin in self.comp
        )


class ButtonPhase(Phase):
    COLORS = ["R", "G", "B"]  # cycle order

    def __init__(self, state_pin, rgb_pins, target, initial_color, timer_phase, submit_phases=()):
        """
        state_pin     -- the DigitalInOut pushbutton input (.value True/False)
        rgb_pins      -- list of three RGB output pins (.value False=on/True=off)
        target        -- digit to match on release (or None to always defuse)
        initial_color -- one of "R","G","B"
        timer_phase   -- your TimerPhase instance (to inspect its .value)
        submit_phases -- tuple of (WiresPhase, TogglesPhase) to submit when blue
        """
        super().__init__(target)
        self.state  = state_pin
        self.rgb    = rgb_pins
        self.timer  = timer_phase
        self._submit = submit_phases

        # cycling state
        self.color_index = ButtonPhase.COLORS.index(initial_color)
        self.last_cycle  = time.time()

        # press detection
        self._pressed = False

        # light starting color
        self._apply_color(initial_color)

    def _apply_color(self, c):
        # False => LED on; True => LED off
        self.rgb[0].value = (c != "R")
        self.rgb[1].value = (c != "G")
        self.rgb[2].value = (c != "B")

    def read(self):
        now = time.time()
        # cycle every 10 seconds
        if now - self.last_cycle >= 10:
            self.last_cycle = now
            self.color_index = (self.color_index + 1) % len(ButtonPhase.COLORS)
            self._apply_color(ButtonPhase.COLORS[self.color_index])

        v = self.state.value
        # detect press
        if v and not self._pressed:
            self._pressed = True
        # detect release
        if not v and self._pressed:
            self._pressed = False

            current_color = ButtonPhase.COLORS[self.color_index]
            if current_color == "B":
                # “submit” Wires & Toggles
                for phase in self._submit:
                    phase.submit()
            else:
                # defuse/release puzzle
                # look at last timer‐seconds digit
                sec = self.timer.value % 60
                last_digit = sec % 10
                if (self.target is None) or (last_digit == int(self.target)):
                    self.defuse()
                else:
                    self.fail()

    def display(self):
        if self.defused:
            return "DEFUSED"
        return "Pressed" if self.state.value else "Released"
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
