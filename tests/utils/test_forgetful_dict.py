import datetime
import time

import pytest

from web.utils import ForgetfulDict


def test_it_remembers():
    d = ForgetfulDict(memory_time=10)

    d["key"] = 5

    assert d["key"] == 5


def test_it_forgets_if_it_has_no_memory():
    d = ForgetfulDict(memory_time=0)

    d["key"] = 5

    with pytest.raises(KeyError):
        d["key"]


def test_it_forgets_with_short_memory():
    d = ForgetfulDict(memory_time=0.1)

    d["key"] = 5
    time.sleep(0.2)

    with pytest.raises(KeyError):
        d["key"]


def test_it_remembers_with_short_memory():
    d = ForgetfulDict(memory_time=0.2)

    d["key"] = 5
    time.sleep(0.1)

    assert d["key"] == 5


def test_it_doesnt_remember():
    d = ForgetfulDict(memory_time=10)

    d["key"] = 5

    with pytest.raises(KeyError):
        d["non-key"]


def test_it_doesnt_forget_with_multiple_assignments():
    d = ForgetfulDict(memory_time=0.2)

    d["key"] = 5
    time.sleep(0.1)
    assert d["key"] == 5

    d["key"] = 7
    assert d["key"] == 7
    time.sleep(0.11)

    assert "key" in d

    time.sleep(0.2)

    assert "key" not in d


def test_constructor_converts_timedeltas():
    d = ForgetfulDict(memory_time=datetime.timedelta(seconds=1))

    assert d.memory_time == 1


def test_set_update_with_key_missing():
    d = ForgetfulDict(memory_time=1)

    assert d.set("key", None, update_existing=True)


def test_set_update_with_key_found():
    d = ForgetfulDict(memory_time=1)

    d["key"] = "This"

    assert d.set("key", "Yes", update_existing=True)
    assert d["key"] == "Yes"


def test_set_no_update_with_key_found():
    d = ForgetfulDict(memory_time=1)

    d["key"] = "This"

    assert not d.set("key", "Nope", update_existing=False)
    assert d["key"] == "This"


def test_set_no_update_with_key_missing():
    d = ForgetfulDict(memory_time=1)

    assert d.set("key", "Yes", update_existing=False)
    assert d["key"] == "Yes"
