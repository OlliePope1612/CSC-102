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
from bomb_configs import quagmire_lines, joe_lines, cleveland_lines

#########
# GUI class
#########

# --- Family Guy Character Commentary ---
quagmire_lines = [
    "Giggity! This keypad's hotter than Lois!",
    "I'd tap that... code.",
    "Giggity giggity goo!"
]

joe_lines = [
    "MY WHEELCHAIR'S DEAD!",
    "HELP! PUSH ME CLOSER!",
    "PETER, YOU'RE OUR ONLY HOPE!"
]

cleveland_lines = [
    "No no no no NO!",
    "Oh, that's not good...",
    "I'm getting outta here!"
]
class Lcd(Frame):
    def __init__(self, window):
        super().__init__(window)
        window.attributes("-fullscreen", True)
        # load a Family Guy background
        try:
            bg = Image.open("family_guy_bg.jpg")
            bg = bg.resize((window.winfo_screenwidth(), window.winfo_screenheight()), Image.ANTIALIAS)
            self._bg_image = ImageTk.PhotoImage(bg)
            bg_label = Label(self, image=self._bg_image)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception:
            # fallback to dark background
            self.configure(bg="#101010")
        self._timer = None
        self._button = None
        self.setupBoot()

    def setupBoot(self):
        # scrolling boot text on top in Family Guy font
        for c, w in enumerate((1,2,1)): self.columnconfigure(c, weight=w)
        self._lscroll = Label(self, bg="#000000", fg="#00ff00",
                              font=("Comic Sans MS", 16, "bold"), text="", justify=LEFT)
        self._lscroll.grid(row=0, column=0, columnspan=3, sticky=W, padx=20, pady=10)
        self.pack(fill=BOTH, expand=True)

    def setup(self):
        # phase status labels with themed styling
        style = {"bg": "#000000", "fg": "#ffcc00", "font": ("Comic Sans MS", 18, "bold"), "justify": LEFT}
        self._ltimer   = Label(self, text="Time left: ", **style)
        self._lkeypad  = Label(self, text="Keypad phase: ", **style)
        self._lwires   = Label(self, text="Wires phase: ", **style)
        self._lbutton  = Label(self, text="Button phase: ", **style)
        self._ltoggles = Label(self, text="Toggles phase: ", **style)
        self._lstrikes = Label(self, text="Strikes left: ", **style)
        # place labels
        self._ltimer.grid(  row=1, column=0, columnspan=3, sticky=W, padx=20)
        self._lkeypad.grid( row=2, column=0, columnspan=3, sticky=W, padx=20)
        self._lwires.grid(  row=3, column=0, columnspan=3, sticky=W, padx=20)
        self._lbutton.grid( row=4, column=0, columnspan=3, sticky=W, padx=20)
        self._ltoggles.grid(row=5, column=0, columnspan=2, sticky=W, padx=20)
        self._lstrikes.grid(row=5, column=2,                sticky=W, padx=20)
        if SHOW_BUTTONS:
            btn_style = {"font": ("Comic Sans MS", 18, "bold"), "bg": "#ff0000", "fg": "white"}
            self._bpause = tkinter.Button(self, text="Pause", command=self.pause, **btn_style)
            self._bquit  = tkinter.Button(self, text="Quit",  command=self.quit,  **btn_style)
            self._bpause.grid(row=6, column=0, pady=30)
            self._bquit.grid( row=6, column=2, pady=30)
        # add rotating Family Guy quotes at bottom
        quote_style = {"bg": "#000000", "fg": "#ffffff", "font": ("Comic Sans MS", 16, "italic"), "justify": CENTER}
        self._lquote = Label(self, text="", **quote_style)
        self._lquote.grid(row=7, column=0, columnspan=3, pady=20)
        self.update_quote()

    def update_quote(self):
        line = random.choice(quagmire_lines + joe_lines + cleveland_lines)
        self._lquote.config(text=line)
        self.after(5000, self.update_quote)

    def setTimer(self, timer):  self._timer = timer
    def setButton(self, button):self._button = button
    def pause(self):           self._timer.pause()

    def conclusion(self, success=False):
        # clear all
        for w in self.winfo_children(): w.destroy()
        # Family Guy wrap-up banner
        msg   = "YOU DID IT!" if success else "OH NO, IT EXPLODED!"
        color = "#00ff00" if success else "#ff0000"
        Label(self, text=msg, bg="#000000", fg=color,
              font=("Comic Sans MS", 48, "bold")).place(relx=0.5, rely=0.2, anchor="center")
        # character image
        imgfile = "peter_drunk.jpg" if success else "meg.jpg"
        try:
            img = Image.open(imgfile).resize((300,300), Image.ANTIALIAS)
            photo = ImageTk.PhotoImage(img)
            Label(self, image=photo, bg="#000000").place(relx=0.5, rely=0.5, anchor="center")
            self._banner_img = photo
        except:
            pass
        # retry/quit buttons themed
        btn_style = {"font": ("Comic Sans MS", 18, "bold"), "bg": "#00aced", "fg": "white"}
        tkinter.Button(self, text="Retry", command=self.retry, **btn_style)
        tkinter.Button(self, text="Quit",  command=self.quit,  **btn_style)

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
    def fail(self): self._failed,  self._running = True, False
    def incorrect(self): self._failed, self._running = True, True

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
                        self.incorrect()
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
# -----------------------------------------------------------------------------
# Button phase — minimal, single‐color, press-and-release defuse logic
# -----------------------------------------------------------------------------
class Button(PhaseThread):
    #colors = ["R", "G", "B"]
    def __init__(self, state_pin, rgb_pins, target, color, timer, name="Button"):
        super().__init__(name, state_pin, target)
        self._rgb    = rgb_pins
        self._timer  = timer
        self._pressed = False

        # set up the color cycle
        #self._color_index = Button.colors.index(initial_color)
        #self._last_cycle  = time.time()
        #self._cycle_period = 10.0
        # light the starting color
        #self._set_color(initial_color)
    def _set_color(self, color):
        self._rgb[0].value = (color != "R")
        self._rgb[1].value = (color != "G")
        self._rgb[2].value = (color != "B")

    def run(self):
        self._running = True
        last_phase = -1
        while self._running:
            elapsed = COUNTDOWN - self._timer._value
            phase = (elapsed // 10) % 3

            if phase != last_phase:
                last_phase = phase
                if phase == 0:
                    self._set_color("R")
                    self._target = [str(n) for n in range (1,4)]
                elif phase == 1:
                    self._set_color("G")
                    self._target = [str(n) for n in range(4,7)]
                elif phase == 2:
                    self._set_color("B")
                    self._target = [str(n) for n in range(7,10)] + ["0"]
            # Step 1: Wait for button press
            while not self._component.value:
                if not self._running:
                    return
                sleep(0.05)
    
            # Step 2: Button is pressed – wait for release
            while self._component.value:
                if not self._running:
                    return
                sleep(0.05)
    
            # Step 3: Button was just released – check target
            current_sec = self._timer._sec[-1]
            if self._target is not None and current_sec in self._target:
                self.defuse()
                self.running = False
                return
            else:
                self.incorrect()
                # Wait briefly to avoid accidental rapid re-press
                sleep(0.5)  # gives user time to let go

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
