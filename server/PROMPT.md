## Basic Rules and Guidelines

1. **Threaded Execution**

   * For a single server instance, the system must handle multiple conversation threads concurrently.
   * Each thread must maintain its own state and context (use LangGraph’s `MemorySaver()` or `StateManager()`).
   * No persistence is required across server restarts.

2. **Modularity**

   * Each agent must be independent and replaceable without impacting other agents.

3. **Human-In-The-Loop Support**

   * If a query is incomplete or needs user intervention, the system should notify the user and await clarification.
   * Use LangGraphs `interrupt(...)` and `Command(...)` to manage user interactions.

4. **Context Maintenance**

   * The system must accept multiple queries in parallel and preserve context for each thread.
   * Use LangGraph’s `add_messages(...)` to append new queries—do **not** use a generic `append` that might lose context.

5. **Use Built-In Tools**

   * Leverage LangGraph/LangChain’s native tools and libraries whenever possible.
   * Only implement custom features if strictly necessary.

---

## User

* A user can submit either a **complete** or **incomplete** query.
* If the query is incomplete, it is routed to the Human-In-The-Loop flow.

```python
# Initial state of the multi-agent system. Additional fields can be added as needed.
multi_agent_system_project_state = {
    "query":        ["", "", …],
    "refined_query": "",
    "keywords":     ["", "", …],
    "filters": {
       "<key1>": ["<value1>", …],
       "<key2>": ["<value2>", …],
       …  
    },
    "boolean_query": "",
    "themes": [
       {
         "name":           "",
         "description":    "",
         "boolean_query":  ""
       },
       …
    ]
}
```

---

## Query Refiner Agent

1. **Input**

   ```json
   {
     "query": ["<Initial query>"]
   }
   ```
2. **Process**

   * Analyze the incoming query.
   * Prefill common defaults (e.g., time window = last 30 days; default sources = Twitter + Instagram).
   * Use context from previous queries and the existing state to determine which defaults make sense.
3. **Output**

   ```json
   {
     "query":         ["<Initial query>"],
     "refined_query": "<Refined query, considering previous queries and state>"
   }
   ```

---

## Data Collector Agent

1. **Input**

   ```json
   {
     "query":         ["<Initial query>"],
     "refined_query": "<Refined query>"
   }
   ```
2. **Process**

   * Examine the `refined_query` in the context of existing filters.
   * Extract **keywords** (considering sentiment) and update `"keywords"`.
   * Update existing filters or create new ones as needed, preserving the same key/value structure.
3. **Output**

   ```json
   {
     "query":         ["<Initial query>"],
     "refined_query": "<Refined query>",
     "keywords":      ["<Keyword1>", "<Keyword2>", …],
     "filters": {
       "<key1>": ["<value1>", …],
       "<key2>": ["<value2>", …],
       …
     }
   }
   ```

---

## Human-In-The-Loop Agent

* **Purpose**: Intervene when the query is ambiguous or incomplete.
* **Goals**:

  1. **Clarification Prompt**

     * If the LLM detects an incomplete/ambiguous query, immediately prompt the user for clarification.
     * Append the user’s response to the `"query"` array in `multi_agent_system_project_state`.
     * Re-invoke the Query Refiner Agent + Data Collector Agent with the updated state.
  2. **Decision Check**

     * At any critical point, ask the user “Yes / No” to proceed:

       * If “Yes,” continue to the Boolean Query Generator Agent.
       * If “No,” loop back to Query Refiner + Data Collector.

---

## Boolean Query Generator Agent

1. **Input**

   ```json
   {
     "query":         ["Query1", "Query2", …],
     "refined_query": "<Final Refined Query>",
     "keywords":      ["<Keyword1>", "<Keyword2>", …],
     "filters": {
       "<key1>": ["<value1>", …],
       "<key2>": ["<value2>", …],
       …
     }
   }
   ```
2. **Process**

   * Generate a Boolean query string using:

     * The final `refined_query`
     * Extracted `keywords`
     * Existing `filters`
   * Leverage any prior Boolean queries for consistency.
