import hashlib
import pickle
from collections.abc import Callable
from functools import wraps
from inspect import BoundArguments, signature
from pathlib import Path
from typing import Any, ParamSpec, TypeVar, cast

import pandas as pd

P = ParamSpec("P")
R = TypeVar("R")


class Cache:
    base_dir: Path

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    def __call__(self, function: Callable[P, R]) -> Callable[P, R]:
        return cached(self.base_dir, function)


def cached(base_dir: Path, function: Callable[P, R]) -> Callable[P, R]:
    sig = signature(function)

    @wraps(function)
    def inner(*args: P.args, **kwargs: P.kwargs) -> R:
        function_dir = base_dir / function.__name__
        cache_path = function_dir / digest_args(sig.bind(*args, **kwargs))
        print(f"{cache_path=}")
        if cache_path.exists():
            with cache_path.open("rb") as f:
                return cast(R, pickle.load(f))
        # Fallback to actual function and cache the result
        result = function(*args, **kwargs)
        function_dir.mkdir(parents=True, exist_ok=True)
        with cache_path.open("wb") as f:
            pickle.dump(result, f)
        return result

    return inner


def arg_to_bytes(x: Any) -> bytes:
    """Lossily condense arbitrary value to a byte sequence."""
    if isinstance(x, (pd.Series, pd.DataFrame)):
        hashes = pd.util.hash_pandas_object(x)
        return hashes.to_numpy().tobytes()
    hashed = hash(x)
    byte_length = (hashed.bit_length() + 7) // 8
    return hashed.to_bytes(byte_length, signed=True, byteorder="little")


def digest_args(binding: BoundArguments) -> str:
    """Lossily condense function arguments to a fixed-length string."""
    h = hashlib.sha256()
    for name, value in sorted(binding.arguments.items(), key=lambda x: x[0]):
        h.update(name.encode())
        h.update(arg_to_bytes(value))
    return h.hexdigest()
