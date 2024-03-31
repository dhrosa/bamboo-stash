from pathlib import Path
from shutil import rmtree
from typing import cast

from pandas import DataFrame, Series
from pytest import fixture

from bamboo_stash import Stash


@fixture
def stash(tmp_path: Path) -> Stash:
    return Stash(tmp_path / "bamboo_stash")


def test_no_args(stash: Stash) -> None:
    call_count = 0

    @stash
    def f() -> int:
        nonlocal call_count
        call_count += 1
        return 4

    assert f() == 4
    assert f() == 4
    assert call_count == 1


def test_args(stash: Stash) -> None:
    call_count = 0

    @stash
    def f(a: int) -> int:
        nonlocal call_count
        call_count += 1
        return a**2

    assert f(1) == 1
    assert f(2) == 4
    assert f(2) == 4
    assert f(1) == 1
    assert call_count == 2


def test_stash_file_deletion(stash: Stash) -> None:
    call_count = 0

    @stash
    def f() -> int:
        nonlocal call_count
        call_count += 1
        return 4

    assert f() == 4
    assert f() == 4
    assert call_count == 1

    rmtree(stash.base_dir)
    assert f() == 4
    assert call_count == 2


def test_series_arg(stash: Stash) -> None:
    call_count = 0

    @stash
    def f(s: "Series[int]") -> int:
        nonlocal call_count
        call_count += 1
        return s.sum()

    s = Series([1, 2, 3])
    assert f(s) == 6
    assert f(s.copy()) == 6
    assert call_count == 1


def test_dataframe_arg(stash: Stash) -> None:
    call_count = 0

    @stash
    def f(df: DataFrame) -> int:
        nonlocal call_count
        call_count += 1
        return cast(int, df.sum().sum())

    df = DataFrame(data=[[1, 2, 3], [4, 5, 6]])
    assert f(df) == 21
    assert f(df.copy()) == 21
    assert call_count == 1
