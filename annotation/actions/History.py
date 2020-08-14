from annotation.actions.Action import create_action


class History:
    SAVE_NAME = "history.json"

    def __init__(self):
        self.h = []
        self.curr = -1
        self.last = -1

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
            # print(self.h)
            print(action.get_data())

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
