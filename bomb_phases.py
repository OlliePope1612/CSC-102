#################################
# CSC 102 Defuse the Bomb Project
# GUI and Phase class definitions
# Team: 
#################################

# import the configs
from bomb_configs import *
# other imports
from tkinter import *
import tkinter
from threading import Thread
from time import sleep
import os
import sys

#########
# classes
#########
# the LCD display GUI
class Lcd(Frame):
    def __init__(self, window):
        super().__init__(window, bg="black")
        # make the GUI fullscreen
        window.attributes("-fullscreen", True)
        # we need to know about the timer (7-segment display) to be able to pause/unpause it
        self._timer = None
        # we need to know about the pushbutton to turn off its LED when the program exits
        self._button = None
        # setup the initial "boot" GUI
        self.setupBoot()

    # sets up the LCD "boot" GUI
    def setupBoot(self):
        # set column weights
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.columnconfigure(2, weight=1)
        # the scrolling informative "boot" text
        self._lscroll = Label(self, bg="black", fg="white", font=("Courier New", 14), text="", justify=LEFT)
        self._lscroll.grid(row=0, column=0, columnspan=3, sticky=W)
        self.pack(fill=BOTH, expand=True)

    # sets up the LCD GUI
    def setup(self):
        # the timer
        self._ltimer = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Time left: ")
        self._ltimer.grid(row=1, column=0, columnspan=3, sticky=W)
        # the keypad passphrase
        self._lkeypad = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Keypad phase: ")
        self._lkeypad.grid(row=2, column=0, columnspan=3, sticky=W)
        # the jumper wires status
        self._lwires = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Wires phase: ")
        self._lwires.grid(row=3, column=0, columnspan=3, sticky=W)
        # the pushbutton status
        self._lbutton = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Button phase: ")
        self._lbutton.grid(row=4, column=0, columnspan=3, sticky=W)
        # the toggle switches status
        self._ltoggles = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Toggles phase: ")
        self._ltoggles.grid(row=5, column=0, columnspan=2, sticky=W)
        # the strikes left
        self._lstrikes = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Strikes left: ")
        self._lstrikes.grid(row=5, column=2, sticky=W)
        if (SHOW_BUTTONS):
            # the pause button (pauses the timer)
            self._bpause = tkinter.Button(self, bg="red", fg="white", font=("Courier New", 18), text="Pause", anchor=CENTER, command=self.pause)
            self._bpause.grid(row=6, column=0, pady=40)
            # the quit button
            self._bquit = tkinter.Button(self, bg="red", fg="white", font=("Courier New", 18), text="Quit", anchor=CENTER, command=self.quit)
            self._bquit.grid(row=6, column=2, pady=40)

    # lets us pause/unpause the timer (7-segment display)
    def setTimer(self, timer):
        self._timer = timer

    # lets us turn off the pushbutton's RGB LED
    def setButton(self, button):
        self._button = button

    # pauses the timer
    def pause(self):
        if (RPi):
            self._timer.pause()

    def conclusion(self, success=False):
        # clear out all phase widgets
        for widget in self.winfo_children():
            widget.destroy()

        # set up a full-screen banner Label
        banner_text = "DEFUSED!" if success else "💥 BOOM! 💥"
        banner_color = "#00ff00" if success else "#ff0000"
        banner = Label(self,
                       text=banner_text,
                       bg="black",
                       fg=banner_color,
                       font=("Courier New", 48, "bold"),
                       justify=CENTER)
        banner.place(relx=0.5, rely=0.4, anchor="center")

        from PIL import Image, ImageTk
        img = Image.open("boom.jpg" if not success else "yayyy.jpg")
        img = img.resize((300,300), Image.ANTIALIAS)
        photo = ImageTk.PhotoImage(img)
        Label(self, image=photo, bg="black").place(relx=0.5, rely=0.6, anchor="center")
        self._banner_img = "peter_drunk.jpg"

        # place Retry + Quit buttons below the banner
        btn_y = 0.8
        self._bretry = Button(self, text="Retry", font=("Courier New", 18),
                              bg="gray20", fg="white", command=self.retry)
        self._bretry.place(relx=0.3, rely=btn_y, anchor="center")

        self._bquit  = Button(self, text="Quit",  font=("Courier New", 18),
                              bg="gray20", fg="white", command=self.quit)
        self._bquit.place(relx=0.7, rely=btn_y, anchor="center")

    # re-attempts the bomb (after an explosion or a successful defusion)
    def retry(self):
        # re-launch the program (and exit this one)
        os.execv(sys.executable, ["python3"] + [sys.argv[0]])
        exit(0)

    # quits the GUI, resetting some components
    def quit(self):
        if (RPi):
            # turn off the 7-segment display
            self._timer._running = False
            self._timer._component.blink_rate = 0
            self._timer._component.fill(0)
            # turn off the pushbutton's LED
            for pin in self._button._rgb:
                pin.value = True
        # exit the application
        exit(0)

