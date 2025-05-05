#!/usr/bin/env python3
"""
bomb.py
Entry point for the Family Guy–themed Defuse the Bomb game using bomb_configs and bomb_phases.
"""
import sys
from tkinter import Tk, Toplevel, Label
from PIL import Image, ImageTk
from bomb_configs import *       # hardware setup & random targets
from bomb_phases import Timer, Keypad, Wires, Toggles, Button, Lcd

# --- Asset paths for Family Guy theme ---
CHALLENGE_IMAGES = [
    "KEYPAD.jpeg",
    "WIRES.jpeg",
    "TOGGLES.jpeg",
    "BUTTON.jpeg",
]
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
    img_window.attributes("-fullscreen")  # or "1280x800", "1920x1080", etc.
    #img_window.pack(fill="both", expand=True)
    #gui = Lcd(window)
    #gui.pack(fill="both", expand=True)
    #gui.after(1000, bootup)
    
    img_window.resizable(False, False)
    w = global_window.winfo_screenwidth() - 100
    h = global_window.winfo_screenheight() - 100
    img = Image.open(path).resize((w, h), Image.LANCZOS)
    img_photo = ImageTk.PhotoImage(img)
    Label(img_window, image=img_photo).pack(fill='both', expand=True)

# End the game: win or lose
def end_game(gui, success: bool):
    img_window.destroy()
    gui.conclude(success)

# Main game loop
def start_game(window, gui):
    gui.setup_game()

    # Instantiate phases
    timer   = Timer(component_7seg, COUNTDOWN)
    keypad  = Keypad(component_keypad, correct_code)
    wires   = Wires(component_wires, correct_wire)
    toggles = Toggles(component_toggles, correct_switch_pattern)
    button  = Button(component_button_state,
                     component_button_RGB,
                     button_color,
                     button_target,
                     timer)
    original = button._original_color
    
    
    # Link with GUI
    gui.set_timer(timer)
    gui.set_button(button)

    # Start all threads
    timer.start()
    for phase in (keypad, wires, toggles, button):
        phase.start()

    strikes = NUM_STRIKES
    current = 0
    phases_list = [keypad, wires, toggles, button]

    def show_phase(idx):
        # only display if index is valid
        if 0 <= idx < len(CHALLENGE_IMAGES):
            show_image(CHALLENGE_IMAGES[idx])

    def controller():
        nonlocal strikes, current
                # Timer expired?
        if timer._failed:
            timer._running = False   # stop the background timer thread
            return end_game(gui, False)

        
        # switch button LED color for submission phases
        if current == 3:
            button.set_color('B')
        else:
            button.set_color(original)

        ph = phases_list[current]
        
        # Phase failure?
        if ph._failed:
            if strikes == 1 or strikes == 2:
                show_image(STRIKE_IMAGES[strikes-1])
            else:
                show_image(STRIKE_IMAGES[strikes-2])
            strikes -= 1
            ph._failed = False
            if strikes <= 0:
                return end_game(gui, False)
            # retry same phase
            window.after(2000, lambda: show_phase(current))
            window.after(200, controller)
            return

                # Phase success?
        if ph._defused:
            button.set_color('G')
            window.after(2000, lambda: button.set_color(original))
            current += 1
            if current >= len(phases_list):
                timer._running = False   # stop the timer here too
                return end_game(gui, True)
            window.after(500, lambda idx=current: show_phase(idx))
            window.after(200, controller)
            return

        # Update the HUD
        gui.update(keypad, wires, toggles, button, strikes)
        window.after(100, controller)

    # launch first image and controller
    show_phase(0)
    window.after(100, controller)

# Entry point
def main():
    global global_window
    global_window = Tk()
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
