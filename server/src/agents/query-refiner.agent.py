"""
# Query Refiner Agent
This agent is responsible for refining user queries based on the RAG Context. It analyzes the user's input, identifies areas for improvement and the additional Contexts that can be Added in the User Query and Generates a More Refined prompt and returns this Refined JSON to the "Data Collector Agent" which Works with HITL.


# RAG Context:
This Consists of the List of all the available and existing Filters / Keyword in the Sprinklr Dashboard. This will be used to search / imporove the User Query and generate a more refined query / Data JSON that will eventually be used to fetch the data from the Sprinklr API.

# Functionality:
- Based on the User Input, the Agent Understands the Context and searches for the most relevant filters / keywords that can be used to refine the user query.
- The Agent using LLM will generate a more refined query based on the user input and the RAG Context.
- The agent then generates a JSON object that contains the refined query and, the key:value pairs based on the refined IInformation that it has Collected or any additional information.
- The Agent returns the JSON Object to the "Data Collector Agent" which will use this refined query / Data JSON to Analyze what more data that needs to be collected from the user and works with HITL to confirm the data.


# Example: 
Input: "I want to do my Brand Health Monitoring"
Output: {
  "refined_query": "Brand Health Monitoring",
  "filters": {
    "topic": "brand health monitoring",
  }
}


"""