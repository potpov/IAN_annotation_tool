from annotation.actions.Action import create_action
import json
import os


class History:
    SAVE_NAME = "history.json"

    def __init__(self, arch_handler, save_func=lambda: None):
        """
        Class that handles action registration and action list save and load operations

        Args:
            arch_handler (annotation.core.ArchHandler.ArchHandler): ArchHandler parent object
            save_func: save function for autosave
        """
        self._edited = False
        self.h = []
        self.autosave = False
        self.arch_handler = arch_handler
        self.save_func = save_func

    def set_autosave(self, autosave):
        self.autosave = autosave

    def add(self, action, debug=False):
        """
        Adds an action to the history

        action (annotation.actions.Action.Action): action to register
        debug (bool): debug flag
        """
        self.h.append(action)
        if debug:
            print(action.get_data())
        self.autosave and self.save_func()
        self._edited = True

    def dump(self):
        """
        Packs the history in a list of dictionaries, each of which is an action with its infos

        Returns:
             (list of dict): history ready for JSON output
        """
        return [action.get_data() for action in self.h]

    def load(self, h, debug=False):
        """
        Loads history

        Args:
            h (list of dict): history from JSON input
            debug (bool): debug flag
        """
        self.h = []
        for a in h:
            action = create_action(**a)
            self.h.append(action)
        if debug:
            print("loaded history:")
            print(self.h)

    def save_(self):
        """Generates a JSON dump of the history and saves it"""
        if not self._edited:
            return
        data = {'history': self.dump()}
        with open(os.path.join(os.path.dirname(self.arch_handler.dicomdir_path), self.SAVE_NAME), "w") as outfile:
            json.dump(data, outfile)
        self._edited = False

    def load_(self):
        """Loads a JSON dumpo of the history"""
        path = os.path.join(os.path.dirname(self.arch_handler.dicomdir_path), self.SAVE_NAME)
        if not os.path.isfile(path):
            print("No history to load")
            return
        with open(path, "r") as infile:
            data = json.load(infile)
        self.load(data['history'])
        self._edited = False

    def has(self, ActionClass):
        """
        Checks if an action of class ActionClass is in history

        Args:
             ActionClass (annotation.actions.Action.Action): class to find
        """
        for action in self.h:
            if isinstance(action, ActionClass):
                return True
        return False
