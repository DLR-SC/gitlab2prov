import sys
import logging

from prov.dot import prov_to_dot

from gitlab2prov.domain import commands
from gitlab2prov.prov import operations
from gitlab2prov.prov import model


log = logging.getLogger(__name__)




def mine_git(cmd: commands.Init, uow, git_miner):
    from_path = repository_filepath(cmd.url, cmd.path)
    repo = git_miner.get_repo(from_path)
    with uow:
        for resource in git_miner.mine(repo):
            log.debug(f"add {resource=}")
            uow.resources.add(resource)
        uow.commit()


def mine_gitlab(cmd: commands.Init, uow, gitlab_miner):
    project = gitlab_miner.get_project(cmd.url, cmd.token)
    with uow:
        for resource in gitlab_miner.mine(project):
            log.debug(f"add {resource=}")
            uow.resources.add(resource)
        uow.commit()


def serialize(cmd: commands.Serialize, uow):
    subgraphs = []
    for prov_model in model.MODELS:
        with uow:
            log.info(f"populate model {prov_model}")
            subgraph = prov_model(operations.graph_factory(), uow.resources)
        subgraphs.append(subgraph)

    graph = operations.combine(subgraphs)
    graph = operations.dedupe(graph)

    if cmd.uncover_double_agents:
        graph = operations.uncover_double_agents(graph, cmd.uncover_double_agents)
        graph = operations.dedupe(graph)
    if cmd.pseudonymize:
        graph = operations.pseudonymize(graph)
    
    if cmd.fmt == "dot":
        print(prov_to_dot(graph), file=sys.stdout)
    else:
        graph.serialize(destination=sys.stdout, format=cmd.fmt)


HANDLERS = {
    commands.Init: [
        mine_git,
        mine_gitlab,
    ],
    commands.Serialize: [serialize],
}
