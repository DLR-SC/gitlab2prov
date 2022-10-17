import hashlib

from prov.model import ProvAgent, ProvDocument, ProvRelation, PROV_ROLE, PROV_TYPE

from gitlab2prov.prov import operations
from gitlab2prov.prov.operations import qualified_name

from tests.random_refs import random_suffix


class TestStats:
    def test_format_as_ascii_table(self):
        d = {"A": 1, "B": 2, "C": 3}
        expected_header = [
            f"|{'Record Type':20}|{'Count':20}|",
            f"+{'-'*20}+{'-'*20}+",
        ]
        expected_body = [
            f"|{'A':20}|{1:20}|",
            f"|{'B':20}|{2:20}|",
            f"|{'C':20}|{3:20}|",
        ]
        table = operations.format_stats_as_ascii_table(d)
        lines = [l.strip() for l in table.split("\n") if l]
        assert lines[:2] == expected_header
        assert lines[2:] == expected_body

    def test_format_stats_as_csv(self):
        d = {"A": 1, "B": 2, "C": 3}
        expected_header = ["Record Type, Count"]
        expected_body = [
            "A, 1",
            "B, 2",
            "C, 3",
        ]
        csv = operations.format_stats_as_csv(d)
        lines = [l.strip() for l in csv.split("\n") if l]
        assert lines[:1] == expected_header
        assert lines[1:] == expected_body


class TestGraphFactory:
    def test_namespace_uri_is_gitlab2prov(self):
        graph = operations.graph_factory()
        expected_uri = "http://github.com/dlr-sc/gitlab2prov/"
        assert graph.get_default_namespace().uri == expected_uri

    def test_init_wo_list_of_records(self):
        uri = "http://github.com/dlr-sc/gitlab2prov/"
        expected_graph = ProvDocument()
        expected_graph.set_default_namespace(uri)
        assert operations.graph_factory() == expected_graph

    def test_init_with_list_of_records(self):
        records = [
            ProvAgent(None, qualified_name(f"agent-id-{random_suffix()}")),
            ProvAgent(None, qualified_name(f"agent-id-{random_suffix()}")),
        ]
        expected_graph = ProvDocument(records)
        assert operations.graph_factory(records) == expected_graph


class TestCombine:
    def test_returns_empty_graph_when_run_wo_subgraphs(self):
        assert operations.combine(iter([])) == operations.graph_factory()

    def test_carries_over_all_records(self):
        agent1 = ProvAgent(None, qualified_name(f"agent-id-{random_suffix()}"))
        agent2 = ProvAgent(None, qualified_name(f"agent-id-{random_suffix()}"))
        graph1 = ProvDocument([agent1])
        graph2 = ProvDocument([agent2])
        subgraphs = [graph1, graph2]
        expected_graph = ProvDocument([agent1, agent2])
        assert operations.combine(iter(subgraphs)) == expected_graph


class TestDedupe:
    def test_removes_duplicate_elements(self):
        agent = ProvAgent(None, qualified_name(f"agent-id-{random_suffix()}"))
        graph = ProvDocument([agent, agent])
        expected_graph = ProvDocument([agent])
        assert list(graph.get_records(ProvAgent)) == [agent, agent]
        assert list(operations.dedupe(graph).get_records(ProvAgent)) == [agent]
        assert operations.dedupe(graph) == expected_graph

    def test_merges_attributes_of_duplicate_elements(self):
        id = qualified_name(f"agent-id-{random_suffix()}")
        graph = ProvDocument()
        graph.agent(id, {"attribute1": 1})
        graph.agent(id, {"attribute2": 2})
        expected_attributes = [
            (qualified_name("attribute1"), 1),
            (qualified_name("attribute2"), 2),
        ]
        agents = list(operations.dedupe(graph).get_records(ProvAgent))
        assert len(agents) == 1
        assert agents[0].attributes == expected_attributes

    def test_remove_duplicate_relations(self):
        graph = ProvDocument()
        agent = graph.agent(qualified_name(f"agent-id-{random_suffix()}"))
        entity = graph.entity(qualified_name(f"entity-id-{random_suffix()}"))
        r1 = graph.wasAttributedTo(entity, agent)
        r2 = graph.wasAttributedTo(entity, agent)
        assert list(graph.get_records(ProvRelation)) == [r1, r2]
        assert list(operations.dedupe(graph).get_records(ProvRelation)) == [r1]

    def test_merges_attributes_of_duplicate_relations(self):
        graph = ProvDocument()
        agent = graph.agent(qualified_name(f"agent-id-{random_suffix()}"))
        entity = graph.entity(qualified_name(f"entity-id-{random_suffix()}"))
        r1_attrs = [(qualified_name("attr"), "val1")]
        r2_attrs = [(qualified_name("attr"), "val2")]
        graph.wasAttributedTo(entity, agent, other_attributes=r1_attrs)
        graph.wasAttributedTo(entity, agent, other_attributes=r2_attrs)

        graph = operations.dedupe(graph)

        relations = list(graph.get_records(ProvRelation))
        assert len(relations) == 1
        expected_extra_attributes = set(
            [
                (qualified_name("attr"), "val1"),
                (qualified_name("attr"), "val2"),
            ]
        )
        assert set(relations[0].extra_attributes) == expected_extra_attributes


