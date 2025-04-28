# Example Project

An example project to demonstrate the Ultimate AI Architect Framework.

## Overview

This project showcases the capabilities of the Ultimate AI Architect Framework by implementing a document analysis and question answering system. It demonstrates how to use the framework's components, agents, and tools to build an AI application.

## Features

- Document loading and processing
- Text chunking and embedding
- Vector storage and retrieval
- Question answering over documents
- Entity extraction
- Summary generation

## Setup

1. Install dependencies:
   ```
   pip install -r ../requirements.txt
   ```

2. Run the project:
   ```
   python project_main.py
   ```

## Configuration

Project configuration is stored in the `configs` directory:
- `project_settings.yaml`: General project settings
- `agent_config.yaml`: Configuration for agents used in the project

## Custom Components

The project includes a custom document processor component in the `custom_components` directory that extends the framework's base agent class to provide document processing capabilities.

## FlowiseAI Integration

The project includes a FlowiseAI flow in the `flowise_exports` directory that can be imported into FlowiseAI to visualize and modify the project's workflow.
