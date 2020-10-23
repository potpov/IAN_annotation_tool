from annotation.components.message.Strategies import MessageStrategy
from annotation.utils.metaclasses import SingletonMeta


class Messenger(metaclass=SingletonMeta):
    _strategy: MessageStrategy = None

    def __init__(self, strategy: MessageStrategy):
        self._strategy = strategy

    def message(self, kind: str, title="", message="", parent=None):
        self._strategy.message(kind, title, message, parent)

    def loading_message(self, message="", func=lambda: None, parent=None):
        self._strategy.loading_message(message, func, parent)

    def progress_message(self, func, func_args: dict, message="", parent=None):
        self._strategy.progress_message(func, func_args, message, parent)

    def question(self, title="", message="", yes=lambda: None,
                 no=lambda: None, default='yes', parent=None):
        self._strategy.question(title, message, yes, no, default, parent)

    def set_strategy(self, strategy: MessageStrategy):
        self._strategy = strategy