class TestUncoverDoubleAgents:
    def test_build_inverse_index(self):
        mapping = {"name": ["alias1", "alias2"]}
        expected_dict = {"alias1": "name", "alias2": "name"}
        assert operations.build_inverse_index(mapping) == expected_dict

    def test_uncover_name(self):
        names = {"alias": "name"}
        graph = operations.graph_factory()
        agent = graph.agent("agent-id", other_attributes={qualified_name("name"): "alias"})
        expected_name = (qualified_name("name"), "name")
        assert operations.uncover_name(agent, names) == expected_name

    def test_uncover_double_agents_resolves_agent_alias(self, mocker):
        d = {"alias1": "name", "alias2": "name"}
        mocker.patch("gitlab2prov.prov.operations.read_double_agent_mapping")
        mocker.patch("gitlab2prov.prov.operations.build_inverse_index", return_value=d)

        graph = operations.graph_factory()
        graph.agent("agent1", {"name": "alias2"})
        graph.agent("agent2", {"name": "alias1"})

        graph = operations.merge_double_agents(graph, "")

        agents = list(graph.get_records(ProvAgent))
        assert len(agents) == 1
        expected_name = "name"
        [(_, name)] = [(k, v) for k, v in agents[0].attributes if k.localpart == "name"]
        assert name == expected_name

    def test_uncover_double_agents_reroutes_relations(self, mocker):
        d = {"alias1": "name", "alias2": "name"}
        mocker.patch("gitlab2prov.prov.operations.read_double_agent_mapping")
        mocker.patch("gitlab2prov.prov.operations.build_inverse_index", return_value=d)

        graph = operations.graph_factory()
        a1 = graph.agent("agent1", {"name": "alias2"})
        a2 = graph.agent("agent2", {"name": "alias1"})
        e1 = graph.entity("entity1")
        e2 = graph.entity("entity2")
        e1.wasAttributedTo(a1)
        e2.wasAttributedTo(a2)

        graph = operations.merge_double_agents(graph, "")

        relations = list(graph.get_records(ProvRelation))
        assert len(relations) == 2
        expected_identifier = "User?name=name"
        assert all(
            relation.formal_attributes[1][1].localpart == expected_identifier
            for relation in relations
        )


class TestPseudonymize:
    def test_pseudonymize_changes_agent_name_and_identifier(self):
        graph = operations.graph_factory()
        name = f"agent-name-{random_suffix()}"
        email = f"agent-email-{random_suffix()}"
        graph.agent("agent1", {"name": name, "email": email})

        graph = operations.pseudonymize(graph)

        expected_name = hashlib.sha256(bytes(name, "utf-8")).hexdigest()
        expected_email = hashlib.sha256(bytes(email, "utf-8")).hexdigest()
        expected_identifier = qualified_name(f"User?name={expected_name}&email={expected_email}")

        agent = next(graph.get_records(ProvAgent))
        assert agent.identifier == expected_identifier
        assert list(agent.get_attribute("name"))[0] == expected_name
        assert list(agent.get_attribute("email"))[0] == expected_email

    def test_pseudonymize_deletes_non_name_attributes_apart_from_role_and_type(self):
        graph = operations.graph_factory()
        graph.agent(
            "agent1",
            {
                "name": f"agent-name-{random_suffix()}",
                "email": f"email-{random_suffix()}",
                "gitlab_username": f"gitlab-username-{random_suffix()}",
                "gitlab_id": f"gitlab-id-{random_suffix()}",
                PROV_ROLE: f"prov-role-{random_suffix()}",
                PROV_TYPE: f"prov-type-{random_suffix()}",
            },
        )

        graph = operations.pseudonymize(graph)

        agent = next(graph.get_records(ProvAgent))
        expected_attributes = [
            PROV_ROLE,
            PROV_TYPE,
            qualified_name("name"),
            qualified_name("email"),
        ]
        assert all([(attr in expected_attributes) for (attr, _) in agent.extra_attributes])
