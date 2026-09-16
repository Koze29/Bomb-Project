#################################
# CSC 102 Defuse the Bomb Project
# Main program
# Team: Lucas and Kobe
#################################

# import the configs
from bomb_configs import *
# import the phases
from bomb_phases import *
import pygame
from time import sleep  

# --- Audio setup ---
pygame.mixer.init()

# Load background music and explosion sound
pygame.mixer.music.load("Bomb.mp3")  # background loop
explosion_snd = pygame.mixer.Sound("Explosion.mp3")  # boom

###########
# functions
###########
 

def show_next_boot_line():
    index = getattr(gui, "_boot_index", 0)

    lines = boot_text.replace("\x00", "").splitlines()
    colors = ["red", "cyan", "yellow", "#39FF14", "orange"]  # Colors

    if index < len(lines):
        line = lines[index]
        color = colors[index % len(colors)]

        # each boot line as its own label in boot_frame
        lbl = Label(gui.boot_frame, text=line, bg="black", fg=color,
                    font=("Courier New", 16), justify=LEFT)
        lbl.pack(anchor="w")

        if not hasattr(gui, "boot_labels"):
            gui.boot_labels = []
        gui.boot_labels.append(lbl)

        gui._boot_index = index + 1

        gui.after(1200, show_next_boot_line)
    else:
       
        # after the last boot line, set up the bomb HUD
        gui.setup()
        if RPi:
            setup_phases()
            check_phases()


def bootup(n=0):
    gui._boot_index = 0
    show_next_boot_line()


    # if we're animating
   
# sets up the phase threads
def setup_phases():
    global timer, keypad, wires, button, toggles
    
    # setup the timer thread
    timer = Timer(component_7seg, COUNTDOWN)
    # bind the 7-segment display to the LCD GUI so that it can be paused/unpaused from the GUI
    gui.setTimer(timer)
    # setup the keypad thread
    keypad = Keypad(component_keypad, keypad_target)
    # setup the jumper wires thread
    wires = Wires(component_wires, wires_target)
    # setup the pushbutton thread
    button = Button(component_button_state, component_button_RGB, button_target, button_color, timer)
    # bind the pushbutton to the LCD GUI so that its LED can be turned off when we quit
    gui.setButton(button)
    # setup the toggle switches thread
    toggles = Toggles(component_toggles, toggles_target)

    # start the phase threads
    timer.start()
    keypad.start()
    wires.start()
    button.start()
    toggles.start()

# checks the phase threads
def check_phases():
    global active_phases
    
    # check the timer
     if (timer._running):
        gui._ltimer["text"] = f"Time left: {timer}"
    else:
        # the countdown has expired -> explode!
        pygame.mixer.music.stop()      # stop background music
        explosion_snd.play()           # play explosion sound

        turn_off()
        gui.after(100, gui.conclusion, False)
        return

    # check the keypad
    if (keypad._running):
        # update the GUI
        gui._lkeypad["text"] = f"Combination: {keypad}"
        # the phase is defused -> stop the thread
        if (keypad._defused):
            keypad._running = False
            active_phases -= 1
        # the phase has failed -> strike
        elif (keypad._failed):
            strike()
            # reset the keypad
            keypad._failed = False
            keypad._value = ""
    # check the wires
    if (wires._running):
        # update the GUI
        gui._lwires["text"] = f"Wires: {wires}"
        # the phase is defused -> stop the thread
        if (wires._defused):
            wires._running = False
            active_phases -= 1
        # the phase has failed -> strike
        elif (wires._failed):
            strike()
            # reset the wires
            wires._failed = False
    # check the button
    if (button._running):
        # update the GUI
        gui._lbutton["text"] = f"Button: {button}"
        # the phase is defused -> stop the thread
        if (button._defused):
            button._running = False
            active_phases -= 1
        # the phase has failed -> strike
        elif (button._failed):
            strike()
            # reset the button
            button._failed = False
    # check the toggles
    if (toggles._running):
        # update the GUI
        gui._ltoggles["text"] = f"Toggles: {toggles}"
        # the phase is defused -> stop the thread
        if (toggles._defused):
            toggles._running = False
            active_phases -= 1
        # the phase has failed -> strike
        elif (toggles._failed):
            strike()
            # reset the toggles
            toggles._failed = False

    # note the strikes on the GUI
    gui._lstrikes["text"] = f"Strikes left: {strikes_left}"
    # too many strikes -> explode!
        if (strikes_left == 0):
        pygame.mixer.music.stop()
        explosion_snd.play()

        turn_off()
        gui.after(1000, gui.conclusion, False)
        return


    # the bomb has been successfully defused!
       if (active_phases == 0):
        # bomb defused successfully: stop music, no explosion
        pygame.mixer.music.stop()

        turn_off()
        gui.after(100, gui.conclusion, True)
        return


    # check the phases again after a slight delay
    gui.after(100, check_phases)

# handles a strike
def strike():
    global strikes_left
    
    # note the strike
    strikes_left -= 1

# turns off the bomb
def turn_off():
    # stop all threads
    timer._running = False
    keypad._running = False
    wires._running = False
    button._running = False
    toggles._running = False

    # turn off the 7-segment display
    component_7seg.blink_rate = 0
    component_7seg.fill(0)
    # turn off the pushbutton's LED
    for pin in button._rgb:
        pin.value = True

######
# MAIN
######

# initialize the LCD
window = Tk()
gui = Lcd(window)

# initialize the bomb strikes and active phases 
strikes_left = NUM_STRIKES
active_phases = NUM_PHASES

# start background music (loop forever)
pygame.mixer.music.play(-1)

# "boot" the bomb
gui.after(100, bootup)

# display the LCD GUI
window.mainloop()





