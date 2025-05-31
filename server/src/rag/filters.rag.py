"""
This Module is to setup the RAG (Retrieval Augmented Generation) Context for Filters used in Sprinklr for the application.

#Filter Information Source : src.knowledge_base.filters.json


# Purpose of this module:
- To Provide the Functionality to Embed the Data from Filters JSON, and Put the data as Embedding in the Vector Database.
- To Provide the Dunctionality to Retrieve the Data from the Vector Database and Perform a Similarity Search to Get the Relevant Filters based on the User Query.

# The Embedding Model is Initialized and Settd Up in the `src/setup/embedding.setup.py` file.
# The Vector Database is Initialized and Set Up in the `src/setup/vector_db.setup.py` file.

The RAG Context is Used by the Query Refiner Agent to Refine the User Query and Generate a More Refined Query that can be used to Fetch the Data from the Sprinklr API.

"""