#################################
# CSC 102 Defuse the Bomb Project
# GUI and Phase class definitions – Consolidated
#################################

# import the configs
from bomb_configs import *            # component definitions, targets, flags
# other imports
from tkinter import *
import tkinter
from threading import Thread
from time import sleep
import os, sys
from PIL import Image, ImageTk

#########
# classes
#########
# the LCD display GUI
class Lcd(Frame):
    def __init__(self, window):
        super().__init__(window, bg="black")
        window.attributes("-fullscreen", True)
        self._timer = None
        self._button = None
        self.setupBoot()

    def setupBoot(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.columnconfigure(2, weight=1)
        self._lscroll = Label(self, bg="black", fg="white", font=("Courier New", 14), text="", justify=LEFT)
        self._lscroll.grid(row=0, column=0, columnspan=3, sticky=W)
        self.pack(fill=BOTH, expand=True)

    def setup(self):
        self._ltimer   = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Time left: ")
        self._lkeypad  = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Keypad phase: ")
        self._lwires   = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Wires phase: ")
        self._lbutton  = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Button phase: ")
        self._ltoggles = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Toggles phase: ")
        self._lstrikes = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Strikes left: ")
        self._ltimer.grid(  row=1, column=0, columnspan=3, sticky=W)
        self._lkeypad.grid( row=2, column=0, columnspan=3, sticky=W)
        self._lwires.grid(  row=3, column=0, columnspan=3, sticky=W)
        self._lbutton.grid( row=4, column=0, columnspan=3, sticky=W)
        self._ltoggles.grid(row=5, column=0, columnspan=2, sticky=W)
        self._lstrikes.grid(row=5, column=2,                sticky=W)
        if SHOW_BUTTONS:
            self._bpause = tkinter.Button(self, text="Pause", font=("Courier New",18), bg="red", fg="white", command=self.pause)
            self._bquit  = tkinter.Button(self, text="Quit",  font=("Courier New",18), bg="red", fg="white", command=self.quit)
            self._bpause.grid(row=6, column=0, pady=40)
            self._bquit.grid( row=6, column=2, pady=40)

    def setTimer(self, timer):  self._timer = timer
    def setButton(self, button):self._button = button
    def pause(self):
        # allow pause in both modes
        self._timer.pause()

    def conclusion(self, success=False):
        # clear all widgets
        for widget in self.winfo_children():
            widget.destroy()
        # banner
        text  = "DEFUSED!" if success else "💥 BOOM! 💥"
        color = "#00ff00" if success else "#ff0000"
        banner = Label(self, text=text, bg="black", fg=color,
                       font=("Courier New",48,"bold"))
        banner.place(relx=0.5, rely=0.3, anchor="center")
        # image
        img_file = "yayyy.jpg" if success else "boom.jpg"
        try:
            img = Image.open(img_file).resize((300,300), Image.ANTIALIAS)
            photo = ImageTk.PhotoImage(img)
            Label(self, image=photo, bg="black").place(relx=0.5, rely=0.6, anchor="center")
            self._banner_img = photo
        except:
            pass
        # buttons
        btn_y = 0.8
        self._bretry = Button(self,text="Retry",font=("Courier New",18),bg="gray20",fg="white",command=self.retry)
        self._bquit  = Button(self,text="Quit", font=("Courier New",18),bg="gray20",fg="white",command=self.quit)
        self._bretry.place(relx=0.3, rely=btn_y, anchor="center")
        self._bquit.place( relx=0.7, rely=btn_y, anchor="center")

    def retry(self):
        os.execv(sys.executable, [sys.executable] + [sys.argv[0]])
    def quit(self):
        if RPi:
            self._timer._running = False
            self._timer._component.blink_rate = 0
            self._timer._component.fill(0)
            for pin in self._button._rgb: pin.value = True
        exit(0)

# base phase thread
class PhaseThread(Thread):
    def __init__(self, name, component=None, target=None):
        super().__init__(name=name, daemon=True)
        self._component = component
        self._target    = target
        self._value     = None
        self._defused   = False
        self._failed    = False
        self._running   = False
    def defuse(self):
        self._defused = True
        self._running = False
    def fail(self):
        self._failed  = True
        self._running = False

# Timer phase
class Timer(PhaseThread):
    def __init__(self, component, initial_value, name="Timer"):
        super().__init__(name, component)
        self._value   = initial_value
        self._paused  = False
        self._min = self._sec = ""
        self._interval = 1
    def run(self):
        self._running = True
        while self._running:
            if not self._paused:
                self._min = f"{self._value//60:02d}"
                self._sec = f"{self._value%60:02d}"
                self._component.print(f"{self._min}:{self._sec}")
                sleep(self._interval)
                if self._value == 0:
                    self._running = False
                self._value -= 1
            else:
                sleep(0.1)
    def pause(self):
        self._paused = not self._paused
        self._component.blink_rate = (2 if self._paused else 0)
    def __str__(self):
        return f"{self._min}:{self._sec}" if not self._defused else "DEFUSED"

# Keypad phase with reset-on-fail
class Keypad(PhaseThread):
    def __init__(self, component, target, name="Keypad", max_len=6, reset_on_fail=True, feedback_fn=None):
        super().__init__(name, component, target)
        self._value        = ""
        self._max_len      = max_len
        self._reset_on_fail= reset_on_fail
        self._feedback_fn  = feedback_fn
    def run(self):
        self._running = True
        while self._running:
            if self._component.pressed_keys:
                key = str(self._component.pressed_keys[0])
                if self._feedback_fn: self._feedback_fn(key)
                while self._component.pressed_keys:
                    sleep(0.05)
                if key == "#" and self._value:
                    self._value = self._value[:-1]
                elif len(self._value) < self._max_len:
                    self._value += key
                if self._value == self._target:
                    self.defuse(); return
                if not self._target.startswith(self._value):
                    if self._reset_on_fail:
                        self._value = ""
                    else:
                        self.fail(); return
            sleep(0.1)
    def __str__(self):
        return "DEFUSED" if self._defused else self._value

# Wires phase
default = None
class Wires(PhaseThread):
    def __init__(self, component, target, name="Wires"):
        super().__init__(name, component, target)
        self._target_str = target
    def run(self):
        target_seq = [int(c) for c in self._target_str]
        cut_seq = []
        self._running = True
        while self._running:
            for idx, wire in enumerate(self._component):
                cut = wire.is_cut() if hasattr(wire, 'is_cut') else wire.value
                if cut and idx not in cut_seq:
                    cut_seq.append(idx)
                    if len(cut_seq) == len(target_seq):
                        if cut_seq == target_seq: self.defuse()
                        else: self.fail()
                        return
            sleep(0.1)
    def __str__(self):
        bits = ''.join(
            '1' if (wire.is_cut() if hasattr(wire, 'is_cut') else wire.value) else '0'
            for wire in self._component
        )
        return "DEFUSED" if self._defused else bits

# Button phase
class Button(PhaseThread):
    def __init__(self, component_state, component_rgb, target, color, timer, name="Button"):
        super().__init__(name, component_state, target)
        self._timer = timer
        self._rgb   = component_rgb
        self._color = color
        self._pressed = False
    def run(self):
        # correct LED polarity: False=off, True=on
        self._rgb[0].value = (self._color == 'R')
        self._rgb[1].value = (self._color == 'G')
        self._rgb[2].value = (self._color == 'B')
        self._running = True
        while self._running:
            val = self._component.value
            if val and not self._pressed:
                self._pressed = True
            if not val and self._pressed:
                if self._target is None or str(self._target) in self._timer._sec:
                    self.defuse()
                else:
                    self.fail()
                return
            sleep(0.1)
    def __str__(self):
        return "DEFUSED" if self._defused else ("Pressed" if self._component.value else "Released")

# Toggles phase
class Toggles(PhaseThread):
    def __init__(self, component, target, name="Toggles"):
        super().__init__(name, component, target)
    def run(self):
        self._running = True
        prev = None
        while self._running:
            # read real or mock
            bits = [str(int(pin.read())) for pin in self._component] if hasattr(self._component[0], 'read') else [str(int(pin.value)) for pin in self._component]
            curr = ''.join(bits)
            if curr != prev:
                if not self._target.startswith(curr):
                    self.fail(); return
                if curr == self._target:
                    self.defuse(); return
                prev = curr
            sleep(0.1)
    def __str__(self):
        return "DEFUSED" if self._defused else ''.join(
            '1' if (pin.read() if hasattr(pin, 'read') else pin.value) else '0'
            for pin in self._component
        )
