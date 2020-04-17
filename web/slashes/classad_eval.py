from typing import Tuple, List

import re
import textwrap

from flask import request, current_app

import htcondor
import classad

from .. import slack, formatting, utils


def handle_classad_eval():
    channel = request.form.get("channel_id")
    user = request.form.get("user_id")
    text = request.form.get("text")

    client = current_app.config["SLACK_CLIENT"]

    utils.run_in_thread(lambda: classad_eval_reply(client, channel, user, text))

    return f":thinking_face: :newspaper:", 200


def classad_eval_reply(client, channel, user, text):
    try:
        ad, exprs = parse(text)
        results = evaluate(ad, exprs)

        prefix = f"<@{user}> asked me to evaluate {'a ' if len(exprs) == 1 else ''}ClassAd expression{formatting.plural(exprs)}"
        if len(ad) != 0:
            msg_lines = [
                f"{prefix} in the context of this ad:",
                "```",
                *textwrap.dedent(str(ad)).strip().splitlines(),
                "```",
                f"Expressions:",
            ]
        else:
            msg_lines = [f"{prefix}:"]

        msg_lines.extend([*[f"`{k}` :arrow_right: `{v}`" for k, v in results.items()]])

        msg = "\n".join(filter(None, msg_lines))
    except Exception as e:
        msg = f"Failed to parse ad or expressions: {e}"

    slack.post_message(client, channel=channel, text=msg)


RE_PARTS = re.compile(r"'(.*?)'")


def parse(text: str) -> Tuple[classad.ClassAd, List[classad.ExprTree]]:
    parts = RE_PARTS.findall(text)

    ad = classad.parseOne(parts[0])
    exprs = [classad.ExprTree(s) for s in parts[1:]]

    return ad, exprs


def evaluate(ad, exprs):
    return {expr: expr.simplify(ad) for expr in exprs}