#!/usr/bin/env python3
"""
Example Project - Main Project File

This is the entry point for the Example Project.
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# Determine framework root using relative paths
framework_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(framework_root))

from ultimate_ai_architect_framework.agents.built_in.framework_strategy_advisor import FrameworkStrategyAdvisor


def parse_arguments() -> Dict[str, Any]:
    """Parse command line arguments and return a dictionary of requirements."""
    parser = argparse.ArgumentParser(description="AI Framework Strategy Advisor")
    
    # Required arguments
    parser.add_argument("--project-type", type=str, required=True,
                        help="Type of project to be developed")
    parser.add_argument("--features", type=str, required=True,
                        help="Comma-separated list of required features")
    
    # Optional arguments
    parser.add_argument("--constraints", type=str, default="{}",
                        help="JSON formatted dictionary of constraints")
    parser.add_argument("--data-sources", type=str, default="",
                        help="Comma-separated list of data sources")
    parser.add_argument("--scale", type=str, default="medium",
                        help="Scale of the project (small, medium, large)")
    
    args = parser.parse_args()
    
    # Process the arguments
    requirements = {
        "project_type": args.project_type,
        "features": [feature.strip() for feature in args.features.split(",") if feature.strip()],
        "scale": args.scale
    }
    
    # Parse constraints JSON
    try:
        constraints = json.loads(args.constraints)
        if not isinstance(constraints, dict):
            raise ValueError("Constraints must be a valid JSON dictionary")
        requirements["constraints"] = constraints
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing constraints JSON: {e}")
        print("Error: Constraints must be a valid JSON string. Example: --constraints '{\"performance\": \"high\", \"accuracy\": \"high\"}'")
        sys.exit(1)
    
    # Add data sources if provided
    if args.data_sources:
        requirements["data_sources"] = [source.strip() for source in args.data_sources.split(",") if source.strip()]
    
    return requirements


def print_recommendations(recommendations: Dict[str, Any]) -> None:
    """Print the advisor recommendations in a readable format."""
    print("\n" + "="*50)
    print(f"{'AI FRAMEWORK STRATEGY RECOMMENDATIONS':^50}")
    print("="*50 + "\n")
    
    # Print overview section
    if "overview" in recommendations:
        print("\n" + "-"*50)
        print(f"{'OVERVIEW':^50}")
        print("-"*50)
        print(recommendations["overview"])
    
    # Print patterns section
    if "patterns" in recommendations:
        print("\n" + "-"*50)
        print(f"{'RECOMMENDED PATTERNS':^50}")
        print("-"*50)
        for pattern in recommendations["patterns"]:
            print(f"• {pattern}")
    
    # Print approach section
    if "approach" in recommendations:
        print("\n" + "-"*50)
        print(f"{'IMPLEMENTATION APPROACH':^50}")
        print("-"*50)
        print(recommendations["approach"])
    
    # Print stack section
    if "stack" in recommendations:
        print("\n" + "-"*50)
        print(f"{'TECHNOLOGY STACK':^50}")
        print("-"*50)
        for category, technologies in recommendations["stack"].items():
            print(f"\n{category.upper()}:")
            for tech in technologies:
                print(f"• {tech}")
    
    print("\n" + "="*50 + "\n")


def main() -> None:
    """Main entry point for the project."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("example_project")
    logger.info("Starting Example Project")
    
    # Parse command line arguments
    requirements = parse_arguments()
    logger.info(f"Parsed requirements: {requirements}")
    
    # Initialize the FrameworkStrategyAdvisor
    try:
        advisor = FrameworkStrategyAdvisor(framework_root=framework_root)
        logger.info("FrameworkStrategyAdvisor initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize FrameworkStrategyAdvisor: {e}")
        print(f"Error: Failed to initialize advisor: {e}")
        sys.exit(1)
    
    # Run the advisor with the requirements
    try:
        result = advisor.run(requirements)
        logger.info("Advisor completed analysis")
    except Exception as e:
        logger.error(f"Error running advisor: {e}")
        print(f"Error: Failed to run advisor: {e}")
        sys.exit(1)
    
    # Check for errors in the result
    if result.get('error'):
        logger.error(f"Advisor returned an error: {result['error']}")
        print(f"Error: {result['error']}")
        sys.exit(1)
    
    # Print the recommendations
    print_recommendations(result)
    logger.info("Recommendations displayed successfully")


if __name__ == "__main__":
    main()
# test test test ignore this message 
