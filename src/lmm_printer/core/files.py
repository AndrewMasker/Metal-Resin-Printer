import json , os , tempfile
from dataclasses import fields , asdict
import subprocess
from pathlib import Path
from lmm_printer.core.types import Result , Printer_State

def return_RM_Drives():
    """Search for and return a result with drives or an error.

    Returns:
        Result: On success the value is a list of drives. On error,
            the message says what failed.
    """
    out = subprocess.check_output(["lsblk" , "-J" , "-o" , "NAME,TYPE,FSTYPE,MOUNTPOINT,PATH"] , text=True)
    tree = json.loads(out)

    drives = []

    def walk(devices):
        for d in devices:
            fstype = d.get("fstype")
            mnt = d.get("mountpoint")
            if d.get("type") in ("part" , "disk") and fstype and mnt and mnt.startswith("/media/"):
                drives.append((d["path"] , mnt))
            walk(d.get("children" , []))

    walk(tree["blockdevices"])

    if len(drives) == 0:
        drives = Result.error(message = "No removable drives found.")
    else:
        drives = Result.success(value = drives , message = "Found drives: " + ", ".join(mnt for dev , mnt in drives))
    return drives

def get_Files(drives):
    """Get all of the files in a list of drives (mount paths).

    Args:
        drives (list): A list of paths to the mount points of loaded removable drives.

    Returns:
        list: List of file paths.
    """

    files = []
    for dev , mnt in drives:
        root = Path(mnt)
        for file in root.iterdir():
            files.append(file)

    return files

def save_Dict(path , data):
    """Save a dict to a path.

    Args:
        path (Path or str): The save path.
        data (dict): The dict to be saved.
    """

    d = os.path.dirname(path)
    fd , temp = tempfile.mkstemp(dir = d)
    try:
        with os.fdopen(fd , "w") as f:
            json.dump(data , f)
        os.replace(temp , path)
    except Exception:
        os.unlink(temp)
        raise

def load_Dict(path):
    """Load a dict from a path.

    Args:
        path (Path or str): The path to load from.

    Returns:
        dict: The dict saved at path.
    """

    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        raise

def save_Printer_State(path , data):
    """Save a Printer_State object as a dict.

    Args:
        path (Path or str): The path to save to.
        data (Printer_State): The data to save.
    """

    save_Dict(path , asdict(data))

def load_Printer_State(path):
    """Load a Printer_State object from path.

    Args:
        path (Path or str): The path to load from.

    Returns:
        Printer_State: The printer state loaded from path.
    """

    if not path.exists():
        state = Printer_State()
        save_Printer_State(path , state)
        return state
    state_dict = load_Dict(path)
    known = {f.name for f in fields(Printer_State)}
    return Printer_State(**{k: v for k , v in state_dict.items() if k in known})
