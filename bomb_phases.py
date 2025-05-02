#################################
# CSC 102 Defuse the Bomb Project
# GUI and Phase class definitions – Final Hardware Fixes
#################################

# import the configs
from bomb_configs import *
# other imports
from tkinter import *
import tkinter
from threading import Thread
from time import sleep
import os, sys
from PIL import Image, ImageTk

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
        for c in range(3): self.columnconfigure(c, weight=[1,2,1][c])
        self._lscroll = Label(self, bg="black", fg="white",
                              font=("Courier New",14), text="", justify=LEFT)
        self._lscroll.grid(row=0, column=0, columnspan=3, sticky=W)
        self.pack(fill=BOTH, expand=True)

    def setup(self):
        labels = [("Time left: ",1),("Keypad phase: ",2),
                  ("Wires phase: ",3),("Button phase: ",4),
                  ("Toggles phase: ",5),("Strikes left: ",5)]
        self._ltimer   = Label(self, bg="black", fg="#00ff00", font=("Courier New",18), text=labels[0][0])
        self._lkeypad  = Label(self, bg="black", fg="#00ff00", font=("Courier New",18), text=labels[1][0])
        self._lwires   = Label(self, bg="black", fg="#00ff00", font=("Courier New",18), text=labels[2][0])
        self._lbutton  = Label(self, bg="black", fg="#00ff00", font=("Courier New",18), text=labels[3][0])
        self._ltoggles = Label(self, bg="black", fg="#00ff00", font=("Courier New",18), text=labels[4][0])
        self._lstrikes = Label(self, bg="black", fg="#00ff00", font=("Courier New",18), text=labels[5][0])
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
        for w in self.winfo_children(): w.destroy()
        text  = "DEFUSED!" if success else "💥 BOOM! 💥"
        color = "#00ff00" if success else "#ff0000"
        Label(self, text=text, bg="black", fg=color,
              font=("Courier New",48,"bold")).place(relx=0.5, rely=0.3, anchor="center")
        imgfile = "yayyy.jpg" if success else "boom.jpg"
        try:
            img = Image.open(imgfile).resize((300,300), Image.ANTIALIAS)
            photo = ImageTk.PhotoImage(img)
            Label(self, image=photo, bg="black").place(relx=0.5, rely=0.6, anchor="center")
            self._banner_img = photo
        except:
            pass
        y = 0.8
        Button(self, text="Retry", font=("Courier New",18), bg="gray20", fg="white",
               command=self.retry).place(relx=0.3, rely=y, anchor="center")
        Button(self, text="Quit",  font=("Courier New",18), bg="gray20", fg="white",
               command=self.quit).place( relx=0.7, rely=y, anchor="center")

    def retry(self): os.execv(sys.executable, [sys.executable]+[sys.argv[0]])
    def quit(self):
        if RPi:
            self._timer._running = False; self._timer._component.blink_rate = 0
            self._timer._component.fill(0)
            for pin in self._button._rgb: pin.value = True
        exit(0)

# base class
class PhaseThread(Thread):
    def __init__(self, name, component=None, target=None):
        super().__init__(daemon=True, name=name)
        self._component = component; self._target = target
        self._defused = False; self._failed = False; self._running = False
    def defuse(self): self._defused=True; self._running=False
    def fail( self): self._failed =True; self._running=False

# Timer phase
default=None
class Timer(PhaseThread):
    def __init__(self, component, initial_value, name="Timer"):
        super().__init__(name, component)
        self._value   = initial_value
        self._paused  = False
        self._min = self._sec = ""
        self._interval = 1

    def run(self):
        import time
        self._running = True
        next_tick = time.time() + self._interval
        while self._running:
            if not self._paused and time.time() >= next_tick:
                # decrement and update
                self._value -= 1
                self._min = f"{max(self._value,0)//60:02d}"
                self._sec = f"{max(self._value,0)%60:02d}"
                # update hardware display
                self._component.print(f"{self._min}:{self._sec}")
                next_tick += self._interval
                if self._value < 0:
                    self._running = False
            else:
                sleep(0.05)

    def pause(self):
        self._paused = not self._paused
        self._component.blink_rate = (2 if self._paused else 0)
        
    def __str__(self): return "DEFUSED" if self._defused else f"{self._min}:{self._sec}"

# Keypad phase – free entry until full length
class Keypad(PhaseThread):
    def __init__(self, component, target, name="Keypad", max_len=None):
        super().__init__(name, component, target)
        self._value = ""
        self._max   = max_len or len(target)

    def run(self):
        self._running = True
        while self._running:
            if self._component.pressed_keys:
                key = str(self._component.pressed_keys[0])
                # Debounce
                while self._component.pressed_keys:
                    sleep(0.05)
                # Reset input on '*'
                if (key == "*" and STAR_CLEARS_PASS):
                    self._value = ""
                elif len(self._value) < self._max:
                    self._value += key
                # Check for completion
                if len(self._value) == len(self._target):
                    if self._value == self._target:
                        self.defuse()
                    else:
                        self.fail()
                    return
            sleep(0.1)
    def __str__(self):
        return "DEFUSED" if self._defused else self._value
    def __str__(self): return "DEFUSED" if self._defused else self._value

# Wires phase
class Wires(PhaseThread):
    def __init__(self, comp, target, name="Wires"):
        super().__init__(name, comp, target);
        self._tstr=target
    def run(self):
        seq=[]; tgt=[int(c) for c in self._tstr]; self._running=True
        while self._running:
            for i,w in enumerate(self._component):
                cut = w.is_cut() if hasattr(w,'is_cut') else w.value
                if cut and i not in seq:
                    seq.append(i)
                    if len(seq)==len(tgt):
                        (self.defuse() if seq==tgt else self.fail()); return
            sleep(0.1)
    def __str__(self):
        bits=''.join('1' if (w.is_cut() if hasattr(w,'is_cut') else w.value) else '0'
                     for w in self._component)
        return "DEFUSED" if self._defused else bits

# Button phase
class Button(PhaseThread):
    def __init__(self, state, rgb, target, color, timer, name="Button"):
        super().__init__(name, state, target)
        self._rgb=color and rgb or rgb; self._color=color; self._timer=timer
        self._pressed=False
    def run(self):
        # True = LED on
        self._rgb[0].value = (self._color=='R')
        self._rgb[1].value = (self._color=='G')
        self._rgb[2].value = (self._color=='B')
        self._running=True
        while self._running:
            val=self._component.value
            if val and not self._pressed: self._pressed=True
            if not val and self._pressed:
                if self._target is None or str(self._target) in self._timer._sec:
                    self.defuse()
                else: self.fail()
                return
            sleep(0.1)
    def __str__(self):
        return "DEFUSED" if self._defused else ("Pressed" if self._component.value else "Released")

# Toggles phase
class Toggles(PhaseThread):
    def __init__(self, comp, target, name="Toggles"):
        super().__init__(name, comp, target)
    def run(self):
        prev=None; self._running=True
        while self._running:
            bits=[str(int(p.read())) for p in self._component] if hasattr(self._component[0],'read') else [str(int(p.value)) for p in self._component]
            curr=''.join(bits)
            if curr!=prev:
                if not self._target.startswith(curr): self.fail(); return
                if curr==self._target: self.defuse(); return
                prev=curr
            sleep(0.1)
    def __str__(self):
        return "DEFUSED" if self._defused else ''.join(
            '1' if (p.read() if hasattr(p,'read') else p.value) else '0'
            for p in self._component)
