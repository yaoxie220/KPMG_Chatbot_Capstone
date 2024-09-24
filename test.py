from kpmg_chatbot_v6 import Chat

class Test:
    def test(question):
        result = Chat("neo4j+s://bed4a8a0.databases.neo4j.io", user="neo4j", password="XbfIA4FEeKePbNnhGT2YtqQ8zqPCcSR7XYYMQbbb70I").__call__(question)
        return result