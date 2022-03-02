import mido


class Axis:
    def __init__(self, port, channel, control, mode):
        # MIDI port
        self.port = port

        # Modes
        self.mode = mode

        # Note Mode
        self.channel = channel
        self.current_note = None
        self.current_bend = 0
        self.min_note = 60
        self.range = 12
        self.continuous = True

        # CC Mode
        self.control = control
        self.current_value = None

    def handle_input(self, position=None):
        note = None
        value = None
        bend = 0

        if position:
            if self.mode == "note":
                note = self.min_note + int(round(position * self.range))
                if self.continuous:
                    bend = (position * self.range) % 1
                    if bend > 0.5:
                        bend -= 1
            if self.mode == "cc":
                value = int(position * 127)

        self.update(note, value, bend)

    def update(self, note, value, bend):
        if note != self.current_note:
            print(f"{self} -> {note}")

            if self.current_note:
                self.port.send(
                    mido.Message(
                        "note_off", note=self.current_note, channel=self.channel
                    )
                )
            self.current_note = note
            if self.current_note:
                self.port.send(
                    mido.Message(
                        "note_on", note=self.current_note, channel=self.channel
                    )
                )

        if value != self.current_value:
            self.current_value = value

            if self.current_value:
                self.port.send(
                    mido.Message(
                        "control_change",
                        control=self.control,
                        value=self.current_value,
                        channel=self.channel,
                    )
                )

        if bend != self.current_bend:
            self.current_bend = bend

            self.port.send(
                mido.Message(
                    "pitchwheel",
                    pitch=int(self.current_bend * 4096),
                    channel=self.channel,
                )
            )

    def toggle_mode(self):
        self.mode = "cc" if self.mode == "note" else "note"

    def __str__(self):
        if self.mode == "note":
            return f"Note Ch{self.channel} N{self.current_note} B{round(self.current_bend, 2)}"
        else:
            return f"CC C{self.control} V{self.current_value}"
