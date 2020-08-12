import json

SLICE_CHANGED = "SLICE_CHANGED"
ARCH_CP_CHANGED = "ARCH_CP_CHANGED"
NO_ACTION = "NO_ACTION"


def create_action(**args):
    kind = args['kind']
    if kind == NO_ACTION:
        return Action()
    elif kind == ARCH_CP_CHANGED:
        return ArchCpChangedAction(args['curr'], args['prev'], args['index'])
    elif kind == SLICE_CHANGED:
        return SliceChangedAction(args['val'])
    else:
        raise ValueError("kind not recognized")


class Action:
    def get_data(self):
        return self.__dict__

    def __repr__(self):
        return json.dumps(self.get_data())


class NoAction(Action):
    def __init__(self):
        self.kind = NO_ACTION


class ArchCpChangedAction(Action):
    def __init__(self, curr, prev, index):
        self.kind = ARCH_CP_CHANGED

        if len(curr) != 2 or len(prev) != 2:
            raise ValueError("curr and prev arguments must be tuples with length 2")

        self.curr = tuple(map(float, curr))
        self.prev = tuple(map(float, prev))
        self.index = int(index)


class SliceChangedAction(Action):
    def __init__(self, val):
        self.kind = SLICE_CHANGED
        self.val = int(val)
