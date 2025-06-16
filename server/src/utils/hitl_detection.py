"""
Intelligent HITL Detection Utility

Analyzes user queries for approval phrases, but never bypasses human verification.
All analysis is for informational purposes only - explicit human approval is always required.
"""

import re
import logging
from typing import Dict, Any, Tuple, List, Optional

logger = logging.getLogger(__name__)

# Define approval patterns with different levels of confidence
APPROVAL_PATTERNS = {
    "high_confidence": [
        r'\b(yes|yep|yeah|yup|ok|okay|alright|sure|proceed|continue|go ahead|approved?|accept(?:ed)?|confirmed?)\b',
        r'\b(satisfied|good to go|looks good|fine|correct|right|perfect|excellent)\b',
        r'\b(that(?:\'s| is) (?:correct|right|good|fine|perfect))\b',
        r'\b(let(?:\'s| us) (?:proceed|continue|go ahead))\b',
    ],
    "medium_confidence": [
        r'\b(sounds good|works for me|no changes|no issues|all set)\b',
        r'\b(ready to (?:proceed|continue|go))\b',
        r'\b(i(?:\'m| am) (?:satisfied|happy|ready))\b',
    ],
    "low_confidence": [
        r'\b(good|fine|ready|done)\b$',  # Only at end of sentence
        r'^\s*(yes|ok|proceed)\s*[.!]?\s*$',  # Simple one-word responses
    ]
}

# Patterns that indicate refinement needed (negative indicators)
REFINEMENT_NEEDED_PATTERNS = [
    r'\b(no|nope|not|never|incorrect|wrong|change|modify|different)\b',
    r'\b(wait|hold|stop|pause|reconsider)\b',
    r'\b(i want|i need|let me|can you|could you|would you|please)\b',
    r'\b(add|remove|include|exclude|filter|adjust)\b',
    r'\b(more|less|other|another|alternative)\b',
    r'\b(set|update|change|modify)\s+(time|period|date|duration|range)\b',  # Time-related modifications
    r'\b(last|past|previous|next|recent)\s+\d+\s+(day|week|month|year)s?\b',  # Time periods like "last 6 months"
    r'\b(from|to|since|until|before|after)\s+\d+\b',  # Date ranges
    r'\b(instead|rather|prefer|better|different)\b',  # Preference indicators
]

