# GraphRAG - Knowledge Graph API

GraphRAG is a FastAPI-based application that processes PDFs, extracts entities and relationships using OpenAI, and stores them in a Neo4j knowledge graph. The application also provides a Streamlit-based UI for querying the knowledge graph.

## Features
- Upload PDFs and extract entities and relationships.
- Store structured data in a Neo4j knowledge graph.
- Query the knowledge graph using natural language.
- Use OpenAI to enhance responses.
- Interactive Streamlit UI.

## Setup Instructions

### Prerequisites
- Docker installed
- Python 3.8+
- OpenAI API Key

### Step 1: Set Up Neo4j in Docker

Run the following command to start a Neo4j container:
```sh
docker run \
    --name neo4j \
    -p 7687:7687 -p 7474:7474 \
    -e NEO4J_AUTH=neo4j/password \
    -d neo4j
```
This will start Neo4j with the default credentials:
- **Username**: neo4j
- **Password**: password

You can access the Neo4j web interface at: [http://localhost:7474](http://localhost:7474)

### Step 2: Install Python Dependencies

Create a virtual environment and install the required dependencies:
```sh
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### Step 3: Set Environment Variables

Create a `.env` file or set environment variables:
```sh
export OPENAI_API_KEY="your-openai-api-key"
```

### Step 4: Run the FastAPI Backend

Start the FastAPI server:
```sh
uvicorn api2:app --host 0.0.0.0 --port 8000 --reload
```

### Step 5: Run the Streamlit UI

Launch the Streamlit application:
```sh
streamlit run app2.py
```

## API Endpoints

### Upload a PDF
```
POST /add_pdf
```
**Parameters:**
- `doc_id` (string) - A unique identifier for the document.
- `file` (PDF) - The document file.

### Query the Knowledge Graph
```
GET /query
```
**Parameters:**
- `query` (string) - The user query to search the knowledge graph.

## Usage
1. Upload a PDF using the Streamlit UI.
2. Query the knowledge graph using natural language.
3. View structured relationships stored in Neo4j.

## Notes
- Ensure Neo4j is running before using the application.
- Modify the `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD` in `api2.py` if needed.

## License
MIT License

