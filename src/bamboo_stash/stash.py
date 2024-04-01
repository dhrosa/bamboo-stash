import inspect
import logging
import pickle
from collections.abc import Callable
from functools import wraps
from hashlib import sha256 as hash_algorithm
from os import PathLike
from pathlib import Path
from typing import Any, ParamSpec, TypeVar, cast

import pandas as pd
from platformdirs import user_cache_path

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


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

    def __call__(self, f: Callable[P, R]) -> Callable[P, R]:
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
        return stashed(self.base_dir, f)


def stashed(base_dir: Path, f: Callable[P, R]) -> Callable[P, R]:
    """Implementation of Stash decorator."""

    signature = inspect.signature(f)

    # Parent folder for this function's data is computed from its name and
    # source code.
    function_dir = base_dir / f.__qualname__ / digest_function(f)

    @wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        # Path for this specific file is computed from the arguments.
        cache_path = function_dir / digest_args(signature.bind(*args, **kwargs))
        cache_path = cache_path.with_suffix(".pickle")
        logging.debug(f"Call to {f.__name__} will use cache path: {cache_path}")
        # Try fetching from cache.
        if cache_path.exists():
            return cast(R, load(cache_path))
        # Cache miss; fallback to actual function and cache the result
        result = f(*args, **kwargs)
        function_dir.mkdir(parents=True, exist_ok=True)
        dump(result, cache_path)
        return result

    return wrapper


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


def stash(f: Callable[P, R]) -> Callable[P, R]:
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
