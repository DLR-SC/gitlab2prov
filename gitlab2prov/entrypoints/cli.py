import cProfile
import pstats
import logging
import tempfile

from gitlab2prov.config import CONFIG, set_config
if CONFIG is None:
    CONFIG = set_config(entrypoint="cli")

from gitlab2prov import bootstrap
from gitlab2prov.domain import commands


if CONFIG.log:
    logging.basicConfig(level=logging.DEBUG, filename="gl2p.log")
log = logging.getLogger(__name__)


def cprofile(func):
    def profiled():
        with cProfile.Profile() as pr:
            func()
        stats = pstats.Stats(pr)
        stats.sort_stats(pstats.SortKey.TIME)
        stats.dump_stats("gl2p.stats")

    if CONFIG.cprofile:
        log.info("enabled profiling")
        return profiled
    log.info("disabled profiling")
    return func


@cprofile
def main():
    bus = bootstrap.bootstrap()
    token = CONFIG.token

    for url in CONFIG.projects:
        # create a temporary directory to clone
        # the project git repo to
        with tempfile.TemporaryDirectory() as tmpdir:
            log.info(f"created {tmpdir=}")
            cmd = commands.Init(url, token, tmpdir)
            bus.handle(cmd)

    # write serialized graph to stdout
    cmd = commands.Serialize(CONFIG.fmt, CONFIG.pseudonymous, CONFIG.double_agents)
    bus.handle(cmd)


if __name__ == "__main__":
    main()
