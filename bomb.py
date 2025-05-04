from tkinter import Tk, Toplevel, Label
from PIL import Image, ImageTk
from bomb_configs import *        # hardware components & constants
from bomb_phases import Timer, Keypad, Wires, Button, Toggles, Lcd

# File names for images
challenge_images = [
    "KEYPAD.jpeg",  # keypad challenge
    "meg.jpg",     # toggles challenge
    "meg.jpg",     # wires challenge
    "meg.jpg",     # button challenge
]
strike_images = [
    "STRIKE1.jpeg",
    "STRIKE1.jpeg",
    "STRIKE1.jpeg",
    "STRIKE1.jpeg",
]
game_over_image = "peter_drunk.jpg"
win_image       = "yayyy.jpg"

# Globals for image window
global img_window, img_photo
img_window = None
img_photo  = None

# Helper: display fullscreen image
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
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    img = Image.open(path).resize((screen_w, screen_h), Image.LANCZOS)
    img_photo = ImageTk.PhotoImage(img)
    lbl = Label(img_window, image=img_photo)
    lbl.pack(fill='both', expand=True)

# Core logic: monitor phases
def check_phases():
    global strikes_left, active_phases
    # update LCD labels
    for attr, phase in [("_ltimer", timer), ("_lkeypad", keypad),
                        ("_ltoggles", toggles), ("_lwires", wires), ("_lbutton", button)]:
        try: getattr(gui, attr)["text"] = f"{attr[2:].replace('_',' ').title()}: {phase}"
        except: pass
    try: gui._lstrikes["text"] = f"Strikes left: {strikes_left}"
    except: pass

    # iterate in order
    for idx, phase in enumerate((keypad, toggles, wires, button)):
        if phase in handled_phases:
            continue
        # failure
        if phase._failed:
            handled_phases.add(phase)
            strikes_left -= 1
            show_image(strike_images[idx])
            # after 5 seconds, either retry or game over
            def resume():
                if strikes_left > 0:
                    show_image(challenge_images[idx])
                    phase._failed = False
                    handled_phases.discard(phase)
                    phase.start()
                else:
                    show_image(game_over_image)
                    gui.conclusion(success=False)
            window.after(5000, resume)
            return
        # defuse
        if phase._defused:
            handled_phases.add(phase)
            active_phases -= 1
            # next challenge or win
            if idx < len(challenge_images) - 1:
                show_image(challenge_images[idx + 1])
            else:
                show_image(win_image)
                gui.conclusion(success=True)
            return

    # keep polling
    window.after(100, check_phases)

# Initialize and start all phases
def setup_phases():
    global timer, keypad, toggles, wires, button, strikes_left, active_phases, handled_phases
    strikes_left  = NUM_STRIKES
    active_phases = NUM_PHASES
    handled_phases = set()

    timer   = Timer(component_7seg, COUNTDOWN)
    keypad  = Keypad(component_keypad, "1999")       # hard-coded
    toggles = Toggles(component_toggles, "1010")     # hard-coded
    wires   = Wires(component_wires, "10101")       # odd wires
    button  = Button(component_button_state,
                     component_button_RGB,
                     button_target, button_color, timer)

    gui.setTimer(timer)
    gui.setButton(button)

    for phase in (timer, keypad, toggles, wires, button):
        phase.start()

    # show first challenge image
    show_image(challenge_images[0])

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
    window.after(100, check_phases)

# MAIN
window = Tk()
gui = Lcd(window)
gui.after(1000, bootup)
boot_duration = 1000 + len(boot_text) * 50
gui.after(boot_duration, start_game)
window.mainloop()
