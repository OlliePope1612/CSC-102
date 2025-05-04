from tkinter import Tk, Toplevel, Label
from PIL import Image, ImageTk
from bomb_configs import *        # hardware components & constants
from bomb_phases import Timer, Keypad, Wires, Button, Toggles, Lcd

# File names for images
challenge_images = [
    "KEYPAD.jpeg",   # keypad challenge
    "TOGGLES.jpeg",  # toggles challenge
    "WIRES.jpeg",    # wires challenge
    "BUTTON.jpeg",   # button challenge
]
strike_images = [
    "STRIKE1.jpeg",
    "STRIKE2.jpeg",
    "STRIKE3.jpeg",
    "STRIKE4.jpeg",
]
game_over_image = "FAILURE.jpeg"
win_image       = "DEFUSED.jpeg"

# Globals for image window
img_window = None
img_photo  = None

# Core state
strikes_left    = 0
active_phases   = 0
handled_phases  = set()

def show_image(path):
    """Display a full-screen image in a separate window."""
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

def resume_phase(idx, phase):
    """
    After a strike, resume the same challenge (keypad=0, toggles=1, wires=2, button=3).
    """
    global strikes_left, handled_phases, keypad, toggles, wires, button

    if strikes_left <= 0:
        show_image(game_over_image)
        gui.conclusion(success=False)
        return

    # show the same challenge again
    show_image(challenge_images[idx])
    handled_phases.discard(phase)

    # rebuild & restart only that phase
    if idx == 0:
        keypad = Keypad(component_keypad, str(keypad_target))
        keypad.start()
    elif idx == 1:
        toggles = Toggles(
            component_toggles,
            bin(toggles_target)[2:].zfill(len(component_toggles))
        )
        toggles.start()
    elif idx == 2:
        wires = Wires(
            component_wires,
            bin(wires_target)[2:].zfill(len(component_wires))
        )
        wires.start()
    else:
        button = Button(
            component_button_state,
            component_button_RGB,
            button_target, button_color, timer,
            submit_phases=(toggles, wires)
        )
        button.start()

    window.after(100, check_phases)

def check_phases():
    global strikes_left, active_phases, handled_phases

    # 1) Update the LCD labels
    for attr, phase in [
        ("_ltimer", timer),
        ("_lkeypad", keypad),
        ("_ltoggles", toggles),
        ("_lwires", wires),
        ("_lbutton", button),
    ]:
        try:
            getattr(gui, attr)["text"] = f"{attr[2:].replace('_',' ').title()}: {phase}"
        except:
            pass

    try:
        gui._lstrikes["text"] = f"Strikes left: {strikes_left}"
    except:
        pass

    # 2) Handle any newly failed (strike) or defused phases
    for i, phase in enumerate((keypad, toggles, wires, button)):
        if phase in handled_phases:
            continue

        if phase._failed:
            handled_phases.add(phase)
            strikes_left -= 1
            # show strike image
            strike_index = min(NUM_STRIKES - strikes_left - 1, len(strike_images) - 1)
            show_image(strike_images[strike_index])
            # schedule resume of this exact phase
            window.after(5000, resume_phase, i, phase)
            return

        if phase._defused:
            handled_phases.add(phase)
            active_phases -= 1
            # move to next challenge or win
            if i < len(challenge_images) - 1:
                show_image(challenge_images[i + 1])
                window.after(100, check_phases)
            else:
                show_image(win_image)
                gui.conclusion(success=True)
            return

    # 3) Check for timer expiration
    if not timer._running:
        gui.conclusion(success=False)
        return

    # 4) Continue polling
    window.after(100, check_phases)

def setup_phases():
    global timer, keypad, toggles, wires, button, strikes_left, active_phases, handled_phases

    strikes_left   = NUM_STRIKES
    active_phases  = NUM_PHASES
    handled_phases = set()

    # instantiate each phase
    timer   = Timer(component_7seg, COUNTDOWN)
    keypad  = Keypad(component_keypad, str(keypad_target))
    toggles = Toggles(
        component_toggles,
        bin(toggles_target)[2:].zfill(len(component_toggles))
    )
    wires   = Wires(
        component_wires,
        bin(wires_target)[2:].zfill(len(component_wires))
    )
    button  = Button(
        component_button_state,
        component_button_RGB,
        button_target, button_color, timer,
        submit_phases=(toggles, wires)
    )

    gui.setTimer(timer)
    gui.setButton(button)

    # start them all
    for phase in (timer, keypad, toggles, wires, button):
        phase.start()

    # show the first challenge image
    show_image(challenge_images[0])

def bootup(n=0):
    """Scroll the boot text, then switch to the GUI."""
    if not ANIMATE or n >= len(boot_text):
        gui.setup()
    else:
        if boot_text[n] != "\x00":
            gui._lscroll["text"] += boot_text[n]
        delay = 25 if boot_text[n] != "\x00" else 750
        gui.after(delay, bootup, n + 1)

def start_game():
    gui.setup()
    setup_phases()
    window.after(100, check_phases)

###########
# MAIN
###########
window = Tk()
gui    = Lcd(window)

# kick off boot animation, then start the game
gui.after(1000, bootup)
boot_duration = 1000 + len(boot_text) * 50
gui.after(boot_duration, start_game)

window.mainloop()
