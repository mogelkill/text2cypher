import re
from pathlib import Path

import neo4j
from neo4j import GraphDatabase
from tqdm import tqdm

URI = "bolt://localhost:7687"
USER = ""
PASSWORD = ""


def modify_cypher_command(command):
    # Regular expression to find a label with a number at the end of the command
    match = re.search(r"SET n:([A-Za-z]+)(\d+);$", command)
    if match:
        # Extract the label and the number
        label = match.group(1)
        number = match.group(2)
        return f"CREATE (n:`UNIQUE IMPORT LABEL`{{`UNIQUE IMPORT ID`: row._id,`number`: {number}}}) SET n += row.properties SET n:{label};"
    else:
        # Return the original command if no label with number is found
        return command


if __name__ == "__main__":
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    scripts = Path("./scripts/CypherScript_XAI4Wind.txt").read_text(encoding="utf-8").split(";\n")
    with driver.session() as session:
        for command in tqdm(scripts):
            script = command.strip()
            if script:
                try:
                    if "CREATE" in script:
                        commands = script.split("CREATE")
                        create_command = f"CREATE {commands[1]};"
                        modified_create_command = modify_cypher_command(create_command)
                        full_command = commands[0] + modified_create_command
                        session.run(full_command)
                except Exception as e:
                    print(f"Error executing {script}")
                    print(e)
