import sqlite3
import os
import hashlib
import shutil
import tempfile
import time
from datetime import datetime, timedelta


class HistoryDaemon:
    """
    TODO store logs functionality

    Daemon to watch chrome history.
    watches for changes in history file then attempt
    to read and store history table.

    Helps resist against history deletion/modification

    Considerations:
        - Doesnt work for incognito as history is never written to disk
        - Hard to predict when chrome will write most recent history to database
        (generally takes a few seconds)
        - If chrome is open a copy will almost always have to be made for the
        database to be accessible increasing the taken time (in orders of seconds)
        - Bookmarks are opened by chrome at startup in the background therefore will show up
        in the logs
        - A time might not be found which will result in the default being recorded 1601-01-01 00:00:00
    """
    epoch: datetime = datetime(1601, 1, 1)
    default_db_path: str = os.getenv("APPDATA") + "\\..\\Local\\Google\\Chrome\\User Data\\Default\\history"
    statement: str = "select url, title, visit_count, last_visit_time from urls"
    temp_name: str = "db_cpy.db"

    def __init__(self):
        self.history = list()
        self.__update_history()  # initial history update

    @staticmethod
    def __get_history(path: str) -> tuple:
        """
        Connects to history db and attempts to read table entries
        will raise an sqlite3.OperationalError if unable to access

        :rtype: tuple
        :return: history entries found
        :param path: Location of history db
        """
        connection = sqlite3.connect(path)
        connection.text_factory = str  # always return byte strings
        return tuple(connection.cursor().execute('select url, title, visit_count, last_visit_time from urls'))

    def __update_history(self):
        """
        Attempts to access original history db from chrome directory
        if fails a copy is made into a temp directory and the copy is
        read instead.

        The rows are stored into a dict, any existing urls
        have their view count amended and the date accessed appended
        """
        try:
            retrieved_history = self.__get_history(self.default_db_path)
        except sqlite3.OperationalError:  # database locked
            temp_dir = tempfile.TemporaryDirectory()
            temp_path = f"{temp_dir.name}\\{self.temp_name}"
            shutil.copy(self.default_db_path, temp_path)
            retrieved_history = self.__get_history(temp_path)
            temp_dir.cleanup()  # cleanup temp dir

        for row in retrieved_history:
            for entry in self.history:
                if row[0] == entry["url"]:
                    entry["visit count"] = int(row[2])  # can cause inaccuracies, logic needs amending
                    date = str(self.epoch + timedelta(microseconds=row[3]))
                    if date not in entry["date(GMT)"]:  # checks if date is already entry
                        entry["date(GMT)"].append(date)
                    break
            else:  # no url was found in current history
                dict_ = dict()
                dict_["url"] = row[0]
                dict_["title"] = row[1]
                dict_["visit count"] = int(row[2])
                dict_["date(GMT)"] = [str(self.epoch + timedelta(microseconds=row[3]))]
                self.history.append(dict_)

    def __get_db_hash(self) -> str:
        """
        Calculates an md5 check sum for history db

        :rtype: str
        :return: md checksum
        """
        hash_md5 = hashlib.md5()
        with open(self.default_db_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def watch(self, delay: int = 1):
        """
        starts watch loop.
        Looks for any changes to the history db file
        if a change occurs __update_history is called
        and the file is processed as necessary

        :param delay: integer defining the time in seconds
        to wait between each loop, by default 1
        """
        db_hash = self.__get_db_hash()
        while True:
            curr_hash = self.__get_db_hash()
            if db_hash != curr_hash:
                self.__update_history()
                db_hash = curr_hash
            time.sleep(delay)


HistoryDaemon().watch()
