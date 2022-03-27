import cProfile
import functools
import pstats
from datetime import datetime
from typing import Callable, Any


def profiling(func: Callable = None, enabled: bool = True) -> Callable:
    if func is None:
        return functools.partial(profiling, enabled=enabled)
    if enabled is False:
        return func

    @functools.wraps(func)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        with cProfile.Profile() as pr:
            result = func(*args, **kwargs)
        stats = pstats.Stats(pr)
        stats.sort_stats(pstats.SortKey.TIME)
        stats.dump_stats(f"gitlab2prov-run-{datetime.now():%Y-%m-%d-%H-%M-%S}.profile")
        return result

    return decorated
