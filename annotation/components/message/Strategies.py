import sys
from abc import ABC, abstractmethod

from annotation.components.message.Dialog import warning, information, LoadingDialog, ProgressLoadingDialog, question


class MessageStrategy(ABC):
    @abstractmethod
    def message(self, kind: str, title="", message="", parent=None):
        pass

    @abstractmethod
    def loading_message(self, message="", func=lambda: None, parent=None):
        pass

    @abstractmethod
    def progress_message(self, func, func_args: dict, message="", parent=None):
        pass

    @abstractmethod
    def question(self, title="", message="", yes=lambda: None, no=lambda: None, default='yes', parent=None):
        pass


class QtMessageStrategy(MessageStrategy):
    def message(self, kind: str, title="", message="", parent=None):
        if kind == "warning":
            warning(parent, title, message)
        elif kind == "information":
            information(parent, title, message)

    def loading_message(self, message="", func=lambda: None, parent=None):
        LoadingDialog(func, message, parent)

    def progress_message(self, func, func_args: dict, message="", parent=None):
        pld = ProgressLoadingDialog(message)
        pld.set_function(lambda: func(step_fn=pld.get_signal(), **func_args))
        pld.start()

    def question(self, title="", message="", yes=lambda: None, no=lambda: None, default='yes', parent=None):
        question(parent, title, message, yes, no, default)


class TerminalMessageStrategy(MessageStrategy):
    def message(self, kind: str, title="", message="", parent=None):
        print("{} -  {}: {}".format(kind.capitalize(), title, message))

    def loading_message(self, message="", func=lambda: None, parent=None):
        print("Wait - {} - Loading... ".format(message), end="")
        func()
        print("Done!")

    def progress_message(self, func, func_args: dict, message="", parent=None):
        def print_bar(val, max):
            print("{}: {}/{} - {}%".format(message, val, max, int(val / max * 100)), end="\r")

        func(step_fn=print_bar, **func_args)
        print("{}: Done!".format(message))

    def question(self, title="", message="", yes=lambda: None, no=lambda: None, default='yes', parent=None):
        valid_yes = ['yes', 'y', 'ye']
        valid_no = ['no', 'n']

        while True:
            sys.stdout.write("{}: {}".format(title, message))
            choice = input().lower()
            if choice == '':
                if default == 'yes':
                    yes()
                else:
                    no()
                return
            elif choice in valid_yes:
                yes()
                return
            elif choice in valid_no:
                no()
                return
            else:
                sys.stdout.write("Please respond with 'yes' or 'no' "
                                 "(or 'y' or 'n').\n")


class ProcessPoolExecutorStategy(TerminalMessageStrategy):

    def progress_message(self, func, func_args: dict, message="", parent=None):
        def print_bar(val, max):
            print("{}: {}/{} - {}%".format(message, val, max, int(val / max * 100)), end="\r")
        
        func(step_fn=print_bar, **func_args)
        print("{}: Done!".format(message))
