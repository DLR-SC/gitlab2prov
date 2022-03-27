import tempfile

from gitlab2prov.config import CONFIG, set_config
if CONFIG is None:
    CONFIG = set_config(entrypoint="cli")

from gitlab2prov import bootstrap
from gitlab2prov.domain import commands







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
