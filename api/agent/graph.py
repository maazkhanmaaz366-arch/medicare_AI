from typing import Sequence, Annotated, TypedDict
from pymongo import MongoClient
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.mongodb import MongoDBSaver
from langchain_groq import ChatGroq
from core.config import settings 
from api.agent.tools import (
    search_doctors_tool,
    book_appointment_tool,
    cancel_appointment_tool,
    clinical_guidlines_tool,
    online_medical_search_tool,
    view_doctor_schedule_tool
)

# 1. state definition 
class ClinicAgentState(TypedDict):
    """Shared Conversation state for MediCare AI"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_id:str
    user_role:str
    user_name:str

# 2. System prompt

CLINIC_SYSTEM_PROMPT = """You are MediCare AI — the smart, compassionate clinical operations copilot for MediCare Clinic.
Your duties:
1. Patient Triage & Doctor Search:
   - When a patient describes symptoms, identify the medical specialty (Cardiology, Dermatology, Orthopedics, Pediatrics, Neurology) and use 'search_doctors_tool' to find matching doctors.
2. Appointment Booking:
   - Help patients schedule consultations using 'book_appointment_tool'. Gather required details: doctor name, patient name, phone, date (YYYY-MM-DD), time slot, and brief symptoms.
3. Official Clinic Policies & Clinical Prep:
   - For ANY question about fasting, tests, cancellation fees, or insurance, ALWAYS call 'clinical_guidelines_tool'. Never guess medical preparation rules.
4. Appointment Cancellations:
   - Cancel appointments using 'cancel_appointment_tool' by reference number.
5. Critical Emergency Rule:
   - If a patient mentions life-threatening symptoms (crushing chest pain, severe breathing difficulty, sudden numbness/stroke signs), immediately advise them to call 911 or visit the nearest emergency room.
6. Confidentiality & Security Rule:
   - 'view_doctor_schedule_tool' is strictly restricted to verified physicians (user_role == 'doctor'). Never call this tool or disclose appointment lists if the user's role is 'patient'. If a patient asks for a doctor's schedule or patient list, explain that medical schedules and patient data are confidential under HIPAA regulations.
Maintain a polite, empathetic, and professional tone at all times.
"""

# 3. Tools Roster and medical binding
tools = [
    search_doctors_tool,
    book_appointment_tool,
    cancel_appointment_tool,
    clinical_guidlines_tool,
    online_medical_search_tool,
    view_doctor_schedule_tool
]

llm = ChatGroq(model='openai/gpt-oss-120b', api_key=settings.GROQ_API_KEY, temperature=0.1)
model_with_tools = llm.bind_tools(tools)

# 4. Agent node with role-awareness and sliding window for memory

async def agent_node(state: ClinicAgentState) -> dict:
    """
    Processes conversation turns with role-awareness and sliding-window memory.
    """
    all_msg = list(state['messages'])

    if len(all_msg) > 10:
        trimmed_msgs = all_msg[-10:]
    else:
        trimmed_msgs = all_msg

    user_role = state.get("user_role", "patient")
    user_name = state.get("user_name", "User")

    role_context = f"\nCURRENT USER CONTEXT: You are speaking to {user_name} whose role is '{user_role}'.\n"
    if user_role == "doctor":
        role_context += "- Since this user is a DOCTOR, you can provide their scheduled appointments using 'view_doctor_schedule_tool'.\n"
    else:
        role_context += "- Since this user is a PATIENT, you help them find doctors, book/cancel consultations, and answer prep policies.\n"

    dynamic_prompt = CLINIC_SYSTEM_PROMPT + role_context
    messages = [SystemMessage(content=dynamic_prompt)] + trimmed_msgs
    response = await model_with_tools.ainvoke(messages)
    return {'messages': [response]}

# 5. Routing Logic

def should_continue(state:ClinicAgentState) -> str:
    message = state['messages']
    last_message = message[-1]
    if getattr(last_message, 'tool_calls', None):
        return "tools"
    
    return END

# 6. Building the state graph
workflow = StateGraph(ClinicAgentState)

workflow.add_node('agent',agent_node)
workflow.add_node('tools',ToolNode(tools))

workflow.add_edge(START, 'agent')
workflow.add_conditional_edges('agent',should_continue,['tools',END])
workflow.add_edge('tools','agent')

# 7. MongoDB Checkpointer Persistence 

sync_client = MongoClient(settings.MONGO_URL)
checkpointer = MongoDBSaver(
    client = sync_client,
    db_name=settings.DATABASE_NAME
)

# 8. Compile the Graph
clinic_agent_graph = workflow.compile(checkpointer=checkpointer)


