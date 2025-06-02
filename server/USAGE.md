## Use-Case Example

### Request :

```json
{
  "query": "Give me my Brand monitor Insights"
}
```

### Response :

1. If the user has not Provided Complete Information, then a Refined Query (Along with tghe Data Collector Agent) will be provided, and all the Releavant Information will be feeded in the States and Be asked for the User for Confirmation, using Human in the Loop (HITL) to ensure the accuracy of the information.
2. IF the User has Provided With all the Information, and after the Refined Query is Generated (Along with Data Collector Agent), the Query will be passed for Further Processing.
3. Aftter the Final Iteration, the User Will be prompted for their Final Yes/ No Confirmation and then the Query will be Passed to the next Agent.

**Here there can be many times when user will be prompted / interrupted for its Input because of the HITL for Information Accuracy**

4. Then the Refined Query / Query will be passed to the Boolean Query Generator Agent, which will generate a Boolean Keyword Query based on the Context Provided to it.
5. This Boolean Query will be passed to the ToolNode, and will be passed appropriately as the payload, and Responses will be Returned from the API.
6. The Responses will be passed to the Data Analyzer Agent along with the Agent State (Containing what all happend till now in langgraph workflow). This Data will be Processes and Classified, using some Classification Algorithm / Model, and Top 10 Quality THemes Will be Returned.
7. These Themes will have a name and description to them, their Description along with the User's Refined Query will be passed to Boolean Query generator Agent, which will generate a Boolean Query specfic to the Theme. This Query will be used to fetch only the Relevant Data for that Theme in Future, if ever needed. And the names, description, and Boolean Query for each theme will returned as a response to the user.

_You can also Return the Langgraph Agent State As well_

### Possible (Not Exact) Refined Query :

```js
messages = [
  HumanMessage(
    (content = "Give me Brand Monitor Insights"),
    (additional_kwargs = {}),
    (response_metadata = {}),
    (id = "caff4190-6fe0-4190-af71-410b3abaa51f")
  ),
];

conversation_id = "a606ab96-ebf3-4696-afc1-8c2c1c71f436";
current_stage = "refining";
current_step = "initializing";
workflow_status = "query_refined";
timestamp = datetime.datetime(2025, 6, 2, 17, 59, 33, 241542);
errors = [];

user_data = UserCollectedData(
  (user_persona = None),
  (products = []),
  (location = None),
  (channels = []),
  (goals = []),
  (time_period = None),
  (additional_notes = None),
  (brand = None)
);

user_query = "Give me Brand Monitor Insights";
user_context = {};
original_query = "Give me Brand Monitor Insights";

query_refinement = QueryRefinementData(
  (original_query = "Give me Brand Monitor Insights"),
  (refined_query =
    "The user is requesting a dashboard or report providing brand monitoring insights, likely encompassing brand mentions, sentiment analysis, and overall brand health. Further clarification is needed to specify the brand(s) to be monitored, the desired time period, and the specific channels to be included in the analysis."),
  (suggested_filters = [
    {
      filter_type: "Brand Mentions",
      description:
        "Filter to track mentions of the specified brand(s) across channels. Requires specification of the brand name(s).",
    },
    {
      filter_type: "Sentiment Analysis",
      description:
        "Filter posts by sentiment (positive, negative, neutral) to understand the emotional tone associated with the brand mentions.",
    },
    {
      filter_type: "Channel Filter",
      description:
        "Filter by social media channels (Twitter, Facebook, Instagram, etc.) to focus the analysis on specific platforms. Requires specification of the desired channels.",
    },
    {
      filter_type: "Time Period",
      description:
        "Filter by date ranges and time periods to analyze trends over time. Requires specification of the desired start and end dates.",
    },
  ]),
  (suggested_themes = [
    {
      theme_name: "Brand Health Monitoring",
      description:
        "Track overall brand perception and health metrics, including sentiment trends, share of voice, and brand reputation.",
    },
  ]),
  (missing_information = [
    "Brand Name(s): Which brand(s) should be monitored?",
    "Time Period: What is the desired date range for the analysis?",
    "Channels: Which social media channels should be included (e.g., Twitter, Facebook, Instagram)?",
    "Specific Metrics: Are there any specific metrics of interest (e.g., share of voice, engagement rate, reach)?",
  ]),
  (confidence_score = 0.7)
);

query_refinement_data = query_refinement;

boolean_query = None;
boolean_query_data = None;
query_generation_data = None;
fetched_data = [];
identified_themes = [];
theme_data = None;
user_collected_data = None;
pending_questions = [];
user_confirmations = {};
hitl_verification_data = None;
rag_context = {};
processing_metadata = {};
dashboard_config = None;
```

### Possible Final Response :

```json
{
    "status": "success",
    "message": "Brand monitor insights have been successfully generated.",
    "themes": [
        {
            "theme_name": "Brand Health Monitoring",
            "description": "Track overall brand perception and health metrics, including sentiment trends, share of voice, and brand reputation.",
            "boolean_query": "(brand:your_brand OR brand:another_brand) AND (sentiment:positive OR sentiment:negative) AND (channel:twitter OR channel:facebook) AND (date:[2023-01-01 TO 2023-12-31])"
        }
        {
            "theme_name": "Social Media Engagement",
            "description": "Analyze engagement metrics across social media platforms to understand audience interaction with the brand.",
            "boolean_query": "(engagement:likes OR engagement:shares OR engagement:comments) AND (channel:instagram OR channel:twitter) AND (date:[2023-01-01 TO 2023-12-31])"
        },
        {
            "theme_name": "Brand Sentiment Analysis",
            "description": "Monitor sentiment trends over time to gauge public perception of the brand.",
            "boolean_query": "(sentiment:positive OR sentiment:negative) AND (channel:facebook OR channel:instagram) AND (date:[2023-01-01 TO 2023-12-31])"
        },
        {
            "theme_name": "Competitor Analysis",
            "description": "Compare brand performance against competitors in terms of mentions, sentiment, and engagement.",
            "boolean_query": "(brand:competitor1 OR brand:competitor2) AND (sentiment:positive OR sentiment:negative) AND (channel:twitter OR channel:facebook) AND (date:[2023-01-01 TO 2023-12-31])"
        },
        {
            "theme_name": "Crisis Management",
            "description": "Identify and analyze potential crises or negative sentiment spikes related to the brand.",
            "boolean_query": "(crisis:yes) AND (sentiment:negative) AND (channel:twitter OR channel:facebook) AND (date:[2023-01-01 TO 2023-12-31])"
        }

    ],
    "refined_query": "The user is requesting a dashboard or report providing brand monitoring insights, likely encompassing brand mentions, sentiment analysis, and overall brand health, over Time Range of last 6 months, across Twitter, Facebook and Instagram channels, in the Countries of USA and India.",
}
```
