import tkinter as tk
from tkinter import ttk

import trig_seq as ts
from imaging import trigger_mode as tw
from imaging import video_mode as vw
# from imaging import playground as play
from imaging import hot_button as hb

hardware_trigger = True

# TESTING IN PROGRESS
# def new_config_test():
#     info_label.config(
#         text="Caution, in progress..."
#     )
#     play.button_wrap()

def run_sequence(autosave_flag, smoothing_type):
    info_label.config(
        text=f"Ran sequence script with parameters:\nautosave={autosave_flag}\ntrigger={hardware_trigger}\nsmoothing={smoothing_type}"
        )

    trigger_seq = ts.TriggeredSequence(autosave=autosave_flag, smoothing=smoothing_type)
    tw(hardware_trigger, trigger_seq)

def run_single(autosave_flag, smoothing_type):
    trigger_seq = ts.TriggeredSequence(autosave=autosave_flag, smoothing=smoothing_type, singlet_flag=True)
    tw(hardware_trigger, trigger_seq)

def start_video():
    info_label.config(
        text="Started video mode"
    )
    vw(hw_mode=hardware_trigger)

def update_hot_pixels():
    hb()

    
# Create main window
root = tk.Tk()
root.title("Basler Interface")
root.geometry("250x295")

top_row = tk.Frame(root)
top_row.pack(pady=8)
# Create test playground button
# test_button = ttk.Button(top_row, text="Feature Test", command=lambda: new_config_test())
# test_button.pack(side='left', padx=8)


# Create hot pixel update button
hot_pixel_button = ttk.Button(top_row, 
                              text="Update Hot Pixel Coords", 
                              command=lambda: update_hot_pixels())
hot_pixel_button.pack(side='right', padx=8)

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

seq_row = tk.Frame(root)
seq_row.pack(pady=8)
# Create singe image button
single_img_button = ttk.Button(seq_row, 
                              text="Single Image", 
                              command=lambda: run_single(save_flag.get(), smoothing_box.get()))
single_img_button.pack(side='left', padx=8)

# Create start triggered sequence button
start_button = ttk.Button(seq_row, 
                          text="Triggered Sequence", 
                          command=lambda: run_sequence(save_flag.get(), smoothing_box.get()))
start_button.pack(side='right', pady=8)

# Create video mode button
video_button = ttk.Button(root, 
                          text="Start Video Mode", 
                          command=lambda: start_video())
video_button.pack(pady=8)


# Create info label
info_label = ttk.Label(root, 
                       text="Waiting to start...\n\nNote: Use w-a-s-d for fine-tuning position in video mode.",
                       justify='left', wraplength=225)
info_label.pack(pady=5, padx=5)

# Run main loop
root.mainloop()
