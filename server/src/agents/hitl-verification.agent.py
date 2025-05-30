"""
#Human-in-the-loop verification agent for evaluating AI-generated content.
This agent is responsible for verifying the accuracy and relevance of the content generated by the AI agents. It interacts with human reviewers to confirm the quality of the generated content, ensuring that it meets the required standards before being used in further processing or presentation.

Functinonality:
- Based on the Content Generated in the "agent_query" by the Data Collector Agent, the HITL Verification Agent will analyze the content and prompt the human reviwer to verify the accuracy and realavance of the Data.
- The agent will present the generated content to the human reviewer, who will evaluate its quality and provide feedback.
- The agent after confirmation will adequately format the data to feeded to the Query-refiner Agent  or Data Collector Agent for further processing.


# Key Outcome:

From the User Query of : "I want to do my Brand Health Monitoring".

The HITL Verification Agent, Data Collector Agent and Query Refiner Agent will work together to refine the user query and collect the necessary data. The final output will be a JSON object that contains the refined query, additional filters, and any other relevant information needed to fetch data from the Sprinklr API.

#Example:
Input : "I want to do my Brand Health Monitoring"

Final Output after Looping Process :
The Filters can be more and more specific, which will be decided by the Query Refiner Agent as it has the Access to the RAG Context of the List of all the available and existing Filters / Keywords in the Sprinklr Dashboard.

{
    "refined_query":"The User wants to do Brand Health Monitoring",
    "data_sections":[
        "How many times has the brand been mentioned in the last 30 days?",
        "What is the sentiment of the brand mentions?",
        "What are the top channels where the brand is mentioned?",
        "What are the key topics discussed about the brand?",
        "Who are the top influencers talking about the brand?",
        "What are the key PR metrics for the brand?"
    ],
    "filters": {
        "topic": "brand health monitoring",
        "time_period": "last 30 days",
        "channels": ["Twitter", "Facebook", "Instagram"],
        "metrics": [
            "Brand Mentions",
            "Sentiment Analysis",
            "Top Channels",
            "Key Topics",
            "Top Influencers",
            "PR Metrics"
        ]
    },
}


"""