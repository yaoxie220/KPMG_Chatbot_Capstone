from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from openai import OpenAI
from langchain_openai import ChatOpenAI
from neo4j.exceptions import CypherSyntaxError, CypherTypeError, ClientError


graph = Neo4jGraph(
    url="neo4j+s://31bcfbcc.databases.neo4j.io:7687", username="neo4j", password="PgZVTMTY_FCNOwA8Y0JnrJtORAEC2uZt4ky6Z2D8nH8"
)

graph.refresh_schema()

chain = GraphCypherQAChain.from_llm(
    llm = ChatOpenAI(temperature=0, api_key="sk-proj-6bQ6nkTnvoydpZAGVEgpT3BlbkFJGMXuEvymfqJFrZvzNYOc"), graph=graph, verbose=False,
    model="gpt-3.5-turbo"
)
    
def test(message):
    try:
        # print(message)
        res = chain.invoke(message)
        res = res['result']
    except (ValueError, CypherTypeError):
        res = "I cannot provide an answer to the question"
    return res         
