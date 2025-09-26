# rag/advanced_sql_generator.py
# Advanced SQL generation with complex joins, CTEs, window functions, and aggregations

from typing import Dict, Any, List, Optional, Tuple
import openai
import re
import logging
from api.config import settings
from rag.retriever import SchemaRetriever

logger = logging.getLogger(__name__)

class AdvancedSQLGenerator:
    """Advanced SQL generator with support for complex joins, CTEs, window functions, and aggregations"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.schema_retriever = SchemaRetriever()
        
        # Advanced SQL patterns and capabilities
        self.sql_capabilities = {
            'joins': ['INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL OUTER JOIN', 'CROSS JOIN'],
            'ctes': ['WITH', 'RECURSIVE'],
            'window_functions': ['ROW_NUMBER()', 'RANK()', 'DENSE_RANK()', 'LAG()', 'LEAD()', 'FIRST_VALUE()', 'LAST_VALUE()', 'SUM() OVER', 'AVG() OVER', 'COUNT() OVER'],
            'aggregations': ['SUM()', 'COUNT()', 'AVG()', 'MIN()', 'MAX()', 'STDDEV()', 'VARIANCE()', 'GROUP BY', 'HAVING'],
            'subqueries': ['EXISTS', 'IN', 'ANY', 'ALL', 'SOME'],
            'advanced_functions': ['CASE WHEN', 'COALESCE', 'NULLIF', 'CAST', 'EXTRACT', 'DATE_TRUNC']
        }
    
    async def generate_advanced_sql(self, question: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate advanced SQL query with complex features
        
        Args:
            question: User's natural language question
            context: Relevant schema and data context
            
        Returns:
            Dictionary containing SQL query and metadata
        """
        try:
            # Analyze question complexity
            complexity_analysis = self._analyze_query_complexity(question)
            
            # Build advanced prompt based on complexity
            prompt = self._build_advanced_sql_prompt(question, context, complexity_analysis)
            
            # Call OpenAI API with advanced prompt
            response = await self._call_openai_api(prompt)
            
            # Parse and validate advanced SQL response
            result = self.parse_advanced_sql_response(response)
            
            # Enhanced validation for advanced SQL
            validation = self.validate_advanced_sql(result.get('sql', ''), complexity_analysis)
            result['validation'] = validation
            result['complexity_analysis'] = complexity_analysis
            
            logger.info(f"Generated advanced SQL for question: {question[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error generating advanced SQL: {e}")
            return {
                'sql': '',
                'explanation': f'Error generating advanced SQL: {str(e)}',
                'confidence': 0.0,
                'validation': {'valid': False, 'errors': [str(e)]},
                'complexity_analysis': {}
            }
    
    def _analyze_query_complexity(self, question: str) -> Dict[str, Any]:
        """
        Analyze the complexity of the query to determine which SQL features to use
        
        Args:
            question: User's natural language question
            
        Returns:
            Complexity analysis with required features
        """
        complexity_indicators = {
            'needs_joins': [
                'compare', 'across', 'between', 'join', 'combine', 'relationship',
                'industry', 'category', 'group by', 'by industry', 'by category'
            ],
            'needs_ctes': [
                'step by step', 'first calculate', 'then', 'intermediate', 'temporary',
                'recursive', 'hierarchy', 'tree', 'parent', 'child'
            ],
            'needs_window_functions': [
                'rank', 'top', 'bottom', 'percentile', 'running total', 'cumulative',
                'previous', 'next', 'lag', 'lead', 'row number', 'partition by',
                'over time', 'trend', 'growth', 'change', 'difference'
            ],
            'needs_advanced_aggregations': [
                'average', 'mean', 'median', 'mode', 'standard deviation', 'variance',
                'percentile', 'quartile', 'distribution', 'statistics', 'summary'
            ],
            'needs_subqueries': [
                'where exists', 'not in', 'greater than all', 'less than any',
                'correlated', 'nested', 'subquery'
            ],
            'needs_case_statements': [
                'if', 'when', 'condition', 'categorize', 'classify', 'group by',
                'bucket', 'segment', 'tier'
            ]
        }
        
        question_lower = question.lower()
        complexity_score = 0
        required_features = []
        
        for feature, indicators in complexity_indicators.items():
            if any(indicator in question_lower for indicator in indicators):
                required_features.append(feature)
                complexity_score += 1
        
        # Determine overall complexity level
        if complexity_score >= 4:
            complexity_level = 'high'
        elif complexity_score >= 2:
            complexity_level = 'medium'
        else:
            complexity_level = 'basic'
        
        return {
            'level': complexity_level,
            'score': complexity_score,
            'required_features': required_features,
            'indicators_found': [indicator for indicator in complexity_indicators.keys() 
                               if any(ind in question_lower for ind in complexity_indicators[indicator])]
        }
    
    def _build_advanced_sql_prompt(self, question: str, context: List[Dict[str, Any]], complexity: Dict[str, Any]) -> str:
        """Build advanced prompt based on query complexity"""
        
        # Build schema context
        schema_context = self._build_schema_context(context)
        
        # Build examples based on complexity
        examples = self._get_advanced_sql_examples(complexity)
        
        # Build feature instructions
        feature_instructions = self._build_feature_instructions(complexity)
        
        prompt = f"""
You are an expert SQL query generator specializing in advanced SQL features for financial and CRM databases. Generate sophisticated SQL queries based on the provided schema and context.

DATABASE SCHEMA:
{schema_context}

QUERY COMPLEXITY ANALYSIS:
- Level: {complexity['level']}
- Required Features: {', '.join(complexity['required_features']) if complexity['required_features'] else 'Basic query'}
- Complexity Score: {complexity['score']}/6

ADVANCED SQL CAPABILITIES AVAILABLE:
{self._format_sql_capabilities()}

FEATURE INSTRUCTIONS:
{feature_instructions}

EXAMPLE QUERIES:
{examples}

USER QUESTION: {question}

INSTRUCTIONS:
1. Generate a sophisticated SQL query that answers the user's question
2. Use only SELECT statements (no DDL/DML operations)
3. Apply appropriate advanced SQL features based on complexity analysis
4. Use proper JOINs, CTEs, window functions, or subqueries as needed
5. Include appropriate WHERE clauses, GROUP BY, HAVING, and ORDER BY
6. Format the SQL clearly with proper indentation and comments
7. Ensure the query is optimized and follows best practices

RESPONSE FORMAT:
SQL: [Your advanced SQL query here]
Explanation: [Detailed explanation of what the query does and why specific features were used]
Confidence: [0.0-1.0 confidence score]
Features Used: [List of advanced SQL features used]

Generate the advanced SQL query:
"""
        return prompt
    
    def _format_sql_capabilities(self) -> str:
        """Format SQL capabilities for the prompt"""
        capabilities_text = []
        for category, features in self.sql_capabilities.items():
            capabilities_text.append(f"{category.upper()}: {', '.join(features)}")
        return '\n'.join(capabilities_text)
    
    def _build_feature_instructions(self, complexity: Dict[str, Any]) -> str:
        """Build specific instructions based on required features"""
        instructions = []
        
        if 'needs_joins' in complexity['required_features']:
            instructions.append("""
- Use appropriate JOINs to connect related tables
- Consider LEFT JOIN for optional relationships
- Use table aliases for clarity
- Ensure proper join conditions to avoid Cartesian products
            """)
        
        if 'needs_ctes' in complexity['required_features']:
            instructions.append("""
- Use Common Table Expressions (CTEs) for complex multi-step queries
- Break down complex logic into readable CTEs
- Use WITH clause for temporary result sets
- Consider RECURSIVE CTEs for hierarchical data
            """)
        
        if 'needs_window_functions' in complexity['required_features']:
            instructions.append("""
- Use window functions for ranking, running totals, and time-series analysis
- Apply PARTITION BY for grouping within window functions
- Use ORDER BY within window functions for ranking
- Consider ROW_NUMBER(), RANK(), DENSE_RANK() for ranking
- Use LAG() and LEAD() for time-series comparisons
            """)
        
        if 'needs_advanced_aggregations' in complexity['required_features']:
            instructions.append("""
- Use advanced aggregation functions (STDDEV, VARIANCE, PERCENTILE_CONT)
- Apply GROUP BY with multiple columns for detailed grouping
- Use HAVING clause for filtering aggregated results
- Consider ROLLUP and CUBE for multi-dimensional analysis
            """)
        
        if 'needs_subqueries' in complexity['required_features']:
            instructions.append("""
- Use subqueries for complex filtering and data retrieval
- Apply EXISTS for existence checks
- Use IN/NOT IN for membership testing
- Consider correlated subqueries for row-by-row processing
            """)
        
        if 'needs_case_statements' in complexity['required_features']:
            instructions.append("""
- Use CASE WHEN statements for conditional logic
- Apply CASE in SELECT, WHERE, and ORDER BY clauses
- Use CASE for data categorization and bucketing
- Consider nested CASE statements for complex conditions
            """)
        
        return '\n'.join(instructions) if instructions else "Use basic SQL features as appropriate."
    
    def _get_advanced_sql_examples(self, complexity: Dict[str, Any]) -> str:
        """Get advanced SQL examples based on complexity"""
        
        examples = []
        
        # Basic examples
        examples.append("""
1. "What is the total revenue for all entities?"
SQL: SELECT SUM(revenue) as total_revenue FROM financial_income;
Explanation: Basic aggregation query summing all revenue values
Confidence: 0.95
Features Used: Basic aggregation
        """)
        
        # Join examples
        if 'needs_joins' in complexity['required_features']:
            examples.append("""
2. "What is the average revenue by industry?"
SQL: SELECT e.industry, AVG(fi.revenue) as avg_revenue
     FROM entities e
     INNER JOIN financial_income fi ON e.id = fi.entity_id
     GROUP BY e.industry
     ORDER BY avg_revenue DESC;
Explanation: Uses INNER JOIN to connect entities and financial data, then groups by industry
Confidence: 0.90
Features Used: JOIN, GROUP BY, ORDER BY
            """)
        
        # CTE examples
        if 'needs_ctes' in complexity['required_features']:
            examples.append("""
3. "Show me entities with above-average revenue and their profit margins"
SQL: WITH avg_revenue AS (
         SELECT AVG(revenue) as avg_rev FROM financial_income
     ),
     high_revenue_entities AS (
         SELECT e.name, fi.revenue, fi.gross_profit,
                (fi.gross_profit / fi.revenue) as profit_margin
         FROM entities e
         JOIN financial_income fi ON e.id = fi.entity_id
         CROSS JOIN avg_revenue ar
         WHERE fi.revenue > ar.avg_rev
     )
     SELECT name, revenue, profit_margin
     FROM high_revenue_entities
     ORDER BY profit_margin DESC;
Explanation: Uses CTEs to first calculate average revenue, then filter entities above average
Confidence: 0.85
Features Used: CTE, JOIN, CROSS JOIN, calculated columns
            """)
        
        # Window function examples
        if 'needs_window_functions' in complexity['required_features']:
            examples.append("""
4. "Rank entities by revenue within each industry"
SQL: SELECT e.name, e.industry, fi.revenue,
            RANK() OVER (PARTITION BY e.industry ORDER BY fi.revenue DESC) as industry_rank,
            ROW_NUMBER() OVER (ORDER BY fi.revenue DESC) as overall_rank
     FROM entities e
     JOIN financial_income fi ON e.id = fi.entity_id
     ORDER BY e.industry, industry_rank;
Explanation: Uses window functions to rank entities within industries and overall
Confidence: 0.88
Features Used: Window functions (RANK, ROW_NUMBER), PARTITION BY
            """)
        
        # Advanced aggregation examples
        if 'needs_advanced_aggregations' in complexity['required_features']:
            examples.append("""
5. "Show revenue statistics by industry with percentiles"
SQL: SELECT e.industry,
            COUNT(*) as entity_count,
            AVG(fi.revenue) as avg_revenue,
            STDDEV(fi.revenue) as revenue_stddev,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY fi.revenue) as median_revenue,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY fi.revenue) as q1_revenue,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY fi.revenue) as q3_revenue
     FROM entities e
     JOIN financial_income fi ON e.id = fi.entity_id
     GROUP BY e.industry
     HAVING COUNT(*) > 5
     ORDER BY avg_revenue DESC;
Explanation: Uses advanced aggregation functions including percentiles and standard deviation
Confidence: 0.82
Features Used: Advanced aggregations, GROUP BY, HAVING, PERCENTILE_CONT
            """)
        
        return '\n'.join(examples)
    
    def _build_schema_context(self, context: List[Dict[str, Any]]) -> str:
        """Build enhanced schema context with relationships"""
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
        
        # Build enhanced schema description with relationships
        for table_name, table_info in tables.items():
            if table_info['columns']:
                columns_desc = '\n'.join([f"  - {col['name']}: {col['description']}" for col in table_info['columns']])
                schema_parts.append(f"Table: {table_name}\nDescription: {table_info['description']}\nColumns:\n{columns_desc}")
        
        # Add relationship information
        schema_parts.append("""
TABLE RELATIONSHIPS:
- entities.id -> financial_income.entity_id (One-to-Many)
- entities.id -> financial_balance.entity_id (One-to-Many)
- entities.id -> transactions.entity_id (One-to-Many)
- entities.id -> crm_companies.entity_id (One-to-Many)
- crm_companies.id -> crm_activities.company_id (One-to-Many)
        """)
        
        return '\n\n'.join(schema_parts)
    
    async def _call_openai_api(self, prompt: str) -> str:
        """Call OpenAI API with advanced SQL generation"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert SQL query generator specializing in advanced SQL features. Generate sophisticated, optimized SQL queries with proper use of joins, CTEs, window functions, and advanced aggregations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=2000    # Increased for complex queries
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def validate_advanced_sql(self, sql: str, complexity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced validation for advanced SQL queries
        
        Args:
            sql: Generated SQL query
            complexity: Complexity analysis
            
        Returns:
            Enhanced validation result
        """
        errors = []
        warnings = []
        features_used = []
        
        if not sql or not sql.strip():
            errors.append("Empty SQL query")
            return {'valid': False, 'errors': errors, 'warnings': warnings, 'features_used': features_used}
        
        sql_upper = sql.upper()
        
        # Check for dangerous operations (same as basic validation)
        dangerous_patterns = [
            r'\b(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE)\b',
            r'\b(EXEC|EXECUTE|sp_)\b',
            r'--',  # SQL comments
            r'/\*.*?\*/',  # Block comments
            r'UNION.*SELECT',  # Union-based attacks
            r'INFORMATION_SCHEMA',  # Schema enumeration
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                if pattern == r'\b(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE)\b':
                    errors.append(f"Dangerous SQL operation detected: {pattern}")
                else:
                    warnings.append(f"Potentially risky pattern detected: {pattern}")
        
        # Check for basic SQL structure
        if not re.search(r'\bSELECT\b', sql_upper):
            errors.append("Query must contain SELECT statement")
        
        # Check for advanced features used
        if re.search(r'\b(WITH|CTE)\b', sql_upper):
            features_used.append('CTE')
        
        if re.search(r'\b(INNER JOIN|LEFT JOIN|RIGHT JOIN|FULL OUTER JOIN|CROSS JOIN)\b', sql_upper):
            features_used.append('JOIN')
        
        if re.search(r'\b(ROW_NUMBER|RANK|DENSE_RANK|LAG|LEAD|FIRST_VALUE|LAST_VALUE)\s*\(', sql_upper):
            features_used.append('WINDOW_FUNCTION')
        
        if re.search(r'\bOVER\s*\(', sql_upper):
            features_used.append('WINDOW_FUNCTION')
        
        if re.search(r'\b(STDDEV|VARIANCE|PERCENTILE_CONT|PERCENTILE_DISC)\b', sql_upper):
            features_used.append('ADVANCED_AGGREGATION')
        
        if re.search(r'\b(EXISTS|IN\s*\(|ANY|ALL|SOME)\b', sql_upper):
            features_used.append('SUBQUERY')
        
        if re.search(r'\bCASE\s+WHEN\b', sql_upper):
            features_used.append('CASE_STATEMENT')
        
        # Check for table names
        valid_tables = ['entities', 'financial_income', 'financial_balance', 'transactions', 'crm_companies', 'crm_activities']
        found_tables = re.findall(r'\b(' + '|'.join(valid_tables) + r')\b', sql_upper)
        
        if not found_tables:
            warnings.append("No recognized table names found in query")
        
        # Check if required features are present based on complexity
        missing_features = []
        for required_feature in complexity.get('required_features', []):
            feature_map = {
                'needs_joins': 'JOIN',
                'needs_ctes': 'CTE',
                'needs_window_functions': 'WINDOW_FUNCTION',
                'needs_advanced_aggregations': 'ADVANCED_AGGREGATION',
                'needs_subqueries': 'SUBQUERY',
                'needs_case_statements': 'CASE_STATEMENT'
            }
            
            if required_feature in feature_map:
                expected_feature = feature_map[required_feature]
                if expected_feature not in features_used:
                    missing_features.append(f"Expected {expected_feature} feature not found")
        
        if missing_features:
            warnings.extend(missing_features)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'features_used': features_used,
            'found_tables': found_tables,
            'complexity_match': len(missing_features) == 0
        }
    
    def parse_advanced_sql_response(self, response: str) -> Dict[str, Any]:
        """Parse OpenAI response to extract advanced SQL and metadata"""
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
            
            # Extract features used
            features_match = re.search(r'Features Used:\s*(.*?)(?=\n|$)', response, re.DOTALL | re.IGNORECASE)
            features_used = features_match.group(1).strip() if features_match else ''
            
            # Clean up SQL (remove markdown formatting if present)
            sql = re.sub(r'^```sql\s*', '', sql, flags=re.IGNORECASE)
            sql = re.sub(r'\s*```$', '', sql, flags=re.IGNORECASE)
            sql = sql.strip()
            
            return {
                'sql': sql,
                'explanation': explanation,
                'confidence': confidence,
                'features_used': features_used,
                'raw_response': response
            }
            
        except Exception as e:
            logger.error(f"Error parsing advanced SQL response: {e}")
            return {
                'sql': '',
                'explanation': f'Error parsing response: {str(e)}',
                'confidence': 0.0,
                'features_used': '',
                'raw_response': response
            }

# Global instance
advanced_sql_generator = AdvancedSQLGenerator()
