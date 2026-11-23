"""Main application for CSC 102: Defuse the Bomb."""
from tkinter import Tk, Label, LEFT

from bomb_configs import *
from bomb_phases import Lcd, Timer, Keypad, Wires, Button, Toggles

# Sound is optional. The program remains playable without pygame or audio files.
try:
    import pygame
    pygame.mixer.init()
    pygame.mixer.music.load("Bomb.mp3")
    explosion_snd = pygame.mixer.Sound("Explosion.mp3")
    AUDIO_ENABLED = True
except Exception as error:
    print(f"Audio disabled: {error}")
    pygame = None
    explosion_snd = None
    AUDIO_ENABLED = False


def stop_music():
    if AUDIO_ENABLED:
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass


def play_explosion():
    if AUDIO_ENABLED:
        try:
            stop_music()
            explosion_snd.play()
        except pygame.error as error:
            print(f"Could not play explosion sound: {error}")


def setup_phases():
    """Create and start the timer and four hardware phase threads."""
    global timer, keypad, wires, button, toggles

    timer = Timer(component_7seg, COUNTDOWN)
    keypad = Keypad(component_keypad, keypad_target)
    wires = Wires(component_wires, wires_target)
    button = Button(
        component_button_state, component_button_RGB,
        button_target, button_color, timer
    )
    toggles = Toggles(component_toggles, toggles_target)

    gui.setTimer(timer)
    gui.setButton(button)
    for phase in (timer, keypad, wires, button, toggles):
        phase.start()


def turn_off():
    """Stop worker threads and safely turn off hardware indicators."""
    for phase_name in ("timer", "keypad", "wires", "button", "toggles"):
        phase = globals().get(phase_name)
        if phase is not None:
            phase.stop()

    if RPi:
        try:
            component_7seg.blink_rate = 0
            component_7seg.fill(0)
            for pin in button._rgb:
                pin.value = True
        except Exception as error:
            print(f"Hardware shutdown warning: {error}")


def finish_game(success):
    global game_finished
    if game_finished:
        return
    game_finished = True
    stop_music()
    if not success:
        play_explosion()
    turn_off()
    gui.after(250, gui.conclusion, success)


def strike():
    global strikes_left
    strikes_left = max(0, strikes_left - 1)


def check_phases():
    """Poll worker-thread state from Tk's main thread."""
    global active_phases

    if game_finished:
        return

    if not timer._running:
        # A just-started worker may not have entered run() yet.
        if timer.is_alive():
            gui.after(100, check_phases)
            return
        finish_game(False)
        return

    gui._ltimer["text"] = f"Time left: {timer}"
    phase_widgets = (
        (keypad, gui._lkeypad, "Combination"),
        (wires, gui._lwires, "Wires"),
        (button, gui._lbutton, "Button"),
        (toggles, gui._ltoggles, "Toggles"),
    )

    for phase, widget, label in phase_widgets:
        if not phase._running:
            continue
        widget["text"] = f"{label}: {phase}"
        if phase._defused:
            phase.stop()
            active_phases -= 1
        elif phase._failed:
            strike()
            phase._failed = False
            if isinstance(phase, Keypad):
                phase._value = ""

    gui._lstrikes["text"] = f"Strikes left: {strikes_left}"

    if strikes_left <= 0:
        finish_game(False)
        return
    if active_phases <= 0:
        finish_game(True)
        return

    gui.after(100, check_phases)


def show_next_boot_line():
    index = gui._boot_index
    lines = boot_text.splitlines()
    colors = ["red", "cyan", "yellow", "#39FF14", "orange"]

    if index < len(lines):
        Label(
            gui.boot_frame, text=lines[index], bg="black",
            fg=colors[index % len(colors)],
            font=("Courier New", 16), justify=LEFT
        ).pack(anchor="w")
        gui._boot_index += 1
        gui.after(700, show_next_boot_line)
        return

    gui.setup()
    if RPi:
        setup_phases()
        gui.after(250, check_phases)
    else:
        Label(
            gui.bomb_frame,
            text=(
                "Windows test mode: Raspberry Pi hardware is disabled.\n"
                "Set RPi = True on the Raspberry Pi to use the components."
            ),
            bg="black", fg="yellow", font=("Courier New", 14),
            justify=LEFT
        ).grid(row=5, column=0, columnspan=3, sticky="w")


def close_application(_event=None):
    stop_music()
    if RPi and "timer" in globals():
        turn_off()
    if AUDIO_ENABLED:
        try:
            pygame.mixer.quit()
        except pygame.error:
            pass
    window.destroy()


strikes_left = NUM_STRIKES
active_phases = NUM_PHASES
game_finished = False

window = Tk()
gui = Lcd(window)
window.bind("<Escape>", close_application)

if AUDIO_ENABLED:
    try:
        pygame.mixer.music.play(-1)
    except pygame.error as error:
        print(f"Background music unavailable: {error}")

gui.after(100, show_next_boot_line)
window.mainloop()
