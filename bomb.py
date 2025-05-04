#!/usr/bin/env python3
# bomb.py
#################################
# CSC 102 Defuse the Bomb Project
# Main program w/ Family Guy “icing”
#################################

import tkinter as tk
from tkinter import Frame, Toplevel, Label, Button
from PIL import Image, ImageTk
from bomb_configs import *               # hardware components & constants
from bomb_phases import Timer, Keypad, Wires, Button as PhaseButton, Toggles

# —————————————————————————————————————————————
# Inline Lcd class (was in bomb_phases.py)
# —————————————————————————————————————————————
class Lcd(Frame):
    def __init__(self, master):
        super().__init__(master, bg="black")
        self.master = master
        master.attributes("-fullscreen", True)
        self._timer = None
        self._button = None

        # we'll store our 6 labels here:
        self.labels = {}
        self.setup_boot()
        self.pack(fill="both", expand=True)

    def setup_boot(self):
        # just the scrolling label
        self._lscroll = Label(self, bg="black", fg="white",
                              font=("Courier New",14), text="", justify="left")
        self._lscroll.grid(row=0, column=0, columnspan=3, sticky="w")
        # prepare grid weights for later
        for c,w in enumerate((1,2,1)):
            self.columnconfigure(c, weight=w)

    def setup(self):
        # remove boot label
        self._lscroll.destroy()

        # create all six phase labels and store them
        self.labels['Time']    = Label(self, bg="black", fg="#0f0", font=("Courier New",18))
        self.labels['Keypad']  = Label(self, bg="black", fg="#0f0", font=("Courier New",18))
        self.labels['Wires']   = Label(self, bg="black", fg="#0f0", font=("Courier New",18))
        self.labels['Toggles'] = Label(self, bg="black", fg="#0f0", font=("Courier New",18))
        self.labels['Button']  = Label(self, bg="black", fg="#0f0", font=("Courier New",18))
        self.labels['Strikes'] = Label(self, bg="black", fg="#0f0", font=("Courier New",18))

        # place them
        self.labels['Time'].grid(   row=1, column=0, columnspan=3, sticky="w")
        self.labels['Keypad'].grid( row=2, column=0, columnspan=3, sticky="w")
        self.labels['Wires'].grid(  row=3, column=0, columnspan=3, sticky="w")
        self.labels['Toggles'].grid(row=4, column=0, columnspan=3, sticky="w")
        self.labels['Button'].grid( row=5, column=0, columnspan=2, sticky="w")
        self.labels['Strikes'].grid(row=5, column=2,               sticky="w")

    def setTimer(self, timer):
        self._timer = timer

    def setButton(self, button):
        self._button = button

    def pause(self):
        if self._timer:
            self._timer.pause()

    def conclusion(self, success=True):
        # clear frame
        for w in self.winfo_children():
            w.destroy()
        # big banner
        text = "DEFUSED!" if success else "💥 BOOM! 💥"
        color = "#0f0" if success else "#f00"
        Label(self, text=text, bg="black", fg=color,
              font=("Courier New",48,"bold")).place(relx=0.5, rely=0.3, anchor="center")
        # retry & quit
        Button(self, text="Retry", font=("Courier New",18),
               command=self._retry).place(relx=0.3, rely=0.8, anchor="center")
        Button(self, text="Quit",  font=("Courier New",18),
               command=self._quit).place( relx=0.7, rely=0.8, anchor="center")

    def _retry(self):
        import os, sys
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def _quit(self):
        import os, sys
        # if you want to turn off real hardware here, do it
        sys.exit(0)


# —————————————————————————————————————————————
# Full-screen image helper
# —————————————————————————————————————————————
img_window = None
img_photo  = None

def show_image(path, hold_ms=1500):
    """Pop up a full-screen Toplevel with the image, auto-close after hold_ms."""
    global img_window, img_photo
    if img_window:
        try: img_window.destroy()
        except: pass

    img_window = Toplevel(root)
    img_window.attributes('-fullscreen', True)
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    img   = Image.open(path).resize((w,h), Image.LANCZOS)
    img_photo = ImageTk.PhotoImage(img)
    Label(img_window, image=img_photo).pack(fill="both", expand=True)

    # schedule auto-close
    root.after(hold_ms, img_window.destroy)


# —————————————————————————————————————————————
# Phase images
# —————————————————————————————————————————————
challenge_images = [
    "KEYPAD.jpeg",
    "WIRES.jpeg",
    "TOGGLES.jpeg",
    "BUTTON.jpeg",
]
strike_images = [f"STRIKE{i+1}.jpeg" for i in range(NUM_STRIKES)]
win_image  = "DEFUSED.jpeg"
lose_image = "FAILURE.jpeg"


