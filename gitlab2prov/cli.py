import json
from prov.dot import prov_to_dot
from . import Gitlab2Prov
from .config import get_config, ConfigurationError

def read_alias_mapping(file_path):
    """Read and transform agent alias listing from a .json file."""
    if not file_path:
        return {}
    with open(file_path, "r") as mapping:
        data = mapping.read()
        obj = json.loads(data)
    aliases = {v: k for k, vs in obj.items() for v in vs}
    return aliases


def serialize(graph, fmt="json"):
    """Serialize prov graph in *fmt* file format."""
    if fmt == "dot":
        return str(prov_to_dot(graph))
    return str(graph.serialize(format=fmt))


def main():
    """Command line script entry point."""
    try:
        config = get_config()
    except ConfigurationError as e:
        print(e)
        return
    alias_mapping = read_alias_mapping(config.aliases)

    gl2p = Gitlab2Prov(config.token, config.rate_limit)

    acc = []
    for url in config.project_urls:
        graph = gl2p.compute_graph(url)
        graph = gl2p.unite_agents(graph, alias_mapping)
        if config.pseudonymize:
            graph = gl2p.pseudonymize(graph)
        acc.append(graph)
    graph = gl2p.unite_graphs(acc)

    if not config.quiet:
        print(serialize(graph, fmt=config.format))


if __name__ == "__main__":
    main()
