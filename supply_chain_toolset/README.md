## Supply Chain Toolset on Cloud Run 

This directory contains a containerized, deployable toolset service designed to be used by AI agents. It acts as a specialized bridge between a *generative AI agent* and a *Neo4j pharmaceutical supply chain graph*.

This service exposes a set of HTTP-accessible tools that:
- Encapsulate complex Cypher queries
- Return structured JSON responses
- Are optimized for remote execution by AI agents (via MCPToolset)

💡 Tip:  You can deploy this toolset to Cloud Run (or any container platform) and build your own custom AI agent workflows on top of it.

### Overview

This service is a remote "toolkit" for an AI. Instead of teaching the AI the complexities of the Cypher query language and the database schema, we provide it with a simple, high-level set of tools. The AI can discover these tools and call them to answer sophisticated questions about the supply chain.

The service is built using FastAPI and is designed to be deployed as a scalable, serverless microservice on **Google Cloud Run**. This architecture ensures that the toolset is always available, secure, and can handle requests efficiently.

This follows the **Multi-Client Platform (MCP)** pattern, where a central service exposes its capabilities via a discovery endpoint (`/tools`), allowing multiple AI agents or clients to connect and leverage its functions.

### Available Tools

The service exposes the following endpoints that an agent can call:

*   **`trace_supply_path`**: Traces the full supply chain path for a given product, from the raw material supplier to the final distributor.
*   **`top_suppliers_by_product_count`**: Returns a ranked list of the most significant suppliers based on the number of distinct products they supply.
*   **`top_suppliers_for_product`**: For a specific product, identifies the key suppliers involved in its supply chain.
... more (check out https://supply-chain-toolset-373589861902.us-central1.run.app/tools for more info)

### Deployment to Google Cloud Run

This service is architected for easy deployment as a container on Google Cloud Run.

1.  **`Dockerfile`**: A complete `Dockerfile` is included to build a production-ready container image for the service.
2.  **`requirements.txt`**: This file lists all the necessary Python dependencies for the service.
3.  **`push.sh`**: This is a utility script to automate the process of building the container image and deploying it to your Google Cloud project.
    *   **Note:** You will need to configure this script with your specific GCP Project ID and desired Cloud Run service name.

### Configuration

The service connects to a Neo4j database and requires the following environment variables to be set in the Cloud Run deployment environment:
*   `NEO4J_URI`: The connection URI for the database.
*   `NEO4J_USER`: The database username.
*   `NEO4J_PASSWORD`: The database password.

It is highly recommended to manage these credentials using Google Secret Manager and integrate it with your Cloud Run service.