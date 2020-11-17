import sys
from abc import ABC, abstractmethod

from annotation.components.message.Dialog import warning, information, LoadingDialog, ProgressLoadingDialog, question


class MessageStrategy(ABC):
    @abstractmethod
    def message(self, kind: str, title="", message="", parent=None):
        """
        Shows a warning or information message

        Args:
            kind (str): "warning" or "information"
            title (str): title of the message
            message (str): content of the message
        """
        pass

    @abstractmethod
    def loading_message(self, message="", func=lambda: None, parent=None):
        """
        Shows a loading message

        Args:
            message (str): content of the loading message
            func: function that is executed in background
        """
        pass

    @abstractmethod
    def progress_message(self, func, func_args: dict, message="", parent=None, cancelable=False):
        """
        Shows a progress loading message

        Args:
            message (str): content of the loading message
            func: function that is executed in background
            func_args (dict): dictionary of arguments for func
            cancelable (bool): cancel button enabled

        Returns:
            (bool): completion of the task
        """
        pass

    @abstractmethod
    def question(self, title="", message="", yes=lambda: None, no=lambda: None, default='yes', parent=None):
        """
        Shows a question message

        Args:
            title (str): title of the question
            message (str): question
            yes: function that has to be executed on yes
            no: function that has to be executed on no
            defualt (str): default answer
        """
        pass


class QtMessageStrategy(MessageStrategy):
    def message(self, kind: str, title="", message="", parent=None):
        if kind == "warning":
            warning(parent, title, message)
        elif kind == "information":
            information(parent, title, message)

    def loading_message(self, message="", func=lambda: None, parent=None):
        LoadingDialog(func, message, parent)

    def progress_message(self, func, func_args: dict, message="", parent=None, cancelable=False):
        pld = ProgressLoadingDialog(message, cancelable=cancelable)
        pld.set_function(lambda: func(step_fn=pld.get_signal(), **func_args))
        pld.start()
        return not pld.progress_canceled

    def question(self, title="", message="", yes=lambda: None, no=lambda: None, default='yes', parent=None):
        question(parent, title, message, yes, no, default)


class TerminalMessageStrategy(MessageStrategy):
    def message(self, kind: str, title="", message="", parent=None):
        print("{} -  {}: {}".format(kind.capitalize(), title, message))

    def loading_message(self, message="", func=lambda: None, parent=None):
        print("Wait - {} - Loading... ".format(message), end="")
        func()
        print("Done!")

    def progress_message(self, func, func_args: dict, message="", parent=None, cancelable=False):
        def print_bar(val, max):
            print("{}: {}/{} - {}%".format(message, val, max, int(val / max * 100)), end="\r")

        func(step_fn=print_bar, **func_args)
        print("{}: Done!".format(message))
        return True

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
