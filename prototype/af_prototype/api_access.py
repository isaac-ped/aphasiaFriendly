"""This file wraps openai access with a simple local cache
so we can play around with subsequent stepes assuming the pipeline remains
the same up until that point"""

import json
import logging
from pathlib import Path
import openai

CACHE_DIR = Path(__file__).parent.parent / ".cache"


def _make_hashable(x):
    if isinstance(x, (list, tuple)):
        return tuple(_make_hashable(y) for y in x)
    if isinstance(x, dict):
        return tuple((_make_hashable(k), _make_hashable(v)) for k, v in x.items())
    return x


def localcache(fn):
    def cache_file(*args, **kwargs) -> tuple[Path, bool]:
        fn_cache = CACHE_DIR / fn.__name__
        if not fn_cache.exists():
            fn_cache.mkdir(parents=True, exist_ok=True)

        to_hash = _make_hashable((args, kwargs))
        h = hash(to_hash)
        cache_file = fn_cache / str(h)
        cache_info = cache_file.with_suffix(".json")

        if cache_info.exists():
            logging.debug(f"Cache file exists: {cache_info}")
            with cache_info.open() as f:
                info = _make_hashable(json.load(f))
                if info == to_hash:
                    logging.debug("Info matches")
                    return cache_file, True
                logging.warning("Something weird happened. Cache info doesn't match.")
                logging.warning("Expected: %s", to_hash)
                logging.warning("Got: %s", info)

        with cache_info.open("w") as f:
            json.dump(to_hash, f)
        return cache_file, False

    def wrapper(*args, **kwargs):
        c_f, is_cached = cache_file(*args, **kwargs)
        logging.debug(f"Cache file: {c_f}")
        logging.debug(f"Cache exists? {is_cached}")
        if is_cached:
            with c_f.open() as f:
                return json.load(f)
        else:
            result = fn(*args, **kwargs)
            with c_f.open("w") as f:
                json.dump(result, f)
            return result

    return wrapper


@localcache
def completion(messages: list[dict], model="gpt-3.5-turbo") -> dict:
    return openai.ChatCompletion.create(model=model, messages=messages)
