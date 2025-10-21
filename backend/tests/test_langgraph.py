"""Tests for the LangGraph agent integration."""

import asyncio

from app.langgraph_agent import StreamingLangGraphUniversityAgent


class TestLangGraphAgent:
    """Test suite for LangGraph streaming agent."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.agent = StreamingLangGraphUniversityAgent()
        self.test_thread_id = "test_thread_123"

    def test_schedule_overview_request(self):
        """Test the streaming LangGraph agent with schedule overview request."""

        async def run_test():
            user_message = "Show me the current schedule overview"
            messages = [{"role": "user", "content": user_message}]

            chunks_received = []
            text_chunks = []
            tool_calls = []

            async for chunk in self.agent.stream_response(self.test_thread_id, messages):
                chunks_received.append(chunk)
                chunk_type = chunk.get("type")

                if chunk_type == "text":
                    text_chunks.append(chunk.get("content", ""))
                elif chunk_type == "tool_call_start":
                    tool_calls.append(chunk.get("tool_name", ""))
                elif chunk_type == "tool_result":
                    # Verify tool results contain expected data
                    result = chunk.get("result", {})
                    assert isinstance(result, dict), "Tool result should be a dictionary"

            # Verify we got some response
            assert len(chunks_received) > 0, "Should receive at least one chunk"

            # Verify we got text response
            full_text = "".join(text_chunks)
            assert len(full_text.strip()) > 0, "Should receive text content"

            # Verify tools were called (should call show_schedule_overview)
            assert "show_schedule_overview" in tool_calls, "Should call schedule overview tool"

            return full_text, tool_calls, chunks_received

        # Run the async test
        result = asyncio.run(run_test())
        assert result is not None, "Test should complete successfully"

    def test_agent_handles_invalid_request(self):
        """Test that the agent handles invalid or unclear requests gracefully."""

        async def run_test():
            user_message = "xyz invalid request 123"
            messages = [{"role": "user", "content": user_message}]

            chunks_received = []

            async for chunk in self.agent.stream_response(self.test_thread_id, messages):
                chunks_received.append(chunk)

                # Should not crash, even with invalid input
                assert "type" in chunk, "Each chunk should have a type"

            # Should receive some kind of response (even if it's an error or clarification)
            assert len(chunks_received) > 0, "Should receive response even for invalid request"

        asyncio.run(run_test())


# Manual test runner for development
async def manual_test_langgraph_agent():
    """Manual test runner for development and debugging."""
    print("🧪 Testing Streaming LangGraph Agent...")
    print("=" * 50)

    agent = StreamingLangGraphUniversityAgent()
    user_message = "Show me the current schedule overview with teacher workloads"
    thread_id = "manual_test_thread"

    print(f"👤 User: {user_message}")
    print("🤖 Agent: ", end="", flush=True)

    try:
        messages = [{"role": "user", "content": user_message}]

        async for chunk in agent.stream_response(thread_id, messages):
            chunk_type = chunk.get("type")
            content = chunk.get("content", "")

            if chunk_type == "text":
                print(content, end="", flush=True)
            elif chunk_type == "tool_call_start":
                tool_name = chunk.get("tool_name", "")
                print(f"\n🔧 [Calling tool: {tool_name}]", end="", flush=True)
            elif chunk_type == "tool_result":
                tool_name = chunk.get("tool_name", "")
                print(f"\n✅ [Tool {tool_name} completed]", end="", flush=True)
            elif chunk_type == "error":
                print(f"\n❌ Error: {content}")

        print("\n" + "=" * 50)
        print("✅ Test completed successfully!")

    except Exception as e:
        print(f"\n❌ Error testing agent: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Run manual test when executed directly
    asyncio.run(manual_test_langgraph_agent())
