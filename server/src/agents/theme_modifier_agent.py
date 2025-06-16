"""
Theme Modifier Agent.

1. This agent's primary function is to Modify the Existing Created Themes by the Data Analyzer Agent.
2. Based on the user Interrupt from the HITL, it will perform the following either of 3 tasks:
    - Add or Remove a theme, mostly Due to a Tool / Function Call. The selection of whether to add or remove a theme can be done by pre-analyzing the query in the HITL step and invoking the respective function / tool
    - Modify an existing theme in the existing themes (one of the primary function of this agent).
    - Generate Children Theme to an existing theme(parent theme) based on the user query in the HITL step. This is done for more granular analysis of the existing parent theme, if user want to.
3. This agent uses Only Supervised Clustering, unlike the Data Analyzer Agent which uses Unsupervised Clustering.
4. This agent can also classify / cluster the existing mapped Data to a Theme, and divide them into sub-themes based on the user query in the HITL step.
"""

import logging
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import numpy as np
from langchain_core.messages import SystemMessage, HumanMessage

from src.setup.llm_setup import LLMSetup
from src.agents.query_generator_agent import QueryGeneratorAgent

logger = logging.getLogger(__name__)

class ThemeModifierAgent:
    """
    Advanced Theme Modifier Agent for supervised theme manipulation.
    
    Uses supervised clustering and LLM-guided theme generation to:
    - Add new themes based on user requirements
    - Remove irrelevant themes  
    - Modify existing theme definitions and boolean queries
    - Generate granular sub-themes for deeper analysis
    """
    
    def __init__(self, llm=None):
        """
        Initialize Theme Modifier Agent with supervised clustering capabilities.
        
        Args:
            llm: Optional LLM instance for theme generation and refinement
        """
        try:
            # Initialize LLM for theme operations
            if llm:
                self.llm = llm
            else:
                llm_setup = LLMSetup()
                self.llm = llm_setup.get_llm()
            
            # Initialize query generator for boolean query creation
            self.query_generator = QueryGeneratorAgent()
            
            # Initialize embedding model for semantic analysis
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            logger.info("✅ Theme Modifier Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Theme Modifier Agent: {e}")
            raise

    async def process_theme_modification(
        self, 
        intent: str, 
        current_themes: List[Dict[str, Any]], 
        user_request: str,
        target_theme: str = None,
        context_data: List[str] = None
    ) -> Dict[str, Any]:
        """
        Process theme modification based on user intent.
        
        Args:
            intent: Type of modification (add, remove, modify, create_sub_theme)
            current_themes: Current list of themes
            user_request: User's modification request
            target_theme: Specific theme to target (optional)
            context_data: Original data for re-clustering (optional)
            
        Returns:
            Dict containing modified themes and operation details
        """
        logger.info(f"🔧 Processing theme modification: {intent}")
        
        try:
            if intent == "add_theme":
                return await self.add_theme(current_themes, user_request, context_data)
            elif intent == "remove_theme": 
                return await self.remove_theme(current_themes, user_request, target_theme)
            elif intent == "modify_theme":
                return await self.modify_theme(current_themes, user_request, target_theme, context_data)
            elif intent == "create_sub_theme":
                return await self.generate_children_theme(current_themes, user_request, target_theme, context_data)
            else:
                logger.warning(f"⚠️ Unknown modification intent: {intent}")
                return {
                    "success": False,
                    "error": f"Unknown modification intent: {intent}",
                    "themes": current_themes
                }
                
        except Exception as e:
            logger.error(f"❌ Theme modification failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "themes": current_themes
            }

    async def add_theme(self, current_themes: List[Dict[str, Any]], user_request: str, context_data: List[str] = None) -> Dict[str, Any]:
        """
        Add a new theme based on user request.
        
        Args:
            current_themes: Current list of themes
            user_request: User's request for new theme
            context_data: Original data for semantic analysis
            
        Returns:
            Dict with updated themes list and operation details
        """
        logger.info(f"➕ Adding new theme based on request: {user_request}")
        
        try:
            # Generate new theme using LLM
            theme_prompt = f"""
            Based on the user's request, create a new theme for data analysis.
            
            User Request: "{user_request}"
            
            Current Themes: {json.dumps([t.get('theme_name', 'Unknown') for t in current_themes], indent=2)}
            
            Create a new theme that:
            1. Is distinct from existing themes
            2. Addresses the user's specific request
            3. Has a clear, descriptive name
            4. Includes relevant keywords for boolean query generation
            
            Return ONLY a JSON object with this structure:
            {{
                "theme_name": "Clear, descriptive theme name",
                "description": "Detailed description of what this theme covers",
                "keywords": ["keyword1", "keyword2", "keyword3"],
                "reasoning": "Why this theme is relevant to the user's request"
            }}
            """
            
            response = await self.llm.ainvoke([HumanMessage(content=theme_prompt)])
            
            # Parse LLM response
            new_theme_data = self._parse_llm_json_response(response.content)
            
            if not new_theme_data:
                raise ValueError("Failed to parse new theme data from LLM response")
            
            # Generate boolean query for the new theme
            boolean_query = await self._generate_boolean_query_for_theme(new_theme_data)
            
            # Create complete theme object
            new_theme = {
                "theme_name": new_theme_data["theme_name"],
                "description": new_theme_data["description"],
                "keywords": new_theme_data.get("keywords", []),
                "boolean_query": boolean_query,
                "confidence_score": 0.85,  # High confidence for user-requested themes
                "document_count": 0,  # Will be populated when data is available
                "created_by": "theme_modifier_agent",
                "creation_timestamp": datetime.now().isoformat(),
                "modification_reason": user_request
            }
            
            # Add to themes list
            updated_themes = current_themes + [new_theme]
            
            logger.info(f"✅ Successfully added new theme: {new_theme['theme_name']}")
            
            return {
                "success": True,
                "operation": "add_theme",
                "themes": updated_themes,
                "new_theme": new_theme,
                "message": f"Added new theme: '{new_theme['theme_name']}'"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to add theme: {e}")
            return {
                "success": False,
                "error": f"Failed to add theme: {str(e)}",
                "themes": current_themes
            }

    async def remove_theme(self, current_themes: List[Dict[str, Any]], user_request: str, target_theme: str = None) -> Dict[str, Any]:
        """
        Remove a theme based on user request.
        
        Args:
            current_themes: Current list of themes
            user_request: User's removal request
            target_theme: Specific theme to remove
            
        Returns:
            Dict with updated themes list and operation details
        """
        logger.info(f"➖ Removing theme based on request: {user_request}")
        
        try:
            theme_to_remove = None
            
            # Find theme to remove
            if target_theme:
                # Direct theme name provided
                for theme in current_themes:
                    if (theme.get('theme_name', '').lower() == target_theme.lower() or 
                        target_theme.lower() in theme.get('theme_name', '').lower()):
                        theme_to_remove = theme
                        break
            
            # If not found by direct match, use LLM to identify
            if not theme_to_remove:
                identification_prompt = f"""
                Based on the user's request, identify which theme should be removed.
                
                User Request: "{user_request}"
                
                Available Themes:
                {json.dumps([{
                    'index': i,
                    'theme_name': theme.get('theme_name', 'Unknown'),
                    'description': theme.get('description', 'No description')
                } for i, theme in enumerate(current_themes)], indent=2)}
                
                Return ONLY a JSON object with:
                {{
                    "theme_index": <index_number>,
                    "theme_name": "exact theme name",
                    "reasoning": "why this theme should be removed"
                }}
                
                If no clear theme can be identified, return {{"theme_index": -1}}
                """
                
                response = await self.llm.ainvoke([HumanMessage(content=identification_prompt)])
                identification_data = self._parse_llm_json_response(response.content)
                
                if identification_data and identification_data.get("theme_index", -1) >= 0:
                    theme_index = identification_data["theme_index"]
                    if 0 <= theme_index < len(current_themes):
                        theme_to_remove = current_themes[theme_index]
            
            if not theme_to_remove:
                return {
                    "success": False,
                    "error": "Could not identify theme to remove based on request",
                    "themes": current_themes,
                    "message": "Please specify which theme you want to remove more clearly."
                }
            
            # Remove the theme
            updated_themes = [t for t in current_themes if t != theme_to_remove]
            
            logger.info(f"✅ Successfully removed theme: {theme_to_remove.get('theme_name')}")
            
            return {
                "success": True,
                "operation": "remove_theme",
                "themes": updated_themes,
                "removed_theme": theme_to_remove,
                "message": f"Removed theme: '{theme_to_remove.get('theme_name')}'"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to remove theme: {e}")
            return {
                "success": False,
                "error": f"Failed to remove theme: {str(e)}",
                "themes": current_themes
            }

    async def modify_theme(self, current_themes: List[Dict[str, Any]], user_request: str, target_theme: str = None, context_data: List[str] = None) -> Dict[str, Any]:
        """
        Modify an existing theme based on user request.
        
        Args:
            current_themes: Current list of themes
            user_request: User's modification request
            target_theme: Specific theme to modify
            context_data: Original data for re-analysis
            
        Returns:
            Dict with updated themes list and operation details
        """
        logger.info(f"🔧 Modifying theme based on request: {user_request}")
        
        try:
            theme_to_modify = None
            theme_index = -1
            
            # Find theme to modify
            if target_theme:
                for i, theme in enumerate(current_themes):
                    if (theme.get('theme_name', '').lower() == target_theme.lower() or 
                        target_theme.lower() in theme.get('theme_name', '').lower()):
                        theme_to_modify = theme
                        theme_index = i
                        break
            
            # If not found by direct match, use LLM to identify
            if not theme_to_modify:
                identification_prompt = f"""
                Based on the user's request, identify which theme should be modified.
                
                User Request: "{user_request}"
                
                Available Themes:
                {json.dumps([{
                    'index': i,
                    'theme_name': theme.get('theme_name', 'Unknown'),
                    'description': theme.get('description', 'No description')
                } for i, theme in enumerate(current_themes)], indent=2)}
                
                Return ONLY a JSON object with:
                {{
                    "theme_index": <index_number>,
                    "theme_name": "exact theme name",
                    "reasoning": "why this theme should be modified"
                }}
                
                If no clear theme can be identified, return {{"theme_index": -1}}
                """
                
                response = await self.llm.ainvoke([HumanMessage(content=identification_prompt)])
                identification_data = self._parse_llm_json_response(response.content)
                
                if identification_data and identification_data.get("theme_index", -1) >= 0:
                    theme_index = identification_data["theme_index"]
                    if 0 <= theme_index < len(current_themes):
                        theme_to_modify = current_themes[theme_index]
            
            if not theme_to_modify:
                return {
                    "success": False,
                    "error": "Could not identify theme to modify based on request",
                    "themes": current_themes,
                    "message": "Please specify which theme you want to modify more clearly."
                }
            
            # Generate modified theme using LLM
            modification_prompt = f"""
            Modify the existing theme based on the user's request.
            
            Current Theme:
            {json.dumps(theme_to_modify, indent=2)}
            
            User Modification Request: "{user_request}"
            
            Modify the theme to address the user's request while maintaining its core purpose.
            You can change:
            - Theme name (if requested)
            - Description (to be more accurate or comprehensive)
            - Keywords (add, remove, or refine)
            - Any other aspects mentioned in the request
            
            Return ONLY a JSON object with the complete modified theme:
            {{
                "theme_name": "Updated theme name",
                "description": "Updated description",
                "keywords": ["updated", "keyword", "list"],
                "modification_summary": "Brief summary of what was changed",
                "reasoning": "Why these changes address the user's request"
            }}
            """
            
            response = await self.llm.ainvoke([HumanMessage(content=modification_prompt)])
            modified_data = self._parse_llm_json_response(response.content)
            
            if not modified_data:
                raise ValueError("Failed to parse modified theme data from LLM response")
            
            # Generate new boolean query for modified theme
            boolean_query = await self._generate_boolean_query_for_theme(modified_data)
            
            # Update the theme
            updated_theme = {
                **theme_to_modify,  # Keep original fields
                "theme_name": modified_data["theme_name"],
                "description": modified_data["description"], 
                "keywords": modified_data.get("keywords", theme_to_modify.get("keywords", [])),
                "boolean_query": boolean_query,
                "last_modified": datetime.now().isoformat(),
                "modification_reason": user_request,
                "modification_summary": modified_data.get("modification_summary", "Theme updated")
            }
            
            # Update themes list
            updated_themes = current_themes.copy()
            updated_themes[theme_index] = updated_theme
            
            logger.info(f"✅ Successfully modified theme: {updated_theme['theme_name']}")
            
            return {
                "success": True,
                "operation": "modify_theme",
                "themes": updated_themes,
                "original_theme": theme_to_modify,
                "modified_theme": updated_theme,
                "message": f"Modified theme: '{updated_theme['theme_name']}' - {modified_data.get('modification_summary', 'Updated')}"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to modify theme: {e}")
            return {
                "success": False,
                "error": f"Failed to modify theme: {str(e)}",
                "themes": current_themes
            }

    async def generate_children_theme(self, current_themes: List[Dict[str, Any]], user_request: str, target_theme: str = None, context_data: List[str] = None) -> Dict[str, Any]:
        """
        Generate sub-themes (children) for an existing theme.
        
        Args:
            current_themes: Current list of themes
            user_request: User's request for sub-themes
            target_theme: Parent theme to create sub-themes for
            context_data: Original data for supervised clustering
            
        Returns:
            Dict with updated themes including sub-themes
        """
        logger.info(f"🌿 Generating sub-themes based on request: {user_request}")
        
        try:
            parent_theme = None
            parent_index = -1
            
            # Find parent theme
            if target_theme:
                for i, theme in enumerate(current_themes):
                    if (theme.get('theme_name', '').lower() == target_theme.lower() or 
                        target_theme.lower() in theme.get('theme_name', '').lower()):
                        parent_theme = theme
                        parent_index = i
                        break
            
            # If not found by direct match, use LLM to identify
            if not parent_theme:
                identification_prompt = f"""
                Based on the user's request, identify which theme should be broken down into sub-themes.
                
                User Request: "{user_request}"
                
                Available Themes:
                {json.dumps([{
                    'index': i,
                    'theme_name': theme.get('theme_name', 'Unknown'),
                    'description': theme.get('description', 'No description')
                } for i, theme in enumerate(current_themes)], indent=2)}
                
                Return ONLY a JSON object with:
                {{
                    "theme_index": <index_number>,
                    "theme_name": "exact theme name",
                    "reasoning": "why this theme should have sub-themes"
                }}
                
                If no clear theme can be identified, return {{"theme_index": -1}}
                """
                
                response = await self.llm.ainvoke([HumanMessage(content=identification_prompt)])
                identification_data = self._parse_llm_json_response(response.content)
                
                if identification_data and identification_data.get("theme_index", -1) >= 0:
                    parent_index = identification_data["theme_index"]
                    if 0 <= parent_index < len(current_themes):
                        parent_theme = current_themes[parent_index]
            
            if not parent_theme:
                return {
                    "success": False,
                    "error": "Could not identify parent theme for sub-theme generation",
                    "themes": current_themes,
                    "message": "Please specify which theme you want to break down into sub-themes."
                }
            
            # Generate sub-themes using LLM
            sub_theme_prompt = f"""
            Generate 3-5 granular sub-themes for the given parent theme based on the user's request.
            
            Parent Theme:
            {json.dumps(parent_theme, indent=2)}
            
            User Request: "{user_request}"
            
            Create sub-themes that:
            1. Are more specific aspects of the parent theme
            2. Don't overlap significantly with each other
            3. Together cover the main aspects of the parent theme
            4. Address the user's specific request for granularity
            
            Return ONLY a JSON array of sub-themes:
            [
                {{
                    "theme_name": "Specific sub-theme name",
                    "description": "Detailed description of this sub-aspect",
                    "keywords": ["specific", "keywords", "for", "this", "sub-theme"],
                    "parent_theme": "{parent_theme.get('theme_name', 'Unknown')}",
                    "reasoning": "Why this sub-theme is relevant"
                }},
                ...
            ]
            """
            
            response = await self.llm.ainvoke([HumanMessage(content=sub_theme_prompt)])
            sub_themes_data = self._parse_llm_json_response(response.content)
            
            if not sub_themes_data or not isinstance(sub_themes_data, list):
                raise ValueError("Failed to parse sub-themes data from LLM response")
            
            # Generate complete sub-theme objects
            new_sub_themes = []
            for i, sub_theme_data in enumerate(sub_themes_data):
                # Generate boolean query
                boolean_query = await self._generate_boolean_query_for_theme(sub_theme_data)
                
                sub_theme = {
                    "theme_name": f"{parent_theme.get('theme_name', 'Parent')} - {sub_theme_data['theme_name']}",
                    "description": sub_theme_data["description"],
                    "keywords": sub_theme_data.get("keywords", []),
                    "boolean_query": boolean_query,
                    "confidence_score": 0.80,  # Slightly lower than parent
                    "document_count": 0,
                    "parent_theme": parent_theme.get("theme_name"),
                    "is_sub_theme": True,
                    "sub_theme_level": 1,
                    "created_by": "theme_modifier_agent",
                    "creation_timestamp": datetime.now().isoformat(),
                    "creation_reason": user_request
                }
                
                new_sub_themes.append(sub_theme)
            
            # Update parent theme to indicate it has sub-themes
            updated_parent = {
                **parent_theme,
                "has_sub_themes": True,
                "sub_theme_count": len(new_sub_themes),
                "last_modified": datetime.now().isoformat()
            }
            
            # Create updated themes list
            updated_themes = current_themes.copy()
            updated_themes[parent_index] = updated_parent
            updated_themes.extend(new_sub_themes)
            
            logger.info(f"✅ Successfully generated {len(new_sub_themes)} sub-themes for: {parent_theme.get('theme_name')}")
            
            return {
                "success": True,
                "operation": "create_sub_themes",
                "themes": updated_themes,
                "parent_theme": updated_parent,
                "sub_themes": new_sub_themes,
                "message": f"Created {len(new_sub_themes)} sub-themes for '{parent_theme.get('theme_name')}'"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to generate sub-themes: {e}")
            return {
                "success": False,
                "error": f"Failed to generate sub-themes: {str(e)}",
                "themes": current_themes
            }

    async def _generate_boolean_query_for_theme(self, theme_data: Dict[str, Any]) -> str:
        """
        Generate boolean query for a theme using the Query Generator Agent.
        
        Args:
            theme_data: Theme data containing name, description, and keywords
            
        Returns:
            Generated boolean query string
        """
        try:
            # Create a mock state for query generation
            mock_state = {
                "refined_query": f"Find data related to {theme_data.get('theme_name', 'theme')}",
                "keywords": theme_data.get("keywords", []),
                "themes": [theme_data]
            }
            
            # Use query generator to create boolean query
            result = await self.query_generator.generate_boolean_queries(mock_state)
            
            if result.get("themes") and len(result["themes"]) > 0:
                return result["themes"][0].get("boolean_query", "")
            
            # Fallback: Create simple boolean query from keywords
            keywords = theme_data.get("keywords", [])
            if keywords:
                return " OR ".join([f'"{keyword}"' for keyword in keywords[:5]])
            
            return f'"{theme_data.get("theme_name", "theme")}"'
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to generate boolean query, using fallback: {e}")
            # Simple fallback
            keywords = theme_data.get("keywords", [])
            if keywords:
                return " OR ".join([f'"{keyword}"' for keyword in keywords[:3]])
            return f'"{theme_data.get("theme_name", "theme")}"'

    def _parse_llm_json_response(self, response_content: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON response from LLM, handling common formatting issues.
        
        Args:
            response_content: Raw LLM response content
            
        Returns:
            Parsed JSON object or None if parsing fails
        """
        try:
            # Clean up response
            content = response_content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            content = content.strip()
            
            # Parse JSON
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ Failed to parse LLM JSON response: {e}")
            logger.debug(f"Raw response: {response_content}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error parsing LLM response: {e}")
            return None