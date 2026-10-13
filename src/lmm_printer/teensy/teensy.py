import threading
import queue

class Teensy:
    def __init__(self , ser):
        self.ser = ser
        self.message_queue = queue.Queue()
        self.buffer = bytearray()
        self._stop = threading.Event()

    def _reader(self):
        while not self._stop.is_set():
            data = self.ser.read(self.ser.in_waiting or 1)
            if data:
                self.buffer.extend(data)
                while b'\n' in self.buffer:
                    line , _ , self.buffer = self.buffer.partition(b'\n')
                    self.message_queue.put(line.decode('utf-8' , errors = 'replace').rstrip('\r')) 

    def get_Messages(self):
        lines = []
        while True:
            try:
                lines.append(self.message_queue.get_nowait())
            except queue.Empty:
                break
        return lines

    def clear(self):
        self.get_Messages()

    def start_Thread(self):
        if getattr(self , '_thread' , None) and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._reader , daemon = True)
        self._thread.start()

    def stop_Thread(self):
        self._stop.set()
        self._thread.join()

    def send_Command(self , command):
        command = command + "\n"
        command = command.encode()
        self.ser.write(command)

    def shutdown(self):
        self.stop_Thread()
        self.ser.close()