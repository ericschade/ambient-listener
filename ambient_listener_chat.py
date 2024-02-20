import autogen
from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
import chromadb
import os
import datetime

config_list = autogen.config_list_from_json(
        env_or_file="OAI_CONFIG_LIST",
        file_location=".",
        filter_dict={
            "model": {
                "gpt-4",
            }
        },
    )

llm_config = {
    "timeout": 60,
    "cache_seed": 42,
    "config_list": config_list,
    "temperature": 0,
}

def termination_msg(x):
    return isinstance(x, dict) and "TERMINATE" == str(x.get("content", ""))[-9:].upper()

# Make a list of the top level folders and file names in the reference_materials folder
def get_reference_materials():
    print("=========================================")
    print("executing get_reference_materials.py from " + os.getcwd())
    directory = "reference_materials/"
    folders = []
    files = []
    for item in os.listdir(directory):
        path = os.path.join(directory, item)
        if os.path.isdir(path):
            folders.append(directory + item)
        else:
            files.append(directory + item)
    
    return folders + files


def main():
    print("=========================================")

    now = datetime.datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    current_location = "the mall"
    ambient_listen_message = """
    Attention all passengers, the flight to Bermuda has been delayed by 2 hours.
      We apologize for the inconvenience. Please check the monitors for updates.
      """

    initiating_message = f"""
    It is {current_time} on {current_date} and I am at {current_location}. I just heard an announcement over a loudspeaker saying the following:


    {ambient_listen_message}
    
    
    Do I need to do anything?

    
    Explain why an action is required or why no action is required. Provide instructions on how to proceed if an action is required.
    """

    # 1. create RetrieveAssistantAgent instance named "assistant"
    itinerary_retrieval_assistant = RetrieveAssistantAgent(
        name="itinerary_retrieval_agent",
        system_message="You are a helpful assistant.",
        llm_config=llm_config,
    )
    
    ragproxyagent = RetrieveUserProxyAgent(
        name="ragproxyagent",
        is_termination_msg=termination_msg,
        human_input_mode="ALWAYS",
        max_consecutive_auto_reply=10,
        default_auto_reply="Reply `TERMINATE` if the task is done.",
        retrieve_config={
            "task": "qa",
            "docs_path": ["corpus/"],
            "custom_text_types": ["json"],
            "chunk_token_size": 2000,
            "model": config_list[0]["model"],
            "client": chromadb.PersistentClient(path="c:/Users/erics/OneDrive/Documents/GitHub/ambient-listener/tmp/chromadb"),
            "embedding_model": "all-mpnet-base-v2",
            "get_or_create": True,  # set to False if you don't want to reuse an existing collection, but you'll need to remove the collection manually
        },
        code_execution_config={
                "work_dir": "/",
                "use_docker": False
            },
    )
    itinerary_retrieval_assistant.reset()
    ragproxyagent.reset()

    # 3. initiate the chat
    ragproxyagent.initiate_chat(itinerary_retrieval_assistant, clear_history=True, problem=initiating_message)


if __name__ == "__main__":
    main()
