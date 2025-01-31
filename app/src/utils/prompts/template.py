from pathlib import Path
from typing import Dict, Any, Set
from pydantic import BaseModel, create_model
import tomllib
import re


class TemplateEngine:
    """
    A template engine that automatically detects required variables from templates.
    Makes it easy to know what variables are needed to format a template.
    """
    
    def __init__(self, path: Path | str, section: str, template_name: str, format_vars: dict = None):
        """
        Initialize the template engine.
        
        :param path: Path to the TOML file containing templates
        :param section: Section in the TOML file
        :param template_name: Name of the specific template
        :param format_vars: Optional static variables to format the template with
        """
        self.template = self._load_template(path, section, template_name)
        
        # Extract required variables before applying static formatting
        self.required_variables = self._extract_variables()
        
        # Apply static formatting if provided
        if format_vars:
            try:
                self.template = self._format_template(format_vars)
                # Remove formatted variables from required list
                self.required_variables -= set(format_vars.keys())
            except Exception as e:
                print(f"Error applying static format: {str(e)}")
            
        # Create a simple model for validation
        self.Model = self._generate_model()
    
    def _load_template(self, path: Path | str, section: str, template_name: str) -> str:
        """Load template from TOML file."""
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
                if section not in data:
                    raise KeyError(f"Section '{section}' not found in TOML file. Available sections: {list(data.keys())}")
                if template_name not in data[section]:
                    raise KeyError(f"Template '{template_name}' not found in section '{section}'. Available templates: {list(data[section].keys())}")
                return data[section][template_name]
        except Exception as e:
            print(f"Error loading template: {str(e)}")
            raise
    
    def _extract_variables(self) -> Set[str]:
        """
        Extract all variable names from the template.
        Looks for variables in double braces like {{VARIABLE_NAME}}
        """
        pattern = r'\{\{([A-Z_][A-Z0-9_]*)\}\}'
        return set(re.findall(pattern, self.template))
    
    def _format_template(self, variables: Dict[str, Any]) -> str:
        """
        Replace variables in the template with their values.
        
        :param variables: Dictionary of variable names and their values
        :return: Formatted template string
        """
        result = self.template
        for var_name, var_value in variables.items():
            result = result.replace(f"{{{{{var_name}}}}}", str(var_value))
        return result
    
    def _generate_model(self) -> type[BaseModel]:
        """Generate a simple Pydantic model for validation."""
        return create_model(
            'TemplateModel',
            **{name: (str, ...) for name in self.required_variables}
        )
    
    def format(self, **kwargs) -> str:
        """
        Format the template with the provided variables.
        
        :param kwargs: Variables to insert into the template
        :return: Formatted template string
        :raises: ValueError if required variables are missing
        """
        missing_vars = self.required_variables - set(kwargs.keys())
        if missing_vars:
            raise ValueError(
                f"Missing required variables: {', '.join(missing_vars)}\n"
                f"Required variables are: {', '.join(self.required_variables)}"
            )
            
        try:
            return self._format_template(kwargs)
        except Exception as e:
            print(f"Error formatting template: {str(e)}")
            raise
    
    def get_required_variables(self) -> Set[str]:
        """
        Get the list of variables required by this template.
        
        :return: Set of variable names needed to format this template
        """
        return self.required_variables
    
    def describe(self) -> str:
        """
        Get a human-readable description of what variables are needed.
        
        :return: Description string
        """
        if not self.required_variables:
            return "This template requires no variables."
            
        return (
            "This template requires the following variables:\n"
            f"- {'\n- '.join(sorted(self.required_variables))}"
        )
