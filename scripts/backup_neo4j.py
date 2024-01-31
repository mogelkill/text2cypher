from pathlib import Path

import neo4j

client = neo4j.GraphDatabase.driver("bolt://localhost:7687", auth=("", ""))

# execute a query that returns a json
result = client.session().run("CALL apoc.export.json.all(null,{stream: true})").data()


backup_file = Path("neo4j_backup.jsonl")
backup_file.write_text(result[0]["data"])
