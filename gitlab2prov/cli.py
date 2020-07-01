from . import Gitlab2Prov
from .config import get_config

def main():
    "Command line script entry point."
    config = get_config()

    g = Gitlab2Prov(config.token, config.rate_limit)

    project_graphs = [g.compute_graph(project, config.aliases, config.pseudonymize) for project in config.project_urls]
    graph = g.unite_graphs(project_graphs)

    if not config.quiet:
        print(g.serialize(graph, fmt=config.format))


if __name__ == "__main__":
    main()
