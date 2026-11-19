import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage
from api.agent.graph import clinic_agent_graph
from core.security import decode_access_token

ws_router = APIRouter(tags=["Clinic WebSocket"])

@ws_router.websocket("/ws/clinic/{client_id}")
async def clinic_chat_websocket(websocket: WebSocket, client_id: str):
    await websocket.accept()
    print(f"🟢 [WebSocket] Client connected: {client_id}")

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                payload = json.loads(raw_data)
                token = payload.get("token")
                
                # 🔒 MANDATORY TOKEN VERIFICATION
                auth_data = decode_access_token(token) if token else None
                if not auth_data:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "🔒 Access Denied: Please log in first to verify your identity."
                    }))
                    continue

                user_role = auth_data.get("role", "patient")
                user_name = auth_data.get("name", "User")
                user_message = payload.get("message", "").strip()
                thread_id = payload.get("thread_id") or f"{user_role}_{client_id}"

                if not user_message:
                    continue

                config = {"configurable": {"thread_id": thread_id}}
                initial_state = {
                    "messages": [HumanMessage(content=user_message)],
                    "user_id": client_id,
                    "user_role": user_role,
                    "user_name": user_name
                }

                await websocket.send_text(json.dumps({
                    "type": "status",
                    "message": "⏳ MediCare AI is reviewing your request..."
                }))
                
                async for event in clinic_agent_graph.astream_events(
                    initial_state,
                    config=config,
                    version="v2"
                ):
                    kind = event.get("event")

                    if kind == "on_tool_start":
                        tool_name = event.get("name", "Medical Tool")
                        await websocket.send_text(json.dumps({
                            "type": "tool_start",
                            "tool": tool_name,
                            "message": f"⚙️ Running {tool_name}..."
                        }))
                    elif kind == "on_chat_model_stream":
                        chunk = event.get("data", {}).get("chunk")
                        if chunk and hasattr(chunk, "content") and chunk.content:
                            if isinstance(chunk.content, str):
                                await websocket.send_text(json.dumps({
                                    "type": "chunk",
                                    "content": chunk.content
                                }))

                await websocket.send_text(json.dumps({
                    "type": "done",
                    "thread_id": thread_id
                }))

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON payload received."
                }))
            except Exception as turn_error:
                print(f"⚠️ [Turn Error]: {turn_error}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Clinical agent error: {str(turn_error)}"
                }))
                await websocket.send_text(json.dumps({"type": "done"}))

    except WebSocketDisconnect:
        print(f"🔴 [WebSocket] Client disconnected: {client_id}")
    except Exception as connection_error:
        print(f"❌ [Connection Error]: {connection_error}")