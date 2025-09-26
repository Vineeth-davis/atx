# agents/enrichment_api_methods.py
# API methods for the Enrichment Agent

from typing import Dict, Any, List, Optional
import asyncio
import aiohttp
import logging
import json
import time
from datetime import datetime
from api.config import settings

logger = logging.getLogger(__name__)

class EnrichmentAPIMethods:
    """API methods for external data enrichment"""
    
    def __init__(self):
        self.timeout = settings.ENRICHMENT_TIMEOUT
        self.sec_base_url = "https://data.sec.gov/api/xbrl/companyfacts"
        self.yahoo_base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        self.perplexity_base_url = "https://api.perplexity.ai/chat/completions"
    
    async def get_sec_company_facts(self, cik: str) -> Optional[Dict[str, Any]]:
        """Get company facts from SEC EDGAR API"""
        try:
            url = f"{self.sec_base_url}/CIK{cik.zfill(10)}.json"
            
            headers = {
                'User-Agent': f'{settings.APP_NAME} ({settings.APP_VERSION})',
                'Accept': 'application/json'
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'company_name': data.get('entityName', ''),
                            'cik': cik,
                            'ticker': data.get('tickers', [''])[0] if data.get('tickers') else '',
                            'sic': data.get('sic', ''),
                            'sic_description': data.get('sicDescription', ''),
                            'last_updated': data.get('lastUpdated', ''),
                            'facts': data.get('facts', {})
                        }
                    else:
                        logger.warning(f"SEC API returned status {response.status} for CIK {cik}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching SEC data for CIK {cik}: {e}")
            return None
    
    async def get_yahoo_stock_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get stock data from Yahoo Finance API"""
        try:
            url = f"{self.yahoo_base_url}/{ticker}"
            
            params = {
                'range': '1d',
                'interval': '1d',
                'includePrePost': 'false'
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data.get('chart', {}).get('result', [])
                        
                        if result:
                            quote = result[0].get('meta', {})
                            return {
                                'ticker': ticker,
                                'current_price': quote.get('regularMarketPrice', 0),
                                'market_cap': quote.get('marketCap', 0),
                                'pe_ratio': quote.get('trailingPE', 0),
                                'dividend_yield': quote.get('dividendYield', 0),
                                'volume': quote.get('regularMarketVolume', 0),
                                'currency': quote.get('currency', 'USD'),
                                'exchange': quote.get('exchangeName', ''),
                                'last_updated': datetime.now().isoformat()
                            }
                    else:
                        logger.warning(f"Yahoo Finance API returned status {response.status} for ticker {ticker}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data for ticker {ticker}: {e}")
            return None
    
    async def get_perplexity_insights(self, context: str) -> Optional[Dict[str, Any]]:
        """Get insights from Perplexity AI"""
        if not settings.PERPLEXITY_API_KEY:
            logger.warning("Perplexity API key not configured")
            return None
            
        try:
            headers = {
                'Authorization': f'Bearer {settings.PERPLEXITY_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'llama-3.1-sonar-small-128k-online',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are a financial analyst providing market insights and analysis. Provide concise, accurate information about companies and market trends.'
                    },
                    {
                        'role': 'user',
                        'content': f"Provide recent market insights and analysis for the following context:\n\n{context}"
                    }
                ],
                'max_tokens': 500,
                'temperature': 0.3
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(self.perplexity_base_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                        
                        return {
                            'insights': content,
                            'source': 'perplexity',
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        logger.warning(f"Perplexity API returned status {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching Perplexity insights: {e}")
            return None