# Theme modification patterns - Enhanced for better detection
THEME_MODIFICATION_PATTERNS = {
    "add_theme": [
        r'\b(add|create|include|insert|new)\s+(?:a\s+)?theme\b',
        r'\b(add|create|include|insert)\s+(?:another|new|additional|more)\s+(?:theme|topic|category)\b',
        r'\b(i(?:\'d| would)\s+like\s+to\s+add|can\s+you\s+add|please\s+add)\b.*\b(theme|topic|category)\b',
        r'\b(missing|forgot|need)\s+(?:a\s+)?theme\s+(?:for|about|on)\b',
        r'\b(also\s+include|additionally\s+add)\b.*\b(theme|topic)\b',
        r'\bi\s+need\s+a\s+theme\s+about\b',
        r'\b(generate|make)\s+(?:a\s+)?(?:new\s+)?theme\s+(?:for|about|on)\b',
    ],
    "remove_theme": [
        r'\b(remove|delete|exclude|drop|eliminate)\s+(?:the\s+)?.*?\btheme\b',
        r'\b(don\'t\s+need|not\s+interested\s+in|not\s+relevant)\b.*\b(theme|topic)\b',
        r'\b(take\s+out|get\s+rid\s+of)\b.*\b(theme|topic)\b',
        r'\b(unnecessary|irrelevant|useless)\s+theme\b',
        r'\b(?:the\s+)?(?:\w+\s+)*theme.*(?:should\s+be\s+)?(?:removed|deleted|excluded)\b',
        r'\bremove\s+(?:the\s+)?(?:\w+\s+)*theme\b',
        r'\bdelete\s+(?:the\s+)?(?:\w+\s+)*theme\b',
        r'\bget\s+rid\s+of\s+(?:the\s+)?(?:\w+\s+)*(?:theme|topic|category)\b',
        r'\bget\s+rid\s+of\s+(?:\w+\s+)*(?:satisfaction|issues|pricing|billing|customer|product)',
    ],
    "modify_theme": [
        r'\b(modify|change|update|edit|alter|adjust)\s+(?:the\s+)?.*?\btheme\b',
        r'\b(rename|retitle|relabel)\s+(?:the\s+)?theme\b',
        r'\b(?:the\s+)?(?:\w+\s+)*theme.*(?:should\s+be\s+)?(?:changed|modified|updated)\b',
        r'\b(improve|enhance|refine)\s+(?:the\s+)?theme\b',
        r'\b(make\s+(?:the\s+)?theme\s+more)\b',
        r'\b(rephrase|reword)\s+(?:the\s+)?theme\b',
        r'\bmodify\s+(?:the\s+)?(?:\w+\s+)*theme\b',
        r'\bchange\s+(?:the\s+)?(?:\w+\s+)*theme\b',
        r'\bupdate\s+(?:the\s+)?(?:\w+\s+)*theme\b',
        r'\bupdate\s+(?:the\s+)?(?:\w+\s+)*(?:description|title|name|label)',
        r'\bchange\s+(?:the\s+)?(?:\w+\s+)*(?:description|title|name|label)',
    ],
    "create_sub_theme": [
        r'\b(sub(?:-|\s)?theme|sub(?:-|\s)?topic|sub(?:-|\s)?category)\b',
        r'\b(break\s+(?:down|up)|split|divide)\s+(?:the\s+)?.*?\btheme\b',
        r'\b(more\s+granular|more\s+detailed|more\s+specific)\s+(?:analysis|themes|breakdown)\b',
        r'\b(children\s+themes?|child\s+themes?|nested\s+themes?)\b',
        r'\b(drill\s+down|go\s+deeper)\s+(?:into|on)\b.*\b(theme|topic)\b',
        r'\b(categorize|organize|group)\s+(?:the\s+)?(?:data|content)\s+(?:under|within)\b.*\b(theme|topic)\b',
        r'\bcreate\s+sub(?:-|\s)?themes?\s+for\b',
        r'\bbreak\s+down\s+(?:the\s+)?(?:\w+\s+)*theme\b',
        r'\bgenerate\s+children\s+themes?\s+for\b',
    ]
}

# Extract target theme patterns - Enhanced for better extraction
THEME_TARGET_PATTERNS = [
    r'\btheme\s+(?:named|called|about|titled|labeled)\s+["\']?([^"\']+)["\']?\b',
    r'\b["\']([^"\']+)["\']?\s+theme\b',
    r'\bthe\s+([^,\.!?]+)\s+theme\b',
    r'\btheme\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b',
    r'\b(?:remove|delete|modify|change|update)\s+(?:the\s+)?([^,\.!?\s]+(?:\s+[^,\.!?\s]+)*)\s+theme\b',
    r'\b([^,\.!?\s]+(?:\s+[^,\.!?\s]+)*)\s+theme\s+(?:should|needs|must)\b',
    r'\bfor\s+([^,\.!?\s]+(?:\s+[^,\.!?\s]+)*)\s+theme\b',
    r'\babout\s+([^,\.!?\s]+(?:\s+[^,\.!?\s]+)*)\s+(?:theme|topic)\b',
    r'\bfor\s+([^,\.!?\s]+(?:\s+[^,\.!?\s]+)*)\b(?=\s*$)',  # "for product issues" at end
    r'\bget\s+rid\s+of\s+([^,\.!?\s]+(?:\s+[^,\.!?\s]+)*)\b',  # "get rid of customer satisfaction"
    r'\bupdate\s+(?:the\s+)?([^,\.!?\s]+(?:\s+[^,\.!?\s]+)*)\s+(?:description|title|name|label)\b',
]

