from pprint import pprint
import re
import threading
import os

from flask import Flask

from slackeventsapi import SlackEventAdapter
from slackclient import SlackClient

import requests
import bs4 as soup

app = Flask(__name__)


@app.route("/")
def index():
    return "I'm alive!"


SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/slack/events", app)

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_CLIENT = SlackClient(SLACK_BOT_TOKEN)


@slack_events_adapter.on("message")
def handle_message_event(event_data):
    pprint(event_data)

    # don't respond to our own messages
    if event_data["event"]["user"] == "U011WEDH24U":
        return

    # TODO: this is bad; we should spin up a thread pool and connect to here via a queue
    threading.Thread(target=lambda: _handle_message(event_data)).start()


def _handle_message(event_data):
    message = event_data["event"]

    for handler in REGEX_HANDLERS:
        matches = handler.regex.findall(message["text"])

        if len(matches) == 0:
            continue

        try:
            handler.handle_message(SLACK_CLIENT, message, matches)
        except Exception as e:
            print(e)


# TODO: make this an actual metaclass
class RegexMessageHandler:
    def handle_message(self, client, message, matches):
        raise NotImplementedError


class FlightworthyTicketLinker(RegexMessageHandler):
    regex = re.compile(r"fw#(\d+)")

    def handle_message(self, client, message, matches):
        msgs = []
        for ticket_id in matches:
            url = f"https://htcondor-wiki.cs.wisc.edu/index.cgi/tktview?tn={ticket_id}"

            response = requests.get(url)
            html = soup.BeautifulSoup(response.text, "html.parser")
            title = html.h2.string.split(": ")[-1]
            status = html.find("td", text="Status:").find_next("td").b.string

            msgs.append(f"<{url}|fw#{ticket_id}> | {title} [{status}]")
        msg = "\n".join(msgs)

        client.api_call(
            "chat.postMessage", channel=message["channel"], text=msg,
        )


class RTTicketLinker(RegexMessageHandler):
    regex = re.compile(r"rt#(\d+)")

    def handle_message(self, client, message, matches):
        msgs = []
        for ticket_id in matches:
            url = f"https://crt.cs.wisc.edu/rt/Ticket/Display.html?id={ticket_id}"
            msgs.append(f"<{url}|rt#{ticket_id}>")
        msg = "\n".join(msgs)

        client.api_call(
            "chat.postMessage", channel=message["channel"], text=msg,
        )


# TODO: this makes me think we should have a config.py file where things like this list go
REGEX_HANDLERS = [FlightworthyTicketLinker(), RTTicketLinker()]

if __name__ == "__main__":
    app.run(port=3000)
