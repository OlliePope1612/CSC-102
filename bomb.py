from tkinter import Tk, Toplevel, Label
from PIL import Image, ImageTk
from bomb_configs import *        # hardware components & constants
from bomb_phases import Timer, Keypad, Wires, Button, Toggles, Lcd

# File names for images
challenge_images = [
    "KEYPAD.jpeg",  # keypad challenge
    "TOGGLES.jpeg",     # toggles challenge
    "WIRES.jpeg",     # wires challenge
    "BUTTON.jpeg",     # button challenge
]
strike_images = [
    "STRIKE4.jpeg",
    "STRIKE3.jpeg",
    "STRIKE2.jpeg",
    "STRIKE1.jpeg",
]
# Globals for image window
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

def setup_phases():
    global timer, keypad, toggles, wires, button, strikes_left, active_phases, handled_phases

    # reset counters
    strikes_left  = NUM_STRIKES
    active_phases = NUM_PHASES
    handled_phases = set()

    # instantiate each phase
    timer   = Timer(component_7seg, COUNTDOWN)
    keypad  = Keypad(component_keypad, str(keypad_target))
    toggles = Toggles(component_toggles, bin(toggles_target)[2:].zfill(len(component_toggles)))
    wires   = Wires(component_wires,    bin(wires_target)[2:].zfill(len(component_wires)))
    button  = Button(
        component_button_state,
        component_button_RGB,
        button_target, button_color, timer,
        submit_phases=(toggles, wires)
    )

    # hook GUI controls into the timer & button
    gui.setTimer(timer)
    gui.setButton(button)

    # start all of them
    for phase in (timer, keypad, toggles, wires, button):
        phase.start()

    # show the very first “challenge” image (Keypad)
    show_image(challenge_images[0])

    # force the button into blue/submit mode until we hit the Button challenge
    button._set_color("B")
    
# Core logic: monitor phases
def check_phases():
    global strikes_left, active_phases, handled_phases
    # update LCD labels
    for attr, phase in [
        ("_ltimer", timer), ("_lkeypad", keypad),
        ("_ltoggles", toggles), ("_lwires", wires), ("_lbutton", button)
    ]:
        try:
            getattr(gui, attr)["text"] = f"{attr[2:].replace('_',' ').title()}: {phase}"
        except:
            pass
    try:
        gui._lstrikes["text"] = f"Strikes left: {strikes_left}"
    except:
        pass

    # iterate in order: keypad, toggles, wires, button
    for i, phase in enumerate((keypad, toggles, wires, button)):
        # skip if already handled
        if phase in handled_phases:
            continue
        # failure handling
        if phase._failed:
            handled_phases.add(phase)
            # decrement strikes and choose strike image based on count
            strikes_left -= 1
            strike_count = NUM_STRIKES - strikes_left  # e.g. 1 for first strike
            img_i = min(strike_count - 1, len(strike_images) - 1)
            show_image(strike_images[img_i])

            def resume():
                global strikes_left, handled_phases, keypad, toggles, wires, button
                if strikes_left > 0:
                    # retry same challenge
                    show_image(challenge_images[i])
                    handled_phases.discard(phase)
                    # recreate and restart thread
                    if i == 0:
                        keypad = Keypad(component_keypad, "1999")
                        keypad.start()
                    elif i == 1:
                        toggles = Toggles(component_toggles, "1010")
                        toggles.start()
                    elif i == 2:
                        wires = Wires(component_wires, "01010")
                        wires.start()
                    else:
                        button = Button(
                            component_button_state,
                            component_button_RGB,
                            button_target, button_color, timer
                        )
                        button.start()
                    window.after(100, check_phases)
                else:
                    show_image(game_over_image)
                    gui.conclusion(success=False)

            window.after(5000, resume)
            return
            return

        # defuse handling
        if phase._defused:
            handled_phases.add(phase)
            active_phases -= 1
        
            if i < len(challenge_images) - 1:
                next_img = challenge_images[i+1]
                show_image(next_img)
        
                # ○ ○ ○  NEW: force button color based on whether it's the BUTTON challenge  ○ ○ ○
                if next_img == "BUTTON.jpeg":
                    # red = defuse‐mode
                    button._set_color("R")
                else:
                    # blue = submit‐mode for wires/toggles
                    button._set_color("B")
                # ○ ○ ○  end NEW  ○ ○ ○
        
                window.after(100, check_phases)
            else:
                show_image(win_image)
                gui.conclusion(success=True)
            return
        
        if timer._running == False:
            gui.conclusion(success=False)
    # continue polling if no state change
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
    wires   = Wires(component_wires, "10101")        # odd-numbered wires
    button  = Button(
        component_button_state,
        component_button_RGB,
        button_target, button_color, timer,
        submit_phases = (toggles, wires)
    )

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
        if boot_text[n] != "\x00":
            gui._lscroll["text"] += boot_text[n]
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
