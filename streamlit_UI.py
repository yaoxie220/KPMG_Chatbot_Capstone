import streamlit as st 
import pandas as pd 
import altair as alt
from kpmg_chatbot_v6 import Chat
from visualization import Count_Visualizaiton
#? Base case comparison
from basecase import test   

import warnings
warnings.filterwarnings("ignore") 

col1, col2, col3 = st.columns([1, 1, 3])
with col1:
    st.image("img/kpmg_logo.png", width=100)
with col2:
    st.image("img/dsi_logo.jpg", width=200)

st.title("KPMG Chatbot")

st.markdown("""
        This chatbot helps you understand the relationships among KPMG's internal reports, models, and databases. Please begin by reviewing the visualizations on the graph database and the instructions for prompts.
    """)

CVisualTool = Count_Visualizaiton("neo4j+s://31bcfbcc.databases.neo4j.io:7687", "neo4j", "PgZVTMTY_FCNOwA8Y0JnrJtORAEC2uZt4ky6Z2D8nH8")
counts = CVisualTool.count_entities()
data_df = pd.DataFrame(list(counts.items()), columns=['Entity', 'Count'])
chart = alt.Chart(data_df).mark_bar().encode(
    x=alt.X('Entity:N', title='Entity Types'),
    y=alt.Y('Count:Q', title='Counts'),
    color=alt.Color('Entity:N', legend=alt.Legend(title="Entity Types"))
).properties(
    title='Counts of Different Entity Types in Neo4j Database'
).interactive()

with st.expander("Visualizations on the Graph Database"):
    st.markdown("""
        **Graph Database:**

        The schema of the dashboard is organized as follows: report -> section -> field -> model -> column -> table -> database.
        
        **Overview of the Graph Database**
    """)
    st.image("img/GraphDatabase_Overall.jpg")
    st.markdown("""
        **Example Flow**
    """)
    st.image("img/GeneralFlow.jpg")
    st.altair_chart(chart, use_container_width=True)

with st.expander("Instructions on Prompts"):
    st.markdown("""
        **Sample Prompts:**
                    
        - Use Case 1: Simple Extraction (one entity)

            e.g. What are the performance metrics of the model named model_925814632?
        - Use Case 2: Simple Extraction (two or more entities)

            e.g. Who are the authors of models model_701015292, model_701015291, and model_925814632?
        - Use Case 3: Complex Extraction with if condition

            e.g. How many models in the field of Real GDP Recovery have an accuracy greater than 0.9?
        - Use Case 4: Finding Relationships

            e.g. Which tables has the report named "Saudi Arabia Budget Report 2024" employed?
        - Use Case 5: Yes/No Verification Problem

            e.g. Do models model_925814632 and model_701015291 use the table named economic_indicators_tb?
        """)

def refresh_all():
    st.session_state.messages = []
    st.session_state["exTool"].reset()
    st.session_state.require_more_info = False 
    
def refresh():
    st.session_state["exTool"].reset()
    st.session_state.require_more_info = False   

if st.sidebar.button('Open a new chat'):
    refresh_all()

# Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "require_more_info" not in st.session_state:
    st.session_state.require_more_info = False
if "chatbot" not in st.session_state:
    st.session_state.chatbot = Chat("neo4j+s://bed4a8a0.databases.neo4j.io", user="neo4j", password="XbfIA4FEeKePbNnhGT2YtqQ8zqPCcSR7XYYMQbbb70I")
if "exTool" not in st.session_state:
    st.session_state.exTool = st.session_state.chatbot.exTool
if "session_end" not in st.session_state:
    st.session_state.session_end = False

# Display chat messages from history 
for message in st.session_state.messages:
    
    if message["role"] == "assistant":
        
        if message["type"] == "need_info":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
        elif message["type"] == "answer":
            with st.chat_message(message["role"]):
                st.markdown("**Response:**")
                st.markdown(message["content"][0])
                st.divider()
                st.markdown("**Generated Cypher Code:**")
                
                st.code(message["content"][1], language="cypher")
        elif message["type"] == "no_answer":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
    elif message["role"] == "user":
        
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
    #? Base case comparison
    elif message["role"] == "base case":
        
        with st.sidebar.chat_message(message["role"]):
            st.markdown(message["content"])
                      
if prompt := st.chat_input("Enter the information:"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )
    
    if st.session_state.require_more_info:
        st.session_state.exTool.add_info(prompt)
                
    with st.chat_message("assistant"):
        with st.status(label="Generating Answer ...", expanded=True) as status:
            
            # Transfer the prompt into the extraction tool
            res = st.session_state.chatbot(prompt) 

            # ? Base case comparison 
            assert st.session_state.chatbot.messages is not None
            # print("system message", st.session_state.chatbot.messages)
            base_res = test(st.session_state.chatbot.messages)

            if res:
                if res != "Sorry. I can not find any relevant information." and  st.session_state.chatbot.type == "ExtractionTool":
                    generated_cypher = st.session_state.exTool.generated_cypher
                    humanRes = st.session_state.chatbot.ansSmoother(st.session_state.exTool.question, res)

                    st.markdown('**Response:**')
                    st.markdown(humanRes)
                    st.divider()
                    st.markdown(f'**Generated Cypher Code:**')
                    st.code(generated_cypher, language="cypher")
                   
                    st.session_state.messages.append(
                        {"role": "assistant", "type": "answer", "content": (humanRes, generated_cypher)}
                    )  

                    # # guardrail
                    # To do: assert the source of extraction from source 
                    print("st.session_state exTool", st.session_state["exTool"])
          
                else:
                    st.markdown('**Response:**')
                    st.markdown(res)                  
                    
                    st.session_state.messages.append(
                        {"role": "assistant", "type": "no_answer", "content": res}
                    ) 

                st.session_state.require_more_info = False
                # end the session
                st.session_state.session_end = True

            else: # we need the user to provide more infomation
                st.session_state.require_more_info = True
                
                res = "Could you provide more information?"

                st.session_state.chatbot.chat_end = False

                st.markdown(res)
                
                st.session_state.messages.append(
                    {"role": "assistant", "type": "need_info", "content": res}
                )

                    
                
            #? Base case comparison
            st.divider()
            st.markdown("**Base Case Response:**")
            st.markdown(base_res)
            st.session_state.messages.append(
                {"role": "base case", "content": base_res}
            )    
                            
            status.update(label="Completed", expanded=True)

if st.session_state.session_end:
    refresh()
