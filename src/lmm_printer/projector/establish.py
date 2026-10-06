import RPi.GPIO as GPIO
import smbus  # I2C
import spidev  # SPI
from lmm_printer.vendored.UV_projector.controller import DLPC1438 , Mode
from lmm_printer.core.types import Result , State
from lmm_printer.utils.vendored_handling import silence


GPIO.setmode(GPIO.BCM)

def return_Projector(spi_max_speed):
    try:
        # Initialize I2C (SMBus) on channel 1
        i2c = smbus.SMBus(1)

        # Initialise SPI (bus 0, with CE0 as chip select pin)
        spi = spidev.SpiDev()
        spi.open(0, 0)
        spi.max_speed_hz = spi_max_speed  # FPGA/DCLP1438 limit: 50 MB/s; 125MHz seems limit for Pi zero 1W
        spi.mode = 3 

        # Initialise the DLPC1438
        with silence():
            projector = DLPC1438(i2c, spi)

        # let's try external print mode now
        with silence():
            projector.configure_external_print(LED_PWM = 1000)
            projector.switch_mode(Mode.EXTERNALPRINT)

            # intialise FPGA buffers to zero
            projector.set_background(intensity = 0, both_buffers = True)

        return Result(value = projector , state = State.SUCCESS , message = "Projector connection successful.")

    except Exception as e:
        GPIO.cleanup()
        return Result(value = None , state = State.ERROR , message = "Can't open projector. " + "Error was: " + str(e))
