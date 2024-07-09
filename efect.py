import tkinter as tk
from tkinter import ttk
from pedalboard import Pedalboard, Chorus, Compressor, Delay, Gain, Reverb, Phaser, Convolution
from pedalboard.io import AudioStream
import sounddevice as sd

def get_audio_devices():
    devices = sd.query_devices()
    input_devices = [device['name'] for device in devices if device['max_input_channels'] > 0]
    output_devices = [device['name'] for device in devices if device['max_output_channels'] > 0]
    return input_devices, output_devices

class AudioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bravelab: Spotify Pedalboard Sandbox")
        self.root.configure(bg='black', padx=100, pady=100)
        
        # Variables to hold effect parameters
        self.gain_db = tk.DoubleVar(value=0.0)
        self.delay_seconds = tk.DoubleVar(value=0.3)
        self.feedback = tk.DoubleVar(value=0.2)
        self.delay_mix = tk.DoubleVar(value=0.5)
        self.room_size = tk.DoubleVar(value=0.5)
        self.input_device = tk.StringVar()
        self.output_device = tk.StringVar()
        
        # Variables to hold effect switches
        self.gain_enabled = tk.BooleanVar(value=True)
        self.delay_enabled = tk.BooleanVar(value=True)
        self.reverb_enabled = tk.BooleanVar(value=True)
        self.streaming_enabled = tk.BooleanVar(value=False)

        self.create_widgets()
        self.stream = None

        # Add trace to variables
        self.gain_db.trace_add("write", self.update_stream)
        self.delay_seconds.trace_add("write", self.update_stream)
        self.feedback.trace_add("write", self.update_stream)
        self.delay_mix.trace_add("write", self.update_stream)
        self.room_size.trace_add("write", self.update_stream)
        self.gain_enabled.trace_add("write", self.update_stream)
        self.delay_enabled.trace_add("write", self.update_stream)
        self.reverb_enabled.trace_add("write", self.update_stream)
        self.input_device.trace_add("write", self.update_stream)
        self.output_device.trace_add("write", self.update_stream)
        self.streaming_enabled.trace_add("write", self.toggle_streaming)

    def create_widgets(self):
        # Gain control
        ttk.Label(self.root, text="Gain (dB)").grid(column=0, row=0, padx=5, pady=5)
        gain_scale = ttk.Scale(self.root, from_=-60, to=20, variable=self.gain_db, orient="horizontal")
        gain_scale.grid(column=1, row=0, padx=5, pady=5)
        ttk.Label(self.root, textvariable=self.gain_db).grid(column=2, row=0, padx=5, pady=5)
        ttk.Checkbutton(self.root, text="Enable Gain", variable=self.gain_enabled).grid(column=3, row=0, padx=5, pady=5)
        self.gain_led = tk.Canvas(self.root, width=20, height=20, highlightthickness=0)
        self.gain_led.grid(column=4, row=0, padx=5, pady=5)
        self.update_led(self.gain_led, self.gain_enabled.get())

        # Delay control
        ttk.Label(self.root, text="Delay (seconds)").grid(column=0, row=1, padx=5, pady=5)
        delay_scale = ttk.Scale(self.root, from_=0, to=2, variable=self.delay_seconds, orient="horizontal")
        delay_scale.grid(column=1, row=1, padx=5, pady=5)
        ttk.Label(self.root, textvariable=self.delay_seconds).grid(column=2, row=1, padx=5, pady=5)
        ttk.Checkbutton(self.root, text="Enable Delay", variable=self.delay_enabled).grid(column=3, row=1, padx=5, pady=5)
        self.delay_led = tk.Canvas(self.root, width=20, height=20, highlightthickness=0)
        self.delay_led.grid(column=4, row=1, padx=5, pady=5)
        self.update_led(self.delay_led, self.delay_enabled.get())

        # Feedback control
        ttk.Label(self.root, text="Feedback").grid(column=0, row=2, padx=5, pady=5)
        feedback_scale = ttk.Scale(self.root, from_=0, to=1, variable=self.feedback, orient="horizontal")
        feedback_scale.grid(column=1, row=2, padx=5, pady=5)
        ttk.Label(self.root, textvariable=self.feedback).grid(column=2, row=2, padx=5, pady=5)

        # Delay mix control
        ttk.Label(self.root, text="Delay Mix").grid(column=0, row=3, padx=5, pady=5)
        delay_mix_scale = ttk.Scale(self.root, from_=0, to=1, variable=self.delay_mix, orient="horizontal")
        delay_mix_scale.grid(column=1, row=3, padx=5, pady=5)
        ttk.Label(self.root, textvariable=self.delay_mix).grid(column=2, row=3, padx=5, pady=5)

        # Reverb control
        ttk.Label(self.root, text="Reverb Room Size").grid(column=0, row=4, padx=5, pady=5)
        reverb_scale = ttk.Scale(self.root, from_=0, to=1, variable=self.room_size, orient="horizontal")
        reverb_scale.grid(column=1, row=4, padx=5, pady=5)
        ttk.Label(self.root, textvariable=self.room_size).grid(column=2, row=4, padx=5, pady=5)
        ttk.Checkbutton(self.root, text="Enable Reverb", variable=self.reverb_enabled).grid(column=3, row=4, padx=5, pady=5)
        self.reverb_led = tk.Canvas(self.root, width=20, height=20, highlightthickness=0)
        self.reverb_led.grid(column=4, row=4, padx=5, pady=5)
        self.update_led(self.reverb_led, self.reverb_enabled.get())

        # Device selection
        input_devices, output_devices = get_audio_devices()

        ttk.Label(self.root, text="Input Device").grid(column=0, row=5, padx=5, pady=5)
        input_combobox = ttk.Combobox(self.root, textvariable=self.input_device, values=input_devices)
        input_combobox.grid(column=1, row=5, padx=5, pady=5)
        input_combobox.current(0)

        ttk.Label(self.root, text="Output Device").grid(column=0, row=6, padx=5, pady=5)
        output_combobox = ttk.Combobox(self.root, textvariable=self.output_device, values=output_devices)
        output_combobox.grid(column=1, row=6, padx=5, pady=5)
        output_combobox.current(0)

        # Streaming on/off switch
        ttk.Checkbutton(self.root, text="Streaming On/Off", variable=self.streaming_enabled).grid(column=0, row=7, padx=5, pady=5)

    def update_led(self, led, state):
        led_color = 'green' if state else 'red'
        led.create_oval(5, 5, 15, 15, fill=led_color)

    def update_stream(self, *args):
        self.update_led(self.gain_led, self.gain_enabled.get())
        self.update_led(self.delay_led, self.delay_enabled.get())
        self.update_led(self.reverb_led, self.reverb_enabled.get())
        if self.stream:
            self.start_streaming()

    def toggle_streaming(self, *args):
        if self.streaming_enabled.get():
            self.start_streaming()
        else:
            self.stop_streaming()

    def start_streaming(self):
        if self.stream:
            self.stop_streaming()
        
        plugins = []
        if self.gain_enabled.get():
            plugins.append(Gain(gain_db=self.gain_db.get()))
        if self.delay_enabled.get():
            plugins.append(Delay(delay_seconds=self.delay_seconds.get(), feedback=self.feedback.get(), mix=self.delay_mix.get()))
        if self.reverb_enabled.get():
            plugins.append(Reverb(room_size=self.room_size.get()))
        
        self.stream = AudioStream(
            input_device_name=self.input_device.get(),
            output_device_name=self.output_device.get()
        )
        self.stream.plugins = Pedalboard(plugins)
        self.stream.__enter__()
        print("Streaming started")

    def stop_streaming(self):
        if self.stream:
            self.stream.__exit__(None, None, None)
            self.stream = None
            print("Streaming stopped")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioApp(root)
    root.mainloop()