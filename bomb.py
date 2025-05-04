#################################
# CSC 102 Defuse the Bomb Project
# Main program w/ Family Guy “icing”
#################################

import tkinter as tk
from tkinter import Toplevel, Label
from PIL import Image, ImageTk

from bomb_configs import *                 # hardware components & constants
from bomb_phases import Timer, Keypad, Wires, Button, Toggles, Lcd

# —————————————————————————————————————————————
# Full-screen image helper
# —————————————————————————————————————————————
_img_window = None
_img_photo  = None

def show_image(path, hold_ms=None):
    """Pop up a full-screen Toplevel with the image, auto-close after hold_ms."""
    global _img_window, _img_photo
    if _img_window:
        try: _img_window.destroy()
        except: pass

    _img_window = Toplevel(root)
    _img_window.attributes('-fullscreen', True)
    w = root.winfo_screenwidth()
    h = root.winfo_screenheight()
    img = Image.open(path).resize((w, h), Image.LANCZOS)
    _img_photo = ImageTk.PhotoImage(img)
    Label(_img_window, image=_img_photo).pack(fill='both', expand=True)
    
    if hold_ms is not None:
        root.after(hold_ms, _img_window.destroy)

# —————————————————————————————————————————————
# Challenge & strike images (in phase order)
# —————————————————————————————————————————————
challenge_images = [
    "KEYPAD.jpeg",   # phase 0 = Keypad
    "WIRES.jpeg",    # phase 1 = Wires
    "TOGGLES.jpeg",  # phase 2 = Toggles
    "BUTTON.jpeg",   # phase 3 = Button
]
strike_images = [
    "STRIKE1.jpeg",
    "STRIKE2.jpeg",
    "STRIKE3.jpeg",
    "STRIKE4.jpeg"
]

# —————————————————————————————————————————————
# Global state
# —————————————————————————————————————————————
strikes_left   = NUM_STRIKES
active_phases  = NUM_PHASES
handled_phases = set()

timer = keypad = wires = toggles = button = None

# —————————————————————————————————————————————
# Create & start all phases
# —————————————————————————————————————————————
def setup_phases():
    global strikes_left, active_phases, handled_phases
    global timer, keypad, wires, toggles, button

    strikes_left   = NUM_STRIKES
    active_phases  = NUM_PHASES
    handled_phases = set()

    # instantiate your phase threads
    timer   = Timer(component_7seg, COUNTDOWN)
    keypad  = Keypad(component_keypad, keypad_target)
    wires   = Wires(component_wires, wires_target)
    toggles = Toggles(component_toggles, toggles_target)
    button  = Button(
        component_button_state,
        component_button_rgb,
        button_target, button_color, timer
    )

    # connect them to the LCD GUI
    gui.setTimer(timer)
    gui.setButton(button)

    # start all threads
    for phase in (timer, keypad, wires, toggles, button):
        phase.start()

    # show the first “challenge” image
    show_image(challenge_images[0])

# —————————————————————————————————————————————
# Poll phases & advance images
# —————————————————————————————————————————————
def update_gui():
    global strikes_left, active_phases

    # … your label updates …

    phases = [keypad, wires, toggles, button]
    for x, ph in enumerate(phases):
        if ph in handled_phases:
            continue

        if ph._failed:
            handled_phases.add(ph)
            strikes_left -= 1
            # show strike image for 3s
            show_image(strike_images[min(strikes_left, len(strike_images)-1)], hold_ms=3000)

            # capture the current phase and index in defaults:
            def retry_phase(failed_phase=ph, idx=x):
                handled_phases.discard(failed_phase)
                # re-create exactly that one phase
                if idx == 0:
                    new = Keypad(component_keypad, keypad_target)
                    globals()['keypad'] = new
                elif idx == 1:
                    new = Wires(component_wires, wires_target)
                    globals()['wires'] = new
                elif idx == 2:
                    new = Toggles(component_toggles, toggles_target)
                    globals()['toggles'] = new
                else:
                    new = Button(component_button_state,
                                 component_button_rgb,
                                 button_target, button_color, timer)
                    globals()['button'] = new
                new.start()
                # immediately resume polling
                update_gui()

            # schedule retry _after_ the strike splash
            root.after(3000, retry_phase)
            return

        if ph._defused:
            handled_phases.add(ph)
            active_phases -= 1
            # … advance to next challenge …
            return

    # … rest of update_gui …

# —————————————————————————————————————————————
# MAIN
# —————————————————————————————————————————————
if __name__ == '__main__':
    root = tk.Tk()
    gui  = Lcd(root)
    gui.setup()             # set up the LCD widgets
    setup_phases()          # fire off the threads & show image
    update_gui()            # begin polling & image transitions
    root.mainloop()
