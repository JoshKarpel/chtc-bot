import abc
from typing import List


class Handler(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def handle(self, app, client, message):
        """
        Parameters
        ----------
        app
            The Flask app.
        client
            A Slack client object.
        message
            The message from the Slack events API.
        """
        raise NotImplementedError


class RegexMessageHandler(Handler):
    def __init__(self, *, regex):
        super().__init__()

        self.regex = regex

    def handle(self, app, client, message):
        matches = self.regex.findall(message["text"])
        matches = self.filter_matches(message, matches)

        if len(matches) == 0:
            return

        try:
            self.handle_message(app, client, message, matches)
        except Exception as e:
            print(e)

    @abc.abstractmethod
    def handle_message(self, app, client, message, matches: List[str]):
        raise NotImplementedError

    def filter_matches(self, message, matches: List[str]):
        return matches