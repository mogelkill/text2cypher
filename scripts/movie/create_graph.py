import argparse
from pathlib import Path

from neo4j import GraphDatabase


def nuke_neo(session):
    session.execute_write(lambda tx: tx.run("MATCH ()-[r]-() delete r"))
    session.execute_write(lambda tx: tx.run("MATCH (n) delete n"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a movie graph and save it into a provided Neo4j Database")
    parser.add_argument("--neo4j_uri", type=str, default="bolt://localhost:7688", help="Neo4j URI")
    parser.add_argument("--neo4j_user", type=str, default="", help="Neo4j user")
    parser.add_argument("--neo4j_password", type=str, default="", help="Neo4j password")

    args = parser.parse_args()

    driver = GraphDatabase.driver(args.neo4j_uri, auth=(args.neo4j_user, args.neo4j_password))
    nuke_neo(driver.session())
    parent = Path(__file__).parent
    statement_file = parent / "statements.txt"
    with open(statement_file) as file:
        statements = file.read()
        driver.session().execute_write(lambda tx: tx.run(statements))
