# KPMG Model Metadata Chatbot with GenAI

## Project Overview
The **KPMG Capstone Project** aimed to develop an AI-powered chatbot using **Generative AI (GenAI)** technology to enhance the management of **model metadata**. The core goal of this initiative was to streamline and optimize **model risk management** and increase the **observability** of models in KPMG's operational landscape.

The chatbot provides a user-friendly interface to interact with and retrieve model metadata from a back-end **Neo4j graph database**. By leveraging **LangChain** and **OpenAI's GPT-3** for natural language processing and query generation, the chatbot efficiently responds to complex user queries, offering insights into the intricate relationships between models and metadata.

The project focused on building a tool that could manage metadata seamlessly, helping data scientists, analysts, engineers, and managers access critical information. With a structured **classification layer** to categorize user queries, the chatbot supports a wide range of use cases, from simple extractions to complex data analysis tasks. The project demonstrates the potential to significantly improve decision-making, increase efficiency, and reduce operational risks within KPMG's business processes.

## Tools Used

- **Neo4j**: A graph database management system used to store and manage the complex relationships between models, reports, and metadata.
   
- **Cypher**: The query language for Neo4j, used to query the graph database and retrieve metadata.

- **LangChain**: Used to integrate the conversational capabilities of GPT with Neo4j, allowing the chatbot to intelligently interact with the graph database.

- **OpenAI GPT-3**: Provides the natural language processing capabilities for understanding and responding to user queries with contextually accurate answers.

- **Streamlit**: A web framework used to build the user interface for the chatbot, enabling users to interact with the system and visualize responses.

- **Python**: The primary programming language used to develop the chatbot's functionalities, integrate the various tools, and manage data processing.

- **Mock Data Generation**: Synthetic data was created to simulate KPMG’s internal metadata, enabling the chatbot to handle data without using proprietary information.
