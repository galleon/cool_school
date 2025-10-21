"""
Integration tests that work both locally and in Docker containers.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Dynamic path setup for both local and container environments
if "/app" in sys.path or os.path.exists("/app"):
    # Container environment
    sys.path.insert(0, "/app")
    ENVIRONMENT = "container"
    RESULTS_PATH = "/tmp/agent_integration_results.json"
else:
    # Local environment
    sys.path.insert(0, str(Path(__file__).parent.parent / "app"))
    ENVIRONMENT = "local"
    RESULTS_PATH = Path(__file__).parent / "test_results" / "agent_integration_results.json"


class TestAgentIntegration:
    """Integration tests for agent functionality across environments."""

    def setup_method(self):
        """Set up test environment."""
        if ENVIRONMENT == "container":
            from schedule_state import SCHEDULE_MANAGER
        else:
            from app.schedule_state import SCHEDULE_MANAGER

        SCHEDULE_MANAGER._initialize_sample_data()
        self.question = "Can you show me the current schedule overview with teacher workloads?"

    async def test_core_tools_consistency(self):
        """Test that core tools work consistently."""
        print(f"🧪 Testing Core Tools Consistency in {ENVIRONMENT} environment...")

        if ENVIRONMENT == "container":
            from core_tools import core_show_schedule_overview
        else:
            from app.core_tools import core_show_schedule_overview

        # Test core function directly
        start_time = time.time()
        result = core_show_schedule_overview()
        duration = time.time() - start_time

        # Validate result structure
        assert isinstance(result, dict)
        assert "teachers" in result
        assert "message" in result

        return {
            "test": "core_tools_consistency",
            "status": "success",
            "duration": round(duration, 4),
            "environment": ENVIRONMENT,
            "result_keys": list(result.keys()),
        }

    async def test_langgraph_tools_invoke(self):
        """Test LangGraph tools invocation."""
        print("🔧 Testing LangGraph Tools Invocation...")

        try:
            if ENVIRONMENT == "container":
                from langgraph_tools import show_schedule_overview
            else:
                from app.langgraph_tools import show_schedule_overview

            start_time = time.time()
            result = show_schedule_overview.invoke({})
            duration = time.time() - start_time

            return {
                "test": "langgraph_tools_invoke",
                "status": "success",
                "duration": round(duration, 4),
                "environment": ENVIRONMENT,
                "tool_callable": True,
            }

        except Exception as e:
            return {
                "test": "langgraph_tools_invoke",
                "status": "error",
                "error": str(e),
                "environment": ENVIRONMENT,
            }

    async def test_streaming_agent_import(self):
        """Test that streaming agent can be imported."""
        print("📡 Testing Streaming Agent Import...")

        try:
            if ENVIRONMENT == "container":
                from langgraph_agent import StreamingLangGraphUniversityAgent
            else:
                from app.langgraph_agent import StreamingLangGraphUniversityAgent

            # Just test that we can create an instance
            agent = StreamingLangGraphUniversityAgent()

            return {
                "test": "streaming_agent_import",
                "status": "success",
                "environment": ENVIRONMENT,
                "agent_created": True,
            }

        except Exception as e:
            return {
                "test": "streaming_agent_import",
                "status": "error",
                "error": str(e),
                "environment": ENVIRONMENT,
            }

    async def run_all_tests(self):
        """Run all integration tests."""
        print(f"🚀 Running Agent Integration Tests in {ENVIRONMENT} environment...")
        print("=" * 60)

        results = {"test_time": datetime.now().isoformat(), "environment": ENVIRONMENT, "tests": {}}

        # Run individual tests
        test_methods = [
            self.test_core_tools_consistency,
            self.test_langgraph_tools_invoke,
            self.test_streaming_agent_import,
        ]

        for test_method in test_methods:
            try:
                test_result = await test_method()
                results["tests"][test_result["test"]] = test_result

                status_icon = "✅" if test_result["status"] == "success" else "❌"
                print(f"{status_icon} {test_result['test']}: {test_result['status']}")

            except Exception as e:
                test_name = test_method.__name__
                results["tests"][test_name] = {
                    "test": test_name,
                    "status": "error",
                    "error": str(e),
                    "environment": ENVIRONMENT,
                }
                print(f"❌ {test_name}: error - {e}")

        # Save results
        os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
        with open(RESULTS_PATH, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n📁 Results saved to: {RESULTS_PATH}")
        print("=" * 60)

        return results


# Standalone execution for Docker
async def main():
    """Main function for standalone execution."""
    tester = TestAgentIntegration()
    tester.setup_method()
    return await tester.run_all_tests()


if __name__ == "__main__":
    # Allow running directly in Docker or locally
    asyncio.run(main())
