from typing import Any, Optional

from neo4j import READ_ACCESS, GraphDatabase, unit_of_work

from .base import DataBaseAdapter

NODE_PROPERTIES_QUERY = """
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE NOT type = "RELATIONSHIP" AND elementType = "node"
WITH label AS nodeLabels, collect({property:property, type:type}) AS properties
RETURN {labels: nodeLabels, properties: properties} AS output

"""

REL_PROPERTIES_QUERY = """
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE NOT type = "RELATIONSHIP" AND elementType = "relationship"
WITH label AS nodeLabels, collect({property:property, type:type}) AS properties
RETURN {type: nodeLabels, properties: properties} AS output
"""

REL_QUERY = """
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE type = "RELATIONSHIP" AND elementType = "node"
UNWIND other AS other_node
RETURN "(:" + label + ")-[:" + property + "]->(:" + toString(other_node) + ")" AS output
"""


class Neo4jAdapter(DataBaseAdapter):
    """Neo4j adapter for Database operations"""

    def __init__(self, uri: str, user: str, password: str, few_shots: Optional[str] = None, query_timeout: int = 10):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.schema = None
        self.few_shots = few_shots
        self.query_timeout = query_timeout

    def connect(self) -> DataBaseAdapter:
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.driver.verify_connectivity()
        self.is_connected = True
        return self

    def disconnect(self) -> DataBaseAdapter:
        self.driver.close()
        self.is_connected = False
        self.driver = None
        return self

    def _wrap_query(self, query: str):
        millis = self.query_timeout * 1000
        return f"CALL apoc.cypher.runTimeboxed(\"{query}\",{'{}'}, {millis})"

    def execute(self, query: str) -> list[dict[str, Any]]:
        result_list = []

        @unit_of_work(timeout=self.query_timeout)
        def transaction(tx):
            return list(tx.run(query))

        with self.driver.session(default_access_mode=READ_ACCESS) as session:
            results = session.execute_read(transaction)
            for result in results:
                result_list.append(result.data())
            return result_list

    def build_prompt(self, question: str) -> str:
        schema = self.get_schema()
        prompt = f"""Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Schema:
{schema}
"""
        if self.few_shots is not None:
            prompt += f"""Hint: You can use the following queries as examples:
{self.few_shots}"""

        prompt += f"""
Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.

The question is:
{question}"""

        return prompt

    def get_schema(self) -> str:
        if self.schema is None:
            node_properties = self.execute(NODE_PROPERTIES_QUERY)
            relationships_properties = self.execute(REL_PROPERTIES_QUERY)
            relationships = self.execute(REL_QUERY)

            self.schema = f"""
            Node properties are the following:
            {[el['output'] for el in node_properties]}
            Relationship properties are the following:
            {[el['output'] for el in relationships_properties]}
            The relationships are the following:
            {[el['output'] for el in relationships]}
            """

        return self.schema

    def build_error_prompt(self, question: str, error_message: str, query: str) -> str:
        schema = self.get_schema()
        prompt = f"""Task:Fix this Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Schema:
{schema}
"""
        if self.few_shots is not None:
            prompt += f"""Hint: You can use the following queries as examples:
{self.few_shots}"""

        prompt += f"""Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.

The question that should be answered is:
{question}

The generated Cypher statement is:
`{query}`

The error message is:
`{error_message}`
"""

        return prompt
