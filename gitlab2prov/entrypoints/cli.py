from gitlab2prov import bootstrap
from gitlab2prov.config import read_config
from gitlab2prov.domain import commands
from gitlab2prov.log import create_logger
from gitlab2prov.profile import profiling


def main():
    config = read_config()
    if config is None:
        return

    @profiling(enabled=config.profile)
    def run():
        bus = bootstrap.bootstrap()

        if config.verbose:
            create_logger()

        for url in config.project_urls:
            cmd = commands.Fetch(url, config.token)
            bus.handle(cmd)

        for fmt in config.format:
            cmd = commands.Serialize(
                fmt, config.pseudonymous, config.double_agents, config.outfile
            )
            bus.handle(cmd)

    run()


if __name__ == "__main__":
    main()
