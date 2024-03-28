import hashlib
import pickle
from collections.abc import Callable
from functools import wraps
from inspect import BoundArguments, signature
from pathlib import Path
from typing import Any, ParamSpec, TypeVar, cast

import pandas as pd

VERSION = "0.0.0"

P = ParamSpec("P")
R = TypeVar("R")

CACHE_PATH: Path | None = None


def init(*, cache_path: Path) -> None:
    global CACHE_PATH
    CACHE_PATH = cache_path


def cached(function: Callable[P, R]) -> Callable[P, R]:
    sig = signature(function)

    @wraps(function)
    def inner(*args: P.args, **kwargs: P.kwargs) -> R:
        if CACHE_PATH is None:
            raise RuntimeError("init() not called.")
        function_path = CACHE_PATH / function.__name__
        cache_path = function_path / digest_args(sig.bind(*args, **kwargs))
        print(f"{cache_path=}")
        if cache_path.exists():
            with cache_path.open("rb") as f:
                return cast(R, pickle.load(f))
        # Fallback to actual function and cache the result
        result = function(*args, **kwargs)
        function_path.mkdir(parents=True, exist_ok=True)
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
