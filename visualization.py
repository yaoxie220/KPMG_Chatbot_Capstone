from neo4j import GraphDatabase
import pandas as pd
import numpy as np

class Count_Visualizaiton:
    def __init__(self, url, username, password):
        """Initialize the connection to the Neo4j database."""
        self.driver = GraphDatabase.driver(url, auth=(username, password))

    def close(self):
        """Close the Neo4j database connection."""
        self.driver.close()

    def count_entities(self):
        """Count entities in the database."""
        queries = [
            "MATCH (n:report) RETURN COUNT(n) as reports",
            "MATCH (n:section) RETURN COUNT(n) as sections",
            "MATCH (n:field) RETURN COUNT(n) as fields",
            "MATCH (n:database) RETURN COUNT(n) as databases",
            "MATCH (n:table) RETURN COUNT(n) as tables",
            "MATCH (n:column) RETURN COUNT(n) as columns",
            "MATCH (n:model) RETURN COUNT(n) as models"
        ]
        
        results = {}
        with self.driver.session() as session:
            for query in queries:
                result = session.run(query)
                records = result.single()
                for key, value in records.items():
                    results[key] = value
        return results
