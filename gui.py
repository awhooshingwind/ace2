import tkinter as tk
from tkinter import ttk

import trig_wrapper as tw
import vid_wrapper as vw

hardware_trigger = True # True to enable HW trigger
## NOTE: adjust image calculation settings in trig_seq.py if necessary
# still testing light/dark frame smoothing and tuning k-size/sigma parameters

def run_sequence(autosave_flag, smoothing_type):
    info_label.config(
        text=f"Ran sequence script with parameters:\nautosave={autosave_flag}\ntrigger={hardware_trigger}\nsmoothing={smoothing_type}"
        )
    tw.trigger_mode(autosave_flag, hardware_trigger, smoothing_type)

def start_video():
    info_label.config(
        text="Started video mode"
    )
    vw.video_mode(hardware_trigger)
    
# Create main window
root = tk.Tk()
root.title("Basler Interface")
root.geometry("250x265")

# Create autosave checkbox toggle
save_flag = tk.IntVar()
save_checkbox = ttk.Checkbutton(root, text= "Enable Autosave", variable=save_flag)
save_checkbox.pack(pady=8)

# Create smoothing options combobox
smoothing_types = ['Gaussian', 'Median Blur']
selection = tk.StringVar()
smoothing_box = ttk.Combobox(root, textvariable=selection,values=smoothing_types)
smoothing_box.configure(state='readonly')
smoothing_box.current(0)
smoothing_box.pack(pady=8)

# Create start button
start_button = ttk.Button(root, text="Run Triggered Sequence", command=lambda: run_sequence(save_flag.get(), smoothing_box.get()))
start_button.pack(pady=8)

# Create video mode button
video_button = ttk.Button(root, text="Start Video Mode", command=lambda: start_video())
video_button.pack(pady=8)

# Create info label
info_label = ttk.Label(root, 
                       text="Waiting to start...\n\nNote: Use w-a-s-d for fine-tuning position in video mode.",
                       justify='left', wraplength=225)
info_label.pack(pady=5, padx=5)

# Run main loop
root.mainloop()
