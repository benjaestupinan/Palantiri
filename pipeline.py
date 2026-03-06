import json

from brain import IntentRouterPrompt
from brain import JobExecutorClient
from brain import JobSelectionPrompt
from brain import MemoryClient
from brain import MemoryContextPrompt
from brain import PromptLLM
from brain import RedactResponsePrompt
from brain import validator

DEBUG = True

session_id = MemoryClient.create_session()

def debug_print(string, debug_bool = DEBUG):
    if debug_bool:
        print(string)

def process_msg(user_msg):
    #step 1 resolve intent
    intent_prompt = IntentRouterPrompt.get_intent_prompt(user_msg)
    intent_raw = PromptLLM.ask_qwen(intent_prompt)

    intent_obj = json.loads(intent_raw)
    intent = intent_obj["category"]
    debug_print(f"intent found: {intent}\n---------------")

    #step 2 cases:

    # END_SESSION
    if intent == "END_SESSION":
        global session_id
        session_id = MemoryClient.create_session()
        debug_print(f"session ended, new session_id: {session_id}\n---------------")
        return PromptLLM.ask_chatty("El usuario se despidió. Respondé con una despedida cordial y breve."), intent

    # COGNITIVE_REQUEST
    if intent == "COGNITIVE_REQUEST":

        #step 3a handle user_msg with chatty LLM, passing session history
        history = MemoryClient.get_history(session_id)
        response = PromptLLM.ask_chatty(user_msg, history=history)
        MemoryClient.save_message(session_id, "user", user_msg)
        MemoryClient.save_message(session_id, "assistant", response)
        return response, intent

    # COGNITIVE_REQUEST_WITH_EXTRA_DATA or SYSTEM_ACTION
    elif intent == "EXTEND_CONTEXT_WITH_SYSTEM_ACTION":
        #step 3b resolve select job
        job_prompt = JobSelectionPrompt.get_job_selection_prompt(user_msg)
        job = PromptLLM.ask_qwen(job_prompt)
        debug_print(f"job_raw: {job}\n---------------")
        job_obj = json.loads(job)
        debug_print(f"job:\n{json.dumps(job_obj, indent=4, ensure_ascii=False)}\n---------------")

        #step 4 handle null job_id (no matching job found)
        if job_obj.get("job_id") is None:
            debug_print(f"no job selected, falling back to chatty LLM\n---------------")
            response = PromptLLM.ask_chatty(RedactResponsePrompt.get_no_capability_prompt(user_msg))
            MemoryClient.save_message(session_id, "user", user_msg)
            MemoryClient.save_message(session_id, "assistant", response)
            return response, intent

        #step 5 validate job structure and parameters
        valid, msg = validator.validate_job(job_obj)

        if not valid:
            if msg.startswith("Unknown job_id"):
                # LLM hallucinated a job that doesn't exist in the catalog
                debug_print(f"hallucinated job_id, falling back to chatty LLM\n---------------")
                response = PromptLLM.ask_chatty(RedactResponsePrompt.get_no_capability_prompt(user_msg))
                MemoryClient.save_message(session_id, "user", user_msg)
                MemoryClient.save_message(session_id, "assistant", response)
                return response, intent
            return f"Job invalido, err: {msg}", intent

        #step 6 send job to job_execution_service via http
        execution_response = JobExecutorClient.execute_job(job_obj)
        debug_print(f"execution response:\nsuccess: {execution_response['success']} | status: {execution_response['status_code']}\n{execution_response['response_text']}\n---------------")

        if not execution_response["success"]:
            return execution_response["response_text"], intent

        ret_msg_prompt = RedactResponsePrompt.get_response_message_prompt(
            user_msg,
            execution_response["response_text"]
        )

        #step 7 send response to chatty LLM along with initial input to generate a natural language response
        ret_msg = PromptLLM.ask_chatty(ret_msg_prompt)
        MemoryClient.save_message(session_id, "user", user_msg)
        MemoryClient.save_message(session_id, "assistant", ret_msg)

        #step 8 return final response
        return ret_msg, intent

if __name__ == "__main__":
    from the_way_of_the_voice.tts_service import speak
    intent = None
    while intent != "END_SESSION":
        msg = str(input("msg: "))
        (resp, intent) = process_msg(msg)
        speak(resp)
