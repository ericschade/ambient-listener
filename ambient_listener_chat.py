import autogen
from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from autogen.agentchat.user_proxy_agent import UserProxyAgent
from autogen.agentchat.assistant_agent import AssistantAgent
from ambient_retrieve_user_proxy import AmbientRetrieveUserProxy
import chromadb
import os
import datetime
from typing import List
import os
import time
import pyaudio
import playsound
from gtts import gTTS
import speech_recognition as sr
from pydub import AudioSegment
from pydub.playback import play

config_list = autogen.config_list_from_json(
        env_or_file="OAI_CONFIG_LIST",
        file_location=".",
        filter_dict={
            "model": {
                "gpt-3.5-turbo",
            }
        },
    )

llm_config = {
    "timeout": 60,
    "cache_seed": 42,
    "config_list": config_list,
    "temperature": 1.5,
}

chromadb_path = os.path.join(os.getcwd(), "/tmp/chromadb")

def termination_msg_no_action(x):
    return isinstance(x, dict) and (("NO ACTION REQUIRED" in str(x.get("content", ""))[:18]) or ("ACTION REQUIRED" in str(x.get("content", ""))[:15]))


def termination_msg(x):
    return isinstance(x, dict) and "TERMINATE" == str(x.get("content", ""))[-9:].upper()


itinerary_retrieval_assistant = AssistantAgent(
    name="itinerary_retrieval_agent",
    system_message="You are a helpful assistant who has access to the user's calendar and travel plan information. After you provide an action recommendation, terminate the program.",
    llm_config=llm_config,
    description="Retrieve information about the user's itinerary",
)

ragproxyagent = AmbientRetrieveUserProxy(
    name="ragproxyagent",
    is_termination_msg=termination_msg_no_action,
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    default_auto_reply="Reply `TERMINATE` if the task is done.",
    retrieve_config={
        "task": "qa",
        # TODO: "custom_prompt": i think we can pass a custom prompt here instad of wrapping the entire rag agent or using the qa task type
        "docs_path": ["corpus/"],
        "custom_text_types": ["json"],
        "chunk_token_size": 2000,
        "model": config_list[0]["model"],
        "client": chromadb.PersistentClient(path=chromadb_path),
        "embedding_model": "all-mpnet-base-v2",
        "get_or_create": True,  # set to False if you don't want to reuse an existing collection, but you'll need to remove the collection manually
        "update_context": False # do not request additional context from the user,
    },
    code_execution_config={
            "work_dir": "/",
            "use_docker": False
        },
)

communication_assistant = AssistantAgent(
    name="communication_assistant",
    human_input_mode="NEVER",
    system_message="You are a knowledgable assistant who knows how best to communicate to the user via digital means depending on the circumstances. Review any actions that are suggested to the user and propose methods of notifying the user in real time to their phone. If the itinerary agent provides an action, terminate the program afterwards",
    llm_config=llm_config,
)

# from https://microsoft.github.io/autogen/blog/2023/10/18/RetrieveChat#integrate-with-other-agents-in-a-group-chat. The description of the function will be used to 
# determine when to call the retrival method
def retrieve_itinerary_information(message: str, n_results=4):
    """
    Retrieve itinerary information for the user.
    """
    ragproxyagent.n_results = n_results  # Set the number of results to be retrieved.
    # Check if we need to update the context.
    ret_msg = ragproxyagent.generate_init_message(message, n_results=n_results)

    # the `ret_msg`` will contain all context and the instructions for another agent 
    # to continue the conversation based on the PROMPT variables in ambient_retrieve_user_proxy.py
    return ret_msg if ret_msg else message

os_operator_agent = UserProxyAgent(
        human_input_mode="NEVER",
        name="os_operator_agent",
        is_termination_msg=termination_msg,
        code_execution_config={
            "work_dir": "/logs",
            "use_docker": False
        },
        llm_config=llm_config,
)


def log_suggested_actions(announcement: str, suggested_actions: List[str]):
    """
    Save the suggested actions to a log file.
    """
    with open("suggested_actions.log", "a") as f:
        f.write(f"{announcement}\n")
        f.write(f"{suggested_actions}\n\n")

autogen.agentchat.register_function(
    retrieve_itinerary_information,
    caller=itinerary_retrieval_assistant,
    executor=itinerary_retrieval_assistant,
    description="Retrieve itinerary information for the user.",
)

autogen.agentchat.register_function(
    log_suggested_actions,
    caller=communication_assistant,
    executor=os_operator_agent,
    description="Record any actions suggested by the agents in the chat to create notifications to the user.",
)

lang = 'en'
def get_audio():
    recognizer = sr.Recognizer()  # create an instance of Recognizer
    with sr.Microphone() as source:
        print("Speak now:")
        audio = recognizer.listen(source)

        try:
            input_text = recognizer.recognize_google(audio)
            print("You said:", input_text)
            return input_text
        except sr.UnknownValueError:
            print("I couldn't understand you")
            return ""

def main():
    print("=========================================")
    
    now = datetime.datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    current_location = "the mall"
    input_text = get_audio()  # Call get_audio to get the user's input
    #  Attention all passengers, the flight to Bermuda has been delayed by 2 hours.
    #  We apologize for the inconvenience. Please check the monitors for updates.
        
    ambient_listen_message = input_text

    initiating_message = f"""
    It is {current_time} on {current_date} and I am at {current_location}. I just heard an announcement over a loudspeaker saying the following:


    {ambient_listen_message}
    
    
    Use my itinerary data to determine if I need to take any actions.

    
    Explain why an action is required or why no action is required. Provide instructions on how to proceed if an action is required. Following action terminate the program.
    """

    # 1. configure the agents
    itinerary_retrieval_assistant.reset()
    ragproxyagent.reset()
    os_operator_agent.reset()


    # 3. initiate the chat
    groupchat = autogen.GroupChat(
        agents=[os_operator_agent, itinerary_retrieval_assistant, communication_assistant], messages=[], max_round=10
    )
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    # Start chatting with the boss as this is the user proxy agent.
    os_operator_agent.initiate_chat(
        manager,
        message=initiating_message,
    )
    

if __name__ == "__main__":
    main()
