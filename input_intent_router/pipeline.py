import json

import IntentRouterPrompt as IntentRouterPrompt
import JobExecutorClient as JobExecutorClient
import JobSelectionPrompt as JobSelectionPrompt
import PromptLLM as PromptLLM
import RedactResponsePrompt as RedactResponsePrompt
import requests
import validator as validator

DEBUG = True

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
            
    # COGNITIVE_REQUEST
    if intent == "COGNITIVE_REQUEST":
      
        #step 3a handle user_msg with chatty LLM
        return PromptLLM.ask_chatty(user_msg)

            # COGNITIVE_REQUEST_WITH_EXTRA_DATA or SYSTEM_ACTION
    elif intent in [ "COGNITIVE_REQUEST_WITH_EXTRA_DATA", "SYSTEM_ACTION" ]:
        #step 3b resolve select job
        job_prompt = JobSelectionPrompt.get_job_selection_prompt(user_msg)
        job = PromptLLM.ask_qwen(job_prompt)
        debug_print(f"job_raw: {job}\n---------------")
        job_obj = json.loads(job)
        debug_print(f"job:\n{json.dumps(job_obj, indent=4, ensure_ascii=False)}\n---------------")

        #step 4 validate job structure and parameters
        valid, msg = validator.validate_job(job_obj) 

        if not valid:
            return f"Job invalido, err: {msg}"        

        #step 5 send job to job_execution_service via http
        # bintent_router_moduleuild body
        # return "Job execution connection not yet implemented"

        execution_response = JobExecutorClient.execute_job(job_obj)
        debug_print(f"execution response:\nsuccess: {execution_response['success']} | status: {execution_response['status_code']}\n{execution_response['response_text']}\n---------------")

        if not execution_response["success"]:
            return execution_response["response_text"]

        ret_msg_prompt = RedactResponsePrompt.get_response_message_prompt(
            user_msg,
            execution_response["response_text"]
        )

        #step 6 send response to chatty LLM along with initial input to generate a natural language response
        ret_msg = PromptLLM.ask_chatty(ret_msg_prompt)

        #step 7 return final response
        return ret_msg

msg = str(input("msg: "))
print(process_msg(msg))
