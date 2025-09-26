# agents/analysis_agent.py
# Advanced Analysis Agent for reasoning, validation, and formatting

from typing import Dict, Any, List, Optional, Union
import openai
import logging
import json
import re
from datetime import datetime
from api.config import settings

logger = logging.getLogger(__name__)

class AnalysisAgent:
    """Advanced Analysis Agent for reasoning, validation, and human-friendly formatting"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def analyze_results(
        self, 
        execution_result: Dict[str, Any], 
        question: str, 
        sql_result: Dict[str, Any],
        context_used: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis of query results with reasoning and validation
        
        Args:
            execution_result: SQL execution results
            question: Original user question
            sql_result: Generated SQL and metadata
            context_used: Schema context used for retrieval
            
        Returns:
            Dictionary with analyzed answer, reasoning, validation, and insights
        """
        try:
            logger.info("🧠 Analysis Agent: Starting comprehensive analysis...")
            
            # Step 1: Validate execution results
            validation_result = self._validate_execution_results(execution_result, question)
            
            # Step 2: Generate reasoning and insights
            reasoning_result = await self._generate_reasoning(
                execution_result, question, sql_result, context_used
            )
            
            # Step 3: Format human-friendly answer
            formatted_answer = await self._format_answer(
                execution_result, question, reasoning_result, validation_result
            )
            
            # Step 4: Generate insights and recommendations
            insights = await self._generate_insights(
                execution_result, question, reasoning_result
            )
            
            result = {
                'answer': formatted_answer,
                'reasoning': reasoning_result,
                'validation': validation_result,
                'insights': insights,
                'confidence': self._calculate_confidence(validation_result, reasoning_result),
                'data_preview': self._create_data_preview(execution_result),
                'summary': self._generate_summary(execution_result, reasoning_result)
            }
            
            logger.info("✅ Analysis Agent: Analysis completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Analysis Agent error: {e}")
            return self._create_fallback_response(execution_result, question, str(e))
    
    def _validate_execution_results(self, execution_result: Dict[str, Any], question: str) -> Dict[str, Any]:
        """Validate SQL execution results and check for data quality issues"""
        validation = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'data_quality': {}
        }
        
        if not execution_result.get('success', False):
            validation['is_valid'] = False
            validation['errors'].append(f"SQL execution failed: {execution_result.get('error', 'Unknown error')}")
            return validation
        
        data = execution_result.get('data', [])
        row_count = execution_result.get('row_count', 0)
        
        # Check for empty results
        if row_count == 0:
            validation['warnings'].append("Query returned no results - this might indicate no matching data")
        
        # Check for suspiciously large result sets
        if row_count > 1000:
            validation['warnings'].append(f"Large result set ({row_count} rows) - consider adding filters")
        
        # Check data quality
        if data:
            validation['data_quality'] = self._assess_data_quality(data)
        
        return validation
    
    def _assess_data_quality(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess the quality of returned data"""
        if not data:
            return {}
        
        quality_metrics = {
            'null_percentage': {},
            'data_types': {},
            'value_ranges': {},
            'uniqueness': {}
        }
        
        # Analyze each column
        columns = list(data[0].keys()) if data else []
        
        for col in columns:
            values = [row.get(col) for row in data if col in row]
            
            # Null percentage
            null_count = sum(1 for v in values if v is None)
            quality_metrics['null_percentage'][col] = (null_count / len(values)) * 100
            
            # Data types
            types = [type(v).__name__ for v in values if v is not None]
            quality_metrics['data_types'][col] = max(set(types), key=types.count) if types else 'unknown'
            
            # Value ranges for numeric data
            numeric_values = [v for v in values if isinstance(v, (int, float)) and v is not None]
            if numeric_values:
                quality_metrics['value_ranges'][col] = {
                    'min': min(numeric_values),
                    'max': max(numeric_values),
                    'avg': sum(numeric_values) / len(numeric_values)
                }
            
            # Uniqueness
            unique_values = set(v for v in values if v is not None)
            quality_metrics['uniqueness'][col] = len(unique_values) / len(values) if values else 0
        
        return quality_metrics
    
    async def _generate_reasoning(
        self, 
        execution_result: Dict[str, Any], 
        question: str, 
        sql_result: Dict[str, Any],
        context_used: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate reasoning about the query and results using AI"""
        try:
            # Prepare context for reasoning
            data_summary = self._create_data_summary(execution_result)
            sql_query = sql_result.get('sql', '')
            sql_explanation = sql_result.get('explanation', '')
            
            # Build reasoning prompt
            reasoning_prompt = f"""
You are an expert data analyst. Analyze the following query execution and provide reasoning:

USER QUESTION: {question}

GENERATED SQL: {sql_query}

SQL EXPLANATION: {sql_explanation}

EXECUTION RESULTS:
{data_summary}

CONTEXT USED: {json.dumps(context_used[:3], indent=2) if context_used else 'None'}

Please provide:
1. REASONING: Why this SQL query was generated for this question
2. INTERPRETATION: What the results mean in business context
3. VALIDATION: Whether the results make sense
4. INSIGHTS: Key findings from the data
5. LIMITATIONS: Any limitations or caveats

Format your response as JSON with these keys: reasoning, interpretation, validation, insights, limitations
"""
            
            response = await self._call_openai_api(reasoning_prompt)
            
            # Parse the response
            try:
                reasoning_data = json.loads(response)
                return reasoning_data
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    'reasoning': response,
                    'interpretation': 'AI reasoning generated',
                    'validation': 'Results appear valid',
                    'insights': 'See reasoning for details',
                    'limitations': 'None identified'
                }
                
        except Exception as e:
            logger.error(f"Error generating reasoning: {e}")
            return {
                'reasoning': f'Unable to generate AI reasoning: {str(e)}',
                'interpretation': 'Manual analysis required',
                'validation': 'Results need manual review',
                'insights': 'See data for details',
                'limitations': 'AI analysis unavailable'
            }
    
    async def _format_answer(
        self, 
        execution_result: Dict[str, Any], 
        question: str, 
        reasoning_result: Dict[str, Any],
        validation_result: Dict[str, Any]
    ) -> str:
        """Format a human-friendly answer using AI"""
        try:
            data_summary = self._create_data_summary(execution_result)
            
            formatting_prompt = f"""
You are a helpful data analyst assistant. Format the following query results into a clear, human-friendly answer:

USER QUESTION: {question}

RESULTS SUMMARY: {data_summary}

REASONING: {reasoning_result.get('reasoning', 'N/A')}

INTERPRETATION: {reasoning_result.get('interpretation', 'N/A')}

VALIDATION ISSUES: {validation_result.get('warnings', [])}

Please provide a clear, concise answer that:
1. Directly answers the user's question
2. Includes relevant numbers and data
3. Explains what the results mean
4. Mentions any important caveats or limitations
5. Uses business-friendly language

Keep the answer under 200 words and make it easy to understand.
"""
            
            formatted_answer = await self._call_openai_api(formatting_prompt)
            return formatted_answer.strip()
            
        except Exception as e:
            logger.error(f"Error formatting answer: {e}")
            return self._create_basic_answer(execution_result, question)
    
    async def _generate_insights(
        self, 
        execution_result: Dict[str, Any], 
        question: str, 
        reasoning_result: Dict[str, Any]
    ) -> List[str]:
        """Generate additional insights and recommendations"""
        try:
            data_summary = self._create_data_summary(execution_result)
            
            insights_prompt = f"""
Based on the following data analysis, provide 2-3 key insights or recommendations:

QUESTION: {question}
RESULTS: {data_summary}
REASONING: {reasoning_result.get('reasoning', 'N/A')}

Provide actionable insights that would be valuable for business decision-making.
Format as a simple list of insights.
"""
            
            insights_response = await self._call_openai_api(insights_prompt)
            
            # Parse insights into a list
            insights = []
            for line in insights_response.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                    insights.append(line[1:].strip())
                elif line and not line.startswith('Based on') and len(line) > 10:
                    insights.append(line)
            
            return insights[:3]  # Limit to 3 insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return ["Unable to generate additional insights at this time"]
    
    def _create_data_summary(self, execution_result: Dict[str, Any]) -> str:
        """Create a summary of the execution results"""
        if not execution_result.get('success', False):
            return f"Execution failed: {execution_result.get('error', 'Unknown error')}"
        
        data = execution_result.get('data', [])
        row_count = execution_result.get('row_count', 0)
        columns = execution_result.get('columns', [])
        
        if row_count == 0:
            return "No data returned"
        
        summary = f"Returned {row_count} rows with columns: {', '.join(columns)}"
        
        if data:
            # Add sample data
            sample_size = min(3, len(data))
            summary += f"\nSample data (first {sample_size} rows):\n"
            for i, row in enumerate(data[:sample_size]):
                summary += f"Row {i+1}: {dict(row)}\n"
        
        return summary
    
    def _create_data_preview(self, execution_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a preview of the data for display"""
        data = execution_result.get('data', [])
        if not data:
            return []
        
        # Return first 5 rows
        return data[:5]
    
    def _generate_summary(self, execution_result: Dict[str, Any], reasoning_result: Dict[str, Any]) -> str:
        """Generate a brief summary of the analysis"""
        row_count = execution_result.get('row_count', 0)
        
        if row_count == 0:
            return "No data found for the query"
        
        summary = f"Analysis completed: {row_count} rows processed"
        
        if reasoning_result.get('insights'):
            summary += f", {len(reasoning_result['insights'])} insights generated"
        
        return summary
    
    def _calculate_confidence(self, validation_result: Dict[str, Any], reasoning_result: Dict[str, Any]) -> float:
        """Calculate confidence score based on validation and reasoning"""
        confidence = 0.8  # Base confidence
        
        # Reduce confidence for validation issues
        if validation_result.get('errors'):
            confidence -= 0.3
        if validation_result.get('warnings'):
            confidence -= 0.1 * len(validation_result['warnings'])
        
        # Increase confidence for good reasoning
        if reasoning_result.get('reasoning') and len(reasoning_result['reasoning']) > 50:
            confidence += 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _create_basic_answer(self, execution_result: Dict[str, Any], question: str) -> str:
        """Create a basic answer when AI formatting fails"""
        if not execution_result.get('success', False):
            return f"Query execution failed: {execution_result.get('error', 'Unknown error')}"
        
        data = execution_result.get('data', [])
        row_count = execution_result.get('row_count', 0)
        
        if row_count == 0:
            return "No data found matching your criteria."
        
        if row_count == 1:
            row = data[0]
            if len(row) == 1:
                key, value = next(iter(row.items()))
                return f"The {key.replace('_', ' ')} is {value}"
            else:
                return f"Found 1 result: {', '.join([f'{k}: {v}' for k, v in row.items()])}"
        else:
            return f"Found {row_count} results. Please review the data for details."
    
    def _create_fallback_response(self, execution_result: Dict[str, Any], question: str, error: str) -> Dict[str, Any]:
        """Create a fallback response when analysis fails"""
        return {
            'answer': self._create_basic_answer(execution_result, question),
            'reasoning': {'reasoning': f'Analysis failed: {error}'},
            'validation': {'is_valid': False, 'errors': [error]},
            'insights': ['Unable to generate insights due to analysis error'],
            'confidence': 0.3,
            'data_preview': self._create_data_preview(execution_result),
            'summary': f'Basic analysis completed with error: {error}'
        }
    
    async def _call_openai_api(self, prompt: str) -> str:
        """Call OpenAI API for analysis"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert data analyst and business intelligence assistant. Provide clear, accurate, and helpful analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

# Global instance
analysis_agent = AnalysisAgent()