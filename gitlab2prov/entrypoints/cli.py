from gitlab2prov import bootstrap
from gitlab2prov.config import read_cli
from gitlab2prov.domain import commands
from gitlab2prov.log import create_logger
from gitlab2prov.profile import profiling


config = read_cli()


@profiling(enabled=config.profile)
def main():
    bus = bootstrap.bootstrap()

    if config.verbose:
        create_logger()

    for url in config.project_urls:
        cmd = commands.Fetch(url, config.token)
        bus.handle(cmd)

    cmd = commands.Serialize(config.format, config.pseudonymous, config.double_agents)
    bus.handle(cmd)


if __name__ == "__main__":
    main()