# template (superclass) for various bomb components/phases
class PhaseThread(Thread):
    def __init__(self, name, component=None, target=None):
        super().__init__(name=name, daemon=True)
        # phases have an electronic component (which usually represents the GPIO pins)
        self._component = component
        # phases have a target value (e.g., a specific combination on the keypad, the proper jumper wires to "cut", etc)
        self._target = target
        # phases can be successfully defused
        self._defused = False
        # phases can be failed (which result in a strike)
        self._failed = False
        # phases have a value (e.g., a pushbutton can be True/Pressed or False/Released, several jumper wires can be "cut"/False, etc)
        self._value = None
        # phase threads are either running or not
        self._running = False
        
    def defuse(self):
        """Mark this phase as defused and stop its thread."""
        self._defused = True
        self._running = False

    def fail(self):
        """Mark this phase as failed (strike) and stop its thread."""
        self._failed  = True
        self._running = False
# the timer phase
class Timer(PhaseThread):
    def __init__(self, component, initial_value, name="Timer"):
        super().__init__(name, component)
        # the default value is the specified initial value
        self._value = initial_value
        # is the timer paused?
        self._paused = False
        # initialize the timer's minutes/seconds representation
        self._min = ""
        self._sec = ""
        # by default, each tick is 1 second
        self._interval = 1

    # runs the thread
    def run(self):
        self._running = True
        while (self._running):
            if (not self._paused):
                # update the timer and display its value on the 7-segment display
                self._update()
                self._component.print(str(self))
                # wait 1s (default) and continue
                sleep(self._interval)
                # the timer has expired -> phase failed (explode)
                if (self._value == 0):
                    self._running = False
                self._value -= 1
            else:
                sleep(0.1)

    # updates the timer (only internally called)
    def _update(self):
        self._min = f"{self._value // 60}".zfill(2)
        self._sec = f"{self._value % 60}".zfill(2)

    # pauses and unpauses the timer
    def pause(self):
        # toggle the paused state
        self._paused = not self._paused
        # blink the 7-segment display when paused
        self._component.blink_rate = (2 if self._paused else 0)

    # returns the timer as a string (mm:ss)
    def __str__(self):
        return f"{self._min}:{self._sec}"

class Keypad(PhaseThread):
    def __init__(self, component, target, name="Keypad"):
        super().__init__(name, component, target)
        self._value = ""

    def run(self):
        self._running = True
        while self._running:
            if self._component.pressed_keys:
                # debounce: wait until keys are released
                while self._component.pressed_keys:
                    try:
                        key = self._component.pressed_keys[0]
                    except:
                        key = ""
                    sleep(0.1)
                # record the key
                self._value += str(key)
                # full match → defuse
                if self._value == self._target:
                    self.defuse()
                    return
                # prefix mismatch → fail
                if not self._target.startswith(self._value):
                    self.fail()
                    return
            sleep(0.1)

    def __str__(self):
        return "DEFUSED" if self._defused else self._value
        
