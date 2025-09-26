# agents/enrichment_agent.py
# Enrichment Agent for external API integration (SEC EDGAR, Yahoo Finance, Perplexity)

from typing import Dict, Any, List, Optional, Union
import asyncio
import aiohttp
import logging
import json
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
from api.config import settings

logger = logging.getLogger(__name__)

@dataclass
class EnrichmentResult:
    """Result from enrichment API call"""
    source: str
    data: Dict[str, Any]
    success: bool
    error: Optional[str] = None
    timestamp: datetime = None
    cache_hit: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class EnrichmentAgent:
    """Agent for enriching data with external APIs"""
    
    def __init__(self):
        self.sec_api_key = settings.SEC_API_KEY
        self.yahoo_api_key = settings.YAHOO_FINANCE_API_KEY
        self.perplexity_api_key = settings.PERPLEXITY_API_KEY
        self.enable_enrichment = settings.ENABLE_ENRICHMENT
        self.cache_ttl = settings.ENRICHMENT_CACHE_TTL
        self.timeout = settings.ENRICHMENT_TIMEOUT
        
        # In-memory cache for enrichment results
        self.cache: Dict[str, EnrichmentResult] = {}
        
        # API endpoints
        self.sec_base_url = "https://data.sec.gov/api/xbrl/companyfacts"
        self.yahoo_base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        self.perplexity_base_url = "https://api.perplexity.ai/chat/completions"
        
        logger.info(f"Enrichment Agent initialized - SEC: {'✓' if self.sec_api_key else '✗'}, "
                   f"Yahoo: {'✓' if self.yahoo_api_key else '✗'}, "
                   f"Perplexity: {'✓' if self.perplexity_api_key else '✗'}")
    
    async def enrich_query_results(self, 
                                 query_results: Dict[str, Any], 
                                 question: str,
                                 context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Enrich query results with external data sources
        
        Args:
            query_results: Results from the main RAG query
            question: Original user question
            context: Schema context used
            
        Returns:
            Enhanced results with external data
        """
        if not self.enable_enrichment:
            logger.info("Enrichment disabled, skipping external API calls")
            return query_results
        
        try:
            logger.info("🔍 Starting enrichment process...")
            
            # Determine what enrichment is needed
            enrichment_needs = self._analyze_enrichment_needs(question, query_results, context)
            
            if not enrichment_needs:
                logger.info("No enrichment needed for this query")
                return query_results
            
            # Perform enrichment in parallel
            enrichment_tasks = []
            
            if enrichment_needs.get('sec_data'):
                enrichment_tasks.append(self._enrich_with_sec_data(query_results, enrichment_needs['sec_data']))
            
            if enrichment_needs.get('yahoo_finance'):
                enrichment_tasks.append(self._enrich_with_yahoo_finance(query_results, enrichment_needs['yahoo_finance']))
            
            if enrichment_needs.get('perplexity_research'):
                enrichment_tasks.append(self._enrich_with_perplexity(question, query_results, enrichment_needs['perplexity_research']))
            
            # Execute enrichment tasks
            enrichment_results = await asyncio.gather(*enrichment_tasks, return_exceptions=True)
            
            # Process enrichment results
            enriched_data = self._process_enrichment_results(enrichment_results)
            
            # Enhance the original results
            enhanced_results = self._enhance_query_results(query_results, enriched_data, question)
            
            logger.info(f"✅ Enrichment completed - {len(enriched_data)} sources enriched")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error in enrichment process: {e}")
            # Return original results if enrichment fails
            return query_results
    
    def _analyze_enrichment_needs(self, 
                                question: str, 
                                query_results: Dict[str, Any], 
                                context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze what enrichment is needed based on the question and results
        
        Args:
            question: User's question
            query_results: Results from main query
            context: Schema context
            
        Returns:
            Dictionary indicating what enrichment is needed
        """
        enrichment_needs = {}
        question_lower = question.lower()
        
        # Check for SEC EDGAR data needs
        sec_indicators = [
            'sec filing', '10-k', '10-q', '8-k', 'filing', 'edgar', 'sec data',
            'financial statements', 'balance sheet', 'income statement', 'cash flow',
            'auditor', 'audit', 'compliance', 'regulatory'
        ]
        
        if any(indicator in question_lower for indicator in sec_indicators):
            # Try to get entities from results first, then from question
            entities = self._extract_entities_from_results(query_results)
            if not entities:
                entities = self._extract_entities_from_question(question)
            
            enrichment_needs['sec_data'] = {
                'entities': entities,
                'data_types': ['financial_statements', 'filings', 'company_info']
            }
        
        # Check for Yahoo Finance data needs
        yahoo_indicators = [
            'stock price', 'market cap', 'trading volume', 'dividend', 'earnings',
            'analyst rating', 'price target', 'market data', 'real-time', 'quote',
            'historical price', 'stock performance', 'market trends'
        ]
        
        if any(indicator in question_lower for indicator in yahoo_indicators):
            # Try to get entities from results first, then from question
            entities = self._extract_entities_from_results(query_results)
            if not entities:
                entities = self._extract_entities_from_question(question)
            
            enrichment_needs['yahoo_finance'] = {
                'entities': entities,
                'data_types': ['stock_data', 'market_data', 'analyst_data']
            }
        
        # Check for Perplexity research needs
        perplexity_indicators = [
            'research', 'analysis', 'insights', 'trends', 'market analysis',
            'industry analysis', 'competitor', 'benchmark', 'comparison',
            'news', 'recent developments', 'industry trends', 'market outlook'
        ]
        
        if any(indicator in question_lower for indicator in perplexity_indicators):
            enrichment_needs['perplexity_research'] = {
                'research_topics': self._extract_research_topics(question, query_results),
                'data_types': ['research', 'analysis', 'insights']
            }
        
        logger.info(f"Enrichment needs identified: {list(enrichment_needs.keys())}")
        if enrichment_needs:
            for key, config in enrichment_needs.items():
                logger.info(f"  {key}: entities={config.get('entities', [])}, data_types={config.get('data_types', [])}")
        return enrichment_needs
    
    def _extract_entities_from_results(self, query_results: Dict[str, Any]) -> List[str]:
        """Extract entity names from query results for API calls"""
        entities = []
        
        # Extract from data preview
        if 'data_preview' in query_results and query_results['data_preview']:
            for row in query_results['data_preview']:
                if isinstance(row, dict):
                    # Look for name fields
                    for key, value in row.items():
                        if 'name' in key.lower() and isinstance(value, str):
                            entities.append(value)
        
        # Extract from answer text
        if 'answer' in query_results:
            answer = query_results['answer']
            # Simple entity extraction (could be enhanced with NER)
            import re
            # Look for company names (capitalized words)
            potential_entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', answer)
            entities.extend(potential_entities[:3])  # Limit to 3 entities
        
        return list(set(entities))  # Remove duplicates
    
    def _extract_entities_from_question(self, question: str) -> List[str]:
        """Extract entity names directly from the question"""
        entities = []
        
        # Known company names that might appear in questions
        known_companies = [
            'Apple', 'Microsoft', 'Google', 'Amazon', 'Tesla', 'Meta', 'Netflix', 'Nvidia',
            'Facebook', 'Alphabet', 'Apple Inc', 'Microsoft Corp', 'Google LLC', 'Amazon.com',
            'Tesla Inc', 'Meta Platforms', 'Netflix Inc', 'NVIDIA Corp'
        ]
        
        question_lower = question.lower()
        
        # Check for known companies
        for company in known_companies:
            if company.lower() in question_lower:
                entities.append(company)
        
        # Extract capitalized words that might be company names
        import re
        potential_entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', question)
        
        # Filter out common words that aren't company names
        common_words = {'Show', 'Me', 'The', 'What', 'How', 'When', 'Where', 'Why', 'Data', 'Financial', 'Statements', 'Filing', 'SEC', 'Current', 'Stock', 'Price', 'Market', 'Cap', 'Real', 'Time', 'Metrics', 'Companies', 'Database', 'Recent', 'Latest', 'Insights', 'Trends', 'Entities'}
        
        for entity in potential_entities:
            if entity not in common_words and len(entity) > 2:
                entities.append(entity)
        
        return list(set(entities))[:3]  # Remove duplicates and limit to 3
    
    def _extract_research_topics(self, question: str, query_results: Dict[str, Any]) -> List[str]:
        """Extract research topics for Perplexity API"""
        topics = []
        
        # Extract industry information
        if 'data_preview' in query_results and query_results['data_preview']:
            for row in query_results['data_preview']:
                if isinstance(row, dict) and 'industry' in row:
                    topics.append(f"{row['industry']} industry analysis")
        
        # Extract from question
        question_lower = question.lower()
        if 'industry' in question_lower:
            topics.append("industry analysis")
        if 'market' in question_lower:
            topics.append("market analysis")
        if 'trend' in question_lower:
            topics.append("market trends")
        
        return topics[:2]  # Limit to 2 topics
    
    async def _enrich_with_sec_data(self, query_results: Dict[str, Any], enrichment_config: Dict[str, Any]) -> EnrichmentResult:
        """Enrich with SEC EDGAR data"""
        if not self.sec_api_key:
            return EnrichmentResult("SEC", {}, False, "SEC API key not configured")
        
        try:
            entities = enrichment_config.get('entities', [])
            if not entities:
                return EnrichmentResult("SEC", {}, False, "No entities found for SEC lookup")
            
            # Use first entity for SEC lookup
            entity_name = entities[0]
            
            # Check cache first
            cache_key = f"sec_{entity_name.lower()}"
            if cache_key in self.cache:
                cached_result = self.cache[cache_key]
                if (datetime.utcnow() - cached_result.timestamp).seconds < self.cache_ttl:
                    logger.info(f"SEC data cache hit for {entity_name}")
                    cached_result.cache_hit = True
                    return cached_result
            
            # Make SEC API call
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Atrean RAG Platform (contact@atrean.com)',
                    'Accept': 'application/json'
                }
                
                # SEC API doesn't require API key for basic company facts
                url = f"{self.sec_base_url}/CIK{self._get_cik_for_entity(entity_name)}.json"
                
                async with session.get(url, headers=headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract relevant financial data
                        enriched_data = self._extract_sec_financial_data(data)
                        
                        result = EnrichmentResult("SEC", enriched_data, True)
                        self.cache[cache_key] = result
                        
                        logger.info(f"SEC data enriched for {entity_name}")
                        return result
                    else:
                        error_msg = f"SEC API error: {response.status}"
                        logger.warning(error_msg)
                        return EnrichmentResult("SEC", {}, False, error_msg)
        
        except Exception as e:
            logger.error(f"SEC enrichment error: {e}")
            return EnrichmentResult("SEC", {}, False, str(e))
    
    def _get_cik_for_entity(self, entity_name: str) -> str:
        """Get CIK (Central Index Key) for entity - simplified mapping"""
        # This is a simplified mapping - in production, you'd use SEC's company tickers API
        entity_mapping = {
            'apple': '0000320193',
            'microsoft': '0000789019',
            'google': '0001652044',
            'amazon': '0001018724',
            'tesla': '0001318605',
            'meta': '0001326801',
            'netflix': '0001067983',
            'nvidia': '0001045810'
        }
        
        entity_lower = entity_name.lower()
        for key, cik in entity_mapping.items():
            if key in entity_lower:
                return cik
        
        # Default to Apple for demo purposes
        return '0000320193'
    
    def _extract_sec_financial_data(self, sec_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant financial data from SEC response"""
        try:
            facts = sec_data.get('facts', {}).get('us-gaap', {})
            
            extracted_data = {
                'company_name': sec_data.get('entityName', 'Unknown'),
                'cik': sec_data.get('cik', 'Unknown'),
                'sic': sec_data.get('sic', 'Unknown'),
                'financial_metrics': {}
            }
            
            # Extract key financial metrics
            key_metrics = [
                'Revenues', 'Assets', 'Liabilities', 'StockholdersEquity',
                'NetIncomeLoss', 'CashAndCashEquivalentsAtCarryingValue'
            ]
            
            for metric in key_metrics:
                if metric in facts:
                    metric_data = facts[metric]
                    if 'units' in metric_data:
                        units = metric_data['units']
                        # Get the most recent value
                        for unit_type, values in units.items():
                            if values and len(values) > 0:
                                latest_value = values[-1]
                                extracted_data['financial_metrics'][metric] = {
                                    'value': latest_value.get('val', 0),
                                    'date': latest_value.get('end', 'Unknown'),
                                    'unit': unit_type
                                }
                                break
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting SEC data: {e}")
            return {'error': str(e)}
    
    async def _enrich_with_yahoo_finance(self, query_results: Dict[str, Any], enrichment_config: Dict[str, Any]) -> EnrichmentResult:
        """Enrich with Yahoo Finance data"""
        if not self.yahoo_api_key:
            return EnrichmentResult("Yahoo Finance", {}, False, "Yahoo Finance API key not configured")
        
        try:
            entities = enrichment_config.get('entities', [])
            if not entities:
                return EnrichmentResult("Yahoo Finance", {}, False, "No entities found for Yahoo Finance lookup")
            
            # Use first entity for Yahoo Finance lookup
            entity_name = entities[0]
            
            # Check cache first
            cache_key = f"yahoo_{entity_name.lower()}"
            if cache_key in self.cache:
                cached_result = self.cache[cache_key]
                if (datetime.utcnow() - cached_result.timestamp).seconds < self.cache_ttl:
                    logger.info(f"Yahoo Finance data cache hit for {entity_name}")
                    cached_result.cache_hit = True
                    return cached_result
            
            # Get ticker symbol for entity
            ticker = self._get_ticker_for_entity(entity_name)
            
            # Make Yahoo Finance API call
            async with aiohttp.ClientSession() as session:
                url = f"{self.yahoo_base_url}/{ticker}"
                params = {
                    'range': '1d',
                    'interval': '1d',
                    'includePrePost': 'false'
                }
                
                async with session.get(url, params=params, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract relevant market data
                        enriched_data = self._extract_yahoo_market_data(data, entity_name)
                        
                        result = EnrichmentResult("Yahoo Finance", enriched_data, True)
                        self.cache[cache_key] = result
                        
                        logger.info(f"Yahoo Finance data enriched for {entity_name}")
                        return result
                    else:
                        error_msg = f"Yahoo Finance API error: {response.status}"
                        logger.warning(error_msg)
                        return EnrichmentResult("Yahoo Finance", {}, False, error_msg)
        
        except Exception as e:
            logger.error(f"Yahoo Finance enrichment error: {e}")
            return EnrichmentResult("Yahoo Finance", {}, False, str(e))
    
    def _get_ticker_for_entity(self, entity_name: str) -> str:
        """Get ticker symbol for entity - simplified mapping"""
        entity_mapping = {
            'apple': 'AAPL',
            'microsoft': 'MSFT',
            'google': 'GOOGL',
            'amazon': 'AMZN',
            'tesla': 'TSLA',
            'meta': 'META',
            'netflix': 'NFLX',
            'nvidia': 'NVDA'
        }
        
        entity_lower = entity_name.lower()
        for key, ticker in entity_mapping.items():
            if key in entity_lower:
                return ticker
        
        # Default to Apple for demo purposes
        return 'AAPL'
    
    def _extract_yahoo_market_data(self, yahoo_data: Dict[str, Any], entity_name: str) -> Dict[str, Any]:
        """Extract relevant market data from Yahoo Finance response"""
        try:
            result = yahoo_data.get('chart', {}).get('result', [])
            if not result:
                return {'error': 'No data in Yahoo Finance response'}
            
            chart_data = result[0]
            meta = chart_data.get('meta', {})
            quotes = chart_data.get('indicators', {}).get('quote', [{}])[0]
            
            extracted_data = {
                'entity_name': entity_name,
                'ticker': meta.get('symbol', 'Unknown'),
                'market_data': {
                    'current_price': meta.get('regularMarketPrice', 0),
                    'previous_close': meta.get('previousClose', 0),
                    'market_cap': meta.get('marketCap', 0),
                    'volume': meta.get('regularMarketVolume', 0),
                    'high_52_week': meta.get('fiftyTwoWeekHigh', 0),
                    'low_52_week': meta.get('fiftyTwoWeekLow', 0),
                    'currency': meta.get('currency', 'USD'),
                    'exchange': meta.get('exchangeName', 'Unknown')
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting Yahoo Finance data: {e}")
            return {'error': str(e)}
    
    async def _enrich_with_perplexity(self, question: str, query_results: Dict[str, Any], enrichment_config: Dict[str, Any]) -> EnrichmentResult:
        """Enrich with Perplexity research"""
        if not self.perplexity_api_key:
            return EnrichmentResult("Perplexity", {}, False, "Perplexity API key not configured")
        
        try:
            research_topics = enrichment_config.get('research_topics', [])
            if not research_topics:
                return EnrichmentResult("Perplexity", {}, False, "No research topics identified")
            
            # Check cache first
            cache_key = f"perplexity_{hash(question)}"
            if cache_key in self.cache:
                cached_result = self.cache[cache_key]
                if (datetime.utcnow() - cached_result.timestamp).seconds < self.cache_ttl:
                    logger.info(f"Perplexity research cache hit for question")
                    cached_result.cache_hit = True
                    return cached_result
            
            # Make Perplexity API call
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.perplexity_api_key}',
                    'Content-Type': 'application/json'
                }
                
                # Build research query
                research_query = f"Research and analyze: {', '.join(research_topics)}. Provide insights and trends."
                
                payload = {
                    'model': 'llama-3.1-sonar-small-128k-online',
                    'messages': [
                        {
                            'role': 'user',
                            'content': research_query
                        }
                    ],
                    'max_tokens': 500,
                    'temperature': 0.2
                }
                
                async with session.post(self.perplexity_base_url, 
                                      headers=headers, 
                                      json=payload, 
                                      timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract research insights
                        enriched_data = self._extract_perplexity_insights(data, research_topics)
                        
                        result = EnrichmentResult("Perplexity", enriched_data, True)
                        self.cache[cache_key] = result
                        
                        logger.info(f"Perplexity research enriched for topics: {research_topics}")
                        return result
                    else:
                        error_msg = f"Perplexity API error: {response.status}"
                        logger.warning(error_msg)
                        return EnrichmentResult("Perplexity", {}, False, error_msg)
        
        except Exception as e:
            logger.error(f"Perplexity enrichment error: {e}")
            return EnrichmentResult("Perplexity", {}, False, str(e))
    
    def _extract_perplexity_insights(self, perplexity_data: Dict[str, Any], research_topics: List[str]) -> Dict[str, Any]:
        """Extract research insights from Perplexity response"""
        try:
            choices = perplexity_data.get('choices', [])
            if not choices:
                return {'error': 'No choices in Perplexity response'}
            
            content = choices[0].get('message', {}).get('content', '')
            
            extracted_data = {
                'research_topics': research_topics,
                'insights': content,
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'Perplexity AI Research'
            }
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting Perplexity insights: {e}")
            return {'error': str(e)}
    
    def _process_enrichment_results(self, enrichment_results: List[Union[EnrichmentResult, Exception]]) -> Dict[str, Any]:
        """Process enrichment results and organize by source"""
        processed_results = {
            'sources': {},
            'summary': {
                'total_sources': 0,
                'successful_sources': 0,
                'failed_sources': 0,
                'cache_hits': 0
            }
        }
        
        for result in enrichment_results:
            if isinstance(result, Exception):
                logger.error(f"Enrichment task failed: {result}")
                processed_results['summary']['failed_sources'] += 1
                continue
            
            processed_results['summary']['total_sources'] += 1
            
            if result.success:
                processed_results['summary']['successful_sources'] += 1
                processed_results['sources'][result.source] = {
                    'data': result.data,
                    'timestamp': result.timestamp.isoformat(),
                    'cache_hit': result.cache_hit
                }
                
                if result.cache_hit:
                    processed_results['summary']['cache_hits'] += 1
            else:
                processed_results['summary']['failed_sources'] += 1
                processed_results['sources'][result.source] = {
                    'error': result.error,
                    'timestamp': result.timestamp.isoformat()
                }
        
        return processed_results
    
    def _enhance_query_results(self, 
                             query_results: Dict[str, Any], 
                             enriched_data: Dict[str, Any], 
                             question: str) -> Dict[str, Any]:
        """Enhance original query results with enriched data"""
        enhanced_results = query_results.copy()
        
        # Add enrichment metadata
        enhanced_results['enrichment'] = {
            'enabled': True,
            'sources_used': list(enriched_data['sources'].keys()),
            'summary': enriched_data['summary'],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Enhance answer with external data insights
        if enriched_data['sources']:
            enrichment_insights = self._generate_enrichment_insights(enriched_data, question)
            if enrichment_insights:
                enhanced_results['enrichment_insights'] = enrichment_insights
                
                # Update the main answer to incorporate enrichment data
                original_answer = enhanced_results.get('answer', '')
                enhanced_answer = self._integrate_enrichment_into_answer(
                    original_answer, enriched_data, question, enrichment_insights
                )
                enhanced_results['answer'] = enhanced_answer
        
        # Add enriched data to context
        enhanced_results['external_data'] = enriched_data['sources']
        
        return enhanced_results
    
    def _generate_enrichment_insights(self, enriched_data: Dict[str, Any], question: str) -> str:
        """Generate insights from enriched data"""
        insights = []
        
        for source, data in enriched_data['sources'].items():
            if 'error' in data:
                continue
            
            if source == 'SEC':
                sec_data = data['data']
                if 'financial_metrics' in sec_data:
                    insights.append(f"SEC Filing Data: {sec_data.get('company_name', 'Company')} has recent financial filings available.")
            
            elif source == 'Yahoo Finance':
                yahoo_data = data['data']
                if 'market_data' in yahoo_data:
                    market_data = yahoo_data['market_data']
                    insights.append(f"Market Data: Current price ${market_data.get('current_price', 0):.2f}, "
                                  f"Market Cap: ${market_data.get('market_cap', 0):,}")
            
            elif source == 'Perplexity':
                perplexity_data = data['data']
                if 'insights' in perplexity_data:
                    insights.append(f"Research Insights: {perplexity_data['insights'][:200]}...")
        
        return " | ".join(insights) if insights else ""
    
    def _integrate_enrichment_into_answer(
        self, 
        original_answer: str, 
        enriched_data: Dict[str, Any], 
        question: str, 
        enrichment_insights: str
    ) -> str:
        """Integrate enrichment data into the main answer"""
        try:
            # If the original answer indicates no data was found, replace it with enrichment data
            if any(phrase in original_answer.lower() for phrase in [
                'no data available', 'no data was found', 'no information', 
                'missing information', 'data unavailability', 'not found'
            ]):
                # Generate a comprehensive answer using enrichment data
                enriched_answer = self._generate_enriched_answer(enriched_data, question)
                return enriched_answer
            
            # If original answer has data, enhance it with enrichment insights
            else:
                enhanced_answer = f"{original_answer}\n\n**Additional External Data:**\n{enrichment_insights}"
                return enhanced_answer
                
        except Exception as e:
            logger.error(f"Error integrating enrichment into answer: {e}")
            return original_answer
    
    def _generate_enriched_answer(self, enriched_data: Dict[str, Any], question: str) -> str:
        """Generate a comprehensive answer using enrichment data"""
        try:
            answer_parts = []
            
            # Add context about external data
            answer_parts.append("Based on external data sources, here's what I found:")
            
            # Process each enrichment source
            for source, data in enriched_data['sources'].items():
                if 'error' in data:
                    continue
                    
                if source == 'SEC':
                    sec_data = data['data']
                    company_name = sec_data.get('company_name', 'The company')
                    
                    answer_parts.append(f"\n**{company_name} - SEC Filing Data:**")
                    
                    if 'financial_metrics' in sec_data:
                        metrics = sec_data['financial_metrics']
                        for metric_name, metric_data in metrics.items():
                            if isinstance(metric_data, dict) and 'value' in metric_data:
                                value = metric_data['value']
                                unit = metric_data.get('unit', 'USD')
                                date = metric_data.get('date', 'Unknown date')
                                
                                # Format the metric name for display
                                display_name = metric_name.replace('_', ' ').title()
                                formatted_value = f"${value:,}" if unit == 'USD' else f"{value:,} {unit}"
                                
                                answer_parts.append(f"• **{display_name}**: {formatted_value} (as of {date})")
                
                elif source == 'Yahoo Finance':
                    yahoo_data = data['data']
                    entity_name = yahoo_data.get('entity_name', 'The company')
                    
                    answer_parts.append(f"\n**{entity_name} - Market Data:**")
                    
                    if 'market_data' in yahoo_data:
                        market_data = yahoo_data['market_data']
                        current_price = market_data.get('current_price', 0)
                        market_cap = market_data.get('market_cap', 0)
                        volume = market_data.get('volume', 0)
                        
                        answer_parts.append(f"• **Current Price**: ${current_price:.2f}")
                        answer_parts.append(f"• **Market Cap**: ${market_cap:,}")
                        answer_parts.append(f"• **Volume**: {volume:,}")
                
                elif source == 'Perplexity':
                    perplexity_data = data['data']
                    insights = perplexity_data.get('insights', '')
                    
                    answer_parts.append(f"\n**Research Insights:**")
                    answer_parts.append(f"{insights}")
            
            # Add note about data sources
            sources_used = list(enriched_data['sources'].keys())
            answer_parts.append(f"\n*Data sourced from: {', '.join(sources_used)}*")
            
            return "\n".join(answer_parts)
            
        except Exception as e:
            logger.error(f"Error generating enriched answer: {e}")
            return "External data was retrieved but could not be properly formatted."

# Global instance
enrichment_agent = EnrichmentAgent()