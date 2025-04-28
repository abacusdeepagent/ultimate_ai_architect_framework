"""
Ultimate AI Architect Framework Dashboard

This Streamlit application provides a user interface for managing and interacting
with the Ultimate AI Architect Framework.
"""

import streamlit as st
import os
import sys
import yaml
import json
from datetime import datetime
import logging
from pathlib import Path

# Add framework modules to path
framework_root = Path(__file__).parent
sys.path.append(str(framework_root))

from core_modules.project_manager import ProjectManager
from core_modules.config_loader import ConfigLoader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dashboard")

# Initialize framework components
project_manager = ProjectManager(str(framework_root))
config_loader = ConfigLoader(str(framework_root))

# Set page config
st.set_page_config(
    page_title="Ultimate AI Architect Framework",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper functions
def validate_yaml(yaml_str):
    """Validate YAML syntax and return (is_valid, error_message)"""
    try:
        yaml.safe_load(yaml_str)
        return True, ""
    except Exception as e:
        return False, str(e)

def save_yaml_config(config_type, yaml_str, project_name=None):
    """Save YAML configuration with validation"""
    is_valid, error_message = validate_yaml(yaml_str)
    if not is_valid:
        return False, f"Invalid YAML syntax: {error_message}"
    
    try:
        config_data = yaml.safe_load(yaml_str)
        config_loader.save_config(config_type, config_data, project_name)
        return True, f"{config_type.title()} configuration saved successfully!"
    except Exception as e:
        return False, f"Failed to save configuration: {str(e)}"

# Sidebar
st.sidebar.title("🧠 Ultimate AI Architect")
st.sidebar.subheader("Framework Dashboard")

# Navigation
page = st.sidebar.radio(
    "Navigation",
    ["Home", "Projects", "Templates", "Configuration", "Documentation"]
)

# Home page
if page == "Home":
    st.title("Ultimate AI Architect Framework")
    st.subheader("Welcome to the AI Architecture Framework Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Framework Overview
        
        The Ultimate AI Architect Framework provides a structured approach to creating and managing AI projects.
        It offers:
        
        - Modular architecture for AI components
        - Reusable agent templates and patterns
        - Project management and configuration tools
        - Integrated development environment for AI systems
        """)
        
        # Quick stats
        projects = project_manager.list_projects()
        st.info(f"Active Projects: {len(projects)}")
        
        # Global config summary
        global_config = config_loader.load_global_config()
        st.subheader("Framework Status")
        st.json({
            "version": global_config.get("version", "1.0.0"),
            "environment": global_config.get("environment", "development"),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    with col2:
        st.subheader("Quick Actions")
        
        # Create new project button
        if st.button("Create New Project"):
            st.session_state.page = "Projects"
            st.session_state.create_project = True
            st.rerun()
        
        # Open documentation button
        if st.button("View Documentation"):
            st.session_state.page = "Documentation"
            st.rerun()
        
        # Recent activity
        st.subheader("Recent Activity")
        st.markdown("""
        - Framework initialized
        - Example project created
        - Configuration loaded
        """)

# Projects page
elif page == "Projects":
    st.title("Projects")
    
    # Create new project form
    with st.expander("Create New Project", expanded=st.session_state.get("create_project", False)):
        with st.form("new_project_form"):
            project_name = st.text_input("Project Name (alphanumeric only)")
            st.caption("Project name must be lowercase, alphanumeric characters and hyphens only.")
            project_description = st.text_area("Project Description")
            
            # Get available templates
            templates_dir = os.path.join(framework_root, "templates")
            if os.path.exists(templates_dir):
                templates = ["None"] + [f.name for f in os.scandir(templates_dir) if f.is_dir()]
            else:
                templates = ["None"]
            
            project_template = st.selectbox(
                "Project Template",
                templates
            )
            
            submit_button = st.form_submit_button("Create Project")
            
            if submit_button:
                if not project_name or not all(c.isalnum() or c == '-' for c in project_name):
                    st.error("Project name must contain only lowercase alphanumeric characters and hyphens")
                else:
                    try:
                        project_manager.create_project(
                            project_name.lower(),
                            project_template if project_template != "None" else None,
                            project_description
                        )
                        st.success(f"Project '{project_name}' created successfully!")
                        st.session_state.create_project = False
                    except Exception as e:
                        st.error(f"Failed to create project: {e}")
    
    # List existing projects
    projects = project_manager.list_projects()
    
    if not projects:
        st.info("No projects found. Create a new project to get started.")
    else:
        for project in projects:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.subheader(project["name"])
                    st.write(project.get("description", ""))
                    st.caption(f"Created: {project.get('created', '')}")
                
                with col2:
                    st.write(f"Status: {project.get('status', 'development')}")
                    st.write(f"Version: {project.get('version', '0.1.0')}")
                
                with col3:
                    if st.button("Open", key=f"open_{project['name']}"):
                        st.session_state.selected_project = project["name"]
                        st.session_state.project_view = True
                        st.rerun()
                    
                    if st.button("Delete", key=f"delete_{project['name']}"):
                        confirm = st.checkbox(f"Confirm deletion of {project['name']}", key=f"confirm_{project['name']}")
                        if confirm and project_manager.delete_project(project["name"]):
                            st.success(f"Project '{project['name']}' deleted successfully!")
                            st.rerun()
                        elif confirm:
                            st.error(f"Failed to delete project '{project['name']}'")
                
                st.divider()
    
    # Project detail view
    if st.session_state.get("project_view", False) and st.session_state.get("selected_project"):
        project_name = st.session_state.selected_project
        st.subheader(f"Project: {project_name}")
        
        # Back button
        if st.button("← Back to Projects List"):
            st.session_state.project_view = False
            st.session_state.selected_project = None
            st.rerun()
        
        try:
            # Load project configuration
            project_config = config_loader.load_project_config(project_name)
            agent_config = config_loader.load_project_agent_config(project_name)
            
            # Project tabs
            tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Configuration", "Agents", "Run"])
            
            with tab1:
                # Project info
                st.subheader("Project Information")
                st.write(f"**Name:** {project_name}")
                st.write(f"**Description:** {project_config.get('description', 'No description')}")
                st.write(f"**Version:** {project_config.get('version', '0.1.0')}")
                st.write(f"**Status:** {project_config.get('status', 'development')}")
                
                # Project structure
                st.subheader("Project Structure")
                project_dir = os.path.join(framework_root, "projects", project_name)
                
                for root, dirs, files in os.walk(project_dir):
                    rel_path = os.path.relpath(root, project_dir)
                    if rel_path == ".":
                        st.write("📁 /")
                    else:
                        st.write(f"📁 /{rel_path}")
                    
                    for file in files:
                        st.write(f"  📄 {file}")
            
            with tab2:
                st.subheader("Project Configuration")
                
                # Display and edit project settings
                with st.expander("Project Settings", expanded=True):
                    edited_config = st.text_area(
                        "Edit project_settings.yaml",
                        yaml.dump(project_config),
                        height=300
                    )
                    
                    if st.button("Save Project Settings"):
                        success, message = save_yaml_config("project", edited_config, project_name)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                
                # Display and edit agent configuration
                with st.expander("Agent Configuration", expanded=True):
                    edited_agent_config = st.text_area(
                        "Edit agent_config.yaml",
                        yaml.dump(agent_config),
                        height=300
                    )
                    
                    if st.button("Save Agent Configuration"):
                        success, message = save_yaml_config("project_agent", edited_agent_config, project_name)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
            
            with tab3:
                st.subheader("Project Agents")
                
                # Display agents
                if "agents" not in agent_config:
                    st.info("No agents configured for this project.")
                else:
                    for agent_id, agent_config in agent_config.get("agents", {}).items():
                        with st.expander(f"Agent: {agent_id}"):
                            st.write(f"**Type:** {agent_config.get('type', 'unknown')}")
                            st.write(f"**Name:** {agent_config.get('config', {}).get('name', agent_id)}")
                            st.write(f"**Description:** {agent_config.get('config', {}).get('description', '')}")
                            
                            # Display agent configuration
                            st.subheader("Agent Configuration")
                            st.json(agent_config.get("config", {}))
            
            with tab4:
                st.subheader("Run Project")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Run Project", key="run_project"):
                        with st.spinner(f"Running project '{project_name}'..."):
                            success = project_manager.run_project(project_name)
                            if success:
                                st.success(f"Project '{project_name}' executed successfully!")
                            else:
                                st.error(f"Failed to run project '{project_name}'")
                
                with col2:
                    # Export project
                    export_path = st.text_input("Export Path", f"/tmp/{project_name}")
                    if st.button("Export Project"):
                        with st.spinner(f"Exporting project '{project_name}'..."):
                            if project_manager.export_project(project_name, export_path):
                                st.success(f"Project exported to {export_path}.zip")
                            else:
                                st.error(f"Failed to export project")
        
        except Exception as e:
            st.error(f"Error loading project: {str(e)}")
            st.button("Back to Projects List", on_click=lambda: setattr(st.session_state, "project_view", False))

# Templates page
elif page == "Templates":
    st.title("Project Templates")
    
    # List available templates
    templates_dir = os.path.join(framework_root, "templates")
    
    if not os.path.exists(templates_dir):
        st.info("Templates directory not found.")
    else:
        templates = [f.name for f in os.scandir(templates_dir) if f.is_dir()]
        
        if not templates:
            st.info("No templates found.")
        else:
            for template in templates:
                with st.expander(template):
                    # Load template readme if available
                    readme_path = os.path.join(templates_dir, template, "README.md")
                    if os.path.exists(readme_path):
                        with open(readme_path, 'r') as f:
                            readme_content = f.read()
                        st.markdown(readme_content)
                    else:
                        st.write("No README.md found for this template.")
                    
                    # Template structure
                    st.subheader("Template Structure")
                    template_dir = os.path.join(templates_dir, template)
                    
                    for root, dirs, files in os.walk(template_dir):
                        rel_path = os.path.relpath(root, template_dir)
                        if rel_path == ".":
                            st.write("📁 /")
                        else:
                            st.write(f"📁 /{rel_path}")
                        
                        for file in files:
                            st.write(f"  📄 {file}")
                    
                    # Use template button
                    if st.button("Use This Template", key=f"use_{template}"):
                        st.session_state.page = "Projects"
                        st.session_state.create_project = True
                        st.session_state.selected_template = template
                        st.rerun()

# Configuration page
elif page == "Configuration":
    st.title("Framework Configuration")
    
    # Load configurations
    global_config = config_loader.load_global_config()
    agent_profiles = config_loader.load_agent_profiles()
    tool_registry = config_loader.load_tool_registry()
    
    # Configuration tabs
    tab1, tab2, tab3 = st.tabs(["Global Settings", "Agent Profiles", "Tool Registry"])
    
    with tab1:
        st.subheader("Global Settings")
        
        edited_global_config = st.text_area(
            "Edit global_settings.yaml",
            yaml.dump(global_config),
            height=400
        )
        
        if st.button("Save Global Settings"):
            success, message = save_yaml_config("global", edited_global_config)
            if success:
                st.success(message)
            else:
                st.error(message)
    
    with tab2:
        st.subheader("Agent Profiles")
        
        edited_agent_profiles = st.text_area(
            "Edit base_agent_profiles.yaml",
            yaml.dump(agent_profiles),
            height=400
        )
        
        if st.button("Save Agent Profiles"):
            success, message = save_yaml_config("agent_profiles", edited_agent_profiles)
            if success:
                st.success(message)
            else:
                st.error(message)
    
    with tab3:
        st.subheader("Tool Registry")
        
        edited_tool_registry = st.text_area(
            "Edit tool_registry.yaml",
            yaml.dump(tool_registry),
            height=400
        )
        
        if st.button("Save Tool Registry"):
            success, message = save_yaml_config("tool_registry", edited_tool_registry)
            if success:
                st.success(message)
            else:
                st.error(message)

# Documentation page
elif page == "Documentation":
    st.title("Framework Documentation")
    
    # Documentation tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Getting Started", "Architecture", "API Reference", "Examples"])
    
    with tab1:
        st.subheader("Getting Started")
        
        st.markdown("""
        ### Installation
        
        1. Clone the repository:
           ```
           git clone https://github.com/yourusername/ultimate_ai_architect_framework.git
           ```
           
        2. Install dependencies:
           ```
           pip install -r requirements.txt
           ```
           
        3. Run the dashboard:
           ```
           streamlit run framework_dashboard.py
           ```
           
        ### Creating Your First Project
        
        1. Navigate to the Projects page
        2. Click "Create New Project"
        3. Enter a name and description
        4. Select a template (optional)
        5. Click "Create Project"
        
        ### Project Structure
        
        Each project follows a standard structure:
        
        ```
        project_name/
        ├── configs/                 # Project-specific configurations
        │   ├── project_settings.yaml  # Project settings
        │   └── agent_config.yaml      # Agent configuration
        ├── custom_components/       # Custom Python components
        ├── project_main.py          # Entry point script
        └── README.md                # Project documentation
        ```
        """)
    
    with tab2:
        st.subheader("Framework Architecture")
        
        st.markdown("""
        ### Core Components
        
        The framework consists of several core components:
        
        1. **Project Manager**: Handles project creation, management, and deployment
        2. **Config Loader**: Manages configuration files and settings
        3. **LLM Router**: Routes requests to appropriate language models
        4. **Tool Handler**: Registers and manages tools for agents to use
        
        ### Agent System
        
        Agents are the primary building blocks of projects:
        
        1. **Base Agent**: Provides common functionality for all agents
        2. **Memory Manager**: Manages agent memory and state
        3. **Built-in Agents**: Pre-configured agents for common tasks
        4. **Custom Agents**: Project-specific agents
        
        ### Configuration System
        
        The framework uses YAML files for configuration:
        
        1. **Global Settings**: Framework-wide settings
        2. **Agent Profiles**: Reusable agent configurations
        3. **Tool Registry**: Available tools and their configurations
        4. **Project Settings**: Project-specific settings
        5. **Agent Config**: Project-specific agent configurations
        """)
    
    with tab3:
        st.subheader("API Reference")
        
        st.markdown("""
        ### Project Manager
        
        ```python
        # Create a new project
        project_manager.create_project(project_name, template=None, description="")
        
        # List all projects
        projects = project_manager.list_projects()
        
        # Delete a project
        project_manager.delete_project(project_name)
        
        # Run a project
        project_manager.run_project(project_name)
        
        # Export a project
        project_manager.export_project(project_name, export_path)
        ```
        
        ### Config Loader
        
        ```python
        # Load global configuration
        global_config = config_loader.load_global_config()
        
        # Load agent profiles
        agent_profiles = config_loader.load_agent_profiles()
        
        # Load tool registry
        tool_registry = config_loader.load_tool_registry()
        
        # Load project configuration
        project_config = config_loader.load_project_config(project_name)
        
        # Load project agent configuration
        agent_config = config_loader.load_project_agent_config(project_name)
        
        # Save configuration
        config_loader.save_config(config_type, config_data, project_name=None)
        ```
        
        ### LLM Router
        
        ```python
        # Initialize LLM Router
        llm_router = LLMRouter(config_path)
        
        # Route a prompt to an LLM
        response = llm_router.route(prompt, model_name=None, parameters={})
        
        # Get available models
        models = llm_router.get_available_models()
        ```
        """)
    
    with tab4:
        st.subheader("Examples")
        
        st.markdown("""
        ### Example Project
        
        The framework includes an example project that demonstrates its capabilities:
        
        ```python
        # Load the example project
        project_config = config_loader.load_project_config("example_project")
        
        # Initialize agents
        advisor = FrameworkStrategyAdvisor()
        document_processor = DocumentProcessor()
        
        # Run the advisor
        recommendations = advisor.run({
            "features": ["knowledge_base", "document_analysis"],
            "constraints": {
                "performance": "high",
                "accuracy": "high"
            }
        })
        ```
        
        ### Custom Agent Example
        
        Creating a custom agent:
        
        ```python
        from core_modules.base_agent import BaseAgent
        
        class MyCustomAgent(BaseAgent):
            def __init__(self, agent_id="custom_agent", config_path=None):
                super().__init__(agent_id, config_path)
                # Custom initialization
            
            def run(self, input_data):
                # Custom processing logic
                return {"result": "processed data"}
        ```
        """)

# Main app initialization
def main():
    # Initialize session state
    if "create_project" not in st.session_state:
        st.session_state.create_project = False
    
    if "project_view" not in st.session_state:
        st.session_state.project_view = False
    
    if "selected_project" not in st.session_state:
        st.session_state.selected_project = None
    
    if "selected_template" not in st.session_state:
        st.session_state.selected_template = None

if __name__ == "__main__":
    main()
