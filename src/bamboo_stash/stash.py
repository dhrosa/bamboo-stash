import inspect
import pickle
from collections.abc import Callable
from functools import update_wrapper
from hashlib import sha256 as hash_algorithm
from logging import getLogger
from os import PathLike
from pathlib import Path
from shutil import rmtree
from typing import Any, Generic, ParamSpec, TypeVar, cast

import pandas as pd
from platformdirs import user_cache_path

logger = getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


class StashedFunction(Generic[P, R]):
    """Callable object that wraps your original function."""

    def __init__(self, base_dir: Path, f: Callable[P, R]) -> None:
        self.f = f
        self.signature = inspect.signature(f)
        # Parent folder for this function's data is computed from its name and
        # source code.
        self.function_dir = base_dir / f.__qualname__ / digest_function(f)
        update_wrapper(self, f)

    def path_for(self, *args: P.args, **kwargs: P.kwargs) -> Path:
        """File where data for a function call with these arguments should be stored."""
        cache_path = self.function_dir / digest_args(
            self.signature.bind(*args, **kwargs)
        )
        return cache_path.with_suffix(".pickle")

    def clear_for(self, *args: P.args, **kwargs: P.kwargs) -> None:
        """Delete cached data (if any exists) for this specific set of arguments."""
        self.path_for(*args, **kwargs).unlink(missing_ok=True)

    def clear(self) -> None:
        """Delete all cached data for this function."""
        logger.info(f"Deleting cached data for function {self.f.__qualname__}")
        rmtree(self.function_dir)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """If a cached file for these arguments exist, returns the cached result.

        Otherwise, calls the wrapped function, caches that result to a file, and
        returns that result.
        """
        cache_path = self.path_for(*args, **kwargs)
        logger.debug(f"Call to {self.f.__name__} will use cache path: {cache_path}")
        # Try fetching from cache.
        if cache_path.exists():
            return cast(R, load(cache_path))
        # Cache miss; fallback to actual function and cache the result
        result = self.f(*args, **kwargs)
        self.function_dir.mkdir(parents=True, exist_ok=True)
        dump(result, cache_path)
        return result


class Stash:
    """An object that can be used to decorate functions to transparently cache its calls.

    If the chosen directory doesn't exist, it will be created (along with its
    parents) the first time a function call is cached to disk.
    """

    base_dir: Path
    """Base directory for storing cached data."""

    def __init__(self, base_dir: PathLike[str] | None = None) -> None:
        """

        :param base_dir: Directory for storing cached data. If the value is
          :py:data:`None` (the default), an appropriate cache directory is
          automatically chosen in the user's home directory. This automatically chosen
          value can be seen using :py:attr:`Stash.base_dir`.

        """
        if base_dir is None:
            base_dir = user_cache_path("bamboo-stash")
        self.base_dir = Path(base_dir)
        logger.info(f"Data will be cached in {base_dir}")

    def clear(self) -> None:
        """Delete all cached data."""
        logger.info(f"Deleting cached data in {self.base_dir}")
        rmtree(self.base_dir)

    def __call__(self, f: Callable[P, R]) -> StashedFunction[P, R]:
        """Decorator to wrap a function to cache its calls.

        You wouldn't call this method explicitly; this method exists to make the
        :py:class:`Stash` object itself callable as a decorator.

        For example:

        .. code:: python

         from bamboo_stash import Stash

         stash = Stash()

         @stash  # <-- This line invokes stash.__call__
         def my_function(): ...
        """
        return StashedFunction(self.base_dir, f)


def load(path: Path) -> Any:
    with path.open("rb") as f:
        return pickle.load(f)


def dump(result: R, path: Path) -> None:
    with path.open("wb") as f:
        pickle.dump(result, f)


def arg_to_bytes(x: Any) -> bytes:
    """Lossily condense arbitrary value to a byte sequence."""
    if isinstance(x, (pd.Series, pd.DataFrame)):
        hashes = pd.util.hash_pandas_object(x)
        return hashes.to_numpy().tobytes()
    hashed = hash(x)
    byte_length = (hashed.bit_length() + 7) // 8
    return hashed.to_bytes(byte_length, signed=True, byteorder="little")


def digest_args(binding: inspect.BoundArguments) -> str:
    """Lossily condense function arguments to a fixed-length string."""
    h = hash_algorithm()
    for name, value in sorted(binding.arguments.items(), key=lambda x: x[0]):
        h.update(name.encode())
        h.update(arg_to_bytes(value))
    return h.hexdigest()


def digest_function(f: Callable[P, R]) -> str:
    """Lossily condense function definition into a fixed-length string."""
    return hash_algorithm(inspect.getsource(f).encode()).hexdigest()


def stash(f: Callable[P, R]) -> StashedFunction[P, R]:
    """Convenience decorator for when you don't care about where the cached data is stored.

    The first time this function is called, this automatically creates a
    :py:class:`Stash` object for you with default arguments. Subsequent calls
    will re-use that object.

    The automatically created :py:class:`Stash` object is intentionally hidden
    from you. If you need to access attributes such as
    :py:attr:`Stash.base_dir`, you should explicitly create a :py:class:`Stash`
    object instead.

    """
    global default_stash
    if default_stash is None:
        default_stash = Stash()
    return default_stash(f)


default_stash: Stash | None = None
"""Default-constructed Stash that is only initialized if stash() is called."""
