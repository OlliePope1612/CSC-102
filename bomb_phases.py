"""
bomb_phases.py
Defines PhaseThread base class and concrete phase subclasses:
Timer, Keypad, Wires, Toggles, Button, and the Lcd GUI frame.
"""
import time
from threading import Thread
from tkinter import Frame, Label
from PIL import Image, ImageTk
from bomb_configs import *

##### GUI / LCD #####
class Lcd(Frame):
    def __init__(self, master):
        super().__init__(master, bg="black")
        master.attributes("-fullscreen", True)
        self._timer = None
        self._button = None
        self.pack(fill='both', expand=True)
        if ANIMATE:
            self._boot_label = Label(self, bg="black", fg="white", font=("Courier", 14), justify='left')
            self._boot_label.pack(anchor='nw', padx=20, pady=20)
        else:
            self.setup_game()

    def setup_boot(self):
        try:
            self._boot_label.config(text="")
        except:
            return
        def step(i=0):
            if not hasattr(self, '_boot_label'):
                return
            if i < len(boot_text):
                try:
                    self._boot_label['text'] += boot_text[i]
                    self.after(30, step, i+1)
                except:
                    return
        step()

    def setup_game(self):
        for w in self.winfo_children(): w.destroy()
        font = ("Courier", 16, "bold")
        self._ltime    = Label(self, text="Time: ", fg="#00FF00", bg="black", font=font)
        self._lstrikes = Label(self, text=f"Strikes: {NUM_STRIKES}", fg="#00FF00", bg="black", font=font)
        self._lkeypad  = Label(self, text="Keypad: ...", fg="#00FF00", bg="black", font=font)
        self._lwires   = Label(self, text="Wires: ...", fg="#00FF00", bg="black", font=font)
        self._ltoggles = Label(self, text="Toggles: ...", fg="#00FF00", bg="black", font=font)
        self._lbutton  = Label(self, text="Button: ...", fg="#00FF00", bg="black", font=font)
        for idx, lbl in enumerate((self._ltime, self._lstrikes,
                                   self._lkeypad, self._lwires,
                                   self._ltoggles, self._lbutton)):
            lbl.place(relx=0.02, rely=0.1 + idx*0.12, anchor='nw')

    def set_timer(self, timer): self._timer = timer
    def set_button(self, button): self._button = button

    def update(self, keypad, wires, toggles, button, strikes):
        if self._timer:
            self._ltime['text'] = f"Time: {self._timer.as_mmss()}"
        self._lstrikes['text'] = f"Strikes: {strikes}"
        self._lkeypad['text'] = f"Keypad: {str(keypad)}"
        self._lwires['text']   = f"Wires: {str(wires)}"
        self._ltoggles['text']= f"Toggles: {str(toggles)}"
        self._lbutton['text']  = f"Button: {str(button)}"

    def conclude(self, success: bool):
        for w in self.winfo_children(): w.destroy()
        msg = ">>> DEFUSED <<<" if success else "!!! BOOM !!!"
        color = "#00FF00" if success else "#FF0000"
        Label(self, text=msg, fg=color, bg="black", font=("Courier", 32, "bold")).pack(expand=True)

##### Phase base #####
class PhaseThread(Thread):
    def __init__(self, component, target):
        super().__init__(daemon=True)
        self._component = component
        self._target    = str(target)
        self._defused   = False
        self._failed    = False
        self._running   = True
    def defuse(self):
        self._defused = True
        self._running = False
    def fail(self):
        self._failed = True
        self._running = False
    def __str__(self):
        return "DEFUSED" if self._defused else "FAILED" if self._failed else "..."

##### Timer Phase #####
class Timer(PhaseThread):
    def __init__(self, component, initial):
        super().__init__(component, initial)
        self._value = int(initial)
    def run(self):
        while self._running and self._value >= 0:
            mins, secs = divmod(self._value, 60)
            self._component.print(f"{mins:02d}:{secs:02d}")
            time.sleep(1)
            self._value -= 1
        if self._value < 0:
            self.fail()
    def as_mmss(self):
        m, s = divmod(max(self._value,0), 60)
        return f"{m:02d}:{s:02d}"

##### Keypad Phase #####
class Keypad(PhaseThread):
    def __init__(self, component, code):
        super().__init__(component, code)
        self._entry = ""

    def run(self):
        last_key = None
        while self._running and not self._defused:
            keys = getattr(self._component, 'pressed_keys', [])
            if keys:
                key = str(keys[0])
                # only act on a new press
                if key != last_key:
                    last_key = key
                    if key == '*':
                        # reset entry on star
                        self._entry = ""
                    elif key == '#':
                        # submit on hash
                        if self._entry == self._target:
                            self.defuse()
                            return
                        else:
                            self._failed = True
                            # clear entry so user can retry
                            self._entry = ""
                    elif key.isdigit():
                        # append digit
                        self._entry += key
            else:
                # no keys pressed, reset last_key
                last_key = None
            time.sleep(0.05)

    def __str__(self):
        return self._entry or "..."

##### Wires Phase #####
class Wires(PhaseThread):
    def __init__(self, component, pattern):
        super().__init__(component, pattern)
    def run(self):
        while self._running:
            bits = []
            for w in self._component:
                if hasattr(w, 'is_cut'):
                    val = w.is_cut()
                elif hasattr(w, 'read'):
                    val = bool(w.read())
                else:
                    val = bool(getattr(w, 'value', False))
                bits.append('1' if val else '0')
            current = ''.join(bits)
            if current == self._target:
                self.defuse()
            time.sleep(0.1)
    def __str__(self):
        return ''.join('1' if (w.is_cut() if hasattr(w, 'is_cut') else bool(getattr(w, 'value', False))) else '0' for w in self._component)

##### Toggles Phase #####
class Toggles(PhaseThread):
    def __init__(self, component, pattern):
        super().__init__(component, pattern)
    def run(self):
        while self._running:
            current = ''.join(str(int(pin.read() if hasattr(pin, 'read') else pin.value)) for pin in self._component)
            if current == self._target:
                self.defuse()
            time.sleep(0.1)
    def __str__(self):
        return ''.join(str(int(pin.read() if hasattr(pin, 'read') else pin.value)) for pin in self._component)

##### Button Phase #####
class Button(PhaseThread):
    def __init__(self, state_pin, rgb_pins, color, presses, timer):
        super().__init__(state_pin, presses)
        self._rgb      = rgb_pins
        self._original = color
        self._presses  = int(presses)
        self._timer    = timer
        self._count    = 0
        self._start_ts = None
        # light the “defuse” LED initially
        self.set_color(color)

    def set_color(self, color):
        # turn on only the LED matching `color`
        for i, led in enumerate(self._rgb):
            led.value = (['R','G','B'][i] != color)

    def run(self):
        import time
        from bomb_configs import BUTTON_MAX_TIME

        while self._running:
            if self._component.value:
                # wait for you to release the button
                while self._component.value:
                    time.sleep(0.02)
                # mark time on first press
                if self._count == 0:
                    self._start_ts = time.time()
                self._count += 1
                # if that was the last press, check your speed
                if self._count >= self._presses:
                    elapsed = time.time() - self._start_ts
                    if elapsed <= BUTTON_MAX_TIME:
                        self.defuse()
                    else:
                        self.fail()
                    return
            time.sleep(0.05)

    def __str__(self):
        return f"{self._count}/{self._presses}"
