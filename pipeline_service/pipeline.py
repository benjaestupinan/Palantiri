import json
import logging
import os
import time
import uuid
from logging.handlers import RotatingFileHandler

from brain import IntentRouterPrompt
from brain import JobExecutorClient
from brain import JobSelectionPrompt
from brain import MCPExtensionsClient
from brain import MemoryClient
from brain import PromptLLM
from brain import RedactResponsePrompt
from brain import validator
from brain.JOB_CATALOG import merge_mcp_catalog

os.makedirs("logs", exist_ok=True)
_handler = RotatingFileHandler("logs/pipeline.log", maxBytes=5_000_000, backupCount=3)
_logger = logging.getLogger("pipeline")
_logger.addHandler(_handler)
_logger.setLevel(logging.INFO)


class Pipeline:

    def __init__(self):
        self._sessions: dict[str, str] = {}  # client_session_id -> memory_session_id
        mcp_catalog = MCPExtensionsClient.get_catalog()
        if mcp_catalog:
            merge_mcp_catalog(mcp_catalog)

    def process_message(self, client_session_id: str | None, user_msg: str) -> tuple[str | None, str, str]:
        """Returns (client_session_id, text_response, flow_id).
        Returns None as session_id when the session ends.
        """
        if client_session_id is None or client_session_id not in self._sessions:
            memory_session_id = MemoryClient.create_session()
            client_session_id = str(uuid.uuid4())
            self._sessions[client_session_id] = memory_session_id

        memory_session_id = self._sessions[client_session_id]

        flow = {
            "flow_id": str(uuid.uuid4()),
            "client_session_id": client_session_id,
            "user_msg": user_msg,
            "steps": [],
            "success": False,
            "error": None,
        }
        flow_start = time.perf_counter()

        try:
            # step 1 resolve intent
            t = time.perf_counter()
            intent_prompt = IntentRouterPrompt.get_intent_prompt(user_msg)
            intent_raw = PromptLLM.ask_qwen(intent_prompt, model="qwen2.5:14b")
            intent = json.loads(intent_raw)["category"]
            flow["steps"].append({"step": "intent", "ms": _ms(t), "intent": intent})

            # END_SESSION
            if intent == "END_SESSION":
                del self._sessions[client_session_id]
                t = time.perf_counter()
                response = PromptLLM.ask_chatty("El usuario se despidió. Respondé con una despedida cordial y breve.")
                flow["steps"].append({"step": "chatty_farewell", "ms": _ms(t), "response": response})
                flow["intent"] = intent
                flow["success"] = True
                return None, response, flow["flow_id"]

            # COGNITIVE_REQUEST
            if intent == "COGNITIVE_REQUEST":
                t = time.perf_counter()
                history = MemoryClient.get_history(memory_session_id)
                response = PromptLLM.ask_chatty(user_msg, history=history)
                flow["steps"].append({"step": "chatty_cognitive", "ms": _ms(t), "response": response})
                MemoryClient.save_message(memory_session_id, "user", user_msg)
                MemoryClient.save_message(memory_session_id, "assistant", response)
                flow["intent"] = intent
                flow["success"] = True
                return client_session_id, response, flow["flow_id"]

            # EXTEND_CONTEXT_WITH_SYSTEM_ACTION
            elif intent == "EXTEND_CONTEXT_WITH_SYSTEM_ACTION":
                t = time.perf_counter()
                job_prompt = JobSelectionPrompt.get_job_selection_prompt(user_msg)
                job_obj = json.loads(PromptLLM.ask_qwen(job_prompt, model="qwen2.5:14b"))
                flow["steps"].append({"step": "job_selection", "ms": _ms(t), "job": job_obj})

                if job_obj.get("job_id") is None:
                    t = time.perf_counter()
                    response = PromptLLM.ask_chatty(RedactResponsePrompt.get_no_capability_prompt(user_msg))
                    flow["steps"].append({"step": "chatty_no_capability", "ms": _ms(t), "reason": "no_job_found", "response": response})
                    MemoryClient.save_message(memory_session_id, "user", user_msg)
                    MemoryClient.save_message(memory_session_id, "assistant", response)
                    flow["intent"] = intent
                    flow["success"] = True
                    return client_session_id, response, flow["flow_id"]

                t = time.perf_counter()
                valid, msg = validator.validate_job(job_obj)
                flow["steps"].append({"step": "validation", "ms": _ms(t), "valid": valid, "msg": msg})

                if not valid:
                    if msg.startswith("Unknown job_id"):
                        t = time.perf_counter()
                        response = PromptLLM.ask_chatty(RedactResponsePrompt.get_no_capability_prompt(user_msg))
                        flow["steps"].append({"step": "chatty_no_capability", "ms": _ms(t), "reason": "hallucinated_job_id", "response": response})
                        MemoryClient.save_message(memory_session_id, "user", user_msg)
                        MemoryClient.save_message(memory_session_id, "assistant", response)
                        flow["intent"] = intent
                        flow["success"] = True
                        return client_session_id, response, flow["flow_id"]
                    flow["intent"] = intent
                    flow["error"] = f"Job invalido: {msg}"
                    return client_session_id, f"Job invalido: {msg}", flow["flow_id"]

                t = time.perf_counter()
                if MCPExtensionsClient.is_mcp_job(job_obj["job_id"]):
                    execution_response = MCPExtensionsClient.execute_mcp_tool(job_obj)
                else:
                    execution_response = JobExecutorClient.execute_job(job_obj)
                flow["steps"].append({
                    "step": "job_execution",
                    "ms": _ms(t),
                    "job_id": job_obj["job_id"],
                    "success": execution_response["success"],
                    "status_code": execution_response["status_code"],
                    "response": execution_response["response_text"],
                })

                if not execution_response["success"]:
                    flow["intent"] = intent
                    flow["error"] = execution_response["response_text"]
                    return client_session_id, execution_response["response_text"], flow["flow_id"]

                t = time.perf_counter()
                ret_msg_prompt = RedactResponsePrompt.get_response_message_prompt(user_msg, execution_response["response_text"])
                ret_msg = PromptLLM.ask_chatty(ret_msg_prompt)
                flow["steps"].append({"step": "chatty_redact", "ms": _ms(t), "response": ret_msg})
                MemoryClient.save_message(memory_session_id, "user", user_msg)
                MemoryClient.save_message(memory_session_id, "assistant", ret_msg)
                flow["intent"] = intent
                flow["success"] = True
                return client_session_id, ret_msg, flow["flow_id"]

        except Exception as e:
            flow["error"] = str(e)
            raise
        finally:
            flow["total_ms"] = _ms(flow_start)
            _logger.info(json.dumps(flow, ensure_ascii=False))


def _ms(t_start: float) -> int:
    return round((time.perf_counter() - t_start) * 1000)
