import argparse
import ast
import json
import os
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple, Union

import pandas as pd
from neo4j import GraphDatabase
from tqdm import tqdm

file = Path(__file__).resolve()
parent = file.parent
clevr_dir = parent / "clevr-graph"

sys.path.append(str(clevr_dir))

# Monkey Patch Gibberish
import gqa.generate_graph
from gibberish import Gibberish
from gql.graph_builder import GraphBuilder

gibberish = Gibberish()
gqa.generate_graph.gibberish = gibberish

from gqa.generate_graph import GraphGenerator, GraphSpec
from gqa.questions import QuestionForm, question_forms

NeoTypes = Union[int, float, str]


@dataclass
class GraphArgs:
    tiny: bool = False
    small: bool = False
    int_names: bool = False


@dataclass
class QuestionGenerationArgs:
    generate_cypher: bool = True


def quote(x: str):
    return f'"{x}"'


def cypherparse(x: Any):
    if isinstance(x, str):
        try:
            parsed = ast.literal_eval(x)
        except:
            return x
        x = parsed

    if isinstance(x, NeoTypes.__args__):
        return x
    else:
        print("WARNING: unsupported type", x, str(x))
        return str(x)


def cypherencode(v: NeoTypes):
    return quote(v) if isinstance(v, str) else v


def CONST_LABEL(label: str) -> Callable[[Dict[str, Any]], List[str]]:
    result = [label]

    def label_fn(entity: Dict[str, Any]):
        return result

    return label_fn


def ALL_PROPERTIES(entity: Dict[str, Any]) -> Dict[str, NeoTypes]:
    return {k: cypherparse(v) for k, v in entity.items()}


def FROM_TO(from_property: str, to_property: str) -> Callable[[Dict[str, Any]], Tuple[NeoTypes, NeoTypes]]:
    def route_fn(entity: Dict[str, Any]):
        return cypherparse(entity[from_property]), cypherparse(entity[to_property])

    return route_fn


def generate_node_inserts(graphSpec: GraphSpec):
    node_label_fn = CONST_LABEL("STATION")
    node_prop_fn = ALL_PROPERTIES
    for key, node in graphSpec.nodes.items():
        labels = node_label_fn(node)
        props = node_prop_fn(node.state)

        props = ", ".join(f"{k}: {quote(v) if isinstance(v, str) else v}" for k, v in props.items())
        template = f"CREATE (n:{':'.join(labels)} {{ {props} }})"
        yield template

    for key, line in graphSpec.lines.items():
        props = node_prop_fn(line.state)
        props = ", ".join(f"{k}: {quote(v) if isinstance(v, str) else v}" for k, v in props.items())
        template = f"CREATE (n:LINE {{ {props} }})"
        yield template


def generate_edge_inserts(graphSpec: GraphSpec):
    edge_label_fn = CONST_LABEL("EDGE")
    edge_prop_fn = ALL_PROPERTIES
    edge_route_fn = FROM_TO("station1", "station2")
    for edge in graphSpec.edges:
        labels = edge_label_fn(edge)
        assert len(labels) > 0, "edges must have at least one label"
        props = edge_prop_fn(edge.state)
        props = ", ".join(f"{k}: {cypherencode(v)}" for k, v in props.items())
        from_id, to_id = edge_route_fn(edge)

        template = (
            f"MATCH (from),(to) "
            f"WHERE from.id = {cypherencode(from_id)} "
            f"and to.id = {cypherencode(to_id)} "
            f"CREATE (from)-[l:{':'.join(labels)} {{ {props} }}]->(to)"
        )

        yield template


def nuke_neo(session):
    session.execute_write(lambda tx: tx.run("MATCH ()-[r]-() delete r"))
    session.execute_write(lambda tx: tx.run("MATCH (n) delete n"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a CLEVR graph and save it into a provided Neo4j Database")
    parser.add_argument("--neo4j_uri", type=str, default="bolt://localhost:7687", help="Neo4j URI")
    parser.add_argument("--neo4j_user", type=str, default="", help="Neo4j user")
    parser.add_argument("--neo4j_password", type=str, default="", help="Neo4j password")

    args = parser.parse_args()

    generator = GraphGenerator(GraphArgs())
    generator = generator.generate()

    driver = GraphDatabase.driver(args.neo4j_uri, auth=(args.neo4j_user, args.neo4j_password))
    node_inserts = list(generate_node_inserts(generator.graph_spec))
    edge_inserts = list(generate_edge_inserts(generator.graph_spec))

    total_inserts = node_inserts + edge_inserts

    nuke_neo(driver.session())
    for insert_statement in tqdm(total_inserts, desc="Inserting nodes and edges"):
        driver.session().execute_write(lambda tx: tx.run(insert_statement))

    cycle_template = next((x for x in question_forms if x.type_string == "HasCycle"), None)
    distinct_template = next((x for x in question_forms if x.type_string == "DistinctRoutes"), None)  #
    question_forms.remove(cycle_template)
    question_forms.remove(distinct_template)

    def get_random_question_template() -> QuestionForm:
        return random.choice(question_forms)

    g = generator.graph_spec
    questions = []
    for i in (bar := tqdm(range(10000), desc="Generating questions")):
        try:
            question_template = get_random_question_template()
            question, answer = question_template.generate(g, QuestionGenerationArgs())
            if question.cypher is None:
                continue
            payload = {
                "question": question.english,
                "cypher": question.cypher,
                "group": question.group,
                "answer": answer,
            }
            questions.append(json.dumps(payload))
        except Exception:
            pass

    with open("questions.jsonl", "w") as file:
        file.write("\n".join(questions))
    
