import os
import logging
import subprocess
import re
import numpy as np

from random import shuffle

logger = logging.getLogger("timeflux")

DEFAULT_CODE_FILE = "codes/example5.npy"

try:
    version = subprocess.check_output(["git", "describe", "--tags"]).strip().decode()
    logger.info(f"Application version: {version}")
except:
    pass

crash_bad_param = bool(os.getenv("EXIT_ON_BAD_PARAMETER", "true"))


def cued_task_sequence(n_classes, repetitions):
    """
    Create a pseudorandom sequence for the cued
    task. Ensures same number of trials for each
    class
    """
    sequence = []
    bag = [i for i in range(n_classes)]

    for _ in range(repetitions):
        shuffle(bag)
        sequence.extend(bag)

    return sequence


# Defining an easy to use function for error handling
def error_handling(key, msg, default, force_fail=False) -> None:
    if crash_bad_param or force_fail:
        raise ValueError(msg)
    else:
        logger.warning(f"{msg}, defaulting to {default}")
        os.environ[key] = default


# generic method to check the type of an environment variable
def check_type(key, t: type):
    if os.environ[key] is None:
        return False
    try:
        t(os.environ[key])
    except:
        return False
    return True


# Specific for int type checking
def check_int(key) -> bool:
    return check_type(key, int)


# Specific for float type checking
def check_float(key) -> bool:
    return check_type(key, float)


# Specific for bool type checking
def check_boolean(key) -> bool:
    return check_type(key, bool)


# Check that the device graph exists
os.environ["DEVICE"] = os.getenv("DEVICE")
if not os.path.exists(os.path.join("graphs", os.environ["DEVICE"] + ".yaml")):
    error_handling(
        "DEVICE",
        f"Could not find graph file {os.environ['DEVICE']}.yaml in the graph folder",
        "graphs/dummy",
    )

# Check positive non zero
os.environ["EPOCH"] = os.getenv("EPOCH")
if not check_float("EPOCH") or float(os.environ["EPOCH"]) <= 0:
    error_handling("EPOCH", f"EPOCH must be a stricty positive float", 0.20)

# Check that it is in single/simple/grid/keyboard
os.environ["CALIBRATION_LAYOUT"] = os.getenv("CALIBRATION_LAYOUT")
if os.environ["CALIBRATION_LAYOUT"] not in ["single", "simple", "grid", "keyboard"]:
    error_handling(
        "CALIBRATION_LAYOUT",
        f"CALIBRATION_LAYOUT must be one of 'single', 'simple', 'grid' or 'keyboard'",
        "simple",
    )

# simple/grid/keyboard
os.environ["TASK_LAYOUT"] = os.getenv("TASK_LAYOUT")
if os.environ["TASK_LAYOUT"] not in ["simple", "grid", "keyboard"]:
    error_handling(
        "TASK_LAYOUT",
        f"TASK_LAYOUT must be one of 'simple', 'grid' or 'keyboard'",
        "simple",
    )

# Check that the file exists
logger.debug(os.getcwd())
os.environ["CODE_FILE"] = os.getenv("CODE_FILE")
if not os.path.exists(os.environ["CODE_FILE"]):
    error_handling(
        "CODE_FILE",
        f"The code file path {os.environ['CODE_FILE']} does not exist",
        DEFAULT_CODE_FILE,
    )
# Supplied code file path not found, defaulted to DEFAULT_CODE_FILE. Checking that it still exists
if not os.path.exists(DEFAULT_CODE_FILE):
    error_handling(
        "CODE_FILE",
        f"The example file for code {os.environ['CODE_FILE']} does not exist",
        None,
        True,
    )

# # derniers codes de fred
codes = np.load(os.environ["CODE_FILE"])
logger.debug("Codes loaded from file: " + str(os.environ["CODE_FILE"]))
logger.debug("Codes used: " + str(codes))

# Check that the codes all consists of 0 and 1
bad_codes = []
for i, c in enumerate(codes):
    val, counts = np.unique(list(c), return_counts=True)
    if len(val) != 2 or ("0" not in val) or ("1" not in val):
        bad_codes.append(i)

if len(bad_codes) > 0:
    error_handling(
        "CALIBRATION_CODES",
        f"The codes {bad_codes} are not composed soloely of 0s and 1s",
        None,
        True,
    )


if os.environ["TASK_LAYOUT"] == "simple":
    os.environ["TASK_NUMBER_OF_CLASSES"] = "3"
