import requests
import IntentRouterPrompt
import JobSelectionPrompt
import validator


def process_msg(user_msg):
    #step 1 resolve intent
    intent_prompt = IntentRouterPrompt.get_intent_prompt(user_msg)
    intent = ask_qwen_llm(intent_prompt)

    #step 2 cases:
            
        # COGNITIVE_REQUEST
    if intent_prompt == "COGNITIVE_REQUEST":
        #step 3a handle user_msg with chatty LLM
        return "Haven't imlemented redirect to chatty llm conversation yet"

            # COGNITIVE_REQUEST_WITH_EXTRA_DATA or SYSTEM_ACTION
    elif intent_prompt in [ "COGNITIVE_REQUEST_WITH_EXTRA_DATA", "SYSTEM_ACTION" ]:
        #step 3b resolve select job
        job = JobSelectionPrompt.get_job_selection_prompt(user_msg)

        #step 4 validate job structure and parameters
        valid, msg = validator.validate_job(job) 

        if not valid:
            return f"Job invalido, err: {msg}"        

        #step 5 send job to job_execution_service via http
        # build body
        response = requests.get("go http server")

        #step 6 send response to chatty LLM along with initial input to generate a natural language response
        ret_msg = ask_chatty_llm(user_msg, response)

        #step 7 return final response
        return ret_msg
