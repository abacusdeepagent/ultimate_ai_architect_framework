# Ultimate AI Architect Framework Skeleton

A comprehensive framework for creating, managing, and deploying AI architecture projects.

## Overview

The Ultimate AI Architect Framework provides a structured approach to building AI systems with a focus on modularity, reusability, and best practices. It serves as a foundation for creating multiple AI projects while maintaining consistency and leveraging shared components.

## Features

- **Modular Architecture**: Organize AI components into reusable modules
- **Agent-Based Design**: Build systems using specialized AI agents
- **FlowiseAI Integration**: Visual workflow design and management
- **Project Management**: Tools for creating and managing multiple projects
- **Configuration System**: Centralized and project-specific configurations
- **LangSmith Integration**: Tracing, evaluation, and monitoring

## Directory Structure

```
/ultimate_ai_architect_framework/
|-- 📁 configs/                      # Central framework configurations
|-- 📁 agents/
|   |-- 🧩 modules/                  # Reusable Python code for agents
|   |-- 🤖 built_in/                 # Framework-provided agents
|-- ⚙️ core_modules/                 # Core Python logic for the framework
|-- 🌊 flowise_templates/            # Reusable FlowiseAI JSON graph templates
|-- 🚀 projects/                     # Root directory for individual projects
|   |-- 🎤 example_project/          # An example project instance
|-- 📊 framework_dashboard.py        # The Streamlit UI application file
|-- 📜 README.md                     # Overall documentation
|-- requirements.txt                 # Core framework Python dependencies
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ultimate_ai_architect_framework.git
   cd ultimate_ai_architect_framework
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the framework dashboard:
   ```
   streamlit run framework_dashboard.py
   ```

## Environment Variables

The framework uses the following environment variables:

- `OPENROUTER_API_KEY`: Your OpenRouter API key for LLM access
- `GOOGLE_API_KEY`: Your Google API key for Gemini models
- `LANGSMITH_API_KEY`: Your LangSmith API key for tracing and evaluation
- `GITHUB_TOKEN`: (Optional) GitHub token for repository access

You can set these in a `.env` file in the root directory:

```
OPENROUTER_API_KEY=your_openrouter_key
GOOGLE_API_KEY=your_google_key
LANGSMITH_API_KEY=your_langsmith_key
GITHUB_TOKEN=your_github_token
```

## Creating a New Project

1. Using the dashboard:
   - Navigate to the Projects page
   - Click "Create New Project"
   - Enter project details and select a template

2. Using the API:
   ```python
   from core_modules.project_manager import ProjectManager
   
   project_manager = ProjectManager("/path/to/framework")
   project_manager.create_project("my_project", template="basic_rag", description="My new project")
   ```

## FlowiseAI Setup

To use the FlowiseAI integration:

1. Install FlowiseAI:
   ```
   npm install -g flowise
   ```

2. Start FlowiseAI:
   ```
   npx flowise start
   ```

3. Import templates from the `flowise_templates` directory

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