elif os.environ["TASK_LAYOUT"] == "keyboard":
    os.environ["TASK_NUMBER_OF_CLASSES"] = "11"
elif os.environ["TASK_LAYOUT"] == "grid":
    os.environ["TASK_NUMBER_OF_CLASSES"] = "9"

if int(os.environ["TASK_NUMBER_OF_CLASSES"]) > len(codes):
    error_handling(
        "TASK_NUMBER_OF_CLASSES",
        f"Not enough codes {len(codes)} for the specified number of classes",
        len(codes),
    )
os.environ["TASK_CODES"] = " ".join(
    ["".join(list(map(str, c))) for c in codes[: int(os.environ["TASK_NUMBER_OF_CLASSES"])]]
)

if os.environ["CALIBRATION_LAYOUT"] == "simple":
    os.environ["CALIBRATION_NUMBER_OF_CLASSES"] = "5"
elif os.environ["CALIBRATION_LAYOUT"] == "keyboard":
    os.environ["CALIBRATION_NUMBER_OF_CLASSES"] = "11"
elif os.environ["CALIBRATION_LAYOUT"] == "grid":
    os.environ["CALIBRATION_NUMBER_OF_CLASSES"] = "9"
elif  os.environ["CALIBRATION_LAYOUT"] == "single":
    os.environ["CALIBRATION_NUMBER_OF_CLASSES"] = "1"

if int(os.environ["CALIBRATION_NUMBER_OF_CLASSES"]) > len(codes):
        error_handling(
            "CALIBRATION_NUMBER_OF_CLASSES",
            f"Not enough codes {len(codes)} for the specified number of classes",
            len(codes),
        )

os.environ["CALIBRATION_CODES"] = " ".join(
    ["".join(list(map(str, c))) for c in codes[: int(os.environ["CALIBRATION_NUMBER_OF_CLASSES"])]]
)

# Check integer
os.environ["SEED"] = os.getenv("SEED")
if not check_int("SEED"):
    error_handling("SEED", "SEED must a be an integer", 6874352413)

# Check that it is a coma separated list of electrode names, trim spaces
os.environ["CHANNELS"] = os.getenv("CHANNELS")
if not os.environ["CHANNELS"]:
    error_handling(
        "CHANNELS",
        "CHANNELS must a list of coma separated  name of electrodes (spaces are trimmed)",
        None,
        True,
    )
chans = os.environ["CHANNELS"].replace(" ", "").split(",")
# Check taht reref is in CHANNELS
os.environ["REREF_CHANNEL"] = os.getenv("REREF_CHANNEL")
if os.environ["REREF_CHANNEL"] is None:
    error_handling(
        "REREF_CHANNEL",
        "REREF_CHANNEL not set meaning an average rereferencing will be used",
        "",
    )
elif not os.environ["REREF_CHANNEL"] in chans:
    error_handling(
        "REREF_CHANNEL",
        "REREF_CHANNEL is set but the electrode was not found in the list of electrodes",
        None,
        True,
    )

# Check tha tit is in gabor/ricker
os.environ["STIM_TYPE"] = os.getenv("STIM_TYPE")
if os.environ["STIM_TYPE"] not in ["ricker", "gabor"]:
    error_handling(
        "STIM_TYPE", f"STIM_TYPE must be one of 'ricker' or 'gabor'", "ricker"
    )

# Check float in range [0..1]
os.environ["STIM_DEPTH"] = os.getenv("STIM_DEPTH")
if (
    not check_float("STIM_DEPTH")
    or float(os.environ["STIM_DEPTH"]) <= 0
    or float(os.environ["STIM_DEPTH"]) > 1
):
    error_handling("STIM_DEPTH", "STIM_DEPTH must be a float in the ]0..1] range", 0.7)

# Check HTML colors
color_regex = "^[0-9A-Fa-f]{6}$"
os.environ["UI_BACKGROUND"] = os.getenv("UI_BACKGROUND")
if not re.search(color_regex, os.environ["UI_BACKGROUND"]):
    error_handling(
        "UI_BACKGROUND",
        "UI_BACKGROUND must be an HTML color (without the #) of the form [0-9A-Za-z]\{6\}",
        "202020",
    )
os.environ["UI_TEXT_COLOR"] = os.getenv("UI_TEXT_COLOR")
if not re.search(color_regex, os.environ["UI_TEXT_COLOR"]):
    error_handling(
        "UI_TEXT_COLOR",
        "UI_TEXT_COLOR must be an HTML color (without the #) of the form [0-9A-Za-z]\{6\}",
        "FFFFFF",
    )
