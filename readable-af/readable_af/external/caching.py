import json
import pickle
from pathlib import Path

from ..logger import logger

CACHE_DIR = Path(__file__).parent.parent.parent / ".cache"

NO_CACHE=False

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
            json.dump(to_hash, f, indent=2)
        return cache_file, False

    def wrapper(*args, **kwargs):
        c_f, is_cached = cache_file(*args, **kwargs)
        logger.debug(f"Cache file: {c_f}")
        logger.debug(f"Cache exists? {is_cached}")
        if is_cached and not NO_CACHE:
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
