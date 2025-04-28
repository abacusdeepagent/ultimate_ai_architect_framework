"""
Project Manager Module

This module provides the ProjectManager class for creating, managing,
listing, deleting, and potentially running/exporting AI architecture projects
within the framework.
"""

import logging
import os
import re
import sys
import shutil
import yaml
import json
import zipfile
import tempfile
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from pathlib import Path
import subprocess
from subprocess import PIPE

# Attempt to import ConfigLoader relative to core_modules
try:
    # Assumes ConfigLoader is in the same directory or Python path is set correctly
    from .config_loader import ConfigLoader
except ImportError:
    # Fallback for direct execution or if structure isn't perfect package yet
    try:
        from config_loader import ConfigLoader
    except ImportError:
        print("ERROR: Could not import ConfigLoader. Ensure it's implemented in core_modules.")
        # Define a dummy class if import fails, allows testing parts of ProjectManager
        class ConfigLoader:
            def __init__(self, root): self.root = root
            def load_global_config(self): return {'paths': {'projects_dir': 'projects/', 'templates_dir': 'templates/'}}
            def load_project_config(self, name): return {}
            def load_project_agent_config(self, name): return {}
            def save_config(self, type, data, name=None): return False # Dummy save
            def merge_configs(self, base, override): return {**base, **override} # Simple merge

logger = logging.getLogger("core.project_manager")

# Custom exceptions for project management
class ProjectError(Exception):
    """Base exception for project-related errors."""
    pass

class ProjectExistsError(ProjectError):
    """Exception raised when a project with the same name already exists."""
    pass

class ProjectNotFoundError(ProjectError):
    """Exception raised when a project is not found."""
    pass

class ProjectNameError(ProjectError):
    """Exception raised when a project name is invalid."""
    pass

