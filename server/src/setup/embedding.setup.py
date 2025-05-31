"""
Embedding setup module for initializing and managing embeddings.


Functionality:
- This module provides functionality to initialize and set up the embedding model.
- It Provides Functions to Take in Text Data / JSON Data and Generate Embeddings for the Data.
- The Embedding Model to be used is Google Generative AI Embeddings, which is suitable for generating high-quality embeddings for text data if using the GoogleGenerativeAI, or use the HuggingFace Embedding Mode : All-MiniLM-L6-v2 for local embedding generation.
- Provides Functonality to Generate the Embedding for User Query and Do a Similarity Search in the Vector Database, based on the User Query and the RAG Context Feeded.
- It is a modular Setup that can be easilt Integrated for Different Rag Contextx.


# Key Notes:
- For Now Use only the HuggingFace Embedding Model : All-MiniLM-L6-v2 for Local Embedding Generation. and Store in ChromaDB Vector Database.
- Keep Room for Future Enhancements to Use Google Generative AI Embeddings or any other Embedding Model.
# - The Embedding Model can be easily swapped out for different models as needed.

"""