# —————————————————————————————————————————————
# Global state
# —————————————————————————————————————————————
strikes_left   = NUM_STRIKES
active_phases  = NUM_PHASES
handled_phases = set()
timer = keypad = wires = toggles = button = None


# —————————————————————————————————————————————
# Create phases & start demo
# —————————————————————————————————————————————
def setup_phases():
    global strikes_left, active_phases, handled_phases
    global timer, keypad, wires, toggles, button

    strikes_left   = NUM_STRIKES
    active_phases  = NUM_PHASES
    handled_phases = set()

    # instantiate
    timer   = Timer(component_7seg, COUNTDOWN)
    keypad  = Keypad(component_keypad, str(keypad_target))
    wires   = Wires(component_wires, bin(wires_target)[2:].zfill(len(component_wires)))
    toggles = Toggles(component_toggles, bin(toggles_target)[2:].zfill(len(component_toggles)))
    button  = PhaseButton(component_button_state,
                          component_button_rgb,
                          button_target, button_color, timer,
                          submit_phases=(wires, toggles))

    # wire up GUI
    gui.setTimer(timer)
    gui.setButton(button)

    # start them
    for p in (timer, keypad, wires, toggles, button):
        p.start()

    # show first challenge
    show_image(challenge_images[0])


# —————————————————————————————————————————————
# Poll phases & advance images
# —————————————————————————————————————————————
def update_gui():
    global strikes_left, active_phases

    # 1) refresh LCD
    gui.labels['Time']['text']    = f"Time left: {timer}"
    gui.labels['Keypad']['text']  = f"Keypad: {keypad}"
    gui.labels['Wires']['text']   = f"Wires: {wires}"
    gui.labels['Toggles']['text'] = f"Toggles: {toggles}"
    gui.labels['Button']['text']  = f"Button: {button}"
    gui.labels['Strikes']['text'] = f"Strikes: {strikes_left}"

    # 2) check each phase in turn
    phases = [keypad, wires, toggles, button]
    for idx, ph in enumerate(phases):
        if ph in handled_phases:
            continue
        if ph._failed:
            # strike!
            handled_phases.add(ph)
            strikes_left -= 1
            show_image(strike_images[min(strikes_left, len(strike_images)-1)])
            # retry that phase after a pause
            def _retry():
                handled_phases.remove(ph)
                if idx==0:
                    globals()['keypad'] = Keypad(component_keypad, str(keypad_target)); keypad.start()
                elif idx==1:
                    globals()['wires']  = Wires(component_wires, bin(wires_target)[2:].zfill(len(component_wires))); wires.start()
                elif idx==2:
                    globals()['toggles']= Toggles(component_toggles, bin(toggles_target)[2:].zfill(len(component_toggles))); toggles.start()
                else:
                    globals()['button'] = PhaseButton(component_button_state,
                                                      component_button_rgb,
                                                      button_target, button_color, timer,
                                                      submit_phases=(wires, toggles))
                    button.start()
                root.after(200, update_gui)
            root.after(1500, _retry)
            return

        if ph._defused:
            # defuse!
            handled_phases.add(ph)
            active_phases -= 1
            next_idx = idx+1
            if next_idx < len(challenge_images):
                show_image(challenge_images[next_idx])
                root.after(500, update_gui)
            else:
                # victory
                timer.pause()
                gui.conclusion(True)
            return

    # 3) timer expired?
    if not timer._running:
        gui.conclusion(False)
        return

    # 4) keep polling
    root.after(100, update_gui)


# —————————————————————————————————————————————
# Boot animation then start game
# —————————————————————————————————————————————
def bootup(i=0):
    if not ANIMATE or i >= len(boot_text):
        gui.setup()
    else:
        if boot_text[i] != "\x00":
            gui._lscroll['text'] += boot_text[i]
        delay = 25 if boot_text[i] != "\x00" else 750
        gui.after(delay, bootup, i+1)


# —————————————————————————————————————————————
# MAIN
# —————————————————————————————————————————————
root = tk.Tk()
gui  = Lcd(root)

# start boot scroll
gui.after(1000, bootup)
# after scroll, show real GUI
root.after(1000 + len(boot_text)*50, gui.setup)
# then setup and poll
root.after(1200 + len(boot_text)*50, setup_phases)
root.after(1300 + len(boot_text)*50, update_gui)

root.mainloop()
