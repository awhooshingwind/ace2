import tkinter as tk
from tkinter import ttk

import trigSeq_v3_test as tS

trigger_flag = False

def run_script(autosave_flag, smoothing_type):
    info_label.config(
        text=f"Script started with parameters: \nautosave={autosave_flag}\ntrigger={trigger_flag}\nsmoothing={smoothing_type}"
        )
    tS.app_wrapper(autosave_flag, trigger_flag, smoothing_type)
    
# Create main window
root = tk.Tk()
root.title("Basler Script Launcher")
root.geometry("300x250")

# Create autosave checkbox toggle
save_flag = tk.IntVar()
save_checkbox = ttk.Checkbutton(root, text= "Enable Autosave", variable=save_flag)
save_checkbox.pack(pady=10)

# Create smoothing options combobox
smoothing_types = ['Gaussian', 'Median Blur']
selection = tk.StringVar()
smoothing_box = ttk.Combobox(root, textvariable=selection,values=smoothing_types)
smoothing_box.configure(state='readonly')
smoothing_box.current(0)
smoothing_box.pack(pady=10)

# Create start button
start_button = ttk.Button(root, text="Start Script", command=lambda: run_script(save_flag.get(), smoothing_box.get()))
start_button.pack(pady=10)

# Create info label
info_label = ttk.Label(root, text="Waiting to start...")
info_label.pack(pady=10)

# Run main loop
root.mainloop()
