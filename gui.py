if __name__ == "__main__":
    pass

import tkinter as tk
import os.path as path
from tkinter import filedialog
from audio import AudioFile
from tkinter import messagebox
import matplotlib.figure as matplotfig
import matplotlib.backends.backend_tkagg as matplottk
import librosa.display as libdisplay


def invert_color(color, tk_object):
    rgb = tk_object.winfo_rgb(color) if type(color) == str else color
    rgb = (65535-rgb[0] >> 8, 65535-rgb[1] >> 8, 65535-rgb[2] >> 8)
    return "#%02x%02x%02x" % rgb


class MainWindow(tk.Tk):
    """Class representing the top-level window in the GUI mode of the application."""

    def __init__(self, application):
        tk.Tk.__init__(self)
        self.application = application
        self.menus = {}
        self.menu_bar = tk.Menu(master=self)
        self.trim_window: AudioTrimWindow = None

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open...", command=self.open_file_dialog)
        file_menu.add_command(label="Trim audio...", command=self.open_trim_window)
        self.menus["file_menu"] = file_menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About")
        self.menus["help_menu"] = help_menu
        self.menu_bar.add_cascade(label="File", menu=self.menus["file_menu"])
        self.menu_bar.add_cascade(label="Help", menu=self.menus["help_menu"])
        self.config(menu=self.menu_bar)

        self.file_info_frame = FileInformationFrame(self)
        self.file_info_frame.grid(row=0, column=0)

        self.waveform_frame = WaveformFrame(self)
        self.waveform_frame.grid(row=1, column=0)

    def open_file_dialog(self):
        self.disable_menu_bar()
        self.application.load_file(filedialog.askopenfilename(
            initialdir=path.expanduser("~"), title="Select audio file"))
        self.update_file_information()
        self.enable_menu_bar()

    def update_file_information(self):
        audio_file = self.application.loaded_audio_file
        self.file_info_frame.update_boxes(audio_file)
        self.waveform_frame.update_waveform(
            audio_file.audio_data if audio_file is not None else None,
            audio_file.sample_rate if audio_file is not None else None
        )

    def trim_audio_data(self, start_time, end_time):
        self.application.trim_audio_data(start_time, end_time)

    def disable_menu_bar(self):
        last_index = self.menu_bar.index("end")
        for entry in range(0, last_index+1):
            self.menu_bar.entryconfigure(entry, state="disabled")

    def enable_menu_bar(self):
        last_index = self.menu_bar.index("end")
        for entry in range(0, last_index + 1):
            self.menu_bar.entryconfigure(entry, state="normal")

    def open_trim_window(self):
        if self.application.loaded_audio_file is None:
            messagebox.showerror("No file loaded", "Cannot trim audio when there is not a file loaded.")
            return
        if self.trim_window is None:
            self.trim_window = AudioTrimWindow(self, self.application.loaded_audio_file)
            self.trim_window.group(self)
        else:
            self.trim_window.lift()
        self.disable_menu_bar()

    def destroy_trim_window(self):
        if self.trim_window is not None:
            self.trim_window = None
        self.update_file_information()
        self.enable_menu_bar()


class FileInformationFrame(tk.Frame):
    """Class representing the frame inside a window which displays information about the loaded audio file."""
    def __init__(self, master):
        super().__init__(master)

        self.file_label = tk.Label(self, text="Open file:")
        self.file_label.grid(row=0, column=0)
        self.file_text_box = tk.Text(self, width=50, height=1)
        self.file_text_box.grid(row=0, column=1)
        self.format_label = tk.Label(self, text="Format:")
        self.format_label.grid(row=1, column=0)
        self.format_text_box = tk.Text(self, width=50, height=1)
        self.format_text_box.grid(row=1, column=1)
        self.artist_label = tk.Label(self, text="Artist:")
        self.artist_label.grid(row=2, column=0)
        self.artist_text_box = tk.Text(self, width=50, height=1)
        self.artist_text_box.grid(row=2, column=1)
        self.title_label = tk.Label(self, text="Track title:")
        self.title_label.grid(row=3, column=0)
        self.title_text_box = tk.Text(self, width=50, height=1)
        self.title_text_box.grid(row=3, column=1)
        self.disable_boxes()

    def update_boxes(self, audio_file: AudioFile):
        self.enable_boxes()
        self.file_text_box.delete("1.0", tk.END)
        self.file_text_box.insert("1.0", audio_file.filepath if audio_file is not None else "")
        self.artist_text_box.delete("1.0", tk.END)
        self.artist_text_box.insert("1.0", audio_file.artist if audio_file is not None else "")
        self.title_text_box.delete("1.0", tk.END)
        self.title_text_box.insert("1.0", audio_file.title if audio_file is not None else "")
        self.disable_boxes()

    def enable_boxes(self):
        self.format_text_box.configure(state="normal")
        self.file_text_box.configure(state="normal")
        self.artist_text_box.configure(state="normal")
        self.title_text_box.configure(state="normal")

    def disable_boxes(self):
        self.format_text_box.configure(state="disabled")
        self.file_text_box.configure(state="disabled")
        self.artist_text_box.configure(state="disabled")
        self.title_text_box.configure(state="disabled")


