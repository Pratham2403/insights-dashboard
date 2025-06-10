```json
{
  "status": "success",
  "message": "Query processed successfully",
  "data": {
    "status": "completed",
    "result": {
      "query": [
        "Give me Brand Monitoring Inights of Apple",
        "Use Channel as Twitter or Reddit"
      ],
      "refined_query": "Comprehensive brand health monitoring insights for Apple, including sentiment analysis, brand mentions, reach, and audience analysis specifically on Twitter and Reddit.",
      "keywords": [
        "Apple",
        "brand health",
        "monitoring",
        "insights",
        "sentiment analysis",
        "brand mentions",
        "reach",
        "audience analysis",
        "Twitter",
        "Reddit",
        "love",
        "hate",
        "worst",
        "best",
        "amazing",
        "terrible",
        "broken",
        "recommend",
        "never buying again",
        "good",
        "bad",
        "happy",
        "sad",
        "disappointed",
        "excited",
        "frustrated",
        "satisfied",
        "helpful",
        "useless",
        "scam",
        "overrated",
        "underrated",
        "reliable",
        "unreliable",
        "fantastic",
        "awful"
      ],
      "filters": {
        "source": ["TWITTER", "REDDIT"]
      },
      "boolean_query": "( love OR hate OR worst OR best OR amazing OR terrible OR broken OR recommend OR \"never buying again\" OR good OR bad OR happy OR sad OR disappointed OR excited OR frustrated OR satisfied OR helpful OR useless OR scam OR overrated OR underrated OR reliable OR unreliable OR fantastic OR awful ) AND Apple AND ( source: TWITTER OR source: REDDIT )",
      "themes": [
        {
          "name": "Apple Product Reliability and Quality Concerns",
          "description": "Identify and analyze mentions related to product reliability, defects, and quality issues of Apple products on Twitter and Reddit.",
          "document_indices": [4, 8, 9, 13, 14, 19, 20, 23, 26, 27, 28, 30, 35],
          "document_count": 13,
          "avg_similarity": 0.5070817470550537,
          "representative_docs": [
            "Terrible. mistake after mistake. what's going on with Apple?  and Mark Gurman just warned us the beta 1 is the buggiest  in 12 years.",
            "@RjeyTech Apple is somehow trying to make things better but its getting worse. Now, they need months to work on this IOS26 and then there is Apple Intelligence. Apple fans will be disappointed.",
            "@joshuatopolsky Apple is useless."
          ],
          "confidence_score": 0.321308889298212,
          "boolean_query": "( worst OR sad OR useless OR good OR bad OR scam OR awful OR mistake OR amazing OR never buying again OR terrible OR love OR disappointed OR hate OR overrated OR underrated OR reliable OR excited OR happy OR unreliable OR frustrated OR best OR broken OR recommend OR helpful ) AND ( apple OR Apple ) AND ( source: TWITTER OR source: REDDIT )"
        },
        {
          "name": "Apple Innovation and Technology Perception",
          "description": "Analyze user opinions on Apple's innovation, technology, and future product expectations on Twitter and Reddit.",
          "document_indices": [
            10, 13, 14, 16, 17, 19, 20, 26, 27, 28, 31, 34, 35
          ],
          "document_count": 13,
          "avg_similarity": 0.497785359621048,
          "representative_docs": [
            "@tim_cook I don't know whether such things really create impact or not but it sad to see apple is lagging behind in AI race, camera, as well as battery life these days",
            "@greggertruck Pathetic from @Apple. One of the worst redesigns ever.😓",
            "@MKBHD Gosh, this is the worst WWDC ever! Call it what it is, enough with sugarcoating Apple. They’re losing their edge and no longer innovating. It’s annoying; we need to call them out so they can step up. We love competition.\n\nYes, the iPadOS update was good, but everything else was…"
          ],
          "confidence_score": 0.3175903343246097,
          "boolean_query": "Apple AND ( worst OR sad OR fantastic OR satisfied OR useless OR good OR bad OR awful OR amazing OR \"never buying again\" OR terrible OR love OR disappointed OR hate OR overrated OR underrated OR reliable OR excited OR happy OR unreliable OR pathetic OR frustrated OR best OR broken OR recommend OR helpful ) AND ( source: TWITTER OR source: REDDIT )"
        },
        {
          "name": "Apple Product Performance Feedback",
          "description": "Gather and analyze user feedback on specific Apple products (e.g., iPhones, MacBooks) from Twitter and Reddit.",
          "document_indices": [
            8, 10, 13, 14, 16, 19, 20, 26, 27, 28, 34, 35, 44
          ],
          "document_count": 13,
          "avg_similarity": 0.46277618408203125,
          "representative_docs": [
            "@RjeyTech Apple is somehow trying to make things better but its getting worse. Now, they need months to work on this IOS26 and then there is Apple Intelligence. Apple fans will be disappointed.",
            "@tim_cook I don't know whether such things really create impact or not but it sad to see apple is lagging behind in AI race, camera, as well as battery life these days",
            "@greggertruck Pathetic from @Apple. One of the worst redesigns ever.😓"
          ],
          "confidence_score": 0.3083485688709078,
          "boolean_query": "( worst OR sad OR fantastic OR satisfied OR useless OR good OR bad OR awful OR amazing OR \"never buying again\" OR terrible OR love OR disappointed OR hate OR overrated OR underrated OR reliable OR excited OR happy OR unreliable OR frustrated OR best OR broken OR recommend OR helpful ) AND ( apple OR Apple ) AND ( source: TWITTER OR source: REDDIT )"
        },
        {
          "name": "Apple User Experience Analysis",
          "description": "Analyze user experiences with Apple products and services, focusing on usability, design, and overall satisfaction on Twitter and Reddit.",
          "document_indices": [
            8, 9, 10, 13, 19, 20, 23, 26, 27, 31, 34, 35, 40
          ],
          "document_count": 13,
          "avg_similarity": 0.45787370204925537,
          "representative_docs": [
            "@RjeyTech Apple is somehow trying to make things better but its getting worse. Now, they need months to work on this IOS26 and then there is Apple Intelligence. Apple fans will be disappointed.",
            "@joshuatopolsky Apple is useless.",
            "@tim_cook I don't know whether such things really create impact or not but it sad to see apple is lagging behind in AI race, camera, as well as battery life these days"
          ],
          "confidence_score": 0.30638757605779743,
          "boolean_query": "( worst OR sad OR fantastic OR satisfied OR useless OR good OR bad OR awful OR amazing OR \"never buying again\" OR terrible OR love OR disappointed OR hate OR overrated OR underrated OR reliable OR excited OR happy OR unreliable OR frustrated OR best OR broken OR recommend OR helpful ) AND ( apple OR Apple ) AND ( source: TWITTER OR source: REDDIT )"
        },
        {
          "name": "Apple Brand Advocacy and Loyalty",
          "description": "Identify and analyze mentions indicating brand advocacy, loyalty, and positive recommendations for Apple on Twitter and Reddit.",
          "document_indices": [
            8, 9, 10, 13, 14, 16, 17, 20, 26, 27, 28, 34, 35
          ],
          "document_count": 13,
          "avg_similarity": 0.4152616262435913,
          "representative_docs": [
            "@RjeyTech Apple is somehow trying to make things better but its getting worse. Now, they need months to work on this IOS26 and then there is Apple Intelligence. Apple fans will be disappointed.",
            "@joshuatopolsky Apple is useless.",
            "@tim_cook I don't know whether such things really create impact or not but it sad to see apple is lagging behind in AI race, camera, as well as battery life these days"
          ],
          "confidence_score": 0.3044221108148968,
          "boolean_query": "( love OR fantastic OR satisfied OR good OR amazing OR happy OR best OR recommend OR helpful ) AND ( apple OR Apple ) AND ( source: TWITTER OR source: REDDIT )"
        },
        {
          "name": "Apple Competitive Benchmarking (Social Media)",
          "description": "Compare Apple's brand performance on Twitter and Reddit against its competitors, analyzing sentiment, mentions, and reach.",
          "document_indices": [
            8, 10, 13, 14, 17, 19, 20, 26, 27, 28, 33, 34, 35
          ],
          "document_count": 13,
          "avg_similarity": 0.40121176838874817,
          "representative_docs": [
            "@RjeyTech Apple is somehow trying to make things better but its getting worse. Now, they need months to work on this IOS26 and then there is Apple Intelligence. Apple fans will be disappointed.",
            "@tim_cook I don't know whether such things really create impact or not but it sad to see apple is lagging behind in AI race, camera, as well as battery life these days",
            "@greggertruck Pathetic from @Apple. One of the worst redesigns ever.😓"
          ],
          "confidence_score": 0.30356407243486433,
          "boolean_query": "( worst OR sad OR fantastic OR satisfied OR useless OR good OR bad OR awful OR amazing OR \"never buying again\" OR terrible OR love OR disappointed OR hate OR overrated OR underrated OR reliable OR excited OR happy OR unreliable OR frustrated OR best OR broken OR recommend OR helpful ) AND ( apple OR Apple ) AND ( source: TWITTER OR source: REDDIT )"
        },
        {
          "name": "Apple Security and Privacy Concerns",
          "description": "Identify and analyze mentions related to security vulnerabilities, privacy issues, and data protection concerns related to Apple on Twitter and Reddit.",
          "document_indices": [5, 8, 9, 10, 13, 17, 20, 26, 27, 31, 33, 34, 35],
          "document_count": 13,
          "avg_similarity": 0.4575223922729492,
          "representative_docs": [
            "@MKBHD Is this the worst beta 1 update from Apple ever?",
            "@RjeyTech Apple is somehow trying to make things better but its getting worse. Now, they need months to work on this IOS26 and then there is Apple Intelligence. Apple fans will be disappointed.",
            "@joshuatopolsky Apple is useless."
          ],
          "confidence_score": 0.30148514738537013,
          "boolean_query": "( worst OR sad OR useless OR bad OR awful OR amazing OR never buying again OR terrible OR love OR disappointed OR hate OR overrated OR underrated OR unreliable OR frustrated OR broken ) AND apple AND ( source: TWITTER OR source: REDDIT )"
        },
        {
          "name": "Apple Brand Sentiment on Social Media",
          "description": "Analyze overall sentiment towards Apple on Twitter and Reddit, identifying positive, negative, and neutral opinions.",
          "document_indices": [
            9, 13, 16, 17, 19, 20, 26, 27, 31, 33, 34, 35, 37
          ],
          "document_count": 13,
          "avg_similarity": 0.41567462682724,
          "representative_docs": [
            "@joshuatopolsky Apple is useless.",
            "@greggertruck Pathetic from @Apple. One of the worst redesigns ever.😓",
            "@gc22gc Break up Apple and Amazon! Walmart I love!\nApple and Amazon are useless and UnAmerican!\nI want a Tesla Phone!"
          ],
          "confidence_score": 0.294269850730896,
          "boolean_query": "( love OR amazing OR excited OR happy OR satisfied OR fantastic OR good OR best OR recommend OR helpful OR reliable OR underrated ) OR ( hate OR worst OR awful OR terrible OR sad OR useless OR bad OR scam OR never buying again OR disappointed OR overrated OR unreliable OR pathetic OR break OR frustrated OR broken ) AND ( apple OR Apple ) AND ( source: TWITTER OR source: REDDIT )"
        },
        {
          "name": "Apple Pricing and Value Perception",
          "description": "Analyze user opinions on the pricing and value proposition of Apple products on Twitter and Reddit.",
          "document_indices": [
            9, 10, 13, 14, 16, 17, 20, 26, 27, 28, 34, 35, 38
          ],
          "document_count": 13,
          "avg_similarity": 0.4223801791667938,
          "representative_docs": [
            "@joshuatopolsky Apple is useless.",
            "@tim_cook I don't know whether such things really create impact or not but it sad to see apple is lagging behind in AI race, camera, as well as battery life these days",
            "@greggertruck Pathetic from @Apple. One of the worst redesigns ever.😓"
          ],
          "confidence_score": 0.28742826214290806,
          "boolean_query": "( worst OR sad OR fantastic OR satisfied OR useless OR good OR bad OR awful OR amazing OR \"never buying again\" OR terrible OR love OR disappointed OR hate OR overrated OR underrated OR reliable OR excited OR happy OR unreliable OR pathetic OR frustrated OR best OR broken OR recommend OR helpful ) AND ( apple OR Apple ) AND ( source: TWITTER OR source: REDDIT )"
        },
        {
          "name": "Apple Customer Service Experiences",
          "description": "Identify and analyze mentions related to Apple's customer service experiences on Twitter and Reddit, focusing on satisfaction and dissatisfaction.",
          "document_indices": [
            8, 9, 13, 16, 17, 19, 20, 23, 26, 27, 31, 33, 35
          ],
          "document_count": 13,
          "avg_similarity": 0.4339727759361267,
          "representative_docs": [
            "@RjeyTech Apple is somehow trying to make things better but its getting worse. Now, they need months to work on this IOS26 and then there is Apple Intelligence. Apple fans will be disappointed.",
            "@joshuatopolsky Apple is useless.",
            "@greggertruck Pathetic from @Apple. One of the worst redesigns ever.😓"
          ],
          "confidence_score": 0.2873033960887364,
          "boolean_query": "source: TWITTER OR source: REDDIT AND ( satisfied OR good OR amazing OR love OR happy OR best OR helpful OR fantastic OR recommend ) AND ( worst OR sad OR useless OR bad OR awful OR terrible OR disappointed OR hate OR overrated OR unreliable OR pathetic OR frustrated OR broken OR scam OR never buying again ) AND apple OR Apple"
        },
        {
          "name": "Apple Brand Reputation Crisis Detection",
          "description": "Detect and monitor potential brand crises related to Apple on Twitter and Reddit, identifying spikes in negative sentiment and emerging issues.",
          "document_indices": [
            8, 10, 13, 16, 17, 20, 26, 27, 30, 31, 33, 34, 35
          ],
          "document_count": 13,
          "avg_similarity": 0.3863378167152405,
          "representative_docs": [
            "@RjeyTech Apple is somehow trying to make things better but its getting worse. Now, they need months to work on this IOS26 and then there is Apple Intelligence. Apple fans will be disappointed.",
            "@tim_cook I don't know whether such things really create impact or not but it sad to see apple is lagging behind in AI race, camera, as well as battery life these days",
            "@greggertruck Pathetic from @Apple. One of the worst redesigns ever.😓"
          ],
          "confidence_score": 0.2825351266860962,
          "boolean_query": "( worst OR sad OR useless OR bad OR awful OR amazing OR never buying again OR terrible OR love OR disappointed OR hate OR overrated OR underrated OR unreliable OR frustrated OR broken ) AND ( apple OR Apple ) AND ( source: TWITTER OR source: REDDIT )"
        },
        {
          "name": "Apple Brand Mention Volume and Reach",
          "description": "Track the volume of mentions of Apple on Twitter and Reddit, and estimate the reach of these mentions.",
          "document_indices": [
            8, 9, 10, 13, 16, 20, 22, 23, 26, 27, 33, 34, 35
          ],
          "document_count": 13,
          "avg_similarity": 0.36980804800987244,
          "representative_docs": [
            "@RjeyTech Apple is somehow trying to make things better but its getting worse. Now, they need months to work on this IOS26 and then there is Apple Intelligence. Apple fans will be disappointed.",
            "@joshuatopolsky Apple is useless.",
            "@tim_cook I don't know whether such things really create impact or not but it sad to see apple is lagging behind in AI race, camera, as well as battery life these days"
          ],
          "confidence_score": 0.27671686999759976,
          "boolean_query": "( apple OR Apple ) AND ( source: TWITTER OR source: REDDIT )"
        },
        {
          "name": "Apple Marketing Campaign Effectiveness (Social Media)",
          "description": "Measure the effectiveness of Apple's marketing campaigns on Twitter and Reddit by analyzing sentiment, engagement, and reach.",
          "document_indices": [
            9, 10, 13, 16, 17, 19, 20, 26, 27, 31, 33, 34, 35
          ],
          "document_count": 13,
          "avg_similarity": 0.3737734258174896,
          "representative_docs": [
            "@joshuatopolsky Apple is useless.",
            "@tim_cook I don't know whether such things really create impact or not but it sad to see apple is lagging behind in AI race, camera, as well as battery life these days",
            "@greggertruck Pathetic from @Apple. One of the worst redesigns ever.😓"
          ],
          "confidence_score": 0.2735411163587419,
          "boolean_query": "( worst OR sad OR fantastic OR satisfied OR useless OR good OR bad OR awful OR amazing OR \"never buying again\" OR terrible OR love OR disappointed OR hate OR overrated OR underrated OR reliable OR excited OR happy OR unreliable OR pathetic OR frustrated OR best OR broken OR recommend OR helpful ) AND ( apple OR Apple ) AND ( source: TWITTER OR source: REDDIT )"
        },
        {
          "name": "Apple Audience Demographics and Interests (Social Media)",
          "description": "Analyze the demographics and interests of users mentioning Apple on Twitter and Reddit to understand the target audience.",
          "document_indices": [
            8, 9, 10, 13, 16, 17, 19, 20, 26, 27, 33, 34, 35
          ],
          "document_count": 13,
          "avg_similarity": 0.38336360454559326,
          "representative_docs": [
            "@RjeyTech Apple is somehow trying to make things better but its getting worse. Now, they need months to work on this IOS26 and then there is Apple Intelligence. Apple fans will be disappointed.",
            "@joshuatopolsky Apple is useless.",
            "@tim_cook I don't know whether such things really create impact or not but it sad to see apple is lagging behind in AI race, camera, as well as battery life these days"
          ],
          "confidence_score": 0.2718216322944278,
          "boolean_query": "Apple OR apple AND source: TWITTER OR source: REDDIT"
        }
      ]
    },
    "thread_id": "98cccef3-d82b-48b2-995d-15d241283e33"
  },
  "timestamp": "2025-06-10T04:07:07.005533"
}
```
