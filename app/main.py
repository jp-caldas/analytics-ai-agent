from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from .graph import app_graph

load_dotenv()

app = FastAPI()

class QueryRequest(BaseModel):
    question: str

@app.post("/v1/chat-ga4")
async def process_query(request: QueryRequest):
    """ 
    Process user question and interact with LangGraph for SQL generation
    """
    state = {
        'input_query': request.question,
        'generated_sql': None,
        'error_message': '',
        'execution_success': False,
        'iterations': 0,
        'query_results': None,
    }
    
    result = app_graph.invoke(state)
    
    return {
        "status": "Success" if result['execution_success'] else "Failure",
        "generated_sql": result['generated_sql'],
        "data": result['query_results'],
        "error": result['error_message']
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)