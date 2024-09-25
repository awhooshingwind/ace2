# Basler Interface and Imaging Scripts

Still a work in progress, built piecewise so final version will need some refactoring for better performance and cleaner integration between modules.

## Requirements:
- pypylon
- OpenCV
- Matplotlib, NumPy

pip install opencv-python pypylon should work (tested in a python 3.11.4 virtual environment) and python 3.8 (or so?) and conda on lab computer

Should install Pylon SDK for best compatibility [Basler software](https://www.baslerweb.com/en-us/software/)

## Usage

As configured, running the gui.py script in editor (Spyder/VS Code) or from command line (in working directory with trig_seq.py, trig_wrapper.py, and vid_wrapper.py) launches tkinter window. Triggered sequence script sets up camera (set hardware_trigger = True in gui.py before running) for external triggering on Line1, with 10ms exposure time, Mono12p pixel format, and camera gain to 30.0 dB.

## Notes

Not a finished product, minimal error-handling/safeguards in place at the moment. Final version will probably be refactored to use ImageEventHandler from pypylon and rework the image display to better integrate with tkinter - but functional enough to successfully set up a Basler ace2 camera for HW triggered and performing image calculation. Images saved as ASCII files in specific format for use with analysis software in lab - files get large! (~7 MB) so use autosave with caution (or adjust saving function in trig_seq.py, using cv2.imwrite can easily save in different file formats, PNG, tiff, etc..)


### Links

- [Basler pypylon-samples repo](https://github.com/basler/pypylon-samples)
- [ace2 product page](https://docs.baslerweb.com/a2a1920-160umbas)