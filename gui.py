import tkinter as tk
from tkinter import ttk

import app_wrapper as aw
import vid_wrapper as vw

trigger_flag = False 

def run_sequence(autosave_flag, smoothing_type):
    info_label.config(
        text=f"Ran sequence script\nParameters: \nautosave={autosave_flag}\ntrigger={trigger_flag}\nsmoothing={smoothing_type}"
        )
    aw.trigger_mode(autosave_flag, trigger_flag, smoothing_type)

def start_video():
    info_label.config(
        text="Started video mode"
    )
    vw.video_mode()
    
# Create main window
root = tk.Tk()
root.title("Basler Script Interface")
root.geometry("220x285")

# Create autosave checkbox toggle
save_flag = tk.IntVar()
save_checkbox = ttk.Checkbutton(root, text= "Enable Autosave", variable=save_flag)
save_checkbox.pack(pady=15)

# Create smoothing options combobox
smoothing_types = ['Gaussian', 'Median Blur']
selection = tk.StringVar()
smoothing_box = ttk.Combobox(root, textvariable=selection,values=smoothing_types)
smoothing_box.configure(state='readonly')
smoothing_box.current(0)
smoothing_box.pack(pady=10)

# Create start button
start_button = ttk.Button(root, text="Run Triggered Sequence", command=lambda: run_sequence(save_flag.get(), smoothing_box.get()))
start_button.pack(pady=10)

# Create video mode button
video_button = ttk.Button(root, text="Start Video Mode", command=lambda: start_video())
video_button.pack(pady=10)

# Create info label
info_label = ttk.Label(root, text="Waiting to start...")
info_label.pack(pady=5)

# Run main loop
root.mainloop()
