from annotation.actions.Action import create_action
import json
import os


class History:
    SAVE_NAME = "history.json"

    def __init__(self, arch_handler, save_func):
        self._edited = False
        self.h = []
        self.autosave = False
        self.arch_handler = arch_handler
        self.save_func = save_func
        self.curr = -1
        self.last = -1

    def set_autosave(self, autosave):
        self.autosave = autosave

    def add(self, action, debug=False):
        if self.curr == self.last:
            self.curr += 1
            self.last += 1
        elif self.curr < self.last:
            self.curr += 1
            self.last = self.curr
            self.h = self.h[:self.curr]
        else:
            raise ValueError("In History Class, it can't happen that self.curr > self.last, but it did...")
        self.h.append(action)
        if debug:
            print(action.get_data())
        self.autosave and self.save_func()
        self._edited = True

    def back(self):
        """DO NOT CALL"""
        self.curr -= 1

    def dump(self):
        return [action.get_data() for action in self.h]

    def load(self, h, debug=False):
        """
        Loads history

        Args:
            h (list of dict): history
            debug (bool): debug flag
        """
        self.h = []
        for a in h:
            action = create_action(**a)
            self.h.append(action)
        self.curr = self.last = len(self.h) - 1
        if debug:
            print("loaded history:")
            print(self.h)

    def save_(self):
        if not self._edited:
            return
        data = {'history': self.dump()}
        with open(os.path.join(os.path.dirname(self.arch_handler.dicomdir_path), self.SAVE_NAME), "w") as outfile:
            json.dump(data, outfile)
        self._edited = False

    def load_(self):
        path = os.path.join(os.path.dirname(self.arch_handler.dicomdir_path), self.SAVE_NAME)
        if not os.path.isfile(path):
            print("No history to load")
            return
        with open(path, "r") as infile:
            data = json.load(infile)
        self.load(data['history'])
        self._edited = False

    def has(self, ActionClass):
        for action in self.h:
            if isinstance(action, ActionClass):
                return True
        return False
