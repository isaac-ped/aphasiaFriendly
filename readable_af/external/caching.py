import json
import pickle

from rsa import verify
from ..config import Config
import redis
import hashlib
from pathlib import Path

from ..logger import logger

CACHE_DIR = Path(__file__).parent.parent.parent / ".cache"

NO_CACHE = False


def _make_hashable(x):
    if isinstance(x, (list, tuple)):
        return tuple(_make_hashable(y) for y in x)
    if isinstance(x, dict):
        return tuple((_make_hashable(k), _make_hashable(v)) for k, v in x.items())
    return x


def cache_af(version: str = "", verify_fn=None):
    """A decorator to cache the results of a function call locally.

    Results are either cached locally or in redis, depending on the configuration.
    The optional "version" string here can be used to invalidate the cache for a given function.
    """

    def decorator(fn):
        redis_host = Config.get().redis_host
        redis_password = Config.get().redis_password
        if redis_host is not None:
            assert redis_password
            rdb = redis.Redis(
                host=redis_host,
                username="default",
                password=redis_password,
                port=6379,
                db=0,
            )
        else:
            rdb = None

        def redis_cache(*args, **kwargs) -> tuple[str, bool]:
            kwargs["__version__"] = version
            fn_cache = fn.__name__.strip("_")
            to_hash = _make_hashable((args, kwargs))
            hash_value = hashlib.md5(str(to_hash).encode("utf-8")).hexdigest()
            key = f"{fn_cache}:{hash_value}"
            info_key = f"{key}-info"
            assert rdb is not None
            logger.debug(f"Checking redis cache for key {key} and {info_key}")

            if rdb.exists(info_key) and rdb.exists(key):
                resp = rdb.get(info_key)
                assert isinstance(resp, bytes)
                resp = resp.decode("utf-8")
                info = _make_hashable(json.loads(resp))
                if info == to_hash:
                    logger.debug("Info matches")
                    return key, True
                logger.warning("Something weird happened. Cache info doesn't match.")
                logger.warning("Expected: %s", to_hash)
                logger.warning("Got: %s", info)
            rdb.set(info_key, json.dumps(to_hash))
            return key, False

        def cache_file(*args, **kwargs) -> tuple[Path, bool]:
            kwargs["__version__"] = version
            fn_cache = CACHE_DIR / fn.__name__
            if not fn_cache.exists():
                fn_cache.mkdir(parents=True, exist_ok=True)

            to_hash = _make_hashable((args, kwargs))
            h = hashlib.md5(str(to_hash).encode("utf-8")).hexdigest()
            cache_file = fn_cache / str(h)
            cache_info = cache_file.with_suffix(".json")

            if cache_file.exists() and cache_info.exists():
                logger.debug(f"Cache info exists: {cache_info}")
                with cache_info.open() as f:
                    info = _make_hashable(json.load(f))
                    if info == to_hash:
                        logger.debug("Info matches")
                        return cache_file, True
                    logger.warning(
                        "Something weird happened. Cache info doesn't match."
                    )
                    logger.warning("Expected: %s", to_hash)
                    logger.warning("Got: %s", info)

            with cache_info.open("w") as f:
                json.dump(to_hash, f, indent=2)
            return cache_file, False

        def redis_cache_wrapper(*args, **kwargs):
            assert rdb is not None
            c_f, is_cached = redis_cache(*args, **kwargs)
            logger.debug(f"Cache file: {c_f}")
            logger.debug(f"Cache exists? {is_cached}")
            if is_cached and not NO_CACHE:
                resp = rdb.get(c_f)
                try:
                    assert isinstance(resp, bytes)
                    loaded = pickle.loads(resp)
                    if verify_fn is not None:
                        if not verify_fn(loaded):
                            reran = fn(*args, **kwargs)
                            rdb.set(c_f, pickle.dumps(reran))
                            return reran
                    return pickle.loads(resp)
                except Exception as e:
                    logger.warning(
                        f"Error loading cache file {c_f}. Continuing without it: {e}"
                    )
            result = fn(*args, **kwargs)
            rdb.set(c_f, pickle.dumps(result))
            return result

        def file_cache_wrapper(*args, **kwargs):
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

        def wrapper(*args, **kwargs):
            if rdb is not None:
                try:
                    return redis_cache_wrapper(*args, **kwargs)
                except redis.ResponseError as e:
                    logger.warning(
                        f"Redis error! Falling back to file cache. Error: {e}"
                    )
            return file_cache_wrapper(*args, **kwargs)

        return wrapper

    return decorator
