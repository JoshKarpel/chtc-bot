import pytest

import time

import htcondor
import classad

from web.commands import classad_eval


@pytest.mark.parametrize(
    "text, expected",
    [
        (
            "'[ foo = 5 ]' 'foo'",
            (classad.ClassAd({"foo": 5}), [classad.ExprTree("foo")]),
        ),
        (
            "'[ foo = \"bar\" ]' 'foo' 'bar'",
            (
                classad.ClassAd({"foo": "bar"}),
                [classad.ExprTree("foo"), classad.ExprTree("bar")],
            ),
        ),
        (
            "'[ foo = bar ]' 'foo' 'bar'",
            (
                classad.ClassAd({"foo": classad.ExprTree("bar")}),
                [classad.ExprTree("foo"), classad.ExprTree("bar")],
            ),
        ),
        ("'[]' '1 + 1'", (classad.ClassAd(), [classad.ExprTree("1 + 1")])),
        ("'' '1 + 1'", (classad.ClassAd(), [classad.ExprTree("1 + 1")])),
        (
            "'foo = 1' 'foo + 1'",
            (classad.ClassAd({"foo": 1}), [classad.ExprTree("foo + 1")]),
        ),
        (
            "'foo = 1; bar = 2' 'foo + 1'",
            (classad.ClassAd({"foo": 1, "bar": 2}), [classad.ExprTree("foo + 1")]),
        ),
        (
            "'[ foo = 1; bar = 2] ' 'foo + 1'",
            (classad.ClassAd({"foo": 1, "bar": 2}), [classad.ExprTree("foo + 1")]),
        ),
    ],
)
def test_parsing(text, expected):
    parsed_ad, parsed_exprs = classad_eval.parse(text)

    expected_ad, expected_exprs = expected

    assert {k: str(v) for k, v in parsed_ad.items()} == {
        k: str(v) for k, v in expected_ad.items()
    }
    assert all(p.sameAs(e) for p, e in zip(parsed_exprs, expected_exprs))


@pytest.mark.parametrize(
    "text", ["'foo'", "'[foo]'", "'[foo = 1]' '^'",],
)
def test_bad_parsing(text):
    with pytest.raises(SyntaxError):
        classad_eval.parse(text)


@pytest.mark.parametrize(
    "ad, exprs, expected",
    [
        (classad.ClassAd({"foo": 5}), [classad.ExprTree("foo")], [5]),
        (
            classad.ClassAd({"foo": 5, "bar": classad.ExprTree("foo + 1")}),
            [classad.ExprTree("foo"), classad.ExprTree("bar")],
            [5, 6],
        ),
    ],
)
def test_evaluating(ad, exprs, expected):
    assert list(classad_eval.evaluate(ad, exprs).values()) == expected


def test_handle_classad_eval_end_to_end(mocker, client):
    mock = mocker.patch("web.slack.post_message")

    client.post(
        "/slash/classad_eval",
        data=dict(
            channel_id="1234", user_id="5678", text="'[foo = 5]' 'foo' 'bar' '1 + 1'"
        ),
    )

    # let the executor run
    time.sleep(0.1)

    assert mock.call_count == 1

    channel = mock.call_args[1]["channel"]

    assert channel == "1234"

    msg = mock.call_args[1]["text"]

    # make a few assertions about the output message,
    # but without holding on too tight
    assert "<@5678>" in msg
    assert "foo = 5" in msg
    assert "undefined" in msg
    assert "2" in msg


def test_handle_classad_eval_classad_parse_failure_end_to_end(mocker, client):
    mock = mocker.patch("web.slack.post_message")

    client.post(
        "/slash/classad_eval",
        data=dict(
            channel_id="1234", user_id="5678", text="'foo = bar, bar = 5]' 'foo' 'bar' '1 + 1'"
        ),
    )

    # let the executor run
    time.sleep(0.1)

    assert mock.call_count == 1

    channel = mock.call_args[1]["channel"]

    assert channel == "1234"

    msg = mock.call_args[1]["text"]

    assert "Unable to parse string into a ClassAd" in msg


def test_handle_classad_eval_expr_parse_failure_end_to_end(mocker, client):
    mock = mocker.patch("web.slack.post_message")

    client.post(
        "/slash/classad_eval",
        data=dict(
            channel_id="1234", user_id="5678", text="'' ''* 123'"
        ),
    )

    # let the executor run
    time.sleep(0.1)

    assert mock.call_count == 1

    channel = mock.call_args[1]["channel"]

    assert channel == "1234"

    msg = mock.call_args[1]["text"]

    # This syntax error's text should be different if it's coming from
    # an expression rather than a ClassAd.
    assert "Unable to parse string into a ClassAd" in msg


def test_handle_classad_eval_with_empty_ad_end_to_end(mocker, client):
    mock = mocker.patch("web.slack.post_message")

    client.post(
        "/slash/classad_eval",
        data=dict(
            channel_id="1234", user_id="5678", text="'' 'foo' 'bar' '5 + 3'"
        ),
    )

    # let the executor run
    time.sleep(0.1)

    assert mock.call_count == 1

    channel = mock.call_args[1]["channel"]

    assert channel == "1234"

    msg = mock.call_args[1]["text"]

    # make a few assertions about the output message,
    # but without holding on too tight
    assert "<@5678>" in msg
    assert "undefined" in msg
    assert "8" in msg


# Upgrading to HTCondor 8.9.8 will get us access to GT#7607, which will
# cause certain problems with bad expression to go away (e.g., 'x = y'
# should not be parsed as 'x' and '123x' as '123').