os.environ["UI_CROSS_COLOR"] = os.getenv("UI_CROSS_COLOR")
if not re.search(color_regex, os.environ["UI_CROSS_COLOR"]):
    error_handling(
        "UI_CROSS_COLOR",
        "UI_CROSS_COLOR must be an HTML color (without the #) of the form [0-9A-Za-z]\{6\}",
        "FFFFFF",
    )
os.environ["UI_TARGET_OFF_COLOR"] = os.getenv("UI_TARGET_OFF_COLOR")
if not re.search(color_regex, os.environ["UI_TARGET_OFF_COLOR"]):
    error_handling(
        "UI_TARGET_OFF_COLOR",
        "UI_TARGET_OFF_COLOR must be an HTML color (without the #) of the form [0-9A-Za-z]\{6\}",
        "797979",
    )
os.environ["UI_TARGET_ON_COLOR"] = os.getenv("UI_TARGET_ON_COLOR")
if not re.search(color_regex, os.environ["UI_TARGET_ON_COLOR"]):
    error_handling(
        "UI_TARGET_ON_COLOR",
        "UI_TARGET_ON_COLOR must be an HTML color (without the #) of the form [0-9A-Za-z]\{6\}",
        "FFFFFF",
    )
os.environ["UI_TARGET_BORDER_COLOR"] = os.getenv("UI_TARGET_BORDER_COLOR")
if not re.search(color_regex, os.environ["UI_TARGET_BORDER_COLOR"]):
    error_handling(
        "UI_TARGET_BORDER_COLOR",
        "UI_TARGET_BORDER_COLOR must be an HTML color (without the #) of the form [0-9A-Za-z]\{6\}",
        "000000",
    )
os.environ["UI_TARGET_CUE_COLOR"] = os.getenv("UI_TARGET_CUE_COLOR")
if not re.search(color_regex, os.environ["UI_TARGET_CUE_COLOR"]):
    error_handling(
        "UI_TARGET_CUE_COLOR",
        "UI_TARGET_CUE_COLOR must be an HTML color (without the #) of the form [0-9A-Za-z]\{6\}",
        "0000FF",
    )
os.environ["UI_TARGET_SUCCESS_COLOR"] = os.getenv("UI_TARGET_SUCCESS_COLOR")
if not re.search(color_regex, os.environ["UI_TARGET_SUCCESS_COLOR"]):
    error_handling(
        "UI_TARGET_SUCCESS_COLOR",
        "UI_TARGET_SUCCESS_COLOR must be an HTML color (without the #) of the form [0-9A-Za-z]\{6\}",
        "00FF00",
    )
os.environ["UI_TARGET_FAILURE_COLOR"] = os.getenv("UI_TARGET_FAILURE_COLOR")
if not re.search(color_regex, os.environ["UI_TARGET_FAILURE_COLOR"]):
    error_handling(
        "UI_TARGET_FAILURE_COLOR",
        "UI_TARGET_FAILURE_COLOR must be an HTML color (without the #) of the form [0-9A-Za-z]\{6\}",
        "FF0000",
    )
os.environ["UI_TARGET_LOCK_COLOR"] = os.getenv("UI_TARGET_LOCK_COLOR")
if not re.search(color_regex, os.environ["UI_TARGET_LOCK_COLOR"]):
    error_handling(
        "UI_TARGET_LOCK_COLOR",
        "UI_TARGET_LOCK_COLOR must be an HTML color (without the #) of the form [0-9A-Za-z]\{6\}",
        "0000FF",
    )

# Check integer positive non zero
os.environ["CALIBRATION_BLOCKS"] = os.getenv("CALIBRATION_BLOCKS")
if not check_int("CALIBRATION_BLOCKS") or int(os.environ["CALIBRATION_BLOCKS"]) < 0:
    error_handling(
        "CALIBRATION_BLOCKS",
        "CALIBRATION_BLOCKS must be a positive integer (can be 0 to skip calibration)",
        5,
    )
os.environ["CALIBRATION_STIM_REP"] = os.getenv("CALIBRATION_STIM_REP")
if (
    not check_int("CALIBRATION_STIM_REP")
    or int(os.environ["CALIBRATION_STIM_REP"]) <= 0
):
    error_handling(
        "CALIBRATION_STIM_REP",
        "CALIBRATION_STIM_REP must be a strictly positive integer, in ms",
        1,
    )
