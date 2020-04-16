from flask import Blueprint, current_app, request

import bs4

from .formatting import plural, bold
from . import slack, utils

slash_bp = Blueprint("slash", __name__)


@slash_bp.route("/slash/knobs", methods=["POST"])
def knobs():
    channel = request.form.get("channel_id")
    knobs = request.form.get("text").upper().split(" ")
    user = request.form.get("user_id")

    utils.run_in_thread(
        lambda: handle_knobs(current_app.config["SLACK_CLIENT"], channel, knobs, user)
    )

    return f"Looking for knob{plural(knobs)} {', '.join(bold(k) for k in knobs)}", 200


KNOBS_URL = (
    "https://htcondor.readthedocs.io/en/latest/admin-manual/configuration-macros.html"
)


def handle_knobs(client, channel, knobs, user):
    response = utils.get_url(KNOBS_URL)
    soup = bs4.BeautifulSoup(response.text, "html.parser")

    descriptions = {knob: get_knob_description(soup, knob) for knob in knobs}

    msg_lines = [
        f"<@{user}> asked for information on knob{plural(knobs)} {', '.join(bold(k) for k in knobs)}"
    ]

    # TODO: this is clunky, we should make a function for this kind of grouping
    good = {k: v for k, v in descriptions.items() if v is not None}
    bad = {k: v for k, v in descriptions.items() if v is None}

    if bad:
        p1 = "they were" if len(bad) > 1 else "it was"
        p2 = "don't" if len(bad) > 1 else "it doesn't"
        msg_lines.append(
            f"I couldn't find information on {', '.join(bold(k) for k, v in bad.items())}. Perhaps {p1} misspelled, or {p2} exist?"
        )
    msg_lines.extend(v + "\n" for v in good.values())

    msg = "\n".join(msg_lines)

    slack.post_message(client, channel=channel, text=msg)


def get_knob_description(knobs_page_soup, knob):
    try:
        header = knobs_page_soup.find("span", id=knob)
        raw_description = header.parent.find_next("dd")
        description = raw_description.text.replace("\n", " ")

        return f"{bold(knob)}\n>{description}"
    except Exception:
        # TODO: add logging
        return None
