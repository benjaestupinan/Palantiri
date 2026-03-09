import json
import uuid

from brain import IntentRouterPrompt
from brain import JobExecutorClient
from brain import JobSelectionPrompt
from brain import MCPExtensionsClient
from brain import MemoryClient
from brain import PromptLLM
from brain import RedactResponsePrompt
from brain import validator
from brain.JOB_CATALOG import merge_mcp_catalog


class Pipeline:

    def __init__(self):
        self._sessions: dict[str, str] = {}  # client_session_id -> memory_session_id
        mcp_catalog = MCPExtensionsClient.get_catalog()
        if mcp_catalog:
            merge_mcp_catalog(mcp_catalog)

    def process_message(self, client_session_id: str | None, user_msg: str) -> tuple[str | None, str]:
        """Returns (client_session_id, text_response).
        Returns None as session_id when the session ends.
        """
        if client_session_id is None or client_session_id not in self._sessions:
            memory_session_id = MemoryClient.create_session()
            client_session_id = str(uuid.uuid4())
            self._sessions[client_session_id] = memory_session_id

        memory_session_id = self._sessions[client_session_id]

        # step 1 resolve intent
        intent_prompt = IntentRouterPrompt.get_intent_prompt(user_msg)
        intent_raw = PromptLLM.ask_qwen(intent_prompt, model="qwen2.5:14b")
        intent = json.loads(intent_raw)["category"]

        # END_SESSION
        if intent == "END_SESSION":
            del self._sessions[client_session_id]
            response = PromptLLM.ask_chatty("El usuario se despidió. Respondé con una despedida cordial y breve.")
            return None, response

        # COGNITIVE_REQUEST
        if intent == "COGNITIVE_REQUEST":
            history = MemoryClient.get_history(memory_session_id)
            response = PromptLLM.ask_chatty(user_msg, history=history)
            MemoryClient.save_message(memory_session_id, "user", user_msg)
            MemoryClient.save_message(memory_session_id, "assistant", response)
            return client_session_id, response

        # EXTEND_CONTEXT_WITH_SYSTEM_ACTION
        elif intent == "EXTEND_CONTEXT_WITH_SYSTEM_ACTION":
            job_prompt = JobSelectionPrompt.get_job_selection_prompt(user_msg)
            job_obj = json.loads(PromptLLM.ask_qwen(job_prompt, model="qwen2.5:14b"))

            if job_obj.get("job_id") is None:
                response = PromptLLM.ask_chatty(RedactResponsePrompt.get_no_capability_prompt(user_msg))
                MemoryClient.save_message(memory_session_id, "user", user_msg)
                MemoryClient.save_message(memory_session_id, "assistant", response)
                return client_session_id, response

            valid, msg = validator.validate_job(job_obj)
            if not valid:
                if msg.startswith("Unknown job_id"):
                    response = PromptLLM.ask_chatty(RedactResponsePrompt.get_no_capability_prompt(user_msg))
                    MemoryClient.save_message(memory_session_id, "user", user_msg)
                    MemoryClient.save_message(memory_session_id, "assistant", response)
                    return client_session_id, response
                return client_session_id, f"Job invalido: {msg}"

            if MCPExtensionsClient.is_mcp_job(job_obj["job_id"]):
                execution_response = MCPExtensionsClient.execute_mcp_tool(job_obj)
            else:
                execution_response = JobExecutorClient.execute_job(job_obj)

            if not execution_response["success"]:
                return client_session_id, execution_response["response_text"]

            ret_msg_prompt = RedactResponsePrompt.get_response_message_prompt(user_msg, execution_response["response_text"])
            ret_msg = PromptLLM.ask_chatty(ret_msg_prompt)
            MemoryClient.save_message(memory_session_id, "user", user_msg)
            MemoryClient.save_message(memory_session_id, "assistant", ret_msg)
            return client_session_id, ret_msg
