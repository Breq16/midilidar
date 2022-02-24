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
        self.min_note = 60
        self.range = 24

        # CC Mode
        self.control = control
        self.current_value = None

    def handle_input(self, position=None):
        note = None
        value = None

        if position:
            if self.mode == "note":
                note = self.min_note + int(position * self.range)
            if self.mode == "cc":
                value = int(position * 127)

        self.update(note, value)

    def update(self, note, value):
        if note != self.current_note:
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

    def toggle_mode(self):
        self.mode = "cc" if self.mode == "note" else "note"

    def __str__(self):
        if self.mode == "note":
            return f"Note Ch{self.channel} N{self.current_note}"
        else:
            return f"CC C{self.control} V{self.current_value}"
