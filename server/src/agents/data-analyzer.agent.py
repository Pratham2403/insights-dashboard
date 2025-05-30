"""
#Data Analyzer Agent
This agent is Responsible for analyzing the Data recieved from the ToolNode after the Data has been fetched from the Sprinklr API. It processes and categorizes the data into buckets. Labels each bucket as a Potential Themes,Add a Name and description to That Bucket, Generate a Boolean Keyword Query Specicifc for that Bucket(That will with maximum probability get only that data that was first categorized for that bucket)and returns Such JSON.
This is the Main Agent that has the most crucial role in the first phase of the Project.

#Data Magniture : Data is an array of JSON Objects. Where the Array lenght can be in range of 2000 to 4000 Object

#Agent Knowledge Base Context:
The agent has access to some example Themes, their description, and the possible boolean keyword queries that can be used to fetch data related to those themes. This context will help the agent in categorizing the data into relevant themes and generating appropriate boolean keyword queries.


#Theme Definition: 
Theme is nothing but a filter that helps in categorizing similar Data Based on the User Input and the data Received. 
For Example, if the Refined User Prompt is "Show me samsungs Brand Mention in the Last 30 Days on Chanells like Twitter, Facebook and Instagram", then the Data Analyzer Agent will categorize the data into different themes such as "Samsung Brand Mentions", "Twitter Mentions", "Facebook Mentions","Mentions in Last 30 Days" and "Instagram Mentions". Each theme will have a name, description, and a boolean keyword query that can be used to fetch data related to that specific theme. These Themes will eventually Help the Customers to Better Filter their Data and Fetch in a More Effecient Way, therefore Reducing the Processing and Searching Cost and Improving User Experience.

#Functionality:
- Based on the data received from the ToolNode, the Data Analyzer Agent will analyze the Data and categorize it into different buckets.
- This Categorization is Done Using the final Refined user Prompt (Existing in the AgentState)  LLM or Machine Learning Models or any other method that the Agent Deems fit. Some Possible Methods can be: Zero-Shot Classification (Bart LLM), Clustering, or any other method that can be used to categorize the data into different themes.
- Each bucket will be labeled as a potential theme, and the agent will generate a name, description and a most optimal Boolean Keyword Query for each theme based on the data in that bucket.
- The agent will then return a JSON object containing the categorized themes, their names, descriptions, and the boolean keyword queries.
- The Boolean Keyword Query can be Generated using the Boolean Keyword Query Generator Agent or can be generated by the Data Analyzer Agent itself based on the Architecture and the Modularity of the Project.

#Example:
Input: 
{
    "data": [
        {
            "id": 1,
            "content": "Samsung Galaxy S21 is the best smartphone of 2021",
            "channel": "Twitter",
            "date": "2021-01-01"
        },
        {
            "id": 2,
            "content": "Samsung's new TV is amazing",
            "channel": "Facebook",
            "date": "2021-02-01"
        },
        {
            "id": 3,
            "content": "Samsung Galaxy S21 review",
            "channel": "Instagram",
            "date": "2021-03-01"
        }
        ... # In total 2000 to 4000 objects
    ]
}


Output:
The Exact Themes and their boolean keyword queries will depend on the data received and the refined user prompt. The Themes can mean something entirely different, and will be known as the System Prompts for the Data Analyzer agent will be written in the Future
{
    "themes": [
        {
            "name": "Samsung Brand Mentions",
            "description": "Data related to mentions of Samsung brand across various channels.",
            "boolean_keyword_query": "(Samsung AND (brand OR mentions))"
        },
        {
            "name": "Twitter Mentions",
            "description": "Data related to mentions of Samsung brand on Twitter.",
            "boolean_keyword_query": "(Samsung AND Twitter)"
        },
        {
            "name": "Facebook Mentions",
            "description": "Data related to mentions of Samsung brand on Facebook.",
            "boolean_keyword_query": "(Samsung AND Facebook)"
        },
        {
            "name": "Instagram Mentions",
            "description": "Data related to mentions of Samsung brand on Instagram.",
            "boolean_keyword_query": "(Samsung AND Instagram)"
        },
        {
            "name": "Mentions in Last 30 Days",
            "description": "Data related to mentions of Samsung brand in the last 30 days.",
            "boolean_keyword_query": "(Samsung AND (mentions OR reviews) AND (last 30 days))"
        }
    ]
}

"""