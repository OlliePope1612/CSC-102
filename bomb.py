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

    gui.labels['Time']['text']    = f"Time left: {timer}"
    gui.labels['Keypad']['text']  = f"Keypad: {keypad}"
    gui.labels['Wires']['text']   = f"Wires: {wires}"
    gui.labels['Toggles']['text'] = f"Toggles: {toggles}"
    gui.labels['Button']['text']  = f"Button: {button}"
    gui.labels['Strikes']['text'] = f"Strikes left: {strikes_left}"

    phases = [keypad, wires, toggles, button]
    for x, ph in enumerate(phases):
        def retry_phase():
            handled_phases.discard(ph)
            if x == 0:
                globals()['keypad'] = Keypad(component_keypad, str(keypad_target))
                keypad.start()
            elif x == 1:
                globals()['wires'] = Wires(component_wires, bin(wires_target)[2:].zfill(len(component_wires)))
                wires.start()
            elif x == 2:
                globals()['toggles'] = Toggles(component_toggles, bin(toggles_target)[2:].zfill(len(component_toggles)))
                toggles.start()
            else:
                globals()['button'] = Button(
                    component_button_state,
                    component_button_rgb,
                    button_target, button_color, timer
                )
                button.start()
            root.after(500, update_gui)

            root.after(1500, retry_phase)
            return
        
        if ph in handled_phases:
            continue

        if ph._failed:
            # strike!
            handled_phases.add(ph)
            strikes_left -= 1
            show_image(strike_images[strikes_left-1], 3000)
            retry_phase()
            

        if ph._defused:
            # phase defused → move on
            handled_phases.add(ph)
            active_phases -= 1
            next_x = x + 1
            if next_x < len(challenge_images):
                show_image(challenge_images[next_x])
                root.after(500, update_gui)
            else:
                # all done!
                timer.pause()
                gui.conclusion(success=True)
            return

    # 3) Timer expired?
    if not timer._running:
        gui.conclusion(success=False)
        return

    # 4) Otherwise keep polling
    root.after(100, update_gui)

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
