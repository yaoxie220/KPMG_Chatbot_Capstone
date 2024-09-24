from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI

graph = Neo4jGraph(
    url="neo4j+s://9014d857.databases.neo4j.io", username="neo4j", password="RYYNymC3Bug5n9Il-ke_RPAHKkIQNlP5zujB-B8H8w8"
)

graph.refresh_schema()

chain = GraphCypherQAChain.from_llm(
    llm = ChatOpenAI(temperature=0, api_key="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"), graph=graph, verbose=False,
    model="gpt-3.5-turbo"
)
    
def test(message):
    try:
        res = chain.invoke(message)
        res = res['result']
    except ValueError:
        res = "I cannot provide an answer to the question"
    return res         
