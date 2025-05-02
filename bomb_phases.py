#################################
# CSC 102 Defuse the Bomb Project
# GUI and Phase class definitions – Final Version
#################################

# import the configs
from bomb_configs import *            # brings in component_7seg, component_keypad, etc.
# other imports
from tkinter import *
import tkinter
from threading import Thread
from time import sleep
import os, sys
from PIL import Image, ImageTk
import time

#########
# GUI class
#########
class Lcd(Frame):
    def __init__(self, window):
        super().__init__(window, bg="black")
        window.attributes("-fullscreen", True)
        self._timer = None
        self._button = None
        self.setupBoot()

    def setupBoot(self):
        for c,w in enumerate((1,2,1)): self.columnconfigure(c, weight=w)
        self._lscroll = Label(self, bg="black", fg="white",
                              font=("Courier New",14), text="", justify=LEFT)
        self._lscroll.grid(row=0, column=0, columnspan=3, sticky=W)
        self.pack(fill=BOTH, expand=True)

    def setup(self):
        self._ltimer   = Label(self, bg="black", fg="#00ff00", font=("Courier New",18), text="Time left: ")
        self._lkeypad  = Label(self, bg="black", fg="#00ff00", font=("Courier New",18), text="Keypad phase: ")
        self._lwires   = Label(self, bg="black", fg="#00ff00", font=("Courier New",18), text="Wires phase: ")
        self._lbutton  = Label(self, bg="black", fg="#00ff00", font=("Courier New",18), text="Button phase: ")
        self._ltoggles = Label(self, bg="black", fg="#00ff00", font=("Courier New",18), text="Toggles phase: ")
        self._lstrikes = Label(self, bg="black", fg="#00ff00", font=("Courier New",18), text="Strikes left: ")
        self._ltimer.grid(  row=1, column=0, columnspan=3, sticky=W)
        self._lkeypad.grid( row=2, column=0, columnspan=3, sticky=W)
        self._lwires.grid(  row=3, column=0, columnspan=3, sticky=W)
        self._lbutton.grid( row=4, column=0, columnspan=3, sticky=W)
        self._ltoggles.grid(row=5, column=0, columnspan=2, sticky=W)
        self._lstrikes.grid(row=5, column=2,                sticky=W)
        if SHOW_BUTTONS:
            self._bpause = tkinter.Button(self, text="Pause", font=("Courier New",18),
                                          bg="red", fg="white", command=self.pause)
            self._bquit  = tkinter.Button(self, text="Quit",  font=("Courier New",18),
                                          bg="red", fg="white", command=self.quit)
            self._bpause.grid(row=6, column=0, pady=40)
            self._bquit.grid( row=6, column=2, pady=40)

    def setTimer(self, timer):  self._timer = timer
    def setButton(self, button):self._button = button
    def pause(self):           self._timer.pause()

    def conclusion(self, success=False):
        # clear all
        for w in self.winfo_children(): w.destroy()
        # banner
        msg   = "DEFUSED!" if success else "💥 BOOM! 💥"
        color = "#00ff00" if success else "#ff0000"
        Label(self, text=msg, bg="black", fg=color,
              font=("Courier New",48,"bold")).place(relx=0.5, rely=0.3, anchor="center")
        # image
        imgfile = "yayyy.jpg" if success else "boom.jpg"
        try:
            img = Image.open(imgfile).resize((300,300), Image.ANTIALIAS)
            photo = ImageTk.PhotoImage(img)
            Label(self, image=photo, bg="black").place(relx=0.5, rely=0.6, anchor="center")
            self._banner_img = photo
        except:
            pass
        # retry/quit buttons
        y = 0.8
        tkinter.Button(self, text="Retry", font=("Courier New",18),
                        bg="gray20", fg="white", command=self.retry
                       ).place(relx=0.3, rely=y, anchor="center")
        tkinter.Button(self, text="Quit",  font=("Courier New",18),
                        bg="gray20", fg="white", command=self.quit
                       ).place(relx=0.7, rely=y, anchor="center")

    def retry(self): os.execv(sys.executable, [sys.executable]+[sys.argv[0]])
    def quit(self):
        if RPi:
            self._timer._running = False; self._timer._component.blink_rate = 0
            self._timer._component.fill(0)
            for p in self._button._rgb: p.value = True
        exit(0)

# base thread
class PhaseThread(Thread):
    def __init__(self, name, component=None, target=None):
        super().__init__(daemon=True, name=name)
        self._component = component; self._target = target
        self._defused = False; self._failed = False; self._running = False
    def defuse(self): self._defused, self._running = True, False
    def fail( self): self._failed,  self._running = True, True

