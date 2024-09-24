from openai import OpenAI
from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain_community.graphs import Neo4jGraph
from typing import Dict, List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from neo4j import GraphDatabase
from neo4j.exceptions import CypherSyntaxError, CypherTypeError, ClientError
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
from prompts import node_properties_query, rel_properties_query, rel_query, schema_text
from prompts import CLASSIFICATION_PROMPT, CHITCHAT_PROMPT, INTRODUCTION_PROMPT, LAYER_ONE_PROMPT, LAYER_TWO_PROMPT, QA_PROMPT


import warnings
warnings.filterwarnings("ignore")

class Tool:
    
    def __init__(self):
        self.api = "sk-proj-6bQ6nkTnvoydpZAGVEgpT3BlbkFJGMXuEvymfqJFrZvzNYOc"   
    def reset(self):
        pass 

class Classification(Tool):
    
    def __init__(self):
        super().__init__()
        self.prompts = [CLASSIFICATION_PROMPT]
        self.chat_clas = ChatOpenAI(api_key=self.api, temperature=0)

    def _classification(self, question):
        messages = [SystemMessage(content=self.prompts[0])]
        messages.extend([HumanMessage(question)])
        response = self.chat_clas.invoke(messages)
        classified_tool = response.dict()['content']
        return classified_tool 


class ExtractionTool(Tool):
    
    def __init__(self, url, user, password):
        super().__init__()
        self.driver = GraphDatabase.driver(url, auth=(user, password))
        self.client = OpenAI(api_key=self.api)
        self.graphDB = Neo4jGraph(url, user, password)
        self.cypherGenerator = CypherGenerator(self)
        self.num_back_forth = 0
        self.bf_threshold = 3
        self.retry = True
        self.keep_history = False
        self.res = ""
        self.generated_cypher = ""
        self.generate_schema()
        self.is_guardrail = True
        self.synonyms_mapping = {
            "input_columns": ["predictors", "features", "independent variables", "explanatory variables", "input variables", "inputs"],
            "output_columns": ["dependent variable", "response variable", "target variable", "target", "label"],
            "author": ["creator", "collaborator", "owner", "developer", "writer"]
        }
    
    def generate_schema(self):
        self.node_props = self.query_schema(node_properties_query)
        self.rel_props = self.query_schema(rel_properties_query)
        self.rels = self.query_schema(rel_query)
        self.schema = schema_text(self.node_props, self.rel_props, self.rels)
     
    def system_message(self):
        text = f"""
        Schema of the database:
        {self.schema}
        Note: Do not include any explanations or apologies in your responses.
        """
        return text
    
    def normalize_question(self, question):
        # Convert question to lowercase to handle case-insensitivity
        question_lower = question
        # Replace synonyms with their canonical forms
        for canonical, synonyms in self.synonyms_mapping.items():
            for synonym in synonyms:
                if synonym in question_lower:
                    question_lower = question_lower.replace(synonym, canonical)
        return question_lower

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
        normalized_question = self.normalize_question(question)
        if not self.keep_history:
            self.messages = [
                SystemMessage(self.system_message()),
                HumanMessage(normalized_question)
            ] 
            self.question = normalized_question 
        cypher = self.cypherGenerator(self.messages)
        return cypher   

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
                    [
                        SystemMessage(self.generated_cypher),
                        HumanMessage(f"""This query returns an error: {str(e)}
                        Give me an improved query that works without any explanation or apologies""")
                    ]
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
        self.question = ""
        self.is_guardrail = True
        
    def add_info(self, info):
        self.messages.append(HumanMessage(info))
        
class AnsSmoother(Tool):
    
    def __init__(self):
        super().__init__()
        self.chat = ChatOpenAI(api_key=self.api, temperature=0)
        
    def __call__(self, question, answer):
        return self.generateAns(question, answer)
        
    def generateAns(self, question, answer):
        if answer == "Sorry. I can not find any relevant information.":
            return answer
        message = {"question": question, "answer": answer}
        human_prompt_template = PromptTemplate.from_template(
        template= "The original question is {question}, the result is {answer}")

        human_prompt = human_prompt_template.format(
            question =  message["question"], 
            answer = message["answer"]
        )

        messages = [
            SystemMessage(
                content=QA_PROMPT
            ),
            HumanMessage(
                content=human_prompt
            )]
        
        response = self.chat.invoke(messages)
        content = response.dict()['content']
        return content           

