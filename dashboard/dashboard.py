import tkinter as tk
from tkinter import ttk
import random


# ==============================
# MAIN WINDOW
# ==============================

root = tk.Tk()
root.title("AI Driver Drowsiness Detection System")
root.geometry("1000x650")
root.configure(bg="#1e1e1e")


# ==============================
# TITLE
# ==============================

title = tk.Label(
    root,
    text="AI DRIVER DROWSINESS DETECTION SYSTEM",
    font=("Arial", 22, "bold"),
    bg="#1e1e1e",
    fg="white"
)
title.pack(pady=20)


# ==============================
# MAIN FRAME
# ==============================

main_frame = tk.Frame(root, bg="#1e1e1e")
main_frame.pack(fill="both", expand=True, padx=30)


# ==============================
# CAMERA / DRIVER VIEW
# ==============================

camera_frame = tk.Frame(
    main_frame,
    bg="#2b2b2b",
    width=450,
    height=350
)

camera_frame.pack(side="left", padx=15, pady=10)
camera_frame.pack_propagate(False)

camera_title = tk.Label(
    camera_frame,
    text="DRIVER MONITORING CAMERA",
    font=("Arial", 15, "bold"),
    bg="#2b2b2b",
    fg="white"
)

camera_title.pack(pady=20)

camera_display = tk.Label(
    camera_frame,
    text="CAMERA FEED\n\nSimulation Mode",
    font=("Arial", 18),
    bg="#111111",
    fg="#00ff99",
    width=28,
    height=10
)

camera_display.pack(pady=10)


# ==============================
# STATUS DASHBOARD
# ==============================

dashboard_frame = tk.Frame(main_frame, bg="#1e1e1e")
dashboard_frame.pack(side="right", fill="both", expand=True)


# ==============================
# STATUS VARIABLES
# ==============================

eye_status_var = tk.StringVar(value="NORMAL")
ear_var = tk.StringVar(value="0.30")
blink_var = tk.StringVar(value="15 / min")
drowsiness_var = tk.StringVar(value="LOW")
alert_var = tk.StringVar(value="NO ALERT")


# ==============================
# DASHBOARD CARD FUNCTION
# ==============================

def create_card(parent, title_text, variable):

    frame = tk.Frame(
        parent,
        bg="#2b2b2b",
        width=400,
        height=75
    )

    frame.pack(pady=7, fill="x")

    title_label = tk.Label(
        frame,
        text=title_text,
        font=("Arial", 11, "bold"),
        bg="#2b2b2b",
        fg="#aaaaaa"
    )

    title_label.pack(anchor="w", padx=15, pady=(10, 0))

    value_label = tk.Label(
        frame,
        textvariable=variable,
        font=("Arial", 16, "bold"),
        bg="#2b2b2b",
        fg="white"
    )

    value_label.pack(anchor="w", padx=15)


# ==============================
# DASHBOARD CARDS
# ==============================

create_card(dashboard_frame, "EYE STATUS", eye_status_var)
create_card(dashboard_frame, "EYE ASPECT RATIO (EAR)", ear_var)
create_card(dashboard_frame, "BLINK RATE", blink_var)
create_card(dashboard_frame, "DROWSINESS LEVEL", drowsiness_var)
create_card(dashboard_frame, "ALERT STATUS", alert_var)


# ==============================
# SIMULATION VARIABLES
# ==============================

simulation_running = False

# Current simulated values
current_ear = 0.30
current_blink_rate = 15
current_drowsiness = 10


# ==============================
# UPDATE SIMULATION
# ==============================

def update_simulation():

    global current_ear
    global current_blink_rate
    global current_drowsiness

    if not simulation_running:
        return

    # --------------------------------
    # Simulate changing EAR
    # --------------------------------

    current_ear += random.uniform(-0.025, 0.025)

    # Keep EAR within realistic simulation range
    current_ear = max(0.10, min(0.35, current_ear))


    # --------------------------------
    # Simulate changing blink rate
    # --------------------------------

    current_blink_rate += random.randint(-2, 2)

    current_blink_rate = max(3, min(20, current_blink_rate))


    # --------------------------------
    # Calculate drowsiness
    # --------------------------------

    # Lower EAR → more drowsiness
    ear_drowsiness = (0.35 - current_ear) / 0.25 * 100

    # Lower blink rate → more drowsiness
    blink_drowsiness = (20 - current_blink_rate) / 17 * 100

    # Combine the two values
    current_drowsiness = (
        ear_drowsiness * 0.7 +
        blink_drowsiness * 0.3
    )

    current_drowsiness = max(
        0,
        min(100, current_drowsiness)
    )


    # --------------------------------
    # Determine driver state
    # --------------------------------

    if current_drowsiness < 30:

        eye_status_var.set("OPEN / NORMAL")
        drowsiness_var.set("LOW")
        alert_var.set("NO ALERT")

        camera_display.config(
            text="CAMERA FEED\n\nDriver Alert",
            fg="#00ff99"
        )

    elif current_drowsiness < 60:

        eye_status_var.set("PARTIALLY CLOSED")
        drowsiness_var.set("MEDIUM")
        alert_var.set("⚠ CAUTION")

        camera_display.config(
            text="CAMERA FEED\n\n⚠ DRIVER FATIGUE",
            fg="#ffff55"
        )

    else:

        eye_status_var.set("CLOSED / DROWSY")
        drowsiness_var.set("HIGH")
        alert_var.set("⚠ WARNING: DRIVER DROWSY!")

        camera_display.config(
            text="CAMERA FEED\n\n⚠ DROWSINESS DETECTED",
            fg="#ff5555"
        )


    # --------------------------------
    # Update dashboard values
    # --------------------------------

    ear_var.set(f"{current_ear:.2f}")
    blink_var.set(f"{current_blink_rate} / min")


    # --------------------------------
    # Schedule next update
    # --------------------------------

    root.after(500, update_simulation)


# ==============================
# START SIMULATION
# ==============================

def start_simulation():

    global simulation_running

    if simulation_running:
        return

    simulation_running = True

    update_simulation()


# ==============================
# STOP SIMULATION
# ==============================

def stop_simulation():

    global simulation_running

    simulation_running = False

    camera_display.config(
        text="CAMERA FEED\n\nSimulation Stopped",
        fg="white"
    )


# ==============================
# BUTTON FRAME
# ==============================

button_frame = tk.Frame(
    root,
    bg="#1e1e1e"
)

button_frame.pack(pady=20)


# ==============================
# START BUTTON
# ==============================

start_button = tk.Button(
    button_frame,
    text="START SIMULATION",
    font=("Arial", 14, "bold"),
    bg="#00aa66",
    fg="white",
    padx=25,
    pady=10,
    command=start_simulation
)

start_button.pack(side="left", padx=10)


# ==============================
# STOP BUTTON
# ==============================

stop_button = tk.Button(
    button_frame,
    text="STOP SIMULATION",
    font=("Arial", 14, "bold"),
    bg="#aa3333",
    fg="white",
    padx=25,
    pady=10,
    command=stop_simulation
)

stop_button.pack(side="left", padx=10)


# ==============================
# RUN APPLICATION
# ==============================

root.mainloop()
