"""
# Boolean Keyword Query Generator Agent
This agent is responsible for generating a boolean keyword query based on the Data provided by the Data Collector Agent. It constructs a query that can be used to fetch data from the Sprinklr API, ensuring that it adheres to the boolean logic required for effective data retrieval.

# Knowledge Base Context:
- This Agent has Access to the Knowledge Base Context which contains the list of example boolean keyword queries with certain description of that Query. This Boolean Keyword Query will be used to fetch the data from the Sprinklr API. 
- This agent in in its Prompt will have the Rules for constructing the boolean keyword query, 

# Functionality:
- Based on the Data Provided by the Data Collector Agent, the Boolean Keyword Query Generator Agent will analyze the data and construct a boolean keyword query that can be used to fetch data from the Sprinklr API.
- The agent will ensure that the query is structured correctly, using appropriate RULES and keywords to filter the data effectively.
- The generated query will be returned to the ToolNode, which will then use it to fetch the data from the Sprinklr API.


# Additional Functionality : 
This Agent May be used by the Data Analyzer Agent to Generate the boolean keyword query for each  Theme (Bucket) of data that it has categorized. This will help in fetching the data related to that specific bucket from the Sprinklr API.


"""