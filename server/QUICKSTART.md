# Quick Start Guide

This guide will help you quickly set up and run the Sprinklr Insights Dashboard server.

## Setup

1. **Install dependencies**

```bash
pip install -r requirements.txt
```

2. **Set up environment variables**

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit the `.env` file to add your OpenAI API key and other configuration options.

3. **Initialize the application**

```bash
python -m app.init
```

This will create necessary directories and prepare the application for first run.

## Running the Server

You can run the server in two ways:

1. **Using the convenience script**:

```bash
./run_server.sh
```

2. **Running manually**:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

## Testing the Conversation Flow

To test the conversation flow without a frontend, you can run the test script:

```bash
python -m app.tests.test_conversation
```

This will simulate a conversation with the system and show the responses at each step.

## API Documentation

Once the server is running, you can access the API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Example Conversation Flow

1. User: "I am the owner of Samsung and I want to know about the Customer Insights about my products."
2. Assistant: "What specific products are you looking for?"
3. User: "Generate for Samsung s25 ultra, s25plus"
4. Assistant: "What channels do you want to analyze? (Twitter, Facebook, etc.)"
5. User: "I want to know about the Twitter and Facebook channels."
6. Assistant: "What are your goals? (Brand Awareness, Customer Satisfaction, etc.)"
7. User: "I want to increase Brand Awareness and Customer Satisfaction."
8. Assistant: "What time period should we analyze?"
9. User: "I want to know about the last 6 months."
10. Assistant: "Any additional focus areas?"
11. User: "Yes, I want to focus on customer feedback and sentiment analysis."
12. Assistant: [Shows compiled data for confirmation]
13. User: "Yes, I am sure."

The system will process the data and generate insights based on the requirements.
