# # # src/core/generator.py

# # QUIZ_SCHEMA = {
# #     "questions": [
# #         {
# #             "id": "int",
# #             "question_text": "string",
# #             "options": ["list", "of", "4", "strings"],
# #             "correct_answer": "string",
# #             "explanation": "string (referencing the report)",
# #             "metadata": {"section": "string", "page": "int"}
# #         }
# #     ]
# # }
# from src.database.vector_store import VectorManager
# from src.api.client import LLMClient
# import json
# def build_full_quiz():
#     # 1. Initialize our tools
#     db = VectorManager()
#     llm = LLMClient()

#     # 2. Get the most 'important' facts from our demo report
#     # We query for general 'financial highlights' to get the best chunks
#     context = db.query_context("financial highlights and key metrics", n_results=5)

#     # 3. Call the LLM with this specific context
#     quiz_json = llm.generate_quiz_data(context)
    
#     return quiz_json
# def clean_llm_json(raw_string):
#     """Strips markdown formatting like ```json ... ``` from the response."""
#     if "```json" in raw_string:
#         raw_string = raw_string.split("```json")[1].split("```")[0]
#     elif "```" in raw_string:
#         raw_string = raw_string.split("```")[1].split("```")[0]
#     return json.loads(raw_string.strip())
import streamlit as st # type: ignore
from src.database.vector_store import VectorManager
from src.api.client import LLMClient

@st.cache_resource
def get_vector_db():
    # This runs ONLY ONCE and stays in memory
    return VectorManager()

@st.cache_resource
def get_llm_client():
    return LLMClient()

def build_full_quiz():
    # Instead of creating new ones, we fetch the cached versions
    db = get_vector_db()
    llm = get_llm_client()
    context = db.query_context("financial highlights", n_results=10)
    
    # SAFETY CHECK: If the DB is empty, we need to know!
    if not context or len(context) == 0:
        st.error("🚨 Database is empty! Please run your indexing script first.")
        st.stop() 

    # If we have data, proceed to the preview
    print(f"DEBUG: Successfully retrieved {len(context)} chunks.")
    return llm.generate_quiz_data(context)