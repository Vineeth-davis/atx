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
    
    def __init__(self, namespace: str = "default", dialect: str = "sqlserver"):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        # Namespaced retriever to avoid cross-dataset contamination
        self.schema_retriever = SchemaRetriever(namespace=namespace)
        # Dialect hint to guide SQL generation (sqlserver, postgresql, mysql)
        self.dialect = dialect
        # Store namespace for use in examples and other methods
        self.namespace = namespace
    
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
            
            # Parse
            result = self.parse_sql_response(response)

            # Enforce dialect-specific identifier formatting using context
            try:
                fixed_sql = self._enforce_identifiers(result.get('sql', ''), context)
                result['sql'] = fixed_sql
            except Exception:
                pass
            
            # Validate SQL for safety using active schema context
            validation = self.validate_sql(result.get('sql', ''), context)
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
    
    def validate_sql(self, sql: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
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
        
        # Build valid table list dynamically from context
        context_tables: List[str] = []
        for item in context or []:
            if item.get('type') == 'table':
                context_tables.append(item.get('table', ''))
        # Normalize and dedupe
        context_tables = [t for t in {t for t in context_tables if t}]
        # Create matching patterns: raw name, bracketed name for SQL Server
        found_tables: List[str] = []
        for t in context_tables:
            t_simple = t.strip()
            # Accept either schema-qualified or plain table segment match
            parts = t_simple.split('.')
            plain = parts[-1]
            patterns = [re.escape(t_simple), re.escape(plain)]
            if self.dialect == 'sqlserver':
                # [schema].[Table] and [Table]
                if len(parts) == 2:
                    patterns.append(re.escape(f"[{parts[0]}].[{parts[1]})").replace('\\)', ']'))
                    patterns.append(re.escape(f"[{parts[1]}]"))
            for p in patterns:
                if re.search(rf"\b{p}\b", sql, flags=re.IGNORECASE):
                    found_tables.append(t_simple)
                    break
        if not found_tables and context_tables:
            warnings.append("No context table names detected in generated SQL; results may be inaccurate")
        
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
        
        # Debug: Log the context to see what tables are being used
        logger.info(f"Schema context for namespace '{self.namespace}': {len(context)} items")
        table_names = [item.get('table', '') for item in context if item.get('type') == 'table']
        logger.info(f"Tables in context: {table_names}")
        
        # Build examples
        examples = self._get_sql_examples(context)
        
        prompt = f"""
You are an expert SQL query generator. Generate accurate, safe SQL for the target database dialect.

TARGET DIALECT: {self.dialect}
Dialect specifics:
- sqlserver: TOP, OFFSET/FETCH, GETDATE(), DATEADD, []-quoted identifiers
- postgresql: LIMIT/OFFSET, NOW(), INTERVAL, ""-quoted identifiers

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
 7. Output SQL for the TARGET DIALECT strictly
 8. Use EXACT identifier names from DATABASE SCHEMA. Do NOT convert names to snake_case or pluralize.
 9. For sqlserver, always bracket identifiers: [schema].[TableName] and [ColumnName]. If schema is present in context, include it.

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
    
    def _get_sql_examples(self, context: List[Dict[str, Any]] = None) -> str:
        """Get example SQL queries for common patterns based on actual schema context"""
        if not context:
            return "No schema context available for examples"
        
        # Extract table names from context
        tables = {}
        for item in context:
            if item.get('type') == 'table':
                table_name = item.get('table', '')
                namespace = item.get('namespace', '')
                # Only use tables from the correct namespace
                if table_name and namespace == self.namespace:
                    tables[table_name] = item.get('description', f'Table {table_name}')
        
        if not tables:
            return "No tables found in schema context"
        
        # Get first few tables for examples
        table_list = list(tables.keys())[:3]
        if len(table_list) < 2:
            return f"SELECT * FROM {table_list[0]};" if table_list else "No tables available"
        
        # Create dynamic examples based on actual schema
        table1 = table_list[0]
        table2 = table_list[1] if len(table_list) > 1 else table_list[0]
        
        examples = f"""
1. "Show me all records from {table1}"
SQL: SELECT * FROM {table1};
Explanation: Retrieves all records from the {table1} table
Confidence: 0.95

2. "Show me records from {table1} with specific criteria"
SQL: SELECT * FROM {table1} WHERE [condition] = 'value';
Explanation: Filters records from {table1} based on specific criteria
Confidence: 0.90
"""
        
        if len(table_list) > 1:
            examples += f"""
3. "Show me data from both {table1} and {table2}"
SQL: SELECT t1.*, t2.* FROM {table1} t1 JOIN {table2} t2 ON t1.id = t2.related_id;
Explanation: Joins {table1} and {table2} tables to show related data
Confidence: 0.85
"""
        
        return examples
    
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

    def _enforce_identifiers(self, sql: str, context: List[Dict[str, Any]]) -> str:
        """Rewrite table/column identifiers to match context exactly.

        - Maps snake_case identifiers to exact SQL Server PascalCase names
        - Handles both table names and column names from schema context
        - Only runs for sqlserver dialect.
        """
        if not sql or self.dialect != 'sqlserver' or not context:
            return sql

        def norm(s: str) -> str:
            return re.sub(r'[^a-z0-9]', '', s.lower())

        # Build comprehensive identifier maps
        table_map = {}  # normalized -> exact qualified (schema.Table)
        short_table_map = {}  # normalized -> exact Table
        column_map = {}  # normalized -> exact Column
        
        for item in context:
            if item.get('type') == 'table':
                qual = item.get('table', '')  # e.g., dbo.PurchaseOrders
                if not qual:
                    continue
                parts = qual.split('.')
                if len(parts) == 2:
                    schema, table = parts
                else:
                    schema, table = 'dbo', parts[-1]
                # Check if table name is already bracketed
                if table.startswith('[') and table.endswith(']'):
                    bracketed_table = table
                else:
                    bracketed_table = f"[{table}]"
                
                table_map[norm(qual)] = f"[{schema}].{bracketed_table}"
                short_table_map[norm(table)] = f"[{schema}].{bracketed_table}"
                # Add snake_case mapping
                short_table_map[norm(table.lower().replace('_', ''))] = f"[{schema}].{bracketed_table}"
                short_table_map[table.lower().replace('_', '')] = f"[{schema}].{bracketed_table}"
                
            elif item.get('type') == 'column':
                table_name = item.get('table', '')  # e.g., dbo.PurchaseOrders
                column_name = item.get('column', '')  # e.g., Id, BaseId, RevisionNumber
                if table_name and column_name:
                    # Map snake_case column names to PascalCase
                    column_map[norm(column_name)] = f"[{column_name}]"
                    # Also map common snake_case patterns
                    snake_case = column_name.lower().replace('_', '')
                    if snake_case != norm(column_name):
                        column_map[snake_case] = f"[{column_name}]"
                    
                    # Add common snake_case mappings for typical column names
                    if column_name == 'Id':
                        column_map[norm('po_number')] = '[Id]'
                        column_map[norm('id')] = '[Id]'
                    elif column_name == 'CreatedDate':
                        column_map[norm('order_date')] = '[CreatedDate]'
                        column_map[norm('created_date')] = '[CreatedDate]'
                    elif column_name == 'Total':
                        column_map[norm('total_amount')] = '[Total]'
                        column_map[norm('amount')] = '[Total]'

        # Replace identifiers in SQL
        fixed_sql = sql
        
        # First pass: Replace table names in FROM/JOIN clauses
        for key, exact in {**short_table_map, **table_map}.items():
            # Pattern for table names in FROM/JOIN (not aliases)
            table_pattern = re.compile(rf'\b({re.escape(key)})\b(?=\s+(?:as\s+)?[a-zA-Z_][a-zA-Z0-9_]*\s*(?:,|$|\n|;))', re.IGNORECASE)
            def table_repl(m):
                tok = m.group(1)
                return exact if tok.lower() == key.lower() else tok
            fixed_sql = table_pattern.sub(table_repl, fixed_sql)
            
            # Also try a simpler pattern for table names
            simple_pattern = re.compile(rf'\b({re.escape(key)})\b', re.IGNORECASE)
            def simple_repl(m):
                tok = m.group(1)
                return exact if tok.lower() == key.lower() else tok
            fixed_sql = simple_pattern.sub(simple_repl, fixed_sql)
        
        # Second pass: Replace column names (after table aliases)
        for key, exact in column_map.items():
            # Pattern for column references (after table.alias)
            column_pattern = re.compile(rf'\.([A-Za-z0-9_]+)\b', re.IGNORECASE)
            def column_repl(m):
                tok = m.group(1)
                return f".{exact}" if norm(tok) == key else m.group(0)
            fixed_sql = column_pattern.sub(column_repl, fixed_sql)
            
            # Also replace standalone column names in SELECT, WHERE, ORDER BY
            standalone_pattern = re.compile(rf'\b([A-Za-z0-9_]+)\b(?=\s*(?:,|FROM|WHERE|ORDER|GROUP|HAVING|$))', re.IGNORECASE)
            def standalone_repl(m):
                tok = m.group(1)
                return exact if norm(tok) == key else tok
            fixed_sql = standalone_pattern.sub(standalone_repl, fixed_sql)

        return fixed_sql
