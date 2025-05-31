"""
# Data Collector Agent
This agent is responsible for collecting data from the user based on the refined query / JSON Object provided by the Query Refiner Agent. It interacts with the user to gather additional information, clarifies any ambiguities, and ensures that all necessary data is collected before proceeding with further processing.

# Agent Knowledge Base Context: 
This agent has the Context from the knowledge base of some pre-existing and Complete User Prompts, and Some Completed Use Cases. This Present in the Form of a simple txt file that contains the list of all the available and existing filters / keywords in the Sprinklr Dashboard. This will be used to search / improve the user query and generate a more refined query that can be used to fetch the data from the Sprinklr API.

# Functionality:
- Based on the refined query / JSON provided by the Query Refiner Agent, the Data Collector Agent will analyze the query and identify any missing information or additional data that needs to be collected from the user.
- The missing information can include specific filters, keywords, or any other relevant data that is necessary to complete the user request, which the agent will undestand from its Knowledgebase
- This Agents then with the HITL Confirms the data with the user and collects the additional information.
- The additional Information is then Again sent to the Query Refiner Agent for further processing.
- And this happens in loop until the user is satisfied with the data collected and the query is complete.
- After the user satisfaction, this data is sent to the Boolean Keyword Query Generator Ageent for Making the final query that can be used to fetch the data from the Sprinklr API.

# Example:
Input: 
{
    "refined_query": "Brand Health Monitoring",
    "filters": {
        "topic": "brand health monitoring",
    }
}

Agent Will Understand that : 
- The user is interested in monitoring the health of their brand on social media.
- The user wants to focus on a specific topic related to brand health monitoring.
- The user may want to analyze data from multiple social media channels.
- The User may want to kno the number of times their brand has been mentioned in the last 30 days.
- What was the sentiment of the mentions, and what were the top channels where their brand was mentioned.
- Key Topics that were discussed about their Brancd on Different Channels.
- What are the top influencers talking about their brand on social media.
- What are the key PR Metrics.

Then the Data is Appropirately Filled into the JSON Object and returned to the Query Refiner Agent for further processing with HITL

# The LLM Will Figure out about the Filters based on the Context
Output: 
{
    "refined_query": "Brand Health Monitoring",
    "agent_query": ["
    "What are the key metrics for brand health monitoring?",
    "What are the top channels where the brand is mentioned?",
    "What is the sentiment of the brand mentions?",
    "What are the key topics discussed about the brand?",
    "Who are the top influencers talking about the brand?",
    "What are the key PR metrics for the brand?"
    ],  
    "filters": {
        "topic": "brand health monitoring",
    }  
}


"""