class ProjectManager:
    """
    Manages AI architecture projects within the framework.

    Provides functionality for:
    - Creating new projects from templates (Flowise JSON + YAML config).
    - Listing existing projects and their metadata.
    - Deleting projects.
    - Exporting projects as zip archives.
    - Importing projects from zip archives.
    - Running project main scripts (basic implementation).
    """

    def __init__(self, framework_root: str):
        """
        Initialize a new ProjectManager instance.

        Args:
            framework_root: Absolute path to the framework root directory.
        """
        self.framework_root = Path(framework_root).resolve()
        self.config_loader = ConfigLoader(str(self.framework_root))
        self.global_config = self.config_loader.load_global_config()

        # Determine project and template directories from config or use defaults
        self.projects_base_dir_name = self.global_config.get('paths', {}).get('projects_dir', 'projects')
        self.templates_base_dir_name = self.global_config.get('paths', {}).get('templates_dir', 'templates')

        self.projects_dir = self.framework_root / self.projects_base_dir_name
        self.templates_dir = self.framework_root / self.templates_base_dir_name

        # Ensure base directories exist
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Project Manager initialized. Projects Dir: {self.projects_dir}, Templates Dir: {self.templates_dir}")

    def _validate_project_name(self, project_name: str) -> bool:
        """
        Validate project name according to requirements.
        
        Args:
            project_name: Name to validate
            
        Returns:
            True if valid, False otherwise
            
        Requirements:
            - Lowercase alphanumeric characters and hyphens only
            - Length between 3 and 40 characters
        """
        pattern = r'^[a-z0-9\-]{3,40}$'
        return bool(re.match(pattern, project_name))

    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all projects found in the projects directory.

        Returns:
            A list of dictionaries, each containing info about a project.
        """
        projects = []
        if not self.projects_dir.is_dir():
            logger.warning(f"Projects directory not found: {self.projects_dir}")
            return []

        for item in self.projects_dir.iterdir():
            if item.is_dir():
                # Check if this is a valid project directory (has project_main.py)
                main_script = item / "project_main.py"
                if not main_script.is_file():
                    logger.debug(f"Skipping directory {item.name} - no project_main.py found")
                    continue
                    
                project_name = item.name
                # Load project config to get more details
                project_config = self.config_loader.load_project_config(project_name)
                project_info = {
                    "name": project_name,
                    "path": str(item),
                    "description": project_config.get("description", "No description."),
                    "version": project_config.get("version", "N/A"),
                    "status": project_config.get("status", "unknown"),
                    "created": project_config.get("created", "N/A"),
                    "template": project_config.get("template", "N/A")
                }
                projects.append(project_info)
        
        logger.debug(f"Found {len(projects)} projects.")
        return projects

    def create_project(self, project_name: str, template_name: Optional[str] = None, 
                      description: str = "") -> Dict[str, Any]:
        """
        Create a new project directory structure, optionally based on a template.

        Args:
            project_name: Name for the new project (lowercase alphanumeric + hyphens, 3-40 chars).
            template_name: Optional name of a template (base name without extension)
                           from the templates directory to copy.
            description: A brief description of the project.

        Returns:
            A dictionary containing info about the created project.

        Raises:
            ProjectNameError: If project name is invalid.
            ProjectExistsError: If project already exists.
            FileNotFoundError: If the specified template does not exist.
        """
        # Validate project name
        if not self._validate_project_name(project_name):
            raise ProjectNameError(
                f"Project name '{project_name}' is invalid. Use lowercase alphanumeric characters "
                f"and hyphens only, with length between 3 and 40 characters."
            )

        project_dir = self.projects_dir / project_name
        if project_dir.exists():
            raise ProjectExistsError(f"Project '{project_name}' already exists at {project_dir}")

        logger.info(f"Creating new project '{project_name}' at {project_dir}")

        # Create project directory structure
        configs_dir = project_dir / "configs"
        logs_dir = project_dir / "logs"
        data_dir = project_dir / "data"
        flows_dir = project_dir / "flowise_exports"
        custom_dir = project_dir / "custom_components"
        
        configs_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(exist_ok=True)
        data_dir.mkdir(exist_ok=True)
        flows_dir.mkdir(exist_ok=True)
        custom_dir.mkdir(exist_ok=True)

        # --- Handle Template if specified ---
        if template_name:
            logger.info(f"Applying template: {template_name}")
            template_flow_path = self.templates_dir / f"{template_name}.flow.json"
            template_config_path = self.templates_dir / f"{template_name}.config.yaml"
            
            # Check if template flow exists
            if not template_flow_path.is_file():
                # Clean up the partially created project
                shutil.rmtree(project_dir, ignore_errors=True)
                raise FileNotFoundError(f"Template flow file not found: {template_flow_path}")
                
            # Copy template flow
            try:
                shutil.copy2(template_flow_path, flows_dir / f"main_{template_name}.flow.json")
                logger.debug(f"Copied template flow: {template_flow_path}")
            except Exception as e:
                # Clean up and re-raise
                shutil.rmtree(project_dir, ignore_errors=True)
                raise FileNotFoundError(f"Failed to copy template flow {template_flow_path}: {e}")
                
            # Apply template config if it exists
            template_config_data = {}
            if template_config_path.is_file():
                try:
                    with open(template_config_path, 'r') as f:
                        template_config_data = yaml.safe_load(f) or {}
                    logger.debug(f"Loaded template config: {template_config_path}")
                except Exception as e:
                    logger.warning(f"Failed to load template config {template_config_path}: {e}")
                    # Continue with empty template config rather than failing

        # --- Create Default Configuration Files ---
        # project_settings.yaml
        project_config_data = {
            "name": project_name,
            "description": description,
            "version": "0.1.0",
            "created": datetime.now().isoformat(),
            "status": "development",
            "template": template_name or "custom",
            "settings": {
                "llm_provider": "default",
                "model": "default"
            },
            "flowise_api_endpoint": f"http://localhost:3000/api/v1/prediction/YOUR-FLOW-ID"
        }
        
        # Merge with template config if available
        if template_name and template_config_data:
            project_config_data = self.config_loader.merge_configs(
                project_config_data, 
                template_config_data.get("project_settings", {})
            )
            
        if not self.config_loader.save_config("project", project_config_data, project_name):
            logger.error(f"Failed to save initial project settings for {project_name}")
            # Clean up and raise exception
            shutil.rmtree(project_dir, ignore_errors=True)
            raise ProjectError(f"Failed to save project settings for {project_name}")

        # agent_config.yaml
        agent_config_data = {
            "agents": {
                "primary_agent": {
                    "profile": "assistant",
                    "config_overrides": {
                        "name": f"{project_name} Assistant",
                    }
                }
            }
        }
        
        # Merge with template config if available
        if template_name and template_config_data:
            agent_config_data = self.config_loader.merge_configs(
                agent_config_data, 
                template_config_data.get("agent_config", {})
            )
            
        if not self.config_loader.save_config("project_agent", agent_config_data, project_name):
            logger.error(f"Failed to save initial agent config for {project_name}")
            # Continue despite error, not critical

        # --- Create project_main.py ---
        main_script_path = project_dir / "project_main.py"
        main_script_content = f"""#!/usr/bin/env python3