def detect_approval_intent(query: str) -> Dict[str, Any]:
    """
    Analyze a user query to determine if it contains approval phrases.
    Note: This is for analysis only and should never bypass HITL verification.
    
    Args:
        query: User's input query
        
    Returns:
        Dict containing:
        - is_approval: bool - Whether this appears to be an approval (for analysis only)
        - confidence: str - Level of confidence (high/medium/low)
        - matched_patterns: List[str] - Patterns that matched
        - should_proceed: bool - Always False - human verification is always required
        - reasoning: str - Explanation of the detection
    """
    if not query or not isinstance(query, str):
        return {
            "is_approval": False,
            "confidence": "none",
            "matched_patterns": [],
            "should_proceed": False,
            "reasoning": "Empty or invalid query"
        }
    
    # Normalize query for analysis
    normalized_query = query.lower().strip()
    
    # Check for refinement needed patterns first (these override approval)
    refinement_matches = []
    for pattern in REFINEMENT_NEEDED_PATTERNS:
        if re.search(pattern, normalized_query, re.IGNORECASE):
            refinement_matches.append(pattern)
    
    if refinement_matches:
        logger.info(f"🚫 Refinement needed detected: {refinement_matches}")
        return {
            "is_approval": False,
            "confidence": "high",
            "matched_patterns": refinement_matches,
            "should_proceed": False,
            "reasoning": "Query contains refinement indicators"
        }
    
    # Check approval patterns by confidence level
    approval_matches = []
    confidence_level = "none"
    
    # Check high confidence patterns first
    for pattern in APPROVAL_PATTERNS["high_confidence"]:
        if re.search(pattern, normalized_query, re.IGNORECASE):
            approval_matches.append(pattern)
            confidence_level = "high"
    
    # If no high confidence, check medium
    if not approval_matches:
        for pattern in APPROVAL_PATTERNS["medium_confidence"]:
            if re.search(pattern, normalized_query, re.IGNORECASE):
                approval_matches.append(pattern)
                confidence_level = "medium"
    
    # If no medium confidence, check low
    if not approval_matches:
        for pattern in APPROVAL_PATTERNS["low_confidence"]:
            if re.search(pattern, normalized_query, re.IGNORECASE):
                approval_matches.append(pattern)
                confidence_level = "low"
    
    is_approval = len(approval_matches) > 0
    
    # Always require human verification regardless of confidence
    should_proceed = False
    
    reasoning = "No approval patterns detected"
    if is_approval:
        reasoning = f"Approval detected with {confidence_level} confidence - still requires human verification"
    
    logger.info(f"🤖 HITL Detection Result: approval={is_approval}, confidence={confidence_level}, proceed={should_proceed}")
    logger.info(f"📝 Query analyzed: '{query[:100]}...'")
    logger.info(f"🎯 Reasoning: {reasoning}")
    
    return {
        "is_approval": is_approval,
        "confidence": confidence_level,
        "matched_patterns": approval_matches,
        "should_proceed": should_proceed,
        "reasoning": reasoning
    }

def is_continuation_query(query: str, conversation_context: Dict[str, Any] = None) -> bool:
    """
    Determine if this query is continuing a previous conversation.
    
    Args:
        query: User's input query
        conversation_context: Previous conversation state
        
    Returns:
        bool: True if this appears to be a continuation query
    """
    if not query:
        return False
    
    continuation_indicators = [
        r'\b(also|additionally|furthermore|moreover|besides|plus)\b',
        r'\b(and|but|however|though|although)\b',
        r'\b(previous|earlier|before|last|above)\b',
        r'\b(continue|continuing|next|then)\b',
    ]
    
    normalized_query = query.lower().strip()
    
    for pattern in continuation_indicators:
        if re.search(pattern, normalized_query, re.IGNORECASE):
            return True
    
    # Check if conversation context suggests continuation
    if conversation_context:
        has_prior_messages = len(conversation_context.get("messages", [])) > 1
        has_workflow_state = conversation_context.get("refined_query") is not None
        
        if has_prior_messages and has_workflow_state:
            return True
    
    return False

