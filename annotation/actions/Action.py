import json

SLICE_CHANGED = "SLICE_CHANGED"
ARCH_CP_CHANGED = "ARCH_CP_CHANGED"
LEFT_CANAL_CP_ADDED = "LEFT_CANAL_CP_ADDED"
LEFT_CANAL_CP_CHANGED = "LEFT_CANAL_CP_CHANGED"
LEFT_CANAL_CP_REMOVED = "LEFT_CANAL_CP_REMOVED"
RIGHT_CANAL_CP_ADDED = "RIGHT_CANAL_CP_ADDED"
RIGHT_CANAL_CP_CHANGED = "RIGHT_CANAL_CP_CHANGED"
RIGHT_CANAL_CP_REMOVED = "RIGHT_CANAL_CP_REMOVED"
NO_ACTION = "NO_ACTION"
SIDE_VOLUME_CP_ADDED = "SIDE_VOLUME_CP_ADDED"
SIDE_VOLUME_CP_REMOVED = "SIDE_VOLUME_CP_REMOVED"
SIDE_VOLUME_CP_CHANGED = "SIDE_VOLUME_CP_CHANGED"
SIDE_VOLUME_SPLINE_EXTRACTED = "SIDE_VOLUME_SPLINE_EXTRACTED"
SIDE_VOLUME_SPLINE_RESET = "SIDE_VOLUME_SPLINE_RESET"


def create_action(**args):
    kind = args['kind']
    if kind == NO_ACTION:
        return Action()
    elif kind == ARCH_CP_CHANGED:
        return ArchCpChangedAction(args['curr'], args['prev'], args['index'])
    elif kind == SLICE_CHANGED:
        return SliceChangedAction(args['val'])
    elif kind == LEFT_CANAL_CP_CHANGED:
        return LeftCanalCpChangedAction(args['curr'], args['prev'], args['index'])
    elif kind == RIGHT_CANAL_CP_CHANGED:
        return RightCanalCpChangedAction(args['curr'], args['prev'], args['index'])
    elif kind == LEFT_CANAL_CP_ADDED:
        return LeftCanalCpAddedAction(args['cp'], args['index'])
    elif kind == RIGHT_CANAL_CP_ADDED:
        return RightCanalCpAddedAction(args['cp'], args['index'])
    elif kind == LEFT_CANAL_CP_REMOVED:
        return LeftCanalCpRemovedAction(args['index'])
    elif kind == RIGHT_CANAL_CP_REMOVED:
        return RightCanalCpRemovedAction(args['index'])
    elif kind == SIDE_VOLUME_CP_ADDED:
        return SideVolumeCpAddedAction(args['cp'], args['index'], args['pos'])
    elif kind == SIDE_VOLUME_CP_REMOVED:
        return SideVolumeCpRemovedAction(args['index'], args['pos'])
    elif kind == SIDE_VOLUME_CP_CHANGED:
        return SideVolumeCpChangedAction(args['curr'], args['prev'], args['index'], args['pos'])
    elif kind == SIDE_VOLUME_SPLINE_EXTRACTED:
        return SideVolumeSplineExtractedAction(args['pos'], args['from_pos'])
    elif kind == SIDE_VOLUME_SPLINE_RESET:
        return SideVolumeSplineResetAction(args['pos'])
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


class CpChangedAction(Action):
    def __init__(self, curr, prev, index):
        if len(curr) != 2 or len(prev) != 2:
            raise ValueError("curr and prev arguments must be tuples with length 2")
        self.curr = tuple(map(float, curr))
        self.prev = tuple(map(float, prev))
        self.index = int(index)


class ArchCpChangedAction(CpChangedAction):
    def __init__(self, curr, prev, index):
        super().__init__(curr, prev, index)
        self.kind = ARCH_CP_CHANGED


class LeftCanalCpChangedAction(CpChangedAction):
    def __init__(self, curr, prev, index):
        super().__init__(curr, prev, index)
        self.kind = LEFT_CANAL_CP_CHANGED


class RightCanalCpChangedAction(CpChangedAction):
    def __init__(self, curr, prev, index):
        super().__init__(curr, prev, index)
        self.kind = RIGHT_CANAL_CP_CHANGED


class CpAddedAction(Action):
    def __init__(self, cp, index):
        if len(cp) != 2:
            raise ValueError("cp must have 2 coordinates (x, y)")
        self.cp = tuple(map(float, cp))
        self.index = int(index)


class LeftCanalCpAddedAction(CpAddedAction):
    def __init__(self, cp, index):
        super().__init__(cp, index)
        self.kind = LEFT_CANAL_CP_ADDED


class RightCanalCpAddedAction(CpAddedAction):
    def __init__(self, cp, index):
        super().__init__(cp, index)
        self.kind = RIGHT_CANAL_CP_ADDED


class CpRemovedAction(Action):
    def __init__(self, index):
        self.index = int(index)


class LeftCanalCpRemovedAction(CpRemovedAction):
    def __init__(self, index):
        super().__init__(index)
        self.kind = LEFT_CANAL_CP_REMOVED


class RightCanalCpRemovedAction(CpRemovedAction):
    def __init__(self, index):
        super().__init__(index)
        self.kind = RIGHT_CANAL_CP_REMOVED


class SliceChangedAction(Action):
    def __init__(self, val):
        self.kind = SLICE_CHANGED
        self.val = int(val)


class SideVolumeCpAddedAction(CpAddedAction):
    def __init__(self, cp, index, pos):
        super().__init__(cp, index)
        self.kind = SIDE_VOLUME_CP_ADDED
        self.pos = pos


class SideVolumeCpRemovedAction(CpRemovedAction):
    def __init__(self, index, pos):
        super().__init__(index)
        self.kind = SIDE_VOLUME_CP_REMOVED
        self.pos = pos


class SideVolumeCpChangedAction(CpChangedAction):
    def __init__(self, curr, prev, index, pos):
        super().__init__(curr, prev, index)
        self.kind = SIDE_VOLUME_CP_CHANGED
        self.pos = pos


class SideVolumeSplineExtractedAction(Action):
    def __init__(self, pos, from_pos):
        self.kind = SIDE_VOLUME_SPLINE_EXTRACTED
        self.pos = pos
        self.from_pos = from_pos


class SideVolumeSplineResetAction(Action):
    def __init__(self, pos):
        self.kind = SIDE_VOLUME_SPLINE_RESET
        self.pos = pos
