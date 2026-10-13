import evdev
from evdev import ecodes

class Encoder_Input:
    def __init__(self):
        self.devices = []
        for path in evdev.list_devices():
            dev = evdev.InputDevice(path)
            caps = dev.capabilities()
            if ecodes.EV_REL in caps or ecodes.KEY_ENTER in caps.get(ecodes.EV_KEY , []):
                dev.grab()
                self.devices.append(dev)
            else:
                dev.close()

    def read(self):
        """Reads the inputs.

        Returns:
            int: Number of detents the encoder has turned.
            bool: Whether the button has been pressed.
        """

        turns , pressed = 0 , False
        for dev in self.devices:
            try:
                for e in dev.read():
                    if e.type == ecodes.EV_REL and e.code == ecodes.REL_X:
                        turns += e.value
                    elif e.type == ecodes.EV_KEY and e.code == ecodes.KEY_ENTER and e.value == 1:
                        pressed = True
            except BlockingIOError:
                pass
        return turns , pressed

    def close(self):
        for dev in self.devices:
            dev.ungrab()
            dev.close()