os.environ["CALIBRATION_DURATION_REST"] = os.getenv("CALIBRATION_DURATION_REST")
if (
    not check_int("CALIBRATION_DURATION_REST")
    or int(os.environ["CALIBRATION_DURATION_REST"]) <= 0
):
    error_handling(
        "CALIBRATION_DURATION_REST",
        "CALIBRATION_DURATION_REST must be a strictly positive integer, in ms",
        2000,
    )
os.environ["CALIBRATION_DURATION_CUE_ON"] = os.getenv("CALIBRATION_DURATION_CUE_ON")
if (
    not check_int("CALIBRATION_DURATION_CUE_ON")
    or int(os.environ["CALIBRATION_DURATION_CUE_ON"]) <= 0
):
    error_handling(
        "CALIBRATION_DURATION_CUE_ON",
        "CALIBRATION_DURATION_CUE_ON must be a strictly positive integer, in ms",
        1500,
    )
os.environ["CALIBRATION_DURATION_CUE_OFF"] = os.getenv("CALIBRATION_DURATION_CUE_OFF")
if (
    not check_int("CALIBRATION_DURATION_CUE_OFF")
    or int(os.environ["CALIBRATION_DURATION_CUE_OFF"]) <= 0
):
    error_handling(
        "CALIBRATION_DURATION_CUE_OFF",
        "CALIBRATION_DURATION_CUE_OFF must be a strictly positive integer, in ms",
        500,
    )

# Check integer positive non zero
os.environ["TASK_DURATION_REST"] = os.getenv("TASK_DURATION_REST")
if not check_int("TASK_DURATION_REST") or int(os.environ["TASK_DURATION_REST"]) <= 0:
    error_handling(
        "TASK_DURATION_REST",
        "TASK_DURATION_REST must be a strictly positive integer, in ms",
        2000,
    )
os.environ["TASK_DURATION_LOCK_ON"] = os.getenv("TASK_DURATION_LOCK_ON")
if (
    not check_int("TASK_DURATION_LOCK_ON")
    or int(os.environ["TASK_DURATION_LOCK_ON"]) <= 0
):
    error_handling(
        "TASK_DURATION_LOCK_ON",
        "TASK_DURATION_LOCK_ON must be a strictly positive integer, in ms",
        1500,
    )
os.environ["TASK_DURATION_LOCK_OFF"] = os.getenv("TASK_DURATION_LOCK_OFF")
if (
    not check_int("TASK_DURATION_LOCK_OFF")
    or int(os.environ["TASK_DURATION_LOCK_OFF"]) <= 0
):
    error_handling(
        "TASK_DURATION_LOCK_OFF",
        "TASK_DURATION_LOCK_OFF must be a strictly positive integer, in ms",
        500,
    )

#  Check boolean
os.environ["CUED_TASK_ENABLE"] = os.getenv("CUED_TASK_ENABLE")
if not check_boolean("CUED_TASK_ENABLE"):
    error_handling(
        "CUED_TASK_ENABLE", "CUED_TASK_ENABLE must be a boolean (true/false)", True
    )
os.environ["PINPAD_ENABLE_TASK"] = os.getenv("PINPAD_ENABLE_TASK")
if not check_boolean("PINPAD_ENABLE_TASK"):
    error_handling(
        "PINPAD_ENABLE_TASK", "PINPAD_ENABLE_TASK must be a boolean (true/false)", True
    )
os.environ["PINPAD_CUE_TARGET"] = os.getenv("PINPAD_CUE_TARGET")
if not check_boolean("PINPAD_CUE_TARGET"):
    error_handling(
        "PINPAD_CUE_TARGET", "PINPAD_CUE_TARGET must be a boolean (true/false)", False
    )
os.environ["PINPAD_CUE_FEEDBACK"] = os.getenv("PINPAD_CUE_FEEDBACK")
if not check_boolean("PINPAD_CUE_FEEDBACK"):
    error_handling(
        "PINPAD_CUE_FEEDBACK",
        "PINPAD_CUE_FEEDBACK must be a boolean (true/false)",
        True,
    )
os.environ["CUED_TASK_SEQUENCE_ENABLE"] = os.getenv("CUED_TASK_SEQUENCE_ENABLE")
if not check_boolean("CUED_TASK_SEQUENCE_ENABLE"):
    error_handling(
        "CUED_TASK_SEQUENCE_ENABLE",
        "CUED_TASK_SEQUENCE_ENABLE must be a boolean (true/false)",
        False,
    )

# Check integer positive non zero
os.environ["CUED_TASK_TARGET_REP"] = os.getenv("CUED_TASK_TARGET_REP")
if (
    not check_int("CUED_TASK_TARGET_REP")
    or int(os.environ["CUED_TASK_TARGET_REP"]) <= 0
):
    error_handling(
        "CUED_TASK_TARGET_REP",
        "CUED_TASK_TARGET_REP must be a strictly positive integer",
        20,
    )
os.environ["PINPAD_SEQUENCES"] = os.getenv("PINPAD_SEQUENCES")
if not check_int("PINPAD_SEQUENCES") or int(os.environ["PINPAD_SEQUENCES"]) <= 0:
    error_handling(
        "PINPAD_SEQUENCES", "PINPAD_SEQUENCES must be a strictly positive integer", 5
    )
os.environ["CUED_TASK_SEQUENCE_REP"] = os.getenv("CUED_TASK_SEQUENCE_REP")
if (
    not check_int("CUED_TASK_SEQUENCE_REP")
    or int(os.environ["CUED_TASK_SEQUENCE_REP"]) <= 0
):
    error_handling(
        "CUED_TASK_SEQUENCE_REP",
        "CUED_TASK_SEQUENCE_REP muse be a strictly positive integer",
        4,
    )


# Check integer positive non zero
# Check MIN_BUFFER <= MAX_BUFFER
os.environ["MIN_BUFFER_LENGTH"] = os.getenv("MIN_BUFFER_LENGTH")
if not check_int("MIN_BUFFER_LENGTH") or int(os.environ["MIN_BUFFER_LENGTH"]) <= 0:
    error_handling(
        "MIN_BUFFER_LENGTH",
        f"MIN_BUFFER_LENGTH must be a strictly positive integer",
        60,
    )
if not check_int("MAX_BUFFER_LENGTH") or int(os.environ["MAX_BUFFER_LENGTH"]) <= 0:
    error_handling(
        "MAX_BUFFER_LENGTH",
        f"MAX_BUFFER_LENGTH must be a strictly positive integer",
        80,
    )
if int(os.environ["MAX_BUFFER_LENGTH"]) < int(os.environ["MIN_BUFFER_LENGTH"]):
    error_handling(
        "MAX_BUFFER_LENGTH",
        f"MAX_BUFFER_LENGTH can not be less than MIN_BUFFER_LENGTH",
        int(os.environ["MIN_BUFFER_LENGTH"]),
    )

# Check integer positive non zero
# Check MIN_PRED <= MAX_PRED
os.environ["MIN_PRED_LENGTH"] = os.getenv("MIN_PRED_LENGTH")
if not check_int("MIN_PRED_LENGTH") or int(os.environ["MIN_PRED_LENGTH"]) <= 0:
    error_handling(
        "MIN_PRED_LENGTH", f"MIN_PRED_LENGTH must be a strictly positive integer", 50
    )
if not check_int("MAX_PRED_LENGTH") or int(os.environ["MAX_PRED_LENGTH"]) <= 0:
    error_handling(
        "MAX_PRED_LENGTH", f"MAX_PRED_LENGTH must be a strictly positive integer", 200
    )
if int(os.environ["MAX_PRED_LENGTH"]) < int(os.environ["MIN_BUFFER_LENGTH"]):
    error_handling(
        "MAX_PRED_LENGTH",
        f"MAX_PRED_LENGTH can not be less than MIN_PRED_LENGTH",
        int(os.environ["MIN_PRED_LENGTH"]),
    )

# Cued task sequence
if os.environ["CUED_TASK_SEQUENCE_ENABLE"]:
    stim_sequence = cued_task_sequence(
        int(os.environ["TASK_NUMBER_OF_CLASSES"]), int(os.environ["CUED_TASK_SEQUENCE_REP"])
    )
    logger.debug(f"Using sequence {stim_sequence} for the cued task")
    os.environ["CUED_TASK_TARGET_REP"] = str(stim_sequence)

# Timeflux
os.environ["RECORD_DATA"] = os.getenv("RECORD_DATA")
if not check_boolean("RECORD_DATA"):
    error_handling("RECORD_DATA", f"RECORD_DATA must be a boolean", "true")

# Threshold and momentum floor printing
md_floor = os.environ["MOMENTUM_FLOOR"]
logger.debug("Momentum Floor : "+ md_floor)

correlation_thresold = os.environ["CORRELATION_THRESHOLD"]
logger.debug("Correlation Threshold : "+ correlation_thresold)

logger.debug("Configuration file loaded successfully")

