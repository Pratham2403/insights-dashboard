"""
This script sets up the LLM for the application.
It initializes the LLM and its components.

# LLMs that will be used in the application:
- GoogleGenerativeAI: For Development
- OpenAI-LLMRouter : For Production


## LLM Router Used:
```bash
curl -X POST 'http://qa6-intuitionx-llm-router-v2.sprinklr.com/chat-completion' \
-H "Content-Type: application/json" \
-d '{
  "model": "gpt-4o",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "client_identifier": "spr-backend-interns-25"
}'
```
 

# Note : For now implementing only GoogleGenerativeAI for development purposes.
# This will be used in the agents to interact with the LLM.
# Make sure to set the environment variable GOOGLE_API_KEY with your Google API key.

"""

import os
from langchain_google_genai import GoogleGenerativeAI
