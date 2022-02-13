import cProfile
import pstats
import logging
import tempfile

# import order for module config is important
from gitlab2prov.config import config

from gitlab2prov import bootstrap
from gitlab2prov.domain import commands


if config.log:
    logging.basicConfig(level=logging.DEBUG, filename="gl2p.log")
log = logging.getLogger(__name__)


def cprofile(func):
    def profiled():
        with cProfile.Profile() as pr:
            func()
        stats = pstats.Stats(pr)
        stats.sort_stats(pstats.SortKey.TIME)
        stats.dump_stats(config.profiling)

    if config.cprofile:
        log.info("enabled profiling")
        return profiled
    log.info("disabled profiling")
    return func


@cprofile
def main():
    bus = bootstrap.bootstrap()
    token = config.token

    for url in config.projects:
        # create a temporary directory to clone
        # the project git repo to
        with tempfile.TemporaryDirectory() as tmpdir:
            log.info(f"created {tmpdir=}")
            cmd = commands.Init(url, token, tmpdir)
            bus.handle(cmd)

    # write serialized graph to stdout
    cmd = commands.Serialize(config.fmt, config.pseudonymous, config.double_agents)
    bus.handle(cmd)


if __name__ == "__main__":
    main()