class WaveformFrame(tk.Canvas):
    def __init__(self, master, use_labels=False, click_event_command=None):
        super().__init__(master)
        self.master = master
        self.figure, self.axes, self.canvas = None, None, None
        self.markers = {}

        self.initialize_canvas(use_labels)
        self.canvas.get_tk_widget().grid(row=0, column=0)
        if click_event_command is not None:
            self.canvas.mpl_connect('button_press_event', click_event_command)
        self.update_canvas()

    def initialize_canvas(self, use_labels):
        self.figure = matplotfig.Figure(figsize=(5,2), dpi=100, tight_layout=True)
        # self.figure.patch.set_facecolor(self.master["background"])
        self.figure.patch.set_facecolor("white")
        self.axes = self.figure.add_subplot(111)
        self.axes.get_yaxis().set_visible(False)
        if not use_labels:
            self.axes.get_xaxis().set_visible(False)
        else:
            # self.axes.xaxis.label.set_color(invert_color(self.master["background"], self))
            self.axes.tick_params(axis="x", colors=invert_color(self.master["background"], self))
        self.canvas = matplottk.FigureCanvasTkAgg(self.figure, self)

    def update_canvas(self):
        for marker in self.markers.values():
            self.axes.axvline(x=marker[0], color=marker[1])
        self.canvas.draw()

    def update_waveform(self, audio_data, audio_sample_rate):
        self.clear_axes()
        if audio_data is not None:
            libdisplay.waveplot(audio_data, audio_sample_rate, x_axis="time", ax=self.axes)
        self.update_canvas()

    def add_marker_definition(self, name, default_position=0.0, color="red"):
        if name not in self.markers.keys():
            self.markers[name] = (default_position, color)

    def update_marker_position(self, name, position):
        temp_marker_definition = list(self.markers[name])
        temp_marker_definition[0] = position
        self.markers[name] = tuple(temp_marker_definition)

    def clear_axes(self):
        self.axes.clear()


class AudioTrimWindow(tk.Toplevel):
    START_MARKER = False
    END_MARKER = True

    def __init__(self, master, audio_file: AudioFile):
        super().__init__(master)
        self.master = master

        self.trimmed_audio_data = audio_file.audio_data
        self.audio_sample_rate = audio_file.sample_rate

        self.marker_movement_mode = tk.BooleanVar()
        self.marker_movement_mode.set(AudioTrimWindow.START_MARKER)

        self.start_marker_button = tk.Radiobutton(self, text="Move start marker", variable=self.marker_movement_mode,
                                                  value=AudioTrimWindow.START_MARKER, indicatoron=0)
        self.end_marker_button = tk.Radiobutton(self, text="Move end marker", variable=self.marker_movement_mode,
                                                value=AudioTrimWindow.END_MARKER, indicatoron=0)
        self.start_marker_button.grid(row=0, column=0)
        self.end_marker_button.grid(row=0, column=1)

        self.waveform_frame = WaveformFrame(self, use_labels=True, click_event_command=self.move_marker)
        self.waveform_frame.grid(row=1, column=0, columnspan=2)
        self.waveform_frame.add_marker_definition("start_marker", 0.0, "red")
        self.waveform_frame.add_marker_definition("end_marker", (len(self.trimmed_audio_data) + 1.)
                                                  / audio_file.sample_rate, "blue")
        self.waveform_frame.update_waveform(self.trimmed_audio_data, audio_file.sample_rate)

        self.accept_button = tk.Button(self, text="Trim audio file", command=self.trim_audio_data)
        self.accept_button.grid(row=2, column=1)

        self.protocol("WM_DELETE_WINDOW", self.kill_trim_window)

    def move_marker(self, event):
        new_marker_position = event.xdata
        if self.marker_movement_mode.get() == AudioTrimWindow.START_MARKER:
            self.waveform_frame.update_marker_position("start_marker", new_marker_position)
        else:
            self.waveform_frame.update_marker_position("end_marker", new_marker_position)
        self.waveform_frame.update_waveform(self.trimmed_audio_data, self.audio_sample_rate)

    def trim_audio_data(self):
        start_marker_position = self.waveform_frame.markers["start_marker"][0]
        end_marker_position = self.waveform_frame.markers["end_marker"][0]

        self.master.trim_audio_data(start_marker_position, end_marker_position)
        self.kill_trim_window()

    def kill_trim_window(self):
        self.master.destroy_trim_window()
        self.destroy()