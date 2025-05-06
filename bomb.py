"""
bomb.py
Entry point for the Defuse the Bomb game with randomized imagery per phase.
"""
import sys
import random
from tkinter import Tk, Toplevel, Label
from PIL import Image, ImageTk
from bomb_configs import *
from bomb_phases import *
import shutil, subprocess
from pygame import mixer

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
    # Destroy previous image window if it exists
    if img_window is not None:
        try:
            img_window.destroy()
        except:
            pass

    # Create new fullscreen image window
    img_window = Toplevel()
    img_window.attributes('-fullscreen', True)

    # Resize and display image
    img = Image.open(path).resize((1000, 800), Image.LANCZOS)
    img_photo = ImageTk.PhotoImage(img)
    lbl = Label(img_window, image=img_photo)
    lbl.pack()


# End the game: win or lose
def end_game(gui, success: bool):
    global img_window
    if img_window:
        try: img_window.destroy()
        except: pass
    if success == True:
        mixer.init()
        mixer.music.load('DEFUSED.wav')
        mixer.music.play()
    else:
        mixer.init()
        mixer.music.load('BOOM.wav')
        mixer.music.play()
    gui.conclude(success)

# Main game loop
def start_game(window, gui):
    global random_button_time
    gui.setup_game()
    update_strikes()

    # Start the shared countdown timer
    timer = Timer(component_7seg, COUNTDOWN)
    gui.set_timer(timer)
    timer.start()

    # Helper to randomly pick image+target and instantiate a phase
    phase_images = [None]*4
    phase_audio = [None]*4
    phases = []
    def create_phase(i):
        if i == 0:
            # Keypad phase
            r = random.randrange(len(keypad_images))
            r_sound = keypad_audio[r]
            phase_images[0] = keypad_images[r]
            mixer.init()
            mixer.music.load(f'{r_sound}')
            mixer.music.play()
            return Keypad(component_keypad, correct_code[r])
        elif i == 1:
            # Wires phase
            r = random.randrange(len(wires_images))
            r_sound = wires_audio[r]
            mixer.init()
            mixer.music.load(f'{r_sound}')
            mixer.music.play()
            phase_images[1] = wires_images[r]
            return Wires(component_wires, correct_wire[r])
        elif i == 2:
            # Toggles phase
            r = random.randrange(len(toggles_images))
            r_sound = toggles_audio[r]
            mixer.init()
            mixer.music.load(f'{r_sound}')
            mixer.music.play()
            phase_images[2] = toggles_images[r]
            return Toggles(component_toggles, correct_switch_pattern[r])
        else:
            # Button phase: random presses target for each play
            r = random.randrange(len(button_images))
            r_sound = button_audio[r]
            s = random.randint(0,3)
            phase_images[3] = button_images[r]
            mixer.init()
            mixer.music.load(f'{r_sound}')
            mixer.music.play()
            random_button_time = BUTTON_MAX_TIME[s]
            btn = Button(component_button_state,
                         component_button_RGB,
                         button_color,
                         amount_of_presses[s],
                         random_button_time,
                         timer
                         )
            gui.set_button(btn)
            return btn

    # Create and start the first interactive phase
    current = 0
    phase = create_phase(current)
    phases.append(phase)
    phase.start()
    show_image(phase_images[current])
    
    def update_strikes():
        gui._lstrikes["text"] = f"Strikes left: {strikes_left}"
        
    # Controller: polls timer + current phase
    def controller():
        nonlocal current, phase
        global strikes_left
        # Timer expired?
        if timer._failed:
            timer._running = False
            return end_game(gui, False)

        ph = phase
        strikes_left -= 1
        update_strikes()
        # Failure in this phase?
        if ph._failed:
            handle_strike()
            sound = strike_audio[strikes]
            mixer.init()
            mixer.music.load(f'{sound}')
            mixer.music.play()
            print(strikes)
            show_image(STRIKE_IMAGES[strikes-1])
            ph._failed = False
            if strikes <= 0:
                return end_game(gui, False)
            # restart same phase after a delay
            window.after(2000, lambda: show_image(phase_images[current]))
            mixer.init()
            mixer.music.load(phase_audio[current])
            mixer.music.play()
            window.after(200, controller)
            return

        # Success in this phase?
        if ph._defused:
            if img_window:
                img_window.destroy()
            current += 1
            if current == 4:
                timer._running = False
                return end_game(gui, True)
            # set up next phase
            phase = create_phase(current)
            phases.append(phase)
            phase.start()
            window.after(500, lambda: show_image(phase_images[current]))
            window.after(200, controller)
            return
        
        if current == 0:
            gui.update_keypad(phases[0])
        elif current == 1:
            gui.update_wires(phases[1])
        elif current == 2:
            gui.update_toggles(phases[2])
        elif current == 3:
            gui.update_button(phases[3])
            phases[3].set_color('G')
        window.after(100, controller)

    # Kick off the controller loop
    window.after(100, controller)

# Entry point
def main():
    global global_window
    global_window = Tk()

    gui = Lcd(global_window)

    if ANIMATE:
        gui.after(200, gui.setup_boot)
        gui.after(len(boot_text)*30 + 500, start_game, global_window, gui)
    else:
        start_game(global_window, gui)

    global_window.mainloop()

if __name__ == '__main__':
    main()
