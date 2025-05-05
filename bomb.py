"""
bomb.py
Entry point for the Defuse the Bomb game with randomized imagery per phase.
"""
import sys
import random
from tkinter import Tk, Toplevel, Label
from PIL import Image, ImageTk
from bomb_configs import *       # hardware setup & random targets
from bomb_phases import Timer, Keypad, Wires, Toggles, Button, Lcd

# --- Image pools for each phase; one is chosen at random at game start ---
keypad_images = ["KEYPAD1.jpeg", "KEYPAD2.jpeg", "KEYPAD3.jpeg", "KEYPAD4.jpeg"]
wires_images  = ["WIRES1.jpeg",  "WIRES2.jpeg",  "WIRES3.jpeg",  "WIRES4.jpeg"]
toggles_images= ["TOGGLES1.jpeg","TOGGLES2.jpeg","TOGGLES3.jpeg","TOGGLES4.jpeg"]
button_images = ["BUTTON1.jpeg","BUTTON2.jpeg","BUTTON3.jpeg","BUTTON4.jpeg"]

STRIKE_IMAGES = [
    "STRIKE1.jpeg",
    "STRIKE2.jpeg",
    "STRIKE3.jpeg",
    "STRIKE4.jpeg",
]

# Globals for image popups
global_window = None
img_window    = None
img_photo     = None

# Show a full-screen image and auto-focus it
def show_image(path):
    global img_window, img_photo
    if img_window:
        try: img_window.destroy()
        except: pass
    img_window = Toplevel(global_window)
    img_window.attributes('-fullscreen', True)
    # scale to fit screen
    screen_w = global_window.winfo_screenwidth()
    screen_h = global_window.winfo_screenheight()
    img = Image.open(path)
    iw, ih = img.size
    scale = min(screen_w/iw, screen_h/ih)
    img = img.resize((int(iw*scale), int(ih*scale)), Image.LANCZOS)
    img_photo = ImageTk.PhotoImage(img)
    lbl = Label(img_window, image=img_photo)
    lbl.place(relx=0.5, rely=0.5, anchor='center')

# End the game: win or lose
def end_game(gui, success: bool):
    global img_window
    if img_window:
        try: img_window.destroy()
        except: pass
    gui.conclude(success)

# Main game loop
def start_game(window, gui):
    gui.setup_game()

    # Start the shared countdown timer
    timer = Timer(component_7seg, COUNTDOWN)
    gui.set_timer(timer)
    timer.start()

    # Helper to randomly pick image+target and instantiate a phase
    phase_images = [None]*4
    phases = []
    def create_phase(idx):
        if idx == 0:
            # Keypad phase
            r = random.randrange(len(keypad_images))
            phase_images[0] = keypad_images[r]
            return Keypad(component_keypad, correct_code[r])
        elif idx == 1:
            # Wires phase
            r = random.randrange(len(wires_images))
            phase_images[1] = wires_images[r]
            return Wires(component_wires, correct_wire[r])
        elif idx == 2:
            # Toggles phase
            r = random.randrange(len(toggles_images))
            phase_images[2] = toggles_images[r]
            return Toggles(component_toggles, correct_switch_pattern[r])
        else:
            # Button phase: random presses target for each play
            r = random.randrange(len(button_images))
            phase_images[3] = button_images[r]
            target = random.randint(1, len(button_images))
            btn = Button(component_button_state,
                         component_button_RGB,
                         button_color,
                         target,
                         timer)
            gui.set_button(btn)
            return btn

    # Create and start the first interactive phase
    current = 0
    phase = create_phase(0)
    phases.append(phase)
    phase.start()
    show_image(phase_images[0])

    strikes = NUM_STRIKES

    # Controller: polls timer + current phase
    def controller():
        nonlocal current, strikes, phase
        # Timer expired?
        if timer._failed:
            timer._running = False
            return end_game(gui, False)

        ph = phase
        # Failure in this phase?
        if ph._failed:
            strikes -= 1
            idx = min(NUM_STRIKES - strikes - 1, len(STRIKE_IMAGES)-1)
            show_image(STRIKE_IMAGES[idx])
            ph._failed = False
            if strikes <= 0:
                return end_game(gui, False)
            # restart same phase after a delay
            window.after(2000, lambda: show_image(phase_images[current]))
            window.after(200, controller)
            return

        # Success in this phase?
        if ph._defused:
            current += 1
            if current >= 4:
                timer._running = False
                return end_game(gui, True)
            # set up next phase
            phase = create_phase(current)
            phases.append(phase)
            phase.start()
            window.after(500, lambda: show_image(phase_images[current]))
            window.after(200, controller)
            return

        # Update HUD and continue polling
        gui.update(phases[0] if current>0 else phase,
                   phases[1] if current>1 else phase,
                   phases[2] if current>2 else phase,
                   phase,
                   strikes)
        window.after(100, controller)

    # Kick off the controller loop
    window.after(100, controller)

# Entry point
def main():
    global global_window
    global_window = Tk()
    global_window.state('zoomed')
    gui = Lcd(global_window)
    if ANIMATE:
        gui.after(200, gui.setup_boot)
        gui.after(len(boot_text)*30 + 500, start_game, global_window, gui)
    else:
        start_game(global_window, gui)
    global_window.mainloop()

# run
if __name__ == '__main__':
    main()
# Entry point
def main():
    global global_window
    global_window = Tk()
    global_window.state('zoomed')  # maximize window
    gui = Lcd(global_window)

    # Boot animation, then start
    if ANIMATE:
        gui.after(200, gui.setup_boot)
        gui.after(len(boot_text)*30 + 500, start_game, global_window, gui)
    else:
        start_game(global_window, gui)

    global_window.mainloop()

if __name__ == '__main__':
    main()