# Timer Logic
class Timer(PhaseThread):
    def __init__(self, component, initial_value, name="Timer"):
        super().__init__(name, component)
        self._value  = initial_value
        self._paused = False
        self._min = self._sec = ""
        self._interval = 1
    def run(self):
        import time
        self._running = True
        next_t = time.time() + self._interval
        while self._running:
            if not self._paused and time.time() >= next_t:
                self._value -= 1
                self._min = f"{max(self._value,0)//60:02d}"
                self._sec = f"{max(self._value,0)%60:02d}"
                self._component.print(f"{self._min}:{self._sec}")
                next_t += self._interval
                if self._value < 0: self._running = False
            sleep(0.05)
    def pause(self):
        self._paused = not self._paused
        self._component.blink_rate = (2 if self._paused else 0)
    def __str__(self):
        return "DEFUSED" if self._defused else f"{self._min}:{self._sec}"

# Keypad Logic (* to clear, # to submit)
class Keypad(PhaseThread):
    def __init__(self, comp, target, name="Keypad"):  # max length = target length
        super().__init__(name, comp, target)
        self._value = ""
    def run(self):
        self._running = True
        while self._running:
            if self._component.pressed_keys:
                key = str(self._component.pressed_keys[0])
                # debounce
                while self._component.pressed_keys:
                    sleep(0.05)
                if key == "*":
                    self._value = ""
                elif key == "#":
                    # submit
                    if self._value == self._target:
                        self.defuse()
                        return
                    else:
                        self.fail()
                elif len(self._value) < len(self._target):
                    self._value += key
            sleep(0.1)
    def __str__(self):
        return "DEFUSED" if self._defused else self._value

# Wires Logic
# in bomb_phases.py, replace your existing Wires class with:

class Wires(PhaseThread):
    def __init__(self, component, target, name="Wires"):
        super().__init__(name, component, target)
        # store the exact bitstring you want to see, e.g. "01101"
        self._target_bits = target

    def run(self):
        self._running = True
        while self._running:
            # build a current 0/1 string from your wires
            bits = "".join(
                "1" if (w.is_cut() if hasattr(w, "is_cut") else w.value)
                else "0"
                for w in self._component
            )
            # once the live pattern exactly matches, defuse
            if bits == self._target_bits:
                self.defuse()
                return
            sleep(0.1)

    def __str__(self):
        return "DEFUSED" if self._defused else "".join(
            "1" if (w.is_cut() if hasattr(w, "is_cut") else w.value) else "0"
            for w in self._component
        )

# Button Logic
class Button(PhaseThread):
    colors = ["R", "G", "B"]

    def __init__(self, state_pin, rgb_pins, target, initial_color, timer, name="Button"):
        super().__init__(name, state_pin, target)
        self._rgb          = rgb_pins
        self._timer        = timer
        self._pressed      = False

        # start cycle at the initial color
        self._color_index  = Button.colors.index(initial_color)
        self._last_cycle   = time.time()
        self._cycle_period = 10.0  # seconds between color changes

        # light the starting color
        self._set_color(initial_color)

    def _set_color(self, color):
        # False → LED on; True → LED off
        self._rgb[0].value = (color != "R")
        self._rgb[1].value = (color != "G")
        self._rgb[2].value = (color != "B")

    def run(self):
        self._running = True
        while self._running:
            now = time.time()
            # only switch once every self._cycle_period seconds
            if now - self._last_cycle >= self._cycle_period:
                self._last_cycle = now
                self._color_index = (self._color_index + 1) % len(Button.colors)
                self._set_color(Button.colors[self._color_index])

            # check for a press → release defuse/strike sequence
            v = self._component.value
            if v and not self._pressed:
                self._pressed = True
            if not v and self._pressed:
                if (self._target is None) or (str(self._target) in self._timer._sec):
                    self.defuse()
                else:
                    self.fail()
                return

            sleep(0.05)

    def __str__(self):
        return "DEFUSED" if self._defused else ("Pressed" if self._component.value else "Released")
        
# Toggles Logic
class Toggles(PhaseThread):
    def __init__(self, component, target, name="Toggles"):
        super().__init__(name, component, target)

    def run(self):
        self._running = True
        while self._running:
            # read the current 0/1 state of each switch
            bits = []
            for pin in self._component:
                if hasattr(pin, "read"):
                    bits.append(str(int(pin.read())))
                else:
                    bits.append(str(int(pin.value)))
            current = "".join(bits)

            # only defuse on a full match
            if current == self._target:
                self.defuse()
                return

            sleep(0.1)

    def __str__(self):
        if self._defused:
            return "DEFUSED"
        return "".join(
            "1" if (p.read() if hasattr(p, "read") else p.value) else "0"
            for p in self._component
        )
