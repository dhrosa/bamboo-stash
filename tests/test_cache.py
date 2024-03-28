from pathlib import Path

from pytest import fixture

from bamboo_stash import Cache


@fixture
def cache(tmp_path: Path) -> Cache:
    return Cache(tmp_path / "bamboo_stash")


def test_no_args(cache: Cache) -> None:
    call_count = 0

    @cache
    def f() -> int:
        nonlocal call_count
        call_count += 1
        return 4

    assert f() == 4
    assert f() == 4
    assert call_count == 1


def test_args(cache: Cache) -> None:
    call_count = 0

    @cache
    def f(a: int) -> int:
        nonlocal call_count
        call_count += 1
        return a**2

    assert f(1) == 1
    assert f(2) == 4
    assert f(2) == 4
    assert f(1) == 1
    assert call_count == 2
