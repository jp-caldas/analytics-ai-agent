import os
from typing import TypedDict, Literal
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from google.cloud import bigquery

from .context import GA4_CONTEXT

load_dotenv()

class GraphState(TypedDict):
    input_query: str
    generated_sql: str
    error_message: str
    execution_success: bool
    iterations: int
    query_results: list

llm = ChatOpenAI(model='gpt-4o', temperature=0)
bq_client = bigquery.Client()

def generate_sql(state: GraphState) -> dict:
    prompt = (
        f"User question: {state['input_query']}\n"
        f"{GA4_CONTEXT}\n"
        "Return ONLY the SQL query, with no explanation, no markdown, no code fences.\n"
    )
    if state.get('error_message'):
        prompt += f"Previous error: {state['error_message']}\nFix the SQL query accordingly.\n"

    response = llm.invoke(prompt)
    sql = response.content.strip()
    sql = sql.removeprefix("```sql").removeprefix("```").removesuffix("```")
    sql = sql.strip()

    return {
        'generated_sql': sql,
        'iterations': state.get('iterations', 0) + 1,
        'error_message': '',
    }

def execute_sql(state: GraphState) -> dict:
    try:
        job_config = bigquery.QueryJobConfig(dry_run=True)
        bq_client.query(state['generated_sql'], job_config=job_config, location='US')

        query_job = bq_client.query(state['generated_sql'], location='US')
        results = [dict(row) for row in query_job.result(max_results=100)]
        return {
            'execution_success': True,
            'query_results': results,
            'error_message': '',
        }
    except Exception as e:
        return {
            'execution_success': False,
            'error_message': str(e),
        }

def should_retry(state: GraphState) -> Literal["retry", "stop"]:
    if state['execution_success'] or state['iterations'] >= 3:
        return "stop"
    return "retry"

builder = StateGraph(GraphState)
builder.add_node("generate_sql", generate_sql)
builder.add_node("execute_sql", execute_sql)
builder.add_edge("__start__", "generate_sql")
builder.add_edge("generate_sql", "execute_sql")
builder.add_conditional_edges("execute_sql", should_retry, {
    "retry": "generate_sql",
    "stop": END,
})

app_graph = builder.compile()
