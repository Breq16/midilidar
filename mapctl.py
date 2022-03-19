import tkinter as tk
import mido
import atexit
import threading


class Axis:
    def __init__(self, port, root, label, color, mode="cc", channel=0, control=16):
        # MIDI port
        self.port = port

        # UI printing
        self.root = root
        self.label = label
        self.color = color

        # Modes
        self.mode = tk.StringVar(self.root, mode)

        # Note Mode
        self.channel = tk.IntVar(self.root, channel + 1)
        self.current_note = None
        self.current_bend = 0
        self.min_note = tk.IntVar(self.root, 60)
        self.max_note = tk.IntVar(self.root, 72)
        self.continuous = tk.BooleanVar(self.root, True)

        # CC Mode
        self.control = control
        self.current_value = None

        # Processing
        self.glide = tk.IntVar(self.root, False)
        self.invert = tk.BooleanVar(self.root, False)

    def handle_input(self, position=None):
        note = None
        value = None
        bend = 0

        if position is not None:
            if self.invert.get():
                position = 1 - position

            if self.mode.get() == "note":
                note = self.min_note.get() + int(
                    round(position * (self.max_note.get() - self.min_note.get()))
                )
                if self.continuous.get():
                    bend = (position * self.range) % 1
                    if bend > 0.5:
                        bend -= 1
            if self.mode.get() == "cc":
                value = int(position * 127)

        self.update(note, value, bend)

    def update(self, note, value, bend):
        if note != self.current_note:
            if self.current_note is not None:
                self.port.send(
                    mido.Message(
                        "note_off",
                        note=self.current_note,
                        channel=self.channel.get() - 1,
                    )
                )
            self.current_note = note
            if self.current_note is not None:
                self.port.send(
                    mido.Message(
                        "note_on",
                        note=self.current_note,
                        channel=self.channel.get() - 1,
                    )
                )

        if value != self.current_value:
            self.current_value = value

            if self.current_value is not None:
                self.port.send(
                    mido.Message(
                        "control_change",
                        control=self.control,
                        value=self.current_value,
                        channel=self.channel.get() - 1,
                    )
                )

        if bend != self.current_bend:
            self.current_bend = bend

            self.port.send(
                mido.Message(
                    "pitchwheel",
                    pitch=int(self.current_bend * 4096),
                    channel=self.channel.get() - 1,
                )
            )

    def __str__(self):
        if self.mode.get() == "note":
            return f"Note Ch{self.channel.get()} N{self.current_note} B{round(self.current_bend, 2)}"
        else:
            return f"CC C{self.control} V{self.current_value}"

    def get_frame(self):
        frame = tk.Frame(self.root)

        label = tk.Label(frame, text=self.label, background=self.color)
        label.grid(row=0, column=0, columnspan=2, sticky=tk.E + tk.W)

        modeFrame = tk.Frame(frame)
        tk.Label(modeFrame, text="Mode").pack(side=tk.LEFT)
        om = tk.OptionMenu(modeFrame, self.mode, "note", "cc")
        om.configure(width=5)
        om.pack(side=tk.LEFT)
        modeFrame.grid(row=1, column=0)

        channelFrame = tk.Frame(frame)
        tk.Label(channelFrame, text="Channel").pack(side=tk.LEFT)
        tk.Entry(channelFrame, textvariable=self.channel, width=2).pack(side=tk.LEFT)
        channelFrame.grid(row=1, column=1)

        tk.Label(frame, text="Note Range").grid(row=2, column=0)

        rangeFrame = tk.Frame(frame)
        tk.Entry(rangeFrame, textvariable=self.min_note, width=2).pack(side=tk.LEFT)
        tk.Label(rangeFrame, text="to").pack(side=tk.LEFT)
        tk.Entry(rangeFrame, textvariable=self.max_note, width=2).pack(side=tk.LEFT)
        rangeFrame.grid(row=2, column=1)

        tk.Checkbutton(frame, text="Bend", variable=self.continuous).grid(
            row=3, column=0
        )
        tk.Checkbutton(frame, text="Invert", variable=self.invert).grid(row=3, column=1)

        glideFrame = tk.Frame(frame)
        tk.Label(glideFrame, text="Glide").pack(side=tk.LEFT)
        tk.Entry(glideFrame, textvariable=self.glide, width=2).pack(side=tk.LEFT)
        tk.Label(glideFrame, text="ms").pack(side=tk.LEFT)
        glideFrame.grid(row=4, column=0)

        return frame


COLORS = ["#ff6666", "#00ff00", "#ffff00", "#00ffff"]


def main(queue):
    root = tk.Tk()

    port = mido.open_output("BMC LIDAR", virtual=True)
    atexit.register(port.close)

    axes = [
        Axis(
            port,
            root,
            f"Axis {i + 1}",
            COLORS[i],
            "note" if i == 0 else "cc",
            i,
            16 + i,
        )
        for i in range(4)
    ]

    for axis in axes:
        frame = axis.get_frame()
        frame.pack(side=tk.TOP, pady=(0, 10))

    def update():
        data = queue.get()

        for i, val in enumerate(data):
            axes[i].handle_input(val)

    threading.Thread(target=update).start()

    root.title("MIDI Mapping Control")
    root.mainloop()
