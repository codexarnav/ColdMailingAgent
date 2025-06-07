from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage, ToolMessage
from typing import Annotated, TypedDict, List, Sequence
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.tools import tool
from langgraph.prebuilt import ToolNode


document_content = ""


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


@tool
def update(content: str) -> str:
    """Update the document with provided content"""
    global document_content
    document_content = content
    return "Document updated successfully."


@tool
def save(filename: str) -> str:
    """Save the document to a file"""
    global document_content
    print(f"Saving document to {filename}...")  
    with open(filename, "w") as f:
        f.write(document_content)
    return "Document saved successfully."

llm = ChatGoogleGenerativeAI(
    model='gemini-1.5-flash',
    temperature=0.1,
    api_key='AIzaSyCVM03md5zcStbs_crXg_56ROj-pdSlBEo'  
)
llm_with_tools = llm.bind_tools([update, save])


def model(state: AgentState) -> AgentState:
    """Generates an email response based on provided needs"""
    system_prompt = SystemMessage(
        content=(
            "You are an email writing specialist. Use the provided information to generate a professional email response. "
            "You can use the tools 'update' and 'save' to modify the document."
        )
    )

    if not state['messages']:
        user_input = "I am ready to help you with your email writing needs. Please provide the content of the email you want to write."
        user_message = HumanMessage(content=user_input)
    else:
        user_input = input("Please provide the content of the email you want to write: ")
        user_message = HumanMessage(content=user_input)

    all_messages = [system_prompt] + list(state['messages']) + [user_message]
    response = llm_with_tools.invoke(all_messages)
    print(response.content)  
    return {'messages': list(state['messages']) + [user_message, response]}


def router(state: AgentState) -> str:
    messages_content = state['messages']
    if not messages_content:
        return 'continue'

    for message in reversed(messages_content):
        if (
            isinstance(message, ToolMessage)
            and 'saved' in message.content.lower()
            and 'document' in message.content.lower()
        ):
            return 'end'
    return 'continue'


graph = StateGraph(AgentState)
graph.add_node('llm', model)
tool_node = ToolNode([update, save])
graph.add_node('tools', tool_node)
graph.add_conditional_edges('llm', router, {'continue': 'tools', 'end': END})
graph.add_edge('tools', 'llm')
graph.add_edge(START, 'llm')
graph.add_edge('llm', END)

app = graph.compile()


user_input = input("Enter your message (or type 'exit' to quit): ")
while user_input.lower() != 'exit':
    result = app.invoke({'messages': []})
    message = result['messages'][-1].content
    print("\nAI Response:\n", message)
    
    with open('email.txt', 'a') as f:  
        f.write(message + "\n\n")

    user_input = input("\nEnter your message (or type 'exit' to quit): ")
