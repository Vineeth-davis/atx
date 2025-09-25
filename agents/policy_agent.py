# agents/policy_agent.py
# Policy Agent for query validation and safety

from typing import Dict, Any, List
import re

class PolicyAgent:
    """Agent responsible for validating queries and enforcing safety policies"""
    
    def __init__(self):
        self.forbidden_patterns = [
            r'\b(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE)\b',
            r'\b(GRANT|REVOKE|EXEC|EXECUTE)\b',
            r'--.*$',  # SQL comments
            r'/\*.*?\*/',  # SQL block comments
            r'UNION.*SELECT',  # SQL injection patterns
            r'OR\s+1\s*=\s*1',  # SQL injection patterns
        ]
    
    async def validate_question(self, question: str) -> Dict[str, Any]:
        """
        Validate user question for safety and policy compliance
        
        Args:
            question: User's natural language question
            
        Returns:
            Validation result with safety status and reason
        """
        # TODO: Implement comprehensive question validation
        # 1. Check for SQL injection patterns
        # 2. Validate question length and content
        # 3. Check for inappropriate content
        # 4. Apply rate limiting if needed
        
        validation_result = {
            "is_safe": True,
            "reason": "",
            "warnings": [],
            "suggestions": []
        }
        
        # Check for forbidden patterns
        for pattern in self.forbidden_patterns:
            if re.search(pattern, question, re.IGNORECASE):
                validation_result["is_safe"] = False
                validation_result["reason"] = f"Question contains forbidden pattern: {pattern}"
                break
        
        # Check question length
        if len(question) > 1000:
            validation_result["warnings"].append("Question is very long, consider breaking it down")
        
        if len(question) < 10:
            validation_result["warnings"].append("Question is very short, please provide more context")
        
        return validation_result
    
    async def validate_sql(self, sql: str) -> Dict[str, Any]:
        """Validate generated SQL for safety"""
        # TODO: Implement SQL validation
        # Check for DDL/DML operations
        # Validate against whitelisted tables/columns
        pass
    
    def check_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limits"""
        # TODO: Implement rate limiting
        pass
