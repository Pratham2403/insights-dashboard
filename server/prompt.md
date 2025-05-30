
Give me the Exact Steps / Guidelines on how should I proceed with The Project and complete in 20 days that will be used in the Sprinklr Insights / Listening dashboard.Below is the Exact use case example : 

## FRONTEND CHAT:

- **User** : I am the owner of Samsung and I want to know about the Customer Insights about my products.
- **AI** : (as a verification check with human in Loop as the user did not mentioned about the Products and the End Goal is to create a dashboard and the LLM has context of what is all is needed to generate the dashboard so it prompts back) What specific products are you looking for ?
- **User**: Generate for Samsung s25 ultra, s25plus 
- **AI** : (Now the Agent has the context of the products, now it will ask for the next relevant information) What specific channels are you looking into ? (Social Media, News, Blogs, etc)
- **User**: I want to know about the Twitter and Facebook channels.
- **AI** : (Now the Agent has the context of the channels, now it will ask for the next relevant information) What is your goal with this data ? (Brand Awareness, Customer Satisfaction, etc)
- **User**: I want to increase Brand Awareness and Customer Satisfaction.
- **AI** : (Now the Agent has the context of the goals, now it will ask for the next relevant information) What is the time period you are looking into ? (Last 6 Months, Last 1 Year, etc)
- **User**: I want to know about the last 6 months.
- **AI** : (Now the Agent has the context of the time period, now it will ask for the next relevant information) Do you have any additional notes or specific areas you want to focus on ? (Customer Feedback, Sentiment Analysis, etc)
- **User**: Yes, I want to focus on customer feedback and sentiment analysis.
- **AI** : (Now the Agent has all the context needed to generate the dashboard, it will compile all the information and show it to the user for confirmation) 
    - User Persona: Sales Manager
    - User Products: Samsung s25 ultra, s25plus
    - User Location: India
    - User Channels: Twitter, Facebook
    - User Goals: Increase Brand Awareness, Customer Satisfaction
    - User Time Period: Last 6 Months
    - User Additional Notes: Focus on customer feedback and sentiment analysis
- **AI** : Are you sure you want to proceed with this data ? (This is the final confirmation before generating the dashboard)
- **User**: Yes, I am sure.
- ........
- ***AI*** : (There can be many Human In the Loop questions, like the Location / Country you are looking into, or the specific channel sources you wanted to explore, etc…… The Agentic System must have the understanding / context of what all is needed. This will be done through heavy prompting giving agent with various examples, m fields needed, use cases and giving data of some real life final dashboards either through prompts or as RAG Context…..Suggest Accordingly. )

*[This Frontend UI Must Also Show in the Right Side what all data has been accumulated by the Agent Till Now maintaining the State. The States must be persisted if suddenly user starts making different dashboard and then come backs again, then Agents must Remember this….this can be using RAG or some other technique]*

*[Now the Multi AI Agent Framework will start working, that is using primary Techctack as Langgraph , RAG]*

----------
---------

## BACKEND PROCESSING OVERALL IDEA:
The Multi AI Agent system is Contextually Heavy. And its Primary Goal is to Understand and Extract the User Data and Generate the Releavant Boolean Keyword Query. Get the Relevant Data(some exposed EXTERNAL_API that just takes in some Boolean Keyword Query as payload and the API Gives the list of Documents fetched ) and based on the Data Extracted, Form the Most Useful Themes out of It and in later stages will be Convert it into the Sprinklr UI Complied JSON Format [NOT NEEDED TO DO NOW]. The main Challenge of the Backend AI Agents is that they are contextually very heavy(either through heavy Prompting, Chain-Of-Thought processing or RAG Context)as they have to make sure that in order to generate a specific Boolean Keyword Query format or generate a Specific Theme, they have to prompt the user back to get the Realevant data and Structure the Fetched data in the Correct Formats(and this format and some examples jsons and everything will be feeded as RAG in the Context of the LLM)

----------------
----------------

## FRONTEND DASHBOARD [NOT PART OF MY PROJECT] : 
With the Received JSON, Generating a dashboard [Containing Many Widgets]. Either I have to make the UI using the Spinklr Internal frontend Library, or just pass the JSON data to some existing API that will generate the Dashboard. So, the Dashboard generation is not a Crucial Task.

----------------------
----------------------


## CRUCIAL / IMPORTANT TASKS : 
The Human In Loop Verification check(as the agent will be give the context of the UI Library and the JSON Formats of Keyword Queries, Themes Examples, etc. through RAG ) and must get in the data. Make the Apporiate query and make the relevant search and after getting the data must do the required analysis based on the prompt and generate the Complied JSON in the right format.

-----------------------------------
-----------------------------------------


# FIRST PROJECT STAGE AND 1 WEEK DEADLINE

## Project Overview
This segment of the Project focuses on Querying the user for 

## 1. FRONTEND

The user-AI chat interface should allow the agent to display the accumulated knowledge (i.e., data extracted from the interaction) on the right side of the UI. The state panel updates continuously as the conversation progresses. The agent moves to the next stage only once the user has provided sufficient details. In the final stage, the agent confirms the collected data by prompting the user with a confirmation message (e.g., "Are you sure?").

For example, after a series of interactions, the agent might display:

```json
{
    // Example JSON format for the accumulated data. May contain different fields different based on the actual implementation.
    "User Persona": "Sales Manager",
    "User Products": "Samsung s25 ultra, s25plus",
    "User Location": "India",
    "User Channels": "Twitter, Facebook",
    "User Goals": "Increase Brand Awareness, Customer Satisfaction",
    "User Time Period": "Last 6 Months",
    "User Additional Notes": "Focus on customer feedback and sentiment analysis"
}
```


## 2. BACKEND

- **HITL (Human In The Loop):**  
    One backend agent(+Tools) way should manage the HITL verification process, ensuring that the AI agent queries the user for any missing or ambiguous information. This process is essential for accurately collecting all necessary data to to generate an effecient Boolean Keyword Query.
- **Query Generation:**  
    One/more backend Agent(+Tools) should generate an optimized / exhaustive list of keywords that will help in generating the Boolean Keyword Queries based on the user's input, which will be used to fetch relevant data and then categorize/Score the Data and generate into Releavant Themes (which are nothing but group of related keywords or Boolean Keyoword Query). The theme can be a single Boolean keyword query or a batch of boolean keyword queries that retrieves a list of documents matching the user's criteria / Theme. Becaue a Single Query can get a lot of data, but different batch of specific will get limited data, eventually reducring the search time, data processing time and the overall cost.

- **Data Processing:**     
    One Agent Should process the Fetched data, rank / score it based on releavance and select top 5 or 10 themes that can be understood from the data using a Scoring Mechanism and Map these Data to What could be the most apropriate Keyword Query for them. This will help in generating a more focused and relevant dashboard.
    *Theme Example*  : A themes is a collection of keyword queries that helps in narrowing down the data to specific insights. For example, a theme could be "Customer Satisfaction" which includes keywords like "happy", "satisfied", "good service", etc.



#### My main job in the first stage is to ensure that the backend agents are capable of working with HITL and generating the required queries based on user input. The backend agents should be able to handle the complexity of the data processing and then must be able to group the queries into meaningful themes and return the Processed data and themes to the Fronted

#### Additional details should be defined as the project advances, ensuring seamless integration with the frontend state management and data compilation system. Tell me what i can do with the first stage of the Project and how to initialize and begin the development process.

