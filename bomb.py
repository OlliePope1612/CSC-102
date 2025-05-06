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

    mixer.init()
    mixer.music.load('DEFUSED.wav' if success else 'BOOM.wav')
    mixer.music.play()

    # <-- NOTE: your Lcd method is called `.conclusion()`, not `.conclude()`
    gui.conclusion(success)


def start_game(window, gui):
    global strikes_left
    strikes_left = NUM_STRIKES

    gui.setup_game()

    # pull out strikes–updater so we can call it whenever
    def update_strikes():
        gui.update_strikes(strikes_left)
    update_strikes()

    # start the timer
    timer = Timer(component_7seg, COUNTDOWN)
    gui.set_timer(timer)
    timer.start()

    # prepare storage for images & audio so we can replay them on retry
    phase_images = [None]*4
    phase_audio  = [None]*4

    def create_phase(i):
        # pick a random index & remember both image+audio
        if i == 0:
            r = random.randrange(len(keypad_images))
            phase_images[0] = keypad_images[r]
            phase_audio[0]  = keypad_audio[r]
            mixer.init(); mixer.music.load(phase_audio[0]); mixer.music.play()
            return Keypad(component_keypad, correct_code[r])

        elif i == 1:
            r = random.randrange(len(wires_images))
            phase_images[1] = wires_images[r]
            phase_audio[1]  = wires_audio[r]
            mixer.init(); mixer.music.load(phase_audio[1]); mixer.music.play()
            return Wires(component_wires, correct_wire[r])

        elif i == 2:
            r = random.randrange(len(toggles_images))
            phase_images[2] = toggles_images[r]
            phase_audio[2]  = toggles_audio[r]
            mixer.init(); mixer.music.load(phase_audio[2]); mixer.music.play()
            return Toggles(component_toggles, correct_switch_pattern[r])

        else:
            r = random.randrange(len(button_images))
            phase_images[3] = button_images[r]
            phase_audio[3]  = button_audio[r]
            mixer.init(); mixer.music.load(phase_audio[3]); mixer.music.play()

            # pick a random press‐count & timeout
            s = random.randrange(len(amount_of_presses))
            timeout = BUTTON_MAX_TIME[s]
            btn = Button(
                component_button_state,
                component_button_RGB,
                button_color,
                amount_of_presses[s],
                timeout,
                timer
            )
            gui.set_button(btn)
            return btn

    # build & start the first phase
    current = 0
    phase   = create_phase(current)
    phase.start()
    show_image(phase_images[current])


    # the polling loop
    def controller():
        nonlocal current, phase, strikes_left

        # check for timer fail
        if timer._failed:
            timer._running = False
            return end_game(gui, False)

        # on failure, strike & retry
        if phase._failed:
            strikes_left -= 1
            update_strikes()

            # play the appropriate strike sound
            mixer.init()
            mixer.music.load(strike_audio[strikes_left])
            mixer.music.play()

            # show strike image for 2s
            show_image(STRIKE_IMAGES[strikes_left], hold_ms=2000)

            phase._failed = False
            if strikes_left <= 0:
                return end_game(gui, False)

            # after 2s, replay the same challenge image+audio
            window.after(2000, lambda: show_image(phase_images[current]))
            window.after(2000, lambda: mixer.init() or mixer.music.load(phase_audio[current]) or mixer.music.play())
            window.after(2100, controller)
            return

        # on success, advance
        if phase._defused:
            if img_window:
                try: img_window.destroy()
                except: pass

            current += 1
            if current >= 4:
                timer._running = False
                return end_game(gui, True)

            phase = create_phase(current)
            phase.start()
            window.after(500, lambda: show_image(phase_images[current]))
            window.after(600, controller)
            return

        # update the LCD for whichever phase is active
        if current == 0:
            gui.update_keypad(phase)
        elif current == 1:
            gui.update_wires(phase)
        elif current == 2:
            gui.update_toggles(phase)
        else:
            gui.update_button(phase)

        # keep polling
        window.after(100, controller)

    # kick off the controller
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
