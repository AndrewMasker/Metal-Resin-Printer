import os
from contextlib import redirect_stdout , contextmanager

@contextmanager
def silence():
    with open(os.devnull , "w") as devnull:
        with redirect_stdout(devnull):
            yield