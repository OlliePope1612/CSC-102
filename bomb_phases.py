"""
bomb_phases.py
Defines each puzzle phase (Timer, Keypad, Wires, Button, Toggles) and the Lcd GUI.
"""
from threading import Thread
from time import sleep
from tkinter import Frame, Label

# Base worker thread for a phase
class PhaseThread(Thread):
    def __init__(self, component, target):
        super().__init__(daemon=True)
        self._component = component
        self._target    = target
        self._defused   = False
        self._failed    = False
        self._running   = False
    def defuse(self):
        self._defused = True
        self._running = False
    def fail(self):
        self._failed  = True
        self._running = False

# Timer phase: counts down once per second
class Timer(PhaseThread):
    def __init__(self, component, seconds):
        super().__init__(component, seconds)
        self._value  = seconds
        self._paused = False
        self._min    = '00'
        self._sec    = '00'
    def run(self):
        self._running = True
        while self._running and self._value >= 0:
            if not self._paused:
                m, s = divmod(self._value, 60)
                self._min = f'{m:02d}'; self._sec = f'{s:02d}'
                self._component.print(f'{self._min}:{self._sec}')
                self._value -= 1
            sleep(1)
    def pause(self):
        self._paused = not self._paused
        self._component.blink_rate = (2 if self._paused else 0)
    def __str__(self):
        return 'DEFUSED' if self._defused else f'{self._min}:{self._sec}'

# Keypad phase: * clears, # submits
class Keypad(PhaseThread):
    def __init__(self, component, target):
        super().__init__(component, target)
        self._value = ''
    def run(self):
        self._running = True
        while self._running:
            keys = getattr(self._component, 'pressed_keys', [])
            if keys:
                k = str(keys[0])
                while getattr(self._component, 'pressed_keys', []):
                    sleep(0.1)
                if k == '*':
                    self._value = ''
                elif k == '#':
                    if self._value == self._target:
                        self.defuse()
                    else:
                        self.fail()
                    return
                else:
                    self._value += k
            sleep(0.1)
    def __str__(self):
        return 'DEFUSED' if self._defused else self._value

# Wires phase: live 0/1 string must match exactly
class Wires(PhaseThread):
    def __init__(self, component, target):
        super().__init__(component, target)
    def run(self):
        self._running = True
        while self._running:
            bits = ''.join(
                '1' if (w.is_cut() if hasattr(w, 'is_cut') else w.value) else '0'
                for w in self._component
            )
            if bits == self._target:
                self.defuse()
                return
            sleep(0.1)
    def __str__(self):
        return 'DEFUSED' if self._defused else ''.join(
            '1' if (w.is_cut() if hasattr(w, 'is_cut') else w.value) else '0'
            for w in self._component
        )

# Button phase: press+release to defuse (or used as submitter for other puzzles)
class Button(PhaseThread):
    def __init__(self, state_pin, rgb_pins, target, timer):
        super().__init__(state_pin, target)
        self._rgb     = rgb_pins
        self._timer   = timer
        self._pressed = False
    def run(self):
        # turn on all RGB channels initially
        for p in self._rgb: p.value = False
        self._running = True
        while self._running:
            v = self._component.value
            if v and not self._pressed:
                self._pressed = True
            if not v and self._pressed:
                # release: check either timer digit or always defuse
                if self._target is None or self._timer._sec == '05':
                    self.defuse()
                else:
                    self.fail()
                return
            sleep(0.1)
    def __str__(self):
        return 'DEFUSED' if self._defused else ('Pressed' if self._component.value else 'Released')

# Toggles phase: live 0/1 string must match exactly
class Toggles(PhaseThread):
    def __init__(self, component, target):
        super().__init__(component, target)
    def run(self):
        self._running = True
        while self._running:
            bits = ''.join(
                '1' if (pin.read() if hasattr(pin, 'read') else pin.value) else '0'
                for pin in self._component
            )
            if bits == self._target:
                self.defuse()
                return
            sleep(0.1)
    def __str__(self):
        return 'DEFUSED' if self._defused else ''.join(
            '1' if (pin.read() if hasattr(pin, 'read') else pin.value) else '0'
            for pin in self._component
        )

# Simple full‐screen LCD GUI
class Lcd(Frame):
    def __init__(self, window):
        super().__init__(window, bg='black')
        window.attributes('-fullscreen', True)
        self._timer = None
        self._button = None
        self.pack(fill='both', expand=True)
    def setup(self):
        self.labels = {}
        for name in ('Time ', 'Keypad ', 'Wires ', 'Button ', 'Toggles ', 'Strikes '):
            lbl = Label(self, text=name, fg='#0f0', bg='black',
                        font=('Courier',18), anchor='w')
            lbl.pack(fill='x')
            self.labels[name.strip()] = lbl
    def setTimer(self, t):  self._timer = t
    def setButton(self, b): self._button = b
    def conclusion(self, success):
        for w in self.winfo_children(): w.destroy()
        msg = 'DEFUSED!' if success else '💥 BOOM! 💥'
        fg  = '#0f0' if success else '#f00'
        Label(self, text=msg, fg=fg, bg='black',
              font=('Courier',48)).pack(expand=True)
