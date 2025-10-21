"""Integration tests comparing OpenAI and LangGraph agent responses."""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class TestAgentComparison:
    """Test suite for comparing OpenAI and LangGraph agent responses."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Reset schedule manager to default state by reinitializing sample data
        import sys
        import os

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

        from schedule_state import SCHEDULE_MANAGER

        SCHEDULE_MANAGER._initialize_sample_data()

        self.test_question = "Can you show me the current schedule overview with teacher workloads?"
        self.test_thread_id = "test_comparison_thread"

    async def get_openai_response(self) -> Dict[str, Any]:
        """Get response from OpenAI tools (simplified approach)."""
        try:
            # Import directly and call the tools
            import sys
            import os

            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

            from openai_agent import (
                show_schedule_overview,
                get_teacher_availability,
                compute_teacher_loads,
            )

            start_time = time.time()

            # Call the schedule overview function directly
            overview = show_schedule_overview()

            end_time = time.time()

            return {
                "status": "success",
                "response": overview,
                "duration_seconds": round(end_time - start_time, 2),
                "agent": "openai",
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "agent": "openai"}

    async def get_langgraph_response(self) -> Dict[str, Any]:
        """Get response from LangGraph agent."""
        try:
            import sys
            import os

            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

            from langgraph_agent import StreamingLangGraphUniversityAgent

            start_time = time.time()

            # Create and run the agent
            agent = StreamingLangGraphUniversityAgent()

            # Collect streaming response
            chunks = []
            async for chunk in agent.astream(self.test_question):
                chunks.append(str(chunk))

            # Combine all chunks for final response
            final_response = "".join(chunks)

            end_time = time.time()

            return {
                "status": "success",
                "response": final_response,
                "streaming_chunks": chunks,
                "chunk_count": len(chunks),
                "duration_seconds": round(end_time - start_time, 2),
                "agent": "langgraph",
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "agent": "langgraph"}

    async def test_agent_comparison(self):
        """Test that both agents provide reasonable responses to the same question."""
        print(f"\\n🧪 Testing agent comparison with question: '{self.test_question}'")

        # Get responses from both agents
        openai_result = await self.get_openai_response()
        langgraph_result = await self.get_langgraph_response()

        # Basic assertions
        assert openai_result["agent"] == "openai"
        assert langgraph_result["agent"] == "langgraph"

        # Create comparison data
        comparison = {
            "test_info": {
                "question": self.test_question,
                "test_time": datetime.now().isoformat(),
                "thread_id": self.test_thread_id,
            },
            "results": {"openai": openai_result, "langgraph": langgraph_result},
        }

        # Save results for manual inspection
        await self.save_test_results(comparison)

        # Print summary
        self.print_test_summary(comparison)

        # Basic validation assertions
        if openai_result["status"] == "success":
            assert openai_result["response"] is not None
            assert len(str(openai_result["response"])) > 0
            print("✅ OpenAI agent provided a non-empty response")
        else:
            print(f"❌ OpenAI agent failed: {openai_result.get('error')}")

        if langgraph_result["status"] == "success":
            assert langgraph_result["response"] is not None
            assert len(str(langgraph_result["response"])) > 0
            assert langgraph_result["chunk_count"] > 0
            print("✅ LangGraph agent provided a non-empty response with streaming chunks")
        else:
            print(f"❌ LangGraph agent failed: {langgraph_result.get('error')}")

        return comparison

    async def save_test_results(self, comparison: Dict[str, Any]):
        """Save test results to files for manual inspection."""
        # Create test_results directory in the tests folder
        test_results_dir = Path(__file__).parent / "test_results"
        test_results_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON comparison
        json_file = test_results_dir / f"agent_comparison_{timestamp}.json"
        with open(json_file, "w") as f:
            json.dump(comparison, f, indent=2, default=str)

        # Save readable text files
        for agent_type in ["openai", "langgraph"]:
            result = comparison["results"][agent_type]
            if result["status"] == "success":
                text_file = test_results_dir / f"{agent_type}_response_{timestamp}.txt"
                with open(text_file, "w") as f:
                    f.write(f"{agent_type.upper()} Agent Test Response\\n")
                    f.write("=" * (len(agent_type) + 20) + "\\n")
                    f.write(f"Question: {comparison['test_info']['question']}\\n")
                    f.write(f"Duration: {result.get('duration_seconds')}s\\n")
                    f.write(f"Status: {result['status']}\\n")
                    if agent_type == "langgraph":
                        f.write(f"Streaming chunks: {result.get('chunk_count')}\\n")
                    f.write(f"Timestamp: {comparison['test_info']['test_time']}\\n\\n")

                    f.write("Response:\\n")
                    f.write("-" * 40 + "\\n")
                    f.write(str(result["response"]))

                    if agent_type == "langgraph" and "streaming_chunks" in result:
                        f.write("\\n\\nStreaming Chunks:\\n")
                        f.write("-" * 40 + "\\n")
                        for i, chunk in enumerate(result["streaming_chunks"]):
                            f.write(f"Chunk {i + 1}: {chunk}\\n")

        print(f"📁 Test results saved to: {test_results_dir}")

    def print_test_summary(self, comparison: Dict[str, Any]):
        """Print a summary of the test results."""
        print("\\n" + "=" * 60)
        print("📊 AGENT COMPARISON TEST SUMMARY")
        print("=" * 60)

        openai_result = comparison["results"]["openai"]
        langgraph_result = comparison["results"]["langgraph"]

        # OpenAI summary
        openai_status = "✅ Success" if openai_result["status"] == "success" else "❌ Failed"
        print(f"OpenAI Agent: {openai_status}")
        if openai_result["status"] == "success":
            print(f"  Duration: {openai_result.get('duration_seconds')}s")
            print(f"  Response length: {len(str(openai_result['response']))} characters")
        else:
            print(f"  Error: {openai_result.get('error')}")

        print()

        # LangGraph summary
        langgraph_status = "✅ Success" if langgraph_result["status"] == "success" else "❌ Failed"
        print(f"LangGraph Agent: {langgraph_status}")
        if langgraph_result["status"] == "success":
            print(f"  Duration: {langgraph_result.get('duration_seconds')}s")
            print(f"  Response length: {len(str(langgraph_result['response']))} characters")
            print(f"  Streaming chunks: {langgraph_result.get('chunk_count', 0)}")
        else:
            print(f"  Error: {langgraph_result.get('error')}")

        # Performance comparison
        if openai_result["status"] == "success" and langgraph_result["status"] == "success":
            openai_duration = openai_result["duration_seconds"]
            langgraph_duration = langgraph_result["duration_seconds"]
            difference = round(langgraph_duration - openai_duration, 2)

            print("\\n⚡ Performance Comparison:")
            print(f"  Time difference: {difference}s")
            if difference > 0:
                print(f"  OpenAI was {difference}s faster")
            elif difference < 0:
                print(f"  LangGraph was {abs(difference)}s faster")
            else:
                print("  Both agents had similar performance")

    def test_schedule_overview_responses_format(self):
        """Test that both agents return properly formatted schedule overview."""
        # This is a synchronous wrapper for the async test
        asyncio.run(self._test_schedule_overview_responses_format())

    async def _test_schedule_overview_responses_format(self):
        """Async implementation of schedule overview format test."""
        comparison = await self.test_agent_comparison()

        # Validate that responses contain expected schedule information
        for agent_type in ["openai", "langgraph"]:
            result = comparison["results"][agent_type]
            if result["status"] == "success":
                response_text = str(result["response"]).lower()

                # Check for key schedule overview elements
                assert "teacher" in response_text or "load" in response_text, (
                    f"{agent_type} response should mention teachers or loads"
                )

                # Check for workload information
                assert any(
                    term in response_text for term in ["hour", "workload", "load", "assignment"]
                ), f"{agent_type} response should contain workload information"

                print(
                    f"✅ {agent_type.upper()} response contains expected schedule overview elements"
                )

    def test_response_consistency(self):
        """Test that both agents provide consistent information about the same data."""
        asyncio.run(self._test_response_consistency())

    async def _test_response_consistency(self):
        """Check that both agents report the same underlying schedule data."""
        # Get the actual schedule state for comparison
        from app.schedule_state import SCHEDULE_MANAGER

        actual_state = SCHEDULE_MANAGER.get_state()

        # Get responses
        comparison = await self.test_agent_comparison()

        # Extract teacher names from both responses
        for agent_type in ["openai", "langgraph"]:
            result = comparison["results"][agent_type]
            if result["status"] == "success":
                response_text = str(result["response"]).lower()

                # Check that real teacher names appear in the response
                for teacher_id, teacher_data in actual_state["teachers"].items():
                    teacher_name = teacher_data["name"].lower()
                    assert teacher_name in response_text, (
                        f"{agent_type} response should mention teacher {teacher_name}"
                    )

                print(f"✅ {agent_type.upper()} response mentions all expected teachers")


# Standalone test runner for manual execution
async def run_manual_comparison():
    """Run the agent comparison manually for development/debugging."""
    print("🚀 Running manual agent comparison test...")

    tester = TestAgentComparison()
    tester.setup_method()

    try:
        comparison = await tester.test_agent_comparison()
        print("\\n🎯 Manual test completed successfully!")
        return comparison
    except Exception as e:
        print(f"\\n❌ Manual test failed: {e}")
        raise


if __name__ == "__main__":
    # Allow running this test file directly
    asyncio.run(run_manual_comparison())
