#!/usr/bin/env python3
"""
Test script for the _get_llm_client method in BaseAgent.
"""
import os
import sys
from agents.modules.base_agent import BaseAgent

def main():
    # Set dummy API keys for testing
    os.environ["OPENAI_API_KEY"] = "dummy_openai_key"
    os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
    os.environ["GOOGLE_API_KEY"] = "dummy_google_key"
    
    # Create a BaseAgent instance
    agent = BaseAgent()
    
    # Test with OpenRouter model
    print("\nTesting with OpenRouter model:")
    openrouter_client = agent._get_llm_client("openrouter.gpt-3.5-turbo")
    print(f"OpenRouter client type: {type(openrouter_client)}")
    
    # Test with Google Gemini model
    print("\nTesting with Google Gemini model:")
    gemini_client = agent._get_llm_client("google_gemini.gemini-pro")
    print(f"Google Gemini client type: {type(gemini_client)}")
    
    # Test with unsupported model prefix
    print("\nTesting with unsupported model prefix:")
    unsupported_client = agent._get_llm_client("unsupported.model")
    print(f"Unsupported client: {unsupported_client}")
    
    print("\nTest completed.")

if __name__ == "__main__":
    main()