def determine_hitl_action(query: str, conversation_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Function to analyze user queries for informational purposes only.
    This does NOT make auto-approval decisions - all queries require human verification.
    
    Args:
        query: User's input query
        conversation_context: Previous conversation state
        
    Returns:
        Dict containing analyzed action and reasoning (for logging only)
    """
    approval_result = detect_approval_intent(query)
    is_continuation = is_continuation_query(query, conversation_context)
    
    # Only analyze the query but NEVER auto-approve
    # This is for logging and informational purposes only
    if approval_result["is_approval"]:
        action = "potential_approval"  # Changed from "proceed_to_boolean_generator"
        reasoning = f"Approval detected but requires explicit human verification"
    else:
        action = "standard_hitl"
        reasoning = "Standard HITL verification required"
    
    return {
        "action": action,
        "reasoning": reasoning,
        "approval_analysis": approval_result,
        "is_continuation": is_continuation,
        "confidence": approval_result["confidence"]
    }

def detect_theme_modification_intent(query: str) -> Dict[str, Any]:
    """
    Detect theme modification intent from user query.
    
    Args:
        query: User's input query
        
    Returns:
        Dict containing:
        - intent: str - Type of modification (add, remove, modify, create_sub_theme, none)
        - confidence: str - Level of confidence (high/medium/low)
        - target_theme: str - Identified target theme if any
        - details: str - Extracted modification details
        - matched_patterns: List[str] - Patterns that matched
    """
    if not query or not isinstance(query, str):
        return {
            "intent": "none",
            "confidence": "none",
            "target_theme": None,
            "details": query,
            "matched_patterns": []
        }
    
    normalized_query = query.lower().strip()
    
    # Check each modification type
    for intent_type, patterns in THEME_MODIFICATION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, normalized_query, re.IGNORECASE):
                # Extract target theme if mentioned
                target_theme = extract_target_theme(query)
                
                logger.info(f"🎯 Theme modification intent detected: {intent_type}")
                return {
                    "intent": intent_type,
                    "confidence": "high",
                    "target_theme": target_theme,
                    "details": query.strip(),
                    "matched_patterns": [pattern]
                }
    
    # If no specific theme modification patterns, check for general modification
    if any(re.search(pattern, normalized_query, re.IGNORECASE) for pattern in REFINEMENT_NEEDED_PATTERNS):
        return {
            "intent": "modify",  # Default to modify for general changes
            "confidence": "medium",
            "target_theme": extract_target_theme(query),
            "details": query.strip(),
            "matched_patterns": ["general_modification"]
        }
    
    return {
        "intent": "none",
        "confidence": "none",
        "target_theme": None,
        "details": query,
        "matched_patterns": []
    }

def extract_target_theme(query: str) -> Optional[str]:
    """
    Extract the target theme name from user query.
    
    Args:
        query: User's input query
        
    Returns:
        Extracted theme name or None if not found
    """
    if not query:
        return None
    
    # Try each pattern to extract theme name
    for pattern in THEME_TARGET_PATTERNS:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            theme_name = match.group(1).strip()
            # Clean up common artifacts
            theme_name = re.sub(r'\s+', ' ', theme_name)  # Normalize whitespace
            theme_name = theme_name.strip('.,!?')  # Remove trailing punctuation
            if len(theme_name) > 2:  # Avoid single letters or very short matches
                logger.info(f"🎯 Extracted target theme: '{theme_name}'")
                return theme_name
    
    return None

def analyze_theme_query_context(query: str, themes: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Comprehensive analysis of user query in theme context.
    
    Args:
        query: User's input query
        themes: Current themes for context
        
    Returns:
        Complete analysis including approval, modification intent, and routing decision
    """
    approval_analysis = detect_approval_intent(query)
    modification_analysis = detect_theme_modification_intent(query)
    
    # Determine primary action
    if modification_analysis["intent"] != "none":
        primary_action = "theme_modification"
        routing_decision = "theme_modifier"
    elif approval_analysis["is_approval"] and approval_analysis["confidence"] in ["high", "medium"]:
        primary_action = "approval"
        routing_decision = "continue"
    else:
        primary_action = "standard_verification"
        routing_decision = "theme_hitl_verification"
    
    return {
        "primary_action": primary_action,
        "routing_decision": routing_decision,
        "approval_analysis": approval_analysis,
        "modification_analysis": modification_analysis,
        "confidence": max(approval_analysis.get("confidence", "none"), 
                         modification_analysis.get("confidence", "none")),
        "reasoning": f"Primary action: {primary_action}, Intent: {modification_analysis['intent']}"
    }
