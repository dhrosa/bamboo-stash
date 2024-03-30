import hashlib
import inspect
import logging
import pickle
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, ParamSpec, TypeVar, cast

import pandas as pd

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


class Cache:
    base_dir: Path

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    def __call__(self, f: Callable[P, R]) -> Callable[P, R]:
        return cached(self.base_dir, f)


def cached(base_dir: Path, f: Callable[P, R]) -> Callable[P, R]:
    signature = inspect.signature(f)
    function_dir = base_dir / f.__qualname__ / digest_function(f)

    @wraps(f)
    def inner(*args: P.args, **kwargs: P.kwargs) -> R:
        cache_path = function_dir / digest_args(signature.bind(*args, **kwargs))
        logging.debug(f"Call to {f.__name__} will use cache path: {cache_path}")
        if cache_path.exists():
            return cast(R, load(cache_path))
        # Fallback to actual function and cache the result
        result = f(*args, **kwargs)
        function_dir.mkdir(parents=True, exist_ok=True)
        dump(result, cache_path)
        return result

    return inner


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
    h = hashlib.sha256()
    for name, value in sorted(binding.arguments.items(), key=lambda x: x[0]):
        h.update(name.encode())
        h.update(arg_to_bytes(value))
    return h.hexdigest()


def digest_function(f: Callable[P, R]) -> str:
    """Lossily condense function definition into a fixed-length string."""
    return hashlib.sha256(inspect.getsource(f).encode()).hexdigest()
