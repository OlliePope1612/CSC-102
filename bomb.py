from tkinter import Tk, Toplevel, Label
from PIL import Image, ImageTk
from bomb_configs import *        # component_7seg, component_keypad, COUNTDOWN, keypad_target, etc.
from bomb_phases import Timer, Keypad, Wires, Button, Toggles, Lcd  # needed classes
import random

# File names for images (place these in your working directory)
challenge_images = [
    "KEYPAD.jpeg",  # for keypad
    "TOGGLES.jpeg",     # for toggles
    "meg.jpg",     # for wires
    "meg.jpg",     # for button
]
strike_images = [
    "STRIKE1.jpeg",
    "STRIKE2.jpeg",
    "STRIKE1.jpeg",
    "STRIKE1.jpeg",
]
game_over_image = "peter_drunk.jpg"
win_image       = "yayyy.jpg"

# Globals for image window
img_window = None
img_photo = None

# Display a fullscreen image in its own window
def show_image(path):
    global img_window, img_photo
    try:
        img_window.destroy()
    except:
        pass
    img_window = Toplevel(window)
    img_window.attributes('-fullscreen', True)
    img_window.lift()
    img_window.focus_force()
    img_window.config(bg='black')
    # load and resize image to screen size using LANCZOS resampling
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    img = Image.open(path).resize((screen_w, screen_h), Image.LANCZOS)
    img_photo = ImageTk.PhotoImage(img)
    lbl = Label(img_window, image=img_photo)
    lbl.pack(fill='both', expand=True)

# Core GUI & game logic
handled_phases = set()

# Map phases to challenge image indices
def phase_index(phase):
    return {keypad:0, toggles:1, wires:2, button:3}[phase]

def check_phases():
    global strikes_left, active_phases
    # update LCD labels
    for attr, phase in [("_ltimer",timer),("_lkeypad",keypad),
                        ("_ltoggles",toggles),("_lwires",wires),
                        ("_lbutton",button)]:
        try: getattr(gui,attr)["text"] = f"{attr[2:].replace('_',' ').title()}: {phase}"
        except: pass
    try: gui._lstrikes["text"] = f"Strikes left: {strikes_left}"
    except: pass

    for phase in (keypad, toggles, wires, button):
        # handle defuse
        if phase._defused and phase not in handled_phases:
            handled_phases.add(phase)
            active_phases -= 1
            idx = phase_index(phase)
            # show next challenge or win
            if idx < len(challenge_images)-1:
                show_image(challenge_images[idx+1])
            else:
                show_image(win_image)
                gui.conclusion(success=True)
            return
        # handle failure
        if phase._failed and phase not in handled_phases:
            handled_phases.add(phase)
            strikes_left -= 1
            idx = phase_index(phase)
            # show strike image briefly
            show_image(strike_images[idx])
            def restore_phase():
                # clear the failure state and allow retry
                phase._failed = False
                handled_phases.discard(phase)
                # reset input state for keypad
                if isinstance(phase, Keypad):
                    phase._value = ""
                # re-display the challenge image
                show_image(challenge_images[idx])
                # resume phase checking
                window.after(100, check_phases)
            if strikes_left > 0:
                window.after(5000, restore_phase)
            else:
                # no strikes left -> game over
                window.after(5000, lambda: show_image(game_over_image))
                window.after(5000, lambda: gui.conclusion(success=False))
            return

    # continue polling
    window.after(100, check_phases)

# Initialize phase threads
def setup_phases():
    global timer, keypad, toggles, wires, button, strikes_left, active_phases
    strikes_left  = NUM_STRIKES
    active_phases = NUM_PHASES
    timer   = Timer(component_7seg, COUNTDOWN)
    keypad  = Keypad(component_keypad, "1999")  # hard-coded code
    toggles = Toggles(component_toggles, "1010")  # first & third flipped up
    wires   = Wires(component_wires, bin(wires_target)[2:].zfill(len(component_wires)))
    button  = Button(component_button_state, component_button_RGB, button_target, button_color, timer)
    gui.setTimer(timer)
    gui.setButton(button)
    for p in (timer, keypad, toggles, wires, button):
        p.start()

# Boot sequence
def bootup(n=0):
    if not ANIMATE or n >= len(boot_text):
        gui.setup()
    else:
        if boot_text[n] != "\x00": gui._lscroll["text"] += boot_text[n]
        delay = 25 if boot_text[n] != "\x00" else 750
        gui.after(delay, bootup, n+1)

# Start game
def start_game():
    gui.setup()
    setup_phases()
    # show first challenge
    show_image(challenge_images[0])
    window.after(100, check_phases)

# MAIN
window = Tk()
    gui = Lcd(window)
    gui.after(1000, bootup)
    boot_duration = 1000 + len(boot_text)*50
    gui.after(boot_duration, start_game)
    window.mainloop()}]}
