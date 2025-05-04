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
img_window = None
img_photo  = None

def show_image(path, hold_ms=None):
    """Pop up a full-screen image. If hold_ms is None, it stays up until next call; otherwise auto-closes."""
    global img_window, img_photo
    if img_window:
        try:
            img_window.destroy()
        except:
            pass
    img_window = Toplevel(root)
    img_window.attributes('-fullscreen', True)
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    img = Image.open(path).resize((w, h), Image.LANCZOS)
    img_photo = ImageTk.PhotoImage(img)
    Label(img_window, image=img_photo).pack(fill='both', expand=True)
    if hold_ms is not None:
        root.after(hold_ms, img_window.destroy)

# —————————————————————————————————————————————
# Challenge & strike images
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
]

# —————————————————————————————————————————————
# Global game state
# —————————————————————————————————————————————
strikes_left   = NUM_STRIKES
active_phases  = NUM_PHASES
handled_phases = set()
timer = keypad = wires = toggles = button = None

# —————————————————————————————————————————————
# Phase setup
# —————————————————————————————————————————————
def setup_phases():
    global strikes_left, active_phases, handled_phases
    global timer, keypad, wires, toggles, button

    strikes_left   = NUM_STRIKES
    active_phases  = NUM_PHASES
    handled_phases = set()

    # instantiate each phase
    timer   = Timer(component_7seg, COUNTDOWN)
    keypad  = Keypad(component_keypad, str(keypad_target))
    wires   = Wires(component_wires, bin(wires_target)[2:].zfill(len(component_wires)))
    toggles = Toggles(component_toggles, bin(toggles_target)[2:].zfill(len(component_toggles)))
    button  = Button(
        component_button_state,
        component_button_rgb,
        button_target, button_color, timer,
        submit_phases=(wires, toggles)
    )

    gui.setTimer(timer)
    gui.setButton(button)

    for p in (timer, keypad, wires, toggles, button):
        p.start()

    # show first challenge (persistent)
    show_image(challenge_images[0])

# —————————————————————————————————————————————
# GUI update & game logic
# —————————————————————————————————————————————
def update_gui():
    global strikes_left, active_phases

    # 1) refresh LCD labels
    gui.labels['Time'][   'text'] = f"Time left: {timer}"
    gui.labels['Keypad']['text'] = f"Keypad phase: {keypad}"
    gui.labels['Wires'][  'text'] = f"Wires phase: {wires}"
    gui.labels['Toggles'][ 'text'] = f"Toggles phase: {toggles}"
    gui.labels['Button'][ 'text'] = f"Button phase: {button}"
    gui.labels['Strikes']['text'] = f"Strikes left: {strikes_left}"

    phases = [keypad, wires, toggles, button]
    for idx, phase in enumerate(phases):
        if phase in handled_phases:
            continue

        # STRIKE?
        if phase._failed:
            handled_phases.add(phase)
            strikes_left -= 1
            img_idx = min(NUM_STRIKES - strikes_left - 1, len(strike_images)-1)
            # flash strike for 2s
            show_image(strike_images[img_idx], hold_ms=2000)
            def retry():
                handled_phases.discard(phase)
                if idx == 0:
                    globals()['keypad'] = Keypad(component_keypad, str(keypad_target))
                    keypad.start()
                elif idx == 1:
                    globals()['wires']  = Wires(component_wires, bin(wires_target)[2:].zfill(len(component_wires)))
                    wires.start()
                elif idx == 2:
                    globals()['toggles']= Toggles(component_toggles, bin(toggles_target)[2:].zfill(len(component_toggles)))
                    toggles.start()
                else:
                    globals()['button'] = Button(
                        component_button_state,
                        component_button_rgb,
                        button_target, button_color, timer,
                        submit_phases=(wires, toggles)
                    )
                    button.start()
                root.after(100, update_gui)
            root.after(2000, retry)
            return

        # DEFUSE?
        if phase._defused:
            handled_phases.add(phase)
            active_phases -= 1
            next_idx = idx + 1
            if next_idx < len(challenge_images):
                show_image(challenge_images[next_idx])
                root.after(100, update_gui)
            else:
                timer.pause()
                gui.conclusion(True)
            return

    # timer expired?
    if not timer._running:
        gui.conclusion(False)
        return

    root.after(100, update_gui)

# —————————————————————————————————————————————
# MAIN
# —————————————————————————————————————————————
root = tk.Tk()
gui  = Lcd(root)
gui.setup()
root.after(200, setup_phases)
root.after(400, update_gui)
root.mainloop()