# the jumper wires phase
class Wires(PhaseThread):
    def __init__(self, component, target_str):
        # Store the exact target string (e.g. "01101")
        self._target_str = target_str
        # Build a dict for the run logic
        target = {i: True for i, b in enumerate(target_str) if b == '1'}
        super().__init__("Wires", component, target)

    def run(self):
        cut_sequence = []
        self._running = True
        # compute the numeric target sequence once
        target_sequence = [int(c) for c in self._target_str]  # if you stored target as string
        while self._running:
            for idx, wire in enumerate(self._component):
                # on real Pi use wire.value, on mock use wire.is_cut()
                cut = wire.is_cut() if hasattr(wire, "is_cut") else wire.value
                if cut and idx not in cut_sequence:
                    cut_sequence.append(idx)
                    if len(cut_sequence) == len(target_sequence):
                        if cut_sequence == target_sequence:
                            self.defuse()
                        else:
                            self.fail()
                        return
            sleep(0.1)

    def __str__(self):
        bits = "".join(
            "1" if (wire.is_cut() if hasattr(wire, "is_cut") else wire.value)
            else "0"
            for wire in self._component
        )
        return "DEFUSED" if self._defused else bits

# the pushbutton phase
class Button(PhaseThread):
    def __init__(self, component_state, component_rgb, target, color, timer, name="Button"):
        super().__init__(name, component_state, target)
        # the default value is False/Released
        self._value = False
        # has the pushbutton been pressed?
        self._pressed = False
        # we need the pushbutton's RGB pins to set its color
        self._rgb = component_rgb
        # the pushbutton's randomly selected LED color
        self._color = color
        # we need to know about the timer (7-segment display) to be able to determine correct pushbutton releases in some cases
        self._timer = timer

    def run(self):
        # set the LED
        self._rgb[0].value = (self._color != "R")
        self._rgb[1].value = (self._color != "G")
        self._rgb[2].value = (self._color != "B")

        self._running = True
        while self._running:
            current = self._component.value
            if current and not self._pressed:
                # button just pressed
                self._pressed = True
            if not current and self._pressed:
                # just released
                if (self._target is None) or (str(self._target) in self._timer._sec):
                    self.defuse()
                else:
                    self.fail()
                return
            sleep(0.1)

    def __str__(self):
        return "DEFUSED" if self._defused else ("Pressed" if self._pressed else "Released")

# the toggle switches phase
class Toggles(PhaseThread):
    def __init__(self, component, target, name="Toggles"):
        super().__init__(name, component, target)

    def run(self):
        self._running = True
        prev = None
        while self._running:
            # read each toggle’s state (real .value or mock .read())
            bits = [str(int(pin.read())) for pin in self._component] if hasattr(self._component[0], "read") \
                   else [str(int(pin.value)) for pin in self._component]
            current = "".join(bits)
            
            # only react on an actual change
            if current != prev:
                if not self._target.startswith(current):
                    self.fail()
                    return
                if current == self._target:
                    self.defuse()
                    return
                prev = current
            sleep(0.1)

    def __str__(self):
        if self._defused:
            return "DEFUSED"
        # prefer mock.read(), else .value
        return "".join(
            "1" if (pin.read() if hasattr(pin, "read") else pin.value) else "0"
            for pin in self._component
        )

class Keypad(PhaseThread):
    def __init__(self, component, target, name="Keypad", max_len=6, reset_on_fail=False, feedback_fn=None):
        super().__init__(name, component, target)
        self._value = ""
        self._max_len = max_len                # prevent overflow
        self._reset_on_fail = reset_on_fail    # allow reset instead of immediate fail
        self._feedback_fn = feedback_fn        # optional callback for UI/audio/etc

    def run(self):
        self._running = True
        while self._running:
            if self._component.pressed_keys:
                key = str(self._component.pressed_keys[0])

                # Optional feedback callback
                if self._feedback_fn:
                    self._feedback_fn(key)

                # Debounce
                while self._component.pressed_keys:
                    sleep(0.05)

                # Handle backspace
                if key == "#" and self._value:
                    self._value = self._value[:-1]
                elif len(self._value) < self._max_len:
                    self._value += key

                # Check for defuse or fail
                if self._value == self._target:
                    self.defuse()
                    return
                elif not self._target.startswith(self._value):
                    if self._reset_on_fail:
                        self._value = ""
                    else:
                        self.fail()
                        return
            sleep(0.1)

    def __str__(self):
        return "DEFUSED" if self._defused else self._value
