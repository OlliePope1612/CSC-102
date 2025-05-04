from tkinter import Tk, Toplevel, Label
from PIL import Image, ImageTk
from bomb_configs import *        # component_7seg, component_keypad, COUNTDOWN, etc.
from bomb_phases import Timer, Keypad, Wires, Button, Toggles, Lcd
import random

# File names for images
challenge_images = [
    "KEYPAD.jpeg",
    "TOGGLES.jpeg",
    "WIRES.jpeg",
    "meg.jpg",
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
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    img = Image.open(path).resize((screen_w, screen_h), Image.LANCZOS)
    img_photo = ImageTk.PhotoImage(img)
    lbl = Label(img_window, image=img_photo)
    lbl.pack(fill='both', expand=True)

# Interactive toggles window using GUI checkboxes
def show_switch_window():
    top = Toplevel(window)
    top.attributes('-fullscreen', True)
    top.lift()
    top.focus_force()
    top.config(bg='black')
    # show background image
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    img = Image.open(challenge_images[1]).resize((screen_w, screen_h), Image.LANCZOS)
    photo = ImageTk.PhotoImage(img)
    bg = Label(top, image=photo)
    bg.image = photo
    bg.pack(fill='both', expand=True)
    # overlay checkboxes
    from tkinter import Frame, IntVar, Checkbutton, Button
    frame = Frame(top, bg='black')
    frame.place(relx=0.5, rely=0.5, anchor='center')
    vars = []
    for i in range(len(toggles._target)):
        v = IntVar(value=0)
        cb = Checkbutton(frame, text=f"Switch {i+1}", variable=v,
                        font=("Courier New",18), fg="white", bg="black",
                        selectcolor="black")
        cb.pack(anchor='w')
        vars.append(v)
    def on_submit():
        pattern = "".join(str(v.get()) for v in vars)
        if pattern == toggles._target:
            toggles.defuse()
            top.destroy()
    btn = Button(frame, text="Submit", font=("Courier New",18),
                 command=on_submit)
    btn.pack(pady=10)

# Core GUI & game logic
def check_phases():
():
    global strikes_left, active_phases
    # Update underlying labels (optional)
    try: gui._ltimer["text"]   = f"Time left: {timer}"
    except: pass
    try: gui._lkeypad["text"]  = f"Keypad: {keypad}"
    except: pass
    try: gui._ltoggles["text"] = f"Toggles: {toggles}"
    except: pass
    try: gui._lwires["text"]   = f"Wires: {wires}"
    except: pass
    try: gui._lbutton["text"]  = f"Button: {button}"
    except: pass
    try: gui._lstrikes["text"] = f"Strikes left: {strikes_left}"
    except: pass

    # Check each phase in order
    for idx, phase in enumerate((keypad, toggles, wires, button)):
        if phase in handled_phases:
            continue
        # failure handling
        if phase._failed:
            handled_phases.add(phase)
            strikes_left -= 1
            # show strike image
            show_image(strike_images[min(idx, len(strike_images)-1)])
            # after 5s, either game over or re-show challenge
            def next_step():
                if strikes_left > 0:
                    show_image(challenge_images[idx])
                else:
                    show_image(game_over_image)
                    gui.conclusion(success=False)
            window.after(5000, next_step)
            return
        # defuse handling
        if phase._defused:
            handled_phases.add(phase)
            active_phases -= 1
            # advance: show next challenge or win
            if idx < len(challenge_images)-1:
                show_image(challenge_images[idx+1])
            else:
                show_image(win_image)
                gui.conclusion(success=True)
            return

    # continue polling
    window.after(100, check_phases)

# Start game after boot
def start_game():
    gui.setup()
    setup_phases()
    window.after(100, check_phases)

# MAIN
window = Tk()
gui = Lcd(window)
gui.after(1000, bootup)
boot_duration = 1000 + len(boot_text)*50
gui.after(boot_duration, start_game)
window.mainloop()
