"""
Comprehensive Agent Tests

Tests Query Agent and Recommend Agent with various inputs,
including edge cases and error scenarios.
"""

import os
from dotenv import load_dotenv
from src.agents.query_agent import QueryAgent
from src.agents.recommend_agent import RecommendAgent

load_dotenv()

def test_query_agent():
    """Test Query Agent with various questions."""

    print("=" * 80)
    print("🧪 QUERY AGENT COMPREHENSIVE TEST")
    print("=" * 80)

    agent = QueryAgent()

    test_queries = [
        "How many workouts did I do in the last 7 days?",
        "What exercises did I do in my most recent workout?",
        "Show me all push workouts from the past month",
        "What's my highest bench press weight?",
        "How many leg workouts have I done?",
        "Did I workout on December 20th?",
        "What's my squat progression looking like?",
        "Compare my push workout frequency to pull workouts",
    ]

    print(f"\nTesting {len(test_queries)} queries...\n")

    results = []
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/{len(test_queries)}: {query}")
        print("-" * 80)

        try:
            answer = agent.query(query)
            print(f"✅ Response:\n{answer[:200]}...")
            results.append({"query": query, "success": True, "response": answer})
        except Exception as e:
            print(f"❌ Error: {str(e)[:100]}")
            results.append({"query": query, "success": False, "error": str(e)})

    # Summary
    successful = sum(1 for r in results if r["success"])
    print(f"\n\n{'='*80}")
    print("QUERY AGENT SUMMARY")
    print("=" * 80)
    print(f"Total queries: {len(test_queries)}")
    print(f"Successful: {successful}/{len(test_queries)} ({successful/len(test_queries)*100:.1f}%)")

    return results


def test_recommend_agent():
    """Test Recommend Agent with various scenarios."""

    print("\n\n" + "=" * 80)
    print("🧪 RECOMMEND AGENT COMPREHENSIVE TEST")
    print("=" * 80)

    agent = RecommendAgent()

    test_scenarios = [
        "What should I do today?",
        "Am I balanced in my training?",
        "What workout did I do last?",
        "Show me my leg day template",
        "What's my weekly split looking like?",
        "Am I overtraining any muscle groups?",
        "When was my last pull workout?",
    ]

    print(f"\nTesting {len(test_scenarios)} scenarios...\n")

    results = []
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/{len(test_scenarios)}: {scenario}")
        print("-" * 80)

        try:
            recommendation = agent.recommend(scenario)
            print(f"✅ Response:\n{recommendation[:200]}...")
            results.append({"scenario": scenario, "success": True, "response": recommendation})
        except Exception as e:
            print(f"❌ Error: {str(e)[:100]}")
            results.append({"scenario": scenario, "success": False, "error": str(e)})

    # Summary
    successful = sum(1 for r in results if r["success"])
    print(f"\n\n{'='*80}")
    print("RECOMMEND AGENT SUMMARY")
    print("=" * 80)
    print(f"Total scenarios: {len(test_scenarios)}")
    print(f"Successful: {successful}/{len(test_scenarios)} ({successful/len(test_scenarios)*100:.1f}%)")

    return results


if __name__ == "__main__":
    query_results = test_query_agent()
    recommend_results = test_recommend_agent()

    print("\n\n" + "=" * 80)
    print("🎉 AGENT TESTING COMPLETE!")
    print("=" * 80)
