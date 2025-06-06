"""
Intelligent HITL Detection Utility

Analyzes user queries for approval phrases, but never bypasses human verification.
All analysis is for informational purposes only - explicit human approval is always required.
"""

import re
import logging
from typing import Dict, Any, Tuple, List

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