\"\"\"
{project_name} - Main Project File
Description: {description}
\"\"\"
import logging
import os
import sys
from pathlib import Path

# Ensure the framework root is in the Python path
framework_root = Path(__file__).resolve().parent.parent
if str(framework_root) not in sys.path:
    sys.path.append(str(framework_root))

# Import necessary framework components
try:
    from core_modules.config_loader import ConfigLoader
    # Uncomment as needed:
    # from core_modules.llm_router import LLMRouter
    # from core_modules.tool_handler import ToolHandler
except ImportError as e:
    print(f"Error importing framework modules: {{e}}")
    print("Ensure framework_root is correctly added to sys.path and modules exist.")
    sys.exit(1)

# Setup logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"{{datetime.now().strftime('%Y%m%d_%H%M%S')}}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("{project_name}")

def run():
    logger.info(f"Starting project: {project_name}")
    try:
        # 1. Load configuration using ConfigLoader
        config_loader = ConfigLoader(str(framework_root))
        project_config = config_loader.load_project_config("{project_name}")
        agent_config = config_loader.load_project_agent_config("{project_name}")
        logger.info("Project configuration loaded.")
        
        # 2. Initialize LLM Router (if needed)
        # llm_router = LLMRouter(str(framework_root))
        # selected_llm = llm_router.route(task_type='conversation')
        # logger.info(f"Selected LLM: {{selected_llm}}")
        
        # 3. Execute main project logic
        logger.info("Executing main project logic...")
        print(f"Hello from {project_name}!")
        print(f"Project description: {{project_config.get('description', 'No description')}}")
        
        # Your project-specific code goes here
        
        logger.info(f"Project {project_name} completed successfully.")
        
    except Exception as e:
        logger.exception(f"An error occurred during project execution: {{e}}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(run())
"""
        with open(main_script_path, 'w', encoding='utf-8') as f:
            f.write(main_script_content)
            
        # Make executable
        try:
            os.chmod(main_script_path, 0o755)
        except Exception as e:
            logger.warning(f"Could not set execute permission on {main_script_path}: {e}")

        # --- Create README.md ---
        readme_path = project_dir / "README.md"
        readme_content = f"""# {project_name}

{description}

## Overview

This project is built using the Ultimate AI Architect Framework.

- **Template**: {template_name or 'Custom'}
- **Created**: {datetime.now().strftime('%Y-%m-%d')}
- **Status**: Development

## Directory Structure

- `configs/` - Configuration files for the project
- `data/` - Data files used by the project
- `logs/` - Log files generated during execution
- `flowise_exports/` - Flowise flow exports (if applicable)
- `custom_components/` - Custom components for the project

## Setup

1. Ensure framework dependencies are installed (`pip install -r requirements.txt` from framework root).
2. Configure environment variables as needed (see framework documentation).
3. Review and update project settings in `configs/project_settings.yaml`.
4. Configure agents in `configs/agent_config.yaml`.

## Running the Project

```bash
# From the project directory
python project_main.py

# Or from the framework root
python projects/{project_name}/project_main.py
```

## Development Notes

Add any project-specific notes, requirements, or development guidelines here.
"""
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

        # Return project info
        return {
            "name": project_name,
            "path": str(project_dir),
            "description": description,
            "version": "0.1.0",
            "status": "development",
            "created": datetime.now().isoformat(),
            "template": template_name or "custom"
        }

    def delete_project(self, project_name: str, confirm: bool = False) -> bool:
        """
        Delete a project directory and all its contents.

        Args:
            project_name: Name of the project to delete.
            confirm: Whether deletion is confirmed (safety check).

        Returns:
            True if deletion was successful, False otherwise.
            
        Raises:
            ProjectNotFoundError: If the project does not exist.
            ProjectError: If deletion is not confirmed.
        """
        project_dir = self.projects_dir / project_name
        
        if not project_dir.exists() or not project_dir.is_dir():
            raise ProjectNotFoundError(f"Project '{project_name}' not found at {project_dir}")
            
        if not confirm:
            raise ProjectError(f"Project deletion not confirmed. Set confirm=True to proceed.")
            
        try:
            logger.info(f"Deleting project '{project_name}' at {project_dir}")
            shutil.rmtree(project_dir)
            logger.info(f"Project '{project_name}' deleted successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to delete project '{project_name}': {e}")
            raise ProjectError(f"Failed to delete project '{project_name}': {e}")

    def run_project(self, project_name: str) -> subprocess.Popen:
        """
        Run a project's main script using non-blocking subprocess.Popen.

        Args:
            project_name: Name of the project to run.

        Returns:
            A subprocess.Popen object representing the running process.
            
        Raises:
            ProjectNotFoundError: If the project does not exist.
            ProjectError: If the main script cannot be found or executed.
        """
        project_dir = self.projects_dir / project_name
        main_script = project_dir / "project_main.py"
        
        if not project_dir.exists() or not project_dir.is_dir():
            raise ProjectNotFoundError(f"Project '{project_name}' not found at {project_dir}")
            
        if not main_script.exists() or not main_script.is_file():
            raise ProjectError(f"Project main script not found at {main_script}")
            
        try:
            logger.info(f"Running project '{project_name}' from {main_script}")
            process = subprocess.Popen(
                [sys.executable, str(main_script)],
                cwd=str(project_dir),
                stdout=PIPE,
                stderr=PIPE,
                text=True,
                bufsize=1
            )
            logger.info(f"Project '{project_name}' started with PID {process.pid}")
            return process
        except Exception as e:
            logger.error(f"Failed to run project '{project_name}': {e}")
            raise ProjectError(f"Failed to run project '{project_name}': {e}")

    def export_project(self, project_name: str, output_path: Optional[str] = None) -> str:
        """
        Export a project as a zip archive.

        Args:
            project_name: Name of the project to export.
            output_path: Optional path where the zip file should be saved.
                         If not provided, a default path will be used.

        Returns:
            Path to the created zip file.
            
        Raises:
            ProjectNotFoundError: If the project does not exist.
            ProjectError: If the export fails.
        """
        project_dir = self.projects_dir / project_name
        
        if not project_dir.exists() or not project_dir.is_dir():
            raise ProjectNotFoundError(f"Project '{project_name}' not found at {project_dir}")
            
        # Determine output path
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.framework_root / "exports" / f"{project_name}_{timestamp}.zip")
        
        # Ensure the exports directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"Exporting project '{project_name}' to {output_path}")
            
            # Create zip file
            shutil.make_archive(
                output_path.rstrip('.zip'),  # shutil.make_archive adds .zip extension
                'zip',
                root_dir=str(self.projects_dir),
                base_dir=project_name
            )
            
            # If output_path doesn't end with .zip, add it for the return value
            if not output_path.endswith('.zip'):
                output_path += '.zip'
                
            logger.info(f"Project '{project_name}' exported successfully to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to export project '{project_name}': {e}")
            raise ProjectError(f"Failed to export project '{project_name}': {e}")

    def import_project(self, zip_path: str, new_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Import a project from a zip archive.

        Args:
            zip_path: Path to the zip file containing the project.
            new_name: Optional new name for the imported project.
                      If not provided, the original project name will be used.

        Returns:
            A dictionary containing info about the imported project.
            
        Raises:
            FileNotFoundError: If the zip file does not exist.
            ProjectExistsError: If a project with the same name already exists.
            ProjectError: If the import fails or the zip file is invalid.
        """
        zip_path = Path(zip_path).resolve()
        
        if not zip_path.exists() or not zip_path.is_file():
            raise FileNotFoundError(f"Zip file not found at {zip_path}")
            
        # Create a temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            
            try:
                logger.info(f"Extracting zip file {zip_path} to temporary directory")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir_path)
                
                # Find the project directory in the extracted files
                # Assume it's either the root or a single directory inside the temp dir
                extracted_items = list(temp_dir_path.iterdir())
                
                if len(extracted_items) == 1 and extracted_items[0].is_dir():
                    # Single directory in the zip - this is likely the project
                    extracted_project_dir = extracted_items[0]
                else:
                    # Multiple items - assume the zip contains the project files directly
                    extracted_project_dir = temp_dir_path
                
                # Verify this is a valid project by checking for project_main.py
                if not (extracted_project_dir / "project_main.py").is_file():
                    raise ProjectError(f"Invalid project archive: No project_main.py found")
                
                # Determine project name
                original_name = extracted_project_dir.name
                project_name = new_name if new_name else original_name
                
                # Validate the project name
                if not self._validate_project_name(project_name):
                    raise ProjectNameError(
                        f"Project name '{project_name}' is invalid. Use lowercase alphanumeric characters "
                        f"and hyphens only, with length between 3 and 40 characters."
                    )
                
                # Check if project already exists
                target_project_dir = self.projects_dir / project_name
                if target_project_dir.exists():
                    raise ProjectExistsError(f"Project '{project_name}' already exists at {target_project_dir}")
                
                # Copy the extracted project to the projects directory
                logger.info(f"Importing project as '{project_name}'")
                shutil.copytree(extracted_project_dir, target_project_dir)
                
                # If the name was changed, update the project_settings.yaml
                if new_name and new_name != original_name:
                    try:
                        project_config = self.config_loader.load_project_config(project_name)
                        project_config["name"] = new_name
                        self.config_loader.save_config("project", project_config, project_name)
                    except Exception as e:
                        logger.warning(f"Failed to update project name in config: {e}")
                
                # Load project info
                project_config = self.config_loader.load_project_config(project_name)
                
                return {
                    "name": project_name,
                    "path": str(target_project_dir),
                    "description": project_config.get("description", "No description."),
                    "version": project_config.get("version", "N/A"),
                    "status": project_config.get("status", "imported"),
                    "created": project_config.get("created", datetime.now().isoformat()),
                    "template": project_config.get("template", "imported")
                }
                
            except zipfile.BadZipFile:
                raise ProjectError(f"Invalid zip file: {zip_path}")
            except Exception as e:
                logger.error(f"Failed to import project from {zip_path}: {e}")
                raise ProjectError(f"Failed to import project: {e}")