3. **Output**

   ```json
   {
     "query":          ["Query1", "Query2", …],
     "refined_query":  "<Final Refined Query>",
     "keywords":       ["<Keyword1>", "<Keyword2>", …],
     "filters": {
       "<key1>": ["<value1>", …],
       "<key2>": ["<value2>", …],
       …
     },
     "boolean_query":  "<Generated Boolean Query>"
   }
   ```

---

## Data Collector ToolNode

* A LangGraph ToolNode that uses the Boolean query to fetch relevant data (posts/comments).

1. **Input**

   ```json
   {
     "query":          ["Query1", "Query2", …],
     "refined_query":  "<Final Refined Query>",
     "keywords":       ["<Keyword1>", "<Keyword2>", …],
     "filters": {
       "<key1>": ["<value1>", …],
       "<key2>": ["<value2>", …],
       …
     },
     "boolean_query":  "<Boolean Query>"
   }
   ```
2. **Tool Input**

   ```json
   {
     "boolean_query": "<Boolean Query>"
   }
   ```
3. **Process**

   * Execute the Boolean query via LangGraph’s ToolNode API.
   * Return a list of 3,000–4,000 relevant items (posts/comments).
4. **Tool Output**

   ```json
   {
     "data": [
       { /* record1 */ },
       { /* record2 */ },
       …  
     ]
   }
   ```

   * **Note**: We pass this data directly to the Theme Generator Agent; we do **not** store it in state.

---

## Theme Generator Agent

1. **Input from State**

   ```json
   {
     "query":          ["Query1", "Query2", …],
     "refined_query":  "<Final Refined Query>",
     "keywords":       ["<Keyword1>", "<Keyword2>", …],
     "filters": {
       "<key1>": ["<value1>", …],
       "<key2>": ["<value2>", …],
       …
     },
     "boolean_query":  "<Boolean Query>"
   }
   ```
2. **Input from Data Collector ToolNode**

   ```json
   {
     "data": [
       { /* record1 */ },
       { /* record2 */ },
       …
     ]
   }
   ```
3. **Process**

   * Use a classification model to identify the **top 10 themes** from the collected data.
   * For each theme, generate:

     * A concise `name`
     * A meaningful `description`
   * For each of those 10 themes, invoke the Boolean Query Generator Agent (passing the theme-specific context) to produce a `boolean_query` for that theme.
4. **Intermediate Output**

   ```json
   {
     "query":          ["Query1", "Query2", …],
     "refined_query":  "<Final Refined Query>",
     "keywords":       ["<Keyword1>", "<Keyword2>", …],
     "filters": {
       "<key1>": ["<value1>", …],
       "<key2>": ["<value2>", …],
       …
     },
     "boolean_query":  "<Boolean Query>",
     "themes": [
       {
         "name":        "<Theme Name 1>",
         "description": "<Theme Description 1>"
       },
       {
         "name":        "<Theme Name 2>",
         "description": "<Theme Description 2>"
       },
       …  
     ]
   }
   ```

   **Final Output (after generating Boolean queries for each theme)**

   ```json
   {
     "query":          ["Query1", "Query2", …],
     "refined_query":  "<Final Refined Query>",
     "keywords":       ["<Keyword1>", "<Keyword2>", …],
     "filters": {
       "<key1>": ["<value1>", …],
       "<key2>": ["<value2>", …],
       …
     },
     "boolean_query":  "<Boolean Query>",
     "themes": [
       {
         "name":          "<Theme Name 1>",
         "description":   "<Theme Description 1>",
         "boolean_query": "<Boolean Query for Theme 1>"
       },
       {
         "name":          "<Theme Name 2>",
         "description":   "<Theme Description 2>",
         "boolean_query": "<Boolean Query for Theme 2>"
       },
       …  
     ]
   }
   ```

---

## Final Output

* Return the updated `multi_agent_system_project_state` (with `"refined_query"`, `"keywords"`, `"filters"`, `"boolean_query"`, and `"themes"` fields populated) for any downstream processing.
