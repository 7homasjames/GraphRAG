from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase
import openai
import os
import pdfplumber
import json
import re
from pydantic import BaseModel

class Document(BaseModel):
    doc_id: str
    content: str

# Load OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Please set the OPENAI_API_KEY in your environment variables.")

# Neo4j Connection
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

db = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def extract_entities(text):
    """Use OpenAI to extract structured entities and relationships from text."""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Extract entities and their relationships from the text. Return the output in strict JSON format."},
            {"role": "user", "content": f"Extract entities and relationships from: {text}. Format it as JSON: {'{'}'entities': ['Entity1', 'Entity2'], 'relationships': [['Entity1', 'Relation', 'Entity2'], ...] {'}'}"}
        ]
    )
    try:
        data = json.loads(response.choices[0].message.content)
        return data
    except json.JSONDecodeError:
        print("Error: OpenAI response is not valid JSON.")
        return {"entities": [], "relationships": []}

def add_to_graph(tx, entity1, relation, entity2):
    """Ensure nodes have 'name' property and store structured relationships."""
    query = """
    MERGE (a:Entity {name: $entity1})
    ON CREATE SET a.name = $entity1

    MERGE (b:Entity {name: $entity2})
    ON CREATE SET b.name = $entity2

    MERGE (a)-[:RELATION {type: $relation}]->(b)
    """
    tx.run(query, {"entity1": entity1, "relation": relation, "entity2": entity2})

@app.post("/add_pdf")
async def add_pdf(doc_id: str = Form(...), file: UploadFile = File(...)):
    """Accepts a PDF file, extracts text, and processes it for entity extraction."""
    try:
        with pdfplumber.open(file.file) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        print("1:", text)

        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF.")

        extracted_data = extract_entities(text)
        print("2:", extracted_data)

        if not extracted_data["relationships"]:
            return {"message": "No relationships extracted."}

        with db.session() as session:
            for entity1, relation, entity2 in extracted_data["relationships"]:
                print("3:", entity1, relation, entity2)
                session.write_transaction(add_to_graph, entity1.strip(), relation.strip(), entity2.strip())

        return {"message": "Entities and relationships added from PDF successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def preprocess_query(query):
    """Extracts important keywords from the user query before searching Neo4j."""
    query = query.lower()
    query = re.sub(r'\b(what|is|who|are|the|a|an|of|in|on|for|to|by|with|about|how|does|do|explain)\b', '', query)
    return query.strip()

@app.get("/query")
def query_graph(query: str):
    """Search Neo4j for related entities and use OpenAI to generate a response."""
    processed_query = preprocess_query(query)  # Extract main keyword(s)
    print("Processed Query:", processed_query)  # Debugging

    cypher_query = """
    MATCH (a)-[r]->(b)
    WHERE toLower(coalesce(a.name, '')) =~ '.*' + toLower($query) + '.*' 
       OR toLower(coalesce(b.name, '')) =~ '.*' + toLower($query) + '.*'
    RETURN coalesce(a.name, 'Unknown') AS entity1, 
           type(r) AS relation, 
           coalesce(b.name, 'Unknown') AS entity2
    LIMIT 5;
    """

    with db.session() as session:
        results = session.run(cypher_query, {"query": processed_query})
        records = list(results)  # Convert Result object into a list

        print("Query Records:", records)  # Debugging print

        knowledge = [{"entity1": row["entity1"], "relation": row["relation"], "entity2": row["entity2"]} for row in records]
    
    if not knowledge:
        return {"response": "No relevant information found in the knowledge graph."}

    # Format knowledge for GPT-4 reasoning
    context = "\n".join([f"{k['entity1']} -> ({k['relation']}) -> {k['entity2']}" for k in knowledge])

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an AI assistant using a knowledge graph."},
            {"role": "user", "content": f"Based on this knowledge:\n{context}\n\nAnswer this question: {query}"}
        ]
    )

    return {"response": response.choices[0].message.content}