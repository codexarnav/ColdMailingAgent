import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage,ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain.tools import tool
from typing import Annotated, TypedDict, Sequence
import smtplib
from email.message import EmailMessage

# ------------------------
# Globals & Email Config
# ------------------------
document_content = ""

class AgentState(TypedDict):
    messages: Annotated[Sequence[HumanMessage], add_messages]

@tool
def update(content: str) -> str:
    """updates the email"""
    global document_content
    document_content = content
    return "Document updated successfully."

@tool
def save(filename: str) -> str:
    """saves the file"""
    global document_content
    with open(filename, "w") as f:
        f.write(document_content)
    return "Document saved successfully."

llm = ChatGoogleGenerativeAI(model='gemini-1.5-flash', temperature=0.2,api_key='Your_Gemini_API_key')
llm_with_tools = llm.bind_tools([update, save])

def model(state: AgentState) -> AgentState:
    """Generates an email response based on provided needs"""
    system_prompt = SystemMessage(
        content="You are an expert email writing assistant. Use the prompt to write a formal, professional email. Use 'update' to write, and 'save' to save it."
    )
    user_message = state['messages'][-1]
    all_messages = [system_prompt] + list(state['messages'])
    response = llm_with_tools.invoke(all_messages)
    return {'messages': list(state['messages']) + [response]}

def router(state: AgentState) -> str:
    """"""
    for message in reversed(state['messages']):
        if hasattr(message, "content") and "document saved" in message.content.lower():
            return 'end'
    return 'continue'

graph = StateGraph(AgentState)
graph.add_node('llm', model)
graph.add_node('tools', ToolNode([update, save]))
graph.add_edge(START, 'llm')
graph.add_conditional_edges('llm', router, {'continue': 'tools', 'end': END})
graph.add_edge('tools', 'llm')
graph.add_edge('llm', END)
app = graph.compile()

# ------------------------
# Email Sending Function
# ------------------------
def send_email(sender_email, password, receiver_email, subject, content):
    msg = EmailMessage()
    msg.set_content(content)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, password)
            smtp.send_message(msg)
        return True, "✅ Email sent successfully!"
    except Exception as e:
        return False, f"❌ Failed to send email: {e}"

# ------------------------
# Streamlit UI
# ------------------------
st.set_page_config(page_title="Email AI Agent & Sender", page_icon="📧")
st.title("📨 Email Generator & Auto-Sender")

st.subheader("🔹 Step 1: Enter Prompt for Email Generation")
prompt = st.text_area("Prompt", placeholder="e.g., write an internship request email")

st.subheader("🔹 Step 2: Email Details")
sender_email = st.text_input("Your Gmail", type="default")
password = st.text_input("App Password (not your actual password)", type="password")
receiver_email = st.text_input("Recipient's Email")
subject = st.text_input("Subject Line", placeholder="Regarding internship opportunity")

if st.button("📨 Generate & Send Email"):
    if not (prompt and sender_email and password and receiver_email and subject):
        st.warning("Please fill all fields to proceed.")
    else:
        result = app.invoke({'messages': [HumanMessage(content=prompt)]})

        # Extract updated content from ToolMessage
        for msg in result["messages"]:
            if isinstance(msg, ToolMessage) and "updated" in msg.content.lower():
                final_email = document_content  # global variable updated by tool
                break
        else:
            final_email = "Error: Email content could not be generated."

        # Display generated email with unique key
        st.success("✅ Email Generated")
        st.text_area("📄 Final Email", final_email, height=250, key="generated_email_display")

        # Save to file
        with open("email.txt", "w") as f:
            f.write(final_email)

        # Send the email
        status, message = send_email(sender_email, password, receiver_email, subject, final_email)
        if status:
            st.success(message)
        else:
            st.error(message)

        # Download option
        st.download_button("📥 Download Email", final_email, file_name="email.txt")
