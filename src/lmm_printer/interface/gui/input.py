import evdev
from evdev import encodes

class Encoder_Input:
    def __init__(self):
        self.devices = []
        for path in evdev.list_devices():
            dev = evdev.InputDevice(path)
            caps = dev.capabilities()
            if encodes.EV_REL in caps or encodes.KEY_ENTER in caps.get(encodes.EV_KEY , []):
                dev.grab()
                self.devices.append(dev)

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
                    if e.type == encodes.EV_REL:
                        turns = e.value
                    elif e.type == encodes.EV_KEY and e.code == encodes.KEY_ENTER and e.value == 1:
                        pressed = True
            except BlockingIOError:
                pass
        return turns , pressed