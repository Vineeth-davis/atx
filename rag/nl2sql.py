# rag/nl2sql.py
# Natural Language to SQL generation

from typing import Dict, Any, List, Optional
import openai
import re
import logging
from api.config import settings
from rag.retriever import SchemaRetriever

logger = logging.getLogger(__name__)

class NL2SQLGenerator:
    """Converts natural language questions to SQL queries"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.schema_retriever = SchemaRetriever()
    
    async def generate_sql(self, question: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate SQL query from natural language question
        
        Args:
            question: User's natural language question
            context: Relevant schema and data context
            
        Returns:
            Dictionary containing SQL query and metadata
        """
        try:
            # Build prompt with question and context
            prompt = self.build_sql_prompt(question, context)
            
            # Call OpenAI API with structured prompt
            response = await self._call_openai_api(prompt)
            
            # Parse and validate SQL response
            result = self.parse_sql_response(response)
            
            # Validate SQL for safety
            validation = self.validate_sql(result.get('sql', ''))
            result['validation'] = validation
            
            logger.info(f"Generated SQL for question: {question[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            return {
                'sql': '',
                'explanation': f'Error generating SQL: {str(e)}',
                'confidence': 0.0,
                'validation': {'valid': False, 'errors': [str(e)]}
            }
    
    async def _call_openai_api(self, prompt: str) -> str:
        """Call OpenAI API to generate SQL"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert SQL query generator. Generate accurate, safe SQL queries based on the provided schema and context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for more consistent results
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def validate_sql(self, sql: str) -> Dict[str, Any]:
        """
        Validate generated SQL for safety and correctness
        
        Args:
            sql: Generated SQL query
            
        Returns:
            Validation result with errors if any
        """
        errors = []
        warnings = []
        
        if not sql or not sql.strip():
            errors.append("Empty SQL query")
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        # Check for dangerous operations
        dangerous_patterns = [
            r'\b(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE)\b',
            r'\b(EXEC|EXECUTE|sp_)\b',
            r'--',  # SQL comments
            r'/\*.*?\*/',  # Block comments
            r'UNION.*SELECT',  # Union-based attacks
            r'INFORMATION_SCHEMA',  # Schema enumeration
        ]
        
        sql_upper = sql.upper()
        for pattern in dangerous_patterns:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                if pattern == r'\b(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE)\b':
                    errors.append(f"Dangerous SQL operation detected: {pattern}")
                else:
                    warnings.append(f"Potentially risky pattern detected: {pattern}")
        
        # Check for basic SQL structure
        if not re.search(r'\bSELECT\b', sql_upper):
            errors.append("Query must contain SELECT statement")
        
        # Check for table names (basic validation)
        valid_tables = ['entities', 'financial_income', 'financial_balance', 'transactions', 'crm_companies', 'crm_activities']
        found_tables = re.findall(r'\b(' + '|'.join(valid_tables) + r')\b', sql_upper)
        
        if not found_tables:
            warnings.append("No recognized table names found in query")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'found_tables': found_tables
        }
    
    def build_sql_prompt(self, question: str, context: List[Dict[str, Any]]) -> str:
        """Build structured prompt for SQL generation"""
        
        # Build schema context
        schema_context = self._build_schema_context(context)
        
        # Build examples
        examples = self._get_sql_examples()
        
        prompt = f"""
You are an expert SQL query generator for a financial and CRM database. Generate accurate SQL queries based on the provided schema and context.

DATABASE SCHEMA:
{schema_context}

EXAMPLE QUERIES:
{examples}

USER QUESTION: {question}

INSTRUCTIONS:
1. Generate a SQL query that answers the user's question
2. Use only SELECT statements (no DDL/DML operations)
3. Use proper JOINs when needed to connect related tables
4. Include appropriate WHERE clauses for filtering
5. Use aggregate functions (SUM, COUNT, AVG, etc.) when appropriate
6. Format the SQL clearly with proper indentation

RESPONSE FORMAT:
SQL: [Your SQL query here]
Explanation: [Brief explanation of what the query does]
Confidence: [0.0-1.0 confidence score]

Generate the SQL query:
"""
        return prompt
    
    def _build_schema_context(self, context: List[Dict[str, Any]]) -> str:
        """Build schema context from retrieved information"""
        if not context:
            return "No schema context available"
        
        schema_parts = []
        
        # Group by table
        tables = {}
        for item in context:
            table = item.get('table', 'unknown')
            if table not in tables:
                tables[table] = {'columns': [], 'description': item.get('description', '')}
            
            if item.get('type') == 'column':
                tables[table]['columns'].append({
                    'name': item.get('column', ''),
                    'description': item.get('description', '')
                })
        
        # Build schema description
        for table_name, table_info in tables.items():
            if table_info['columns']:
                columns_desc = '\n'.join([f"  - {col['name']}: {col['description']}" for col in table_info['columns']])
                schema_parts.append(f"Table: {table_name}\nDescription: {table_info['description']}\nColumns:\n{columns_desc}")
        
        return '\n\n'.join(schema_parts)
    
    def _get_sql_examples(self) -> str:
        """Get example SQL queries for common patterns"""
        return """
1. "What is the total revenue for all entities?"
SQL: SELECT SUM(revenue) as total_revenue FROM financial_income;
Explanation: Sums all revenue values from the financial_income table
Confidence: 0.95

2. "Show me companies in the tech industry"
SQL: SELECT name, industry, country FROM entities WHERE industry = 'Tech';
Explanation: Filters entities by industry to show only tech companies
Confidence: 0.90

3. "What is the average net income by industry?"
SQL: SELECT e.industry, AVG(fi.net_income) as avg_net_income 
     FROM entities e 
     JOIN financial_income fi ON e.id = fi.entity_id 
     GROUP BY e.industry;
Explanation: Joins entities and financial_income tables to calculate average net income by industry
Confidence: 0.85

4. "Show me the top 5 entities by revenue"
SQL: SELECT e.name, fi.revenue 
     FROM entities e 
     JOIN financial_income fi ON e.id = fi.entity_id 
     ORDER BY fi.revenue DESC 
     LIMIT 5;
Explanation: Joins tables and orders by revenue to show top performers
Confidence: 0.90
"""
    
    def parse_sql_response(self, response: str) -> Dict[str, Any]:
        """Parse OpenAI response to extract SQL and metadata"""
        try:
            # Extract SQL query
            sql_match = re.search(r'SQL:\s*(.*?)(?=Explanation:|$)', response, re.DOTALL | re.IGNORECASE)
            sql = sql_match.group(1).strip() if sql_match else ''
            
            # Extract explanation
            explanation_match = re.search(r'Explanation:\s*(.*?)(?=Confidence:|$)', response, re.DOTALL | re.IGNORECASE)
            explanation = explanation_match.group(1).strip() if explanation_match else ''
            
            # Extract confidence
            confidence_match = re.search(r'Confidence:\s*([0-9.]+)', response, re.IGNORECASE)
            confidence = float(confidence_match.group(1)) if confidence_match else 0.5
            
            # Clean up SQL (remove markdown formatting if present)
            sql = re.sub(r'^```sql\s*', '', sql, flags=re.IGNORECASE)
            sql = re.sub(r'\s*```$', '', sql, flags=re.IGNORECASE)
            sql = sql.strip()
            
            return {
                'sql': sql,
                'explanation': explanation,
                'confidence': confidence,
                'raw_response': response
            }
            
        except Exception as e:
            logger.error(f"Error parsing SQL response: {e}")
            return {
                'sql': '',
                'explanation': f'Error parsing response: {str(e)}',
                'confidence': 0.0,
                'raw_response': response
            }
