import autogen
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from termcolor import colored

PROMPT_DEFAULT = """You're a retrieve augmented chatbot. You answer user's questions based on your own knowledge and the
context provided by the user. You should follow the following steps to answer a question:
Step 1, you estimate the user's intent based on the question and context. The intent can be a code generation task or
a question answering task.
Step 2, you reply based on the intent.
If you can't answer the question with or without the current context, you should reply exactly `UPDATE CONTEXT`.
If user's intent is code generation, you must obey the following rules:
Rule 1. You MUST NOT install any packages because all the packages needed are already installed.
Rule 2. You must follow the formats below to write your code:
```language
# your code
```

If user's intent is question answering, you must give as short an answer as possible.

User's question is: {input_question}

Context is: {input_context}
"""

PROMPT_CODE = """You're a retrieve augmented coding assistant. You answer user's questions based on your own knowledge and the
context provided by the user.
If you can't answer the question with or without the current context, you should reply exactly `UPDATE CONTEXT`.
For code generation, you must obey the following rules:
Rule 1. You MUST NOT install any packages because all the packages needed are already installed.
Rule 2. You must follow the formats below to write your code:
```language
# your code
```

User's question is: {input_question}

Context is: {input_context}
"""

PROMPT_QA = """You're a retrieve augmented chatbot. You will be given information about the user's environment and must either suggest an 
action for the user to take or conclude that no action is needed based on your own knowledge and the context provided by the user.

You are an itinerary manager with access to the user's calendar information. You suggest actions for a user to take in order 
for them to meet the deadlines in their calendar. Consider the user's current location, the current date and time, and the locations and
 dates and times at which events are scheduled in the user's calendar to make a suggestion.

Assume that all information provided is accurate and that the user is able to follow any instructions you provide.


If you can't answer the question with or without the current context, your reply should be given in the following format:

`NO ACTION REQUIRED`
 ```
 explain what context is missing and suggest what additional information would be needed to make a suggestion confidently.
 ```

 If you can answer the question, your reply should be given in the following format:

 'ACTION REQUIRED'
 ```
 explain in detail the steps that the user should take in order to meet the deadlines in their calendar.
 ```

User's question is: {input_question}

Context is: {input_context}
"""
# can maybe just pass a custom prompt instead of wrap the entire agent
class AmbientRetrieveUserProxy(RetrieveUserProxyAgent):
    """(Experimental) Retrieve User Proxy agent, designed to solve a task with LLM.

    RetrieveUserProxy is a subclass of RetrieveUserProxy configured with a default system message.
    """

    def _generate_message(self, doc_contents, task="default"):
        if not doc_contents:
            print(colored("No more context, will terminate.", "green"), flush=True)
            return "TERMINATE"
        if self.customized_prompt:
            message = self.customized_prompt.format(input_question=self.problem, input_context=doc_contents)
        elif task.upper() == "CODE":
            message = PROMPT_CODE.format(input_question=self.problem, input_context=doc_contents)
        elif task.upper() == "QA":
            message = PROMPT_QA.format(input_question=self.problem, input_context=doc_contents)
        elif task.upper() == "DEFAULT":
            message = PROMPT_DEFAULT.format(input_question=self.problem, input_context=doc_contents)
        else:
            raise NotImplementedError(f"task {task} is not implemented.")
        return message