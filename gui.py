import tkinter as tk
from tkinter import ttk

import trigSeq_v3_test as tS

def run_script(toggle_param):
    # update with Basler script logic
    tS.app_wrapper(toggle_param)
    info_label.config(text=f"Script started with toggle={toggle_param}")

# Create main window
root = tk.Tk()
root.title("Script Launcher")

# Create autosave checkbox toggle
save_flag = tk.IntVar()
save_checkbox = ttk.Checkbutton(root, text= "Enable Autosave", variable=save_flag)
save_checkbox.pack(pady=10)

# Create start button
start_button = ttk.Button(root, text="Start Script", command=lambda: run_script(save_flag.get()))
start_button.pack(pady=10)

# Create info label
info_label = ttk.Label(root, text="Waiting to start...")
info_label.pack(pady=10)
# Run main loop
root.mainloop()
