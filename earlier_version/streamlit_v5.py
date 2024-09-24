import streamlit as st  
from kpmg_chatbot_v3 import ExtractionTool 
#? Base case comparison
from Basecase import test      

st.title("KPMG Chatbot")

def refresh_all():
    st.session_state.messages = []
    st.session_state["extool"].reset()
    st.session_state.require_more_info = False 
    
def refresh():
    st.session_state["extool"].reset()
    st.session_state.require_more_info = False   

if st.sidebar.button('Open a new chat'):
    refresh_all()

# Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "require_more_info" not in st.session_state:
    st.session_state.require_more_info = False
if "extool" not in st.session_state:
    st.session_state["extool"] = ExtractionTool("neo4j+s://9014d857.databases.neo4j.io", user="neo4j", password="RYYNymC3Bug5n9Il-ke_RPAHKkIQNlP5zujB-B8H8w8")
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
        st.session_state["extool"].add_info(prompt)
                
    with st.chat_message("assistant"):
        with st.status(label="Generating Answer ...", expanded=True) as status:
            
            # Transfer the prompt into the extraction tool
            res = st.session_state["extool"].extract(prompt) 
            #? Base case comparison 
            base_res = test(st.session_state["extool"].messages)
            if res:
                if res != "Sorry. I can not find any relevant information.":
                    generated_cypher = st.session_state["extool"].generated_cypher
                    st.markdown('**Response:**')
                    st.markdown(res)
                    st.divider()
                    st.markdown(f'**Generated Cypher Code:**')
                    st.code(generated_cypher, language="cypher")
                   
                    st.session_state.messages.append(
                        {"role": "assistant", "type": "answer", "content": (res, generated_cypher)}
                    )                 
                        
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