"""This file wraps openai access with a simple local cache
so we can play around with subsequent stepes assuming the pipeline remains
the same up until that point"""

import json
import pickle
from pathlib import Path

import openai

from . import config
from .logger import logger

CACHE_DIR = Path(__file__).parent.parent / ".cache"


def _make_hashable(x):
    if isinstance(x, (list, tuple)):
        return tuple(_make_hashable(y) for y in x)
    if isinstance(x, dict):
        return tuple((_make_hashable(k), _make_hashable(v)) for k, v in x.items())
    return x

def localcache(fn):
    """A decorator to cache the results of a function call locally.

    Results are cached in the file .cache/fn_name/hash_of_args_and_kwargs.
    """
    def cache_file(*args, **kwargs) -> tuple[Path, bool]:
        fn_cache = CACHE_DIR / fn.__name__
        if not fn_cache.exists():
            fn_cache.mkdir(parents=True, exist_ok=True)

        to_hash = _make_hashable((args, kwargs))
        h = abs(hash(to_hash))
        cache_file = fn_cache / str(h)
        cache_info = cache_file.with_suffix(".json")

        if cache_file.exists() and cache_info.exists():
            logger.debug(f"Cache info exists: {cache_info}")
            with cache_info.open() as f:
                info = _make_hashable(json.load(f))
                if info == to_hash:
                    logger.debug("Info matches")
                    return cache_file, True
                logger.warning("Something weird happened. Cache info doesn't match.")
                logger.warning("Expected: %s", to_hash)
                logger.warning("Got: %s", info)

        with cache_info.open("w") as f:
            json.dump(to_hash, f)
        return cache_file, False

    def wrapper(*args, **kwargs):
        c_f, is_cached = cache_file(*args, **kwargs)
        logger.debug(f"Cache file: {c_f}")
        logger.debug(f"Cache exists? {is_cached}")
        if is_cached:
            with c_f.open("rb") as f:
                try:
                    return pickle.load(f)
                except Exception as e:
                    logger.warning(
                        f"Error loading cache file {c_f}. Continuing without it: {e}"
                    )
        result = fn(*args, **kwargs)
        with c_f.open("wb") as f:
            pickle.dump(result, f)
        return result

    return wrapper


@localcache
def completion(messages: list[dict], model="gpt-4") -> dict:

    openai.organization = config.ORGANIZATION_ID
    openai.api_key = config.openai_api_key()
    logger.debug(
        "Sending the following prompt: \n"
        + "\n"
        + json.dumps(messages, indent=2)
        + "\n"
    )
    return openai.ChatCompletion.create(model=model, messages=messages)