# Example usage (for testing purposes)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # Assume framework root is the parent directory of core_modules
    script_dir = os.path.dirname(os.path.abspath(__file__))
    framework_root_dir = os.path.dirname(script_dir)

    print(f"Testing ProjectManager with framework root: {framework_root_dir}")
    
    pm = ProjectManager(framework_root=framework_root_dir)
    
    # List existing projects
    projects = pm.list_projects()
    print(f"Found {len(projects)} projects:")
    for project in projects:
        print(f"  - {project['name']}: {project['description']}")
    
    # Create a test project (uncomment to test)
    # try:
    #     new_project = pm.create_project(
    #         project_name="test-project",
    #         description="A test project created by ProjectManager"
    #     )
    #     print(f"Created new project: {new_project['name']}")
    # except Exception as e:
    #     print(f"Failed to create project: {e}")
    
    # Export a project (uncomment to test)
    # try:
    #     export_path = pm.export_project("test-project")
    #     print(f"Exported project to: {export_path}")
    # except Exception as e:
    #     print(f"Failed to export project: {e}")
    
    # Import a project (uncomment to test)
    # try:
    #     imported_project = pm.import_project(export_path, new_name="imported-test")
    #     print(f"Imported project: {imported_project['name']}")
    # except Exception as e:
    #     print(f"Failed to import project: {e}")
    
    # Run a project (uncomment to test)
    # try:
    #     process = pm.run_project("test-project")
    #     print(f"Project running with PID: {process.pid}")
    #     # Wait for a bit to see output
    #     import time
    #     time.sleep(2)
    #     stdout, stderr = process.communicate(timeout=1)
    #     print(f"Output: {stdout}")
    #     if stderr:
    #         print(f"Errors: {stderr}")
    # except Exception as e:
    #     print(f"Failed to run project: {e}")
    
    # Delete a project (uncomment to test)
    # try:
    #     pm.delete_project("test-project", confirm=True)
    #     print("Project deleted successfully")
    # except Exception as e:
    #     print(f"Failed to delete project: {e}")
