import settings
from openai import OpenAI
from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from typing import Dict, List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from neo4j import GraphDatabase
from neo4j.exceptions import CypherSyntaxError, CypherTypeError, ClientError

class ExtractionTool:
    
    def __init__(self, url, user, password):
        self.driver = GraphDatabase.driver(url, auth=(user, password))
        self.client = OpenAI(api_key="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")
        self.num_back_forth = 0
        self.bf_threshold = 3
        self.retry = True
        self.keep_history = False
        self.res = ""
        self.generated_cypher = ""
        self.generate_schema()
    
    def generate_schema(self):
        self.node_props = self.query_schema(settings.node_properties_query)
        self.rel_props = self.query_schema(settings.rel_properties_query)
        self.rels = self.query_schema(settings.rel_query)
        self.schema = settings.schema_text(self.node_props, self.rel_props, self.rels)
        
    def system_message(self):
        return f"""
        Task: Generate Cypher queries to query a Neo4j graph database based on the provided schema definition.
        Instructions:
        Use only the provided relationship types and properties.
        Do not use any other relationship types or properties that are not provided.
        If you cannot generate a Cypher statement based on the provided schema, explain the reason to the user.
        Schema:
        {self.schema}

        Note: Do not include any explanations or apologies in your responses.
        """
        
    def query_schema(self, query):
        def execute_query(tx):
            result = tx.run(query)
            return [record["output"] for record in result]
        with self.driver.session() as session:
            results = session.execute_write(execute_query)
        return results
    
    def query_database(self, neo4j_query, params={}):
        with self.driver.session() as session:
            result = session.execute_write(self._execute_query, neo4j_query, params)
            return [r.data() for r in result]  
        
    @staticmethod  
    def _execute_query(tx, neo4j_query, params):
        # Function to execute the query
        result = tx.run(neo4j_query, **params)
        return [record for record in result]  
    
    def get_cypher(self, question):
        if not self.keep_history:
            self.messages = [
                {"role": "system", "content": self.system_message()},
                {"role": "user", "content": question}
            ]  
        
        completion = self.client.chat.completions.create(model="gpt-3.5-turbo", messages=self.messages)
        return completion.choices[0].message.content
    
    def extract(self, question):
        self.generated_cypher = self.get_cypher(question)
        try:
            res = self.query_database(self.generated_cypher)
            if not res:
                self.num_back_forth += 1
                if self.num_back_forth <= self.bf_threshold:
                    self.keep_history = True
                    return 
                else:
                    self.res = "Sorry. I can not find any relevant information."
                    return self.res
            self.res = res
            return self.res                 
        except (CypherSyntaxError, ValueError, CypherTypeError, ClientError) as e:
            if self.retry:
                self.messages.extend(
                    [{"role": "assistant", "content": self.generated_cypher},
                     {"role": "user",
                      "content": f"""This query returns an error: {str(e)}
                      Give me an improved query that works without any explanation or apologies"""}]
                )
                self.retry = False
                self.keep_history = True
                return self.extract(question)
            elif not self.retry:
                self.num_back_forth += 1
                if self.num_back_forth <= self.bf_threshold:
                    self.keep_history = True
                    return 
                else:
                    self.res = "Sorry. I can not find any relevant information."
                    return self.res
        
    def reset(self):
        self.num_back_forth = 0
        self.retry = True
        self.keep_history = False
        self.start = True
        self.conv = None
        self.res = ""
        self.generated_cypher = ""
        
    def add_info(self, info):
        self.messages.append({"role": "user", "content": info})  

          
            