class AnsJudgeTool(Tool):
    
    def __init__(self):
        super().__init__()
        
class ChatSummarizeTool(Tool):
    
    def __init__(self):
        super().__init__()
        
class IntroductionTool(Tool):
    
    def __init__(self):
        super().__init__()
        self.prompts = [INTRODUCTION_PROMPT]
        self.chat_intro = ChatOpenAI(api_key=self.api, temperature=0)
        self.messages = None
    def intro(self, question):
        messages = [SystemMessage(content=self.prompts[0])]
        messages.extend([HumanMessage(question)])
        self.messages = HumanMessage(question)
        response = self.chat_intro.invoke(messages)
        content = response.dict()['content']
        return content

class ChitChatTool(Tool):
    
    def __init__(self):
        super().__init__()
        self.prompts = [CHITCHAT_PROMPT]
        self.chat_chit = ChatOpenAI(api_key=self.api, temperature=0)
        self.messages = None

    def chit(self, question):
        messages = [SystemMessage(content=self.prompts[0])]
        messages.extend([HumanMessage(question)])
        self.messages = HumanMessage(question)
        response = self.chat_chit.invoke(messages)
        content = response.dict()['content']
        return content



class Chat:
    
    def __init__(self, url, user, password):
        self.exTool = ExtractionTool(url, user, password)
        self.intTool = IntroductionTool()
        self.chatTool = ChitChatTool()
        self.ansJugTool = AnsJudgeTool()
        self.chatSumTool = ChatSummarizeTool()
        self.ansSmoother = AnsSmoother()
        
        self.messages = None
        self.Tool = {}
        self.chat_end = True
        # self.guardrail = Guardrail()

    def __call__(self, question):

        classified_tool = Classification()._classification(question)
        print("classification tool", classified_tool)
        self.type = classified_tool
        if classified_tool == "ExtractionTool":
            result = self.exTool.extract(question)
            self.Tool["question"] = self.exTool
            self.messages = self.exTool.messages

        elif classified_tool == "IntroductionTool":
            result = self.intTool.intro(question)
            self.Tool["question"] = self.intTool
            self.messages = self.intTool.messages

        elif classified_tool == "ChitChatTool":
            result = self.chatTool.chit(question)
            self.Tool["question"] = self.intTool
            self.messages = self.chatTool.messages
        return result
 

class CypherGenerator(Tool):
    
    def __init__(self, exTool: ExtractionTool):
        super().__init__()
        self.prompts = [LAYER_ONE_PROMPT, LAYER_TWO_PROMPT]
        self.chat1 = ChatOpenAI(api_key=self.api, temperature=0)
        self.chat2 = ChatOpenAI(api_key=self.api, temperature=0)
        self.graphDB = exTool.graphDB   
        self.exTool = exTool
        
    def __call__(self, message_input):
        return self.getCypher(message_input)
    
    def _distillation(self, message):
        messages = [SystemMessage(content=self.prompts[0])]
        messages.extend(message)
        response = self.chat1.invoke(messages)
        content = response.dict()['content']
        print("content", content)
        return content      

            
    def _queryGeneration(self, message):
        messages = [SystemMessage(content=self.prompts[1])]
        messages.extend(message)
        response = self.chat2.invoke(messages)
        content = response.dict()['content']
        return content 

    #! Modify
    def getCypher(self, message):
        user_requirement = message.copy()
        response = self._distillation(user_requirement)
        
        updatemessage = "User Requirement:" + str(self.exTool.question) + "\n" + "Query Logic Extraction:" + str(response)
        updatemessage = [HumanMessage(updatemessage)]
        query = self._queryGeneration(updatemessage) 
        print("query", query)
        return query