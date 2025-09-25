# scripts/demo_queries.py
# Demo queries for testing and demonstration

import asyncio

DEMO_QUERIES = [
    {
        "question": "What are the total liabilities in Company X?",
        "expected_tables": ["financials_balance", "entities"],
        "expected_aggregation": "SUM(liabilities)"
    },
    {
        "question": "What's the YoY revenue growth in 2024?",
        "expected_tables": ["financials_income", "entities"],
        "expected_aggregation": "revenue growth calculation"
    },
    {
        "question": "Show me all companies in the technology sector",
        "expected_tables": ["entities"],
        "expected_filter": "sector = 'technology'"
    },
    {
        "question": "What is the average transaction amount for investments?",
        "expected_tables": ["transactions", "entities"],
        "expected_aggregation": "AVG(amount)"
    },
    {
        "question": "Which companies have the highest cash reserves?",
        "expected_tables": ["financials_balance", "entities"],
        "expected_aggregation": "MAX(cash)"
    }
]

class DemoQueryRunner:
    """Runs demo queries for testing and demonstration"""
    
    def __init__(self):
        # TODO: Initialize API client or database connection
        pass
    
    async def run_demo_queries(self):
        """Run all demo queries and display results"""
        # TODO: Implement demo query execution
        # 1. Send each query to the API
        # 2. Display results in a formatted way
        # 3. Validate that expected tables/aggregations are used
        # 4. Show SQL generated and execution time
        
        print("Demo query execution not yet implemented")
        print("Demo queries:")
        for i, query in enumerate(DEMO_QUERIES, 1):
            print(f"{i}. {query['question']}")
            print(f"   Expected tables: {query['expected_tables']}")
            print(f"   Expected aggregation: {query['expected_aggregation']}")
            print()
    
    async def run_single_query(self, question: str):
        """Run a single demo query"""
        # TODO: Implement single query execution
        pass

async def main():
    """Main entry point for demo query runner"""
    runner = DemoQueryRunner()
    await runner.run_demo_queries()

if __name__ == "__main__":
    asyncio.run(main())
