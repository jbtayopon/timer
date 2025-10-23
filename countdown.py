import tkinter as tk
from tkinter import ttk
import threading
import time
import winsound

# -------------------------------
# Globals
# -------------------------------
time_left = 0
running = False
paused = False
display_window = None
display_countdown_label = None
display_message_label = None
beep_triggered_5min = False
beep_triggered_2min = False
beep_triggered_0min = False
timer_job = None  # track after job to prevent duplicates

# -------------------------------
# Beep helper
# -------------------------------
def beep_sequence(seconds=5, freq=1000, duration_ms=400):
    def _beep_loop():
        for _ in range(seconds):
            try:
                winsound.Beep(freq, duration_ms)
            except RuntimeError:
                pass
            time.sleep(1)
    t = threading.Thread(target=_beep_loop, daemon=True)
    t.start()

# -------------------------------
# Update labels
# -------------------------------
def update_control_display(time_text, message_text=None, color="white"):
    countdown_label.config(text=time_text, fg=color)
    if message_text is not None:
        message_label.config(text=message_text)
    if display_window and display_window.winfo_exists():
        display_countdown_label.config(text=time_text, fg=color)
        if message_text is not None:
            display_message_label.config(
                text=message_text,
                wraplength=max(200, display_window.winfo_width()-40)
            )

# -------------------------------
# Dropdown / Start / Reset / Pause
# -------------------------------
def update_preview(event=None):
    global beep_triggered_5min, beep_triggered_2min, beep_triggered_0min, time_left
    beep_triggered_5min = False
    beep_triggered_2min = False
    beep_triggered_0min = False
    try:
        hrs = int(hour_var.get())
        mins = int(minutes_var.get())
        secs = int(seconds_var.get())
        total_seconds = hrs * 3600 + mins * 60 + secs
        time_left = total_seconds
        update_control_display(f"{hrs:02}:{mins:02}:{secs:02}", "Time Remaining", "white")
        if display_window and display_window.winfo_exists():
            display_countdown_label.config(text=f"{hrs:02}:{mins:02}:{secs:02}", fg="white")
            display_message_label.config(text="Time Remaining", fg="white",
                                         wraplength=display_window.winfo_width()-40)
    except Exception:
        pass

def set_time_from_dropdown():
    global time_left
    try:
        hrs = int(hour_var.get())
        mins = int(minutes_var.get())
        secs = int(seconds_var.get())
        time_left = hrs * 3600 + mins * 60 + secs
    except Exception:
        time_left = 0

def start_countdown():
    global running, paused, beep_triggered_5min, beep_triggered_2min, beep_triggered_0min
    if not running:
        beep_triggered_5min = False
        beep_triggered_2min = False
        beep_triggered_0min = False
        set_time_from_dropdown()
        running = True
        paused = False
        pause_btn.config(text="Pause")
        countdown_tick()

def reset_countdown():
    global running, paused, time_left, beep_triggered_5min, beep_triggered_2min, beep_triggered_0min, timer_job
    running = False
    paused = False
    beep_triggered_5min = False
    beep_triggered_2min = False
    beep_triggered_0min = False
    time_left = 0
    if timer_job:
        root.after_cancel(timer_job)
        timer_job = None
    update_control_display("00:00:00", "", "white")
    if display_window and display_window.winfo_exists():
        display_countdown_label.config(text="00:00:00", fg="white")
        display_message_label.config(text="", wraplength=display_window.winfo_width()-40)
    pause_btn.config(text="Pause")

def toggle_pause():
    global paused, timer_job
    if not running:
        return
    paused = not paused
    pause_btn.config(text="Resume" if paused else "Pause")
    if paused:
        if timer_job:
            root.after_cancel(timer_job)
            timer_job = None
    else:
        countdown_tick()

# -------------------------------
# Countdown logic
# -------------------------------
def countdown_tick():
    global time_left, running, paused, beep_triggered_5min, beep_triggered_2min, beep_triggered_0min, timer_job

    if not running:
        return

    hrs = time_left // 3600
    mins = (time_left % 3600) // 60
    secs = time_left % 60
    time_text = f"{hrs:02}:{mins:02}:{secs:02}"

    # Determine color and message
    if time_left == 0:
        msg = "THANK YOU, UP NEXT AWARDING OF PLAQUE OF APPRECIATION."
        color = "red"
        update_control_display(time_text, msg, color)
        if not beep_triggered_0min:
            beep_triggered_0min = True
            beep_sequence(5)
        running = False
        paused = False
        pause_btn.config(text="Pause")
        return
    elif time_left <= 120:
        msg = "PLEASE WRAP UP YOUR TALK...."
        color = "red"
        update_control_display(time_text, msg, color)
        if not beep_triggered_2min:
            beep_triggered_2min = True
            beep_sequence(5)
    elif time_left <= 300:
        msg = "Time Remaining"
        color = "yellow"
        update_control_display(time_text, msg, color)
        if not beep_triggered_5min:
            beep_triggered_5min = True
            beep_sequence(5)
    else:
        msg = "Time Remaining"
        color = "white"
        update_control_display(time_text, msg, color)

    if not paused:
        time_left -= 1

    if timer_job:
        root.after_cancel(timer_job)
    timer_job = root.after(1000, countdown_tick)

# -------------------------------
# Display window and font scaling
# -------------------------------
def center_window(win):
    win.update_idletasks()
    w = win.winfo_width()
    h = win.winfo_height()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw // 2) - (w // 2)
    y = (sh // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")

def open_display():
    global display_window, display_countdown_label, display_message_label
    if display_window and display_window.winfo_exists():
        return

    display_window = tk.Toplevel(root)
    display_window.title("Countdown Display")
    display_window.geometry("600x350")
    display_window.configure(bg="black")
    center_window(display_window)
    display_window.bind("<Escape>", lambda e: display_window.destroy())

    display_countdown_label = tk.Label(display_window, text="00:00:00", font=("Arial", 80), fg="white", bg="black")
    display_countdown_label.place(relx=0.5, rely=0.35, anchor="center")

    display_message_label = tk.Label(display_window, text="", font=("Arial", 24), fg="white", bg="black",
                                     wraplength=display_window.winfo_width()-40, justify="center")
    display_message_label.place(relx=0.5, rely=0.65, anchor="center")

    def on_resize(event=None):
        try:
            w = display_window.winfo_width()
            h = display_window.winfo_height()
            base = min(w, h)
            countdown_size = max(20, int(base / 4))
            message_size = max(12, int(base / 15))
            display_countdown_label.config(font=("Arial", countdown_size))
            display_message_label.config(font=("Arial", message_size), wraplength=w-40)
        except Exception:
            pass
    display_window.bind("<Configure>", lambda e: on_resize())

# -------------------------------
# Control panel UI
# -------------------------------
root = tk.Tk()
root.title("Countdown Control Panel")
root.geometry("650x380")
root.configure(bg="black")

# Header labels
header_frame = tk.Frame(root, bg="black")
header_frame.pack(pady=(10, 0))
tk.Label(header_frame, text="Hour", font=("Arial", 12), fg="white", bg="black", width=10).grid(row=0, column=0, padx=10)
tk.Label(header_frame, text="Minutes", font=("Arial", 12), fg="white", bg="black", width=10).grid(row=0, column=1, padx=10)
tk.Label(header_frame, text="Seconds", font=("Arial", 12), fg="white", bg="black", width=10).grid(row=0, column=2, padx=10)

# Time selection dropdowns
time_select_frame = tk.Frame(root, bg="black")
time_select_frame.pack(pady=(2, 10))

hour_var = tk.StringVar(value="0")
hour_dropdown = ttk.Combobox(time_select_frame, textvariable=hour_var,
                             values=list(range(0, 13)), state="normal", width=8)
hour_dropdown.grid(row=0, column=0, padx=10)
hour_dropdown.bind("<KeyRelease>", update_preview)
hour_dropdown.bind("<<ComboboxSelected>>", update_preview)

minutes_var = tk.StringVar(value="5")
minutes_dropdown = ttk.Combobox(time_select_frame, textvariable=minutes_var,
                                values=list(range(0, 61)), state="normal", width=8)
minutes_dropdown.grid(row=0, column=1, padx=10)
minutes_dropdown.bind("<KeyRelease>", update_preview)
minutes_dropdown.bind("<<ComboboxSelected>>", update_preview)

seconds_var = tk.StringVar(value="0")
seconds_dropdown = ttk.Combobox(time_select_frame, textvariable=seconds_var,
                                values=list(range(0, 61)), state="normal", width=8)
seconds_dropdown.grid(row=0, column=2, padx=10)
seconds_dropdown.bind("<KeyRelease>", update_preview)
seconds_dropdown.bind("<<ComboboxSelected>>", update_preview)

# Countdown label + message
countdown_label = tk.Label(root, text="00:00:00", font=("Arial", 50), fg="white", bg="black")
countdown_label.pack(pady=8)

message_label = tk.Label(root, text="", font=("Arial", 16), fg="white", bg="black",
                         wraplength=520, justify="center")
message_label.pack(pady=4)

# Buttons
btn_frame = tk.Frame(root, bg="black")
btn_frame.pack(pady=12)

start_btn = tk.Button(btn_frame, text="Start", width=10, bg="green", command=start_countdown)
start_btn.grid(row=0, column=0, padx=6)

reset_btn = tk.Button(btn_frame, text="Reset", width=10, bg="red", command=reset_countdown)
reset_btn.grid(row=0, column=1, padx=6)

pause_btn = tk.Button(btn_frame, text="Pause", width=10, bg="yellow", command=toggle_pause)
pause_btn.grid(row=0, column=2, padx=6)

open_btn = tk.Button(btn_frame, text="Open Display", width=12, bg="lightblue", command=open_display)
open_btn.grid(row=0, column=3, padx=6)

update_preview()
root.mainloop()
