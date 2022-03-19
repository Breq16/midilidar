import threading
import rplidar


class Lidar:
    def __init__(self):
        self.dev = rplidar.RPLidar("/dev/tty.usbserial-0001")
        self.measurements = []
        self.measure_thread = None
        self._stop = False

    def start(self):
        self.dev.start_motor()

    def stop(self):
        if self.measure_thread:
            self._stop = True
            self.measure_thread.join()

        self.dev.stop()
        self.dev.stop_motor()
        self.dev.disconnect()

    def start_measuring(self):
        def measure():
            for scan in self.dev.iter_scans(min_len=50):
                if self._stop:
                    return

                self.measurements = [
                    (angle, distance) for quality, angle, distance in scan
                ]

        self.measure_thread = threading.Thread(
            target=measure, daemon=True, name="LIDAR Measurements"
        )

        self.measure_thread.start()
