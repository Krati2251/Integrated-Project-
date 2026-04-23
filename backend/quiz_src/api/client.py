# # # # import os
# # # # from dotenv import load_dotenv # type: ignore

# # # # load_dotenv() # Loads the .env file

# # # # class LLMClient:
# # # #     def __init__(self):
# # # #         self.api_key = os.getenv("LLM_API_KEY")

# # # #     def generate_quiz_data(self, context_chunks):
# # # #         """
# # # #         Sends the report context to the LLM and asks for 10 questions.
# # # #         """
# # # #         # We combine the chunks into one coherent block of 'truth'
# # # #         combined_context = "\n---\n".join(context_chunks)

# # # #         system_prompt = (
# # # #             "You are a professional financial analyst. Based ONLY on the report "
# # # #             "provided below, generate 10 multiple-choice questions. "
# # # #             "Format the output as a clean JSON list."
# # # #         )

# # # #         user_prompt = f"REPORT CONTEXT:\n{combined_context}\n\nGenerate the 10-question quiz now."

# # # #         # LOGIC: Here you would call your specific LLM (Gemini/OpenAI/etc.)
# # # #         # For now, we print it to verify our 'Core' is passing the right data.
# # # #         print("--- PROMPT SENT TO LLM ---")
# # # #         print(user_prompt[:500] + "...") 
        
# # # #         return "Raw LLM Response would go here"
# # # # src/api/client.py
# # # import json

# # # class LLMClient:
# # #     def generate_quiz_data(self, context_chunks):
# # #         # This print statement is your first verification point
# # #         print(f"\n[VERIFICATION] Number of context chunks received: {len(context_chunks)}")
        
# # #         # This simulates a successful LLM response
# # #         mock_response = {
# # #             "status": "success",
# # #             "message": "Core pipeline is connected. Ready for API key."
# # #         }
# # #         return json.dumps(mock_response)
# # import os
# # from openai import OpenAI
# # from dotenv import load_dotenv

# # load_dotenv()

# # class LLMClient:
# #     def __init__(self):
# #         # Automatically looks for OPENAI_API_KEY in your .env
# #         self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# #     def generate_quiz_data(self, context_chunks):
# #         combined_context = "\n".join(context_chunks)
        
# #         # We define the system instructions and the context
# #         response = self.client.chat.completions.create(
# #             model="gpt-4o-mini",
# #             messages=[
# #                 {
# #                     "role": "system", 
# #                     "content": "You are a financial educator. Create a 10-question multiple-choice quiz based ONLY on the provided report. Return the response in strict JSON format."
# #                 },
# #                 {
# #                     "role": "user", 
# #                     "content": f"CONTEXT:\n{combined_context}\n\nProvide 10 questions with 4 options each, the correct answer, and a brief explanation."
# #                 }
# #             ],
# #             response_format={ "type": "json_object" } # This forces valid JSON output
# #         )
        
# #         return response.choices[0].message.content
# import os
# from openai import OpenAI
# from dotenv import load_dotenv

# # Ensure .env is loaded from the project root
# load_dotenv()

# class LLMClient:
#     def __init__(self):
#         api_key = os.getenv("OPENAI_API_KEY")
    
#         # Guardrail: Catch the error before making the network request
#         if not api_key or "your-api" in api_key:
#             print("\n❌ ERROR: Valid OpenAI API Key not found in .env file.")
#             print("Current Value:", api_key)
#             raise ValueError("Update your .env file with a real key starting with 'sk-'.")

#         self.client = OpenAI(api_key=api_key)

#     def generate_quiz_data(self, context_chunks):
#         # Join chunks with clear separators for the LLM
#         combined_context = "\n\n--- SECTION BREAK ---\n\n".join(context_chunks)
        
#         response = self.client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {
#                     "role": "system", 
#                     "content": (
#                         "You are a financial educator. Create a 10-question multiple-choice quiz "
#                         "based ONLY on the provided report. You must return a JSON object with "
#                         "a 'quiz_title' and a 'questions' array. Each question must include "
#                         "'question', 'options' (list of 4), 'answer', and 'explanation'."
#                     )
#                 },
#                 {
#                     "role": "user", 
#                     "content": f"CONTEXT FROM FINANCIAL REPORT:\n{combined_context}"
#                 }
#             ],
#             response_format={ "type": "json_object" }
#         )
        
#         return response.choices[0].message.content
import os
from openai import OpenAI  # We still use the OpenAI library!
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        
        # Groq is OpenAI-compatible, we just change the base_url
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key
        )

#     def generate_quiz_data(self, context_chunks):
#         combined_context = "\n\n--- SECTION ---\n\n".join(context_chunks)
        
#         response = self.client.chat.completions.create(
#             # Llama 3 70B is excellent for financial reasoning
#             model="llama-3.1-8b-instant", 
#             messages=[
#     {
#         "role": "system", 
#         "content": (
#             "You are a strict JSON generator. Your ONLY task is to output a quiz. "
#             "Do NOT include a quiz name, description, or introduction. "
#             "Do NOT include any text outside of the JSON object. "
#             "Your response MUST start with '{' and end with '}'."
#         )
#     },
#     {
#     "role": "user", 
#     "content": (
#         f"CONTEXT FROM FINANCIAL REPORT:\n{combined_context}\n\n"
#         "TASK: Generate a 10-question quiz based EXCLUSIVELY on the facts in the context above. "
#         "STRICT RULE: If a fact is not mentioned in the provided context, DO NOT include it in the quiz. "
#         "Do not use general knowledge. Focus on specific figures, risks, and strategies mentioned in the text."
#         "STRICT JSON RULE: You must use the key 'question' for the question text and 'options' for the choices. Any other key names will break the system."
#     )
# }
# ],
#             response_format={ "type": "json_object" },
#             temperature=0
#         )
        
#         return response.choices[0].message.content
    def generate_quiz_data(self, context_chunks):
            combined_context = "\n\n--- SECTION ---\n\n".join(context_chunks)
            
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a strict JSON generator. Your ONLY task is to output a quiz based on provided context. Do not include any conversational text."
                    },
                    {
                        "role": "user", 
                        "content": (
                            f"CONTEXT:\n{combined_context}\n\n"
                            "TASK: Create a 10-question quiz based ONLY on the context. "
                            "YOU MUST USE THIS EXACT JSON STRUCTURE OR THE SYSTEM WILL CRASH:\n"
                            "{\n"
                            "  'questions': [\n"
                            "    {\n"
                            "      'question': 'What is X?',\n"
                            "      'options': ['Choice A', 'Choice B', 'Choice C', 'Choice D'],\n"
                            "      'answer': 'Choice A'\n"
                            "    }\n"
                            "  ]\n"
                            "}\n"
                            "RULE: The 'answer' string must exactly match one of the strings in 'options'."
                        )
                    }
                ],
                response_format={ "type": "json_object" },
                temperature=0
            )
            
            return response.choices[0].message.content