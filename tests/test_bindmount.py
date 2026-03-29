import pytest
from pathlib import Path
from typing import Optional
import ambergris.bindmount


def test_make_io_relative_to_container(tmp_path, test_bindmounts):
    @ambergris.bindmount.make_io_relative_to_container
    # we want to test that:
    ## a. the Path translation works for submitted *args and **kwargs
    ## b. the decorator ignores non-Path arguments
    def test_func(
        in_path: Path,
        some_int_arg: int,
        mounts,
        some_list_arg: Optional[list[int]] = None,
        out_path: Optional[Path] = None,
    ):
        return in_path, some_int_arg, out_path, some_list_arg

    actual_in_path, actual_int_arg, actual_out_path, actual_list_arg = test_func(
        tmp_path / "host" / "test" / "in",
        42,
        mounts=test_bindmounts,
        some_list_arg=[1, 2, 3, 4, 5],
        out_path=tmp_path / "host" / "test" / "out",
    )

    expected_in_path = Path("/container") / "test" / "in"
    expected_out_path = Path("/container") / "test" / "out"

    assert actual_in_path == expected_in_path
    assert actual_out_path == expected_out_path
    ## Make sure the function only changes Path-type inputs
    assert actual_int_arg == 42
    assert actual_list_arg == [1, 2, 3, 4, 5]


def test_get_container_path(tmp_path, test_bindmounts):
    test_in = tmp_path / "host" / "test" / "in"
    actual_container_in_path = ambergris.bindmount.get_container_path(
        test_in, test_bindmounts[0]
    )
    expected_container_in_path = Path("/container") / "test" / "in"
    assert actual_container_in_path == expected_container_in_path


def test_get_container_path_multiple_bindmounts(tmp_path, test_bindmounts):
    test_in = tmp_path / "host" / "test" / "in"
    actual_container_in_path = ambergris.bindmount.get_container_path(
        test_in, *test_bindmounts
    )
    expected_container_in_path = Path("/container") / "test" / "in"
    assert actual_container_in_path == expected_container_in_path


def test_get_container_path_no_match(tmp_path, test_bindmounts, recwarn):
    expected_test_nomatch = tmp_path / "does" / "not" / "match"
    actual_test_nomatch = ambergris.bindmount.get_container_path(
        expected_test_nomatch, *test_bindmounts
    )
    # The function is supposed to return the path as-is if it's not found in your bindmounts
    assert actual_test_nomatch == expected_test_nomatch
    # It should also warn the user about it
    assert len(recwarn) == 1


def test_make_bindmounts(tmp_path, test_bindmounts):
    actual_bindmounts = ambergris.bindmount.make_bindmounts(
        (tmp_path / "host" / "test" / "in", Path("/container") / "test" / "in"),
        (tmp_path / "host" / "test" / "out", Path("/container") / "test" / "out"),
    )
    assert actual_bindmounts == test_bindmounts


def test_make_bindmount(tmp_path, test_bindmounts):
    actual_bindmount = ambergris.bindmount.make_bindmount(
        tmp_path / "host" / "test" / "in", Path("/container") / "test" / "in"
    )
    assert actual_bindmount == test_bindmounts[0]
    assert Path(actual_bindmount["Source"]).is_absolute()
