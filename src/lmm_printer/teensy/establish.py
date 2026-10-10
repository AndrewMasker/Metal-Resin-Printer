import serial
import serial.tools.list_ports
from lmm_printer.core.types import Result , State
from lmm_printer.teensy.teensy import Teensy

def find_Teensy_Port_Fallback(teensy_vid):
    for port in serial.tools.list_ports.comports():
        if port.vid == teensy_vid:
            return port.device
    for port in serial.tools.list_ports.comports():
        if port.description and "Teensy" in port.description:
            return port.device
    return None

def open_Serial(port , baudrate , timeout):
    return serial.Serial(port , baudrate = baudrate , timeout = timeout)

def is_Teensy_Listening(ser):
    ser.reset_input_buffer()
    ser.write(b"\nE hello\n")
    line = ser.readline().decode("utf-8" , errors = "ignore")
    line = ' '.join(line.split())
    return line == "hello"

def teensy_Handshake(port , baudrate , timeout):
    try:
        ser = open_Serial(port , baudrate , timeout)   
    except Exception as e:
        return Result(value = None , state = State.ERROR , message = "Can't open Teensy port. " + "Error opening the serial port: " + port + " Error was: " + str(e))

    if is_Teensy_Listening(ser):
        return Result(value = Teensy(ser) , state = State.SUCCESS , message = "Teensy connection successful.")
    else:
        ser.close()
        return Result(value = None , state = State.ERROR , message = "Teensy not listening.")

def return_Teensy_Serial(teensy_vid , baudrate , timeout , enable_fallback):
    port = "/dev/serial0"
    handshake_result = teensy_Handshake(port , baudrate , timeout)
    if not enable_fallback or handshake_result.state == State.SUCCESS:
        return handshake_result
    else:
        port = find_Teensy_Port_Fallback(teensy_vid)
        if port is None:
            return Result(value = None , state = State.ERROR , message = "No Teensy port found on fallback." + " Error causing fallback was: " + handshake_result.message)
        fallback_handshake_result = teensy_Handshake(port , baudrate , timeout)
        fallback_handshake_result.message = "On fallback: " + fallback_handshake_result.message + " Error causing fallback was: " + handshake_result.message
        return fallback_handshake_result





