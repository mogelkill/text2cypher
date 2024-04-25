# Text2Cypher

Text2Cypher provides a natural language interface for generating Cypher query language (CQL) statements for Neo4j databases, based on a specified database schema.

## Setup Instructions

Follow these steps to set up the Text2Cypher service:

1. **Environment Configuration**: Copy the contents from [`.example_env`](.example_env) into a new file named `.env`. Insert your OpenAI API key into this file to enable the API integration.
2. **Service Deployment**: Use Docker Compose to build and start the service by running the following commands in your terminal:

   ```bash
   docker compose build && docker compose up
   ```

3. **Accessing the Interface**: After the service starts, open your web browser and go to [localhost:7860](http://localhost:7860) to interact with the Chat UI.

## Evaluation

For an overview of the system's performance, refer to the [Evaluation Notebook](Evaluation.ipynb). This notebook provides a basic evaluation of the query generation capabilities of Text2Cypher.