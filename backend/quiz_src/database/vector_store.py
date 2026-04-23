# # import chromadb # type: ignore
# # from pathlib import Path

# # class VectorManager:
# #     def __init__(self, db_name="quiz_db"):
# #         # Local storage folder for the DB
# #         self.client = chromadb.PersistentClient(path="./chroma_db")
# #         self.collection = self.client.get_or_create_collection(name=db_name)
# import chromadb
# from chromadb.config import Settings

# class VectorManager:
#     def __init__(self, db_name="quiz_db"):
#         # Adding Settings helps with the 'tenant' and 'database' initialization issues
#         self.client = chromadb.PersistentClient(
#             path="./chroma_db",
#             settings=Settings(allow_reset=True, anonymized_telemetry=False)
#         )
#         self.collection = self.client.get_or_create_collection(name=db_name)

#     def add_chunks(self, chunks):
#         """Adds text chunks to the vector database."""
#         # We need unique IDs for each chunk
#         ids = [f"id_{i}" for i in range(len(chunks))]
        
#         self.collection.add(
#             documents=chunks,
#             ids=ids
#         )
#         print(f"Successfully indexed {len(chunks)} chunks.")

#     # def query_context(self, query_text, n_results=5):
#     #     """Searches the DB for the most relevant chunks based on a query."""
#     #     results = self.collection.query(
#     #         query_texts=[query_text],
#     #         n_results=n_results
#     #     )
#     def query_context(self, query_text, n_results=5):
#         results = self.collection.query(
#         query_texts=[query_text],
#         n_results=n_results
#         )
#     # ChromaDB returns a list of lists: [[doc1, doc2, ...]]
#     # We want the first list (results['documents'][0])
#        return results.get('documents', [[]])[0]
import os
import chromadb
from chromadb.config import Settings

class VectorManager:
    # def __init__(self, db_name="quiz_db"):
    #     # Adding Settings helps with the 'tenant' and 'database' initialization issues
    #     base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    #     db_path = os.path.join(base_path, "chroma_db")
    #     self.client = chromadb.PersistentClient(
    #         path="./chroma_db",
    #         settings=Settings(allow_reset=True, anonymized_telemetry=False)
    #     )
    #     self.collection = self.client.get_or_create_collection(name=db_name)

    def __init__(self, db_name="quiz_db"):
        # Get absolute path to the root directory
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(base_path, "chroma_db")
        
        # Simpler initialization often fixes the tenant issue
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name=db_name)

    def add_chunks(self, chunks):
        """Adds text chunks to the vector database."""
        # We need unique IDs for each chunk
        ids = [f"id_{i}" for i in range(len(chunks))]
        
        self.collection.add(
            documents=chunks,
            ids=ids
        )
        print(f"Successfully indexed {len(chunks)} chunks.")

    def query_context(self, query_text, n_results=5):
        """Searches the DB for the most relevant chunks based on a query."""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        # This part MUST be indented to stay inside the query_context function
        if results and 'documents' in results:
            # ChromaDB returns a list of lists; we take the first list of docs
            return results['documents'][0]
        
        return []