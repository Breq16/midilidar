import multiprocessing

import mapctl
import sensorctl

if __name__ == "__main__":
    queue = multiprocessing.Queue()

    sensorproc = multiprocessing.Process(
        target=sensorctl.main, args=(queue,), name="Sensor Control"
    )
    mapproc = multiprocessing.Process(
        target=mapctl.main, args=(queue,), name="MIDI Mapping Control"
    )

    sensorproc.start()
    mapproc.start()

    sensorproc.join()
    mapproc.join()
