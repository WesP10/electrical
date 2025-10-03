"""Module loading utilities."""
import importlib
import os
from typing import List, Type, Any, Optional

from config.log_config import get_logger

logger = get_logger(__name__)


def load_modules_from_directory(
    directory_path: str,
    base_class: Type,
    file_suffix: str = ".py",
    exclude_files: List[str] = None
) -> List[Any]:
    """Load modules from a directory that inherit from a base class."""
    if exclude_files is None:
        exclude_files = ["__init__.py", "base_sensor.py", "base_tab.py"]
    
    modules = []
    
    try:
        if not os.path.exists(directory_path):
            logger.warning(f"Directory does not exist: {directory_path}")
            return modules
        
        # Get the relative path for imports
        relative_path = os.path.relpath(directory_path).replace(os.sep, '.')
        
        for filename in os.listdir(directory_path):
            if not filename.endswith(file_suffix) or filename in exclude_files:
                continue
            
            module_name = f"{relative_path}.{filename[:-3]}"
            
            try:
                module = importlib.import_module(module_name)
                
                # Look for classes that inherit from base_class
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, base_class) and 
                        attr != base_class):
                        modules.append(attr)
                        logger.debug(f"Loaded module: {module_name}.{attr_name}")
                        break
                
            except Exception as e:
                logger.error(f"Failed to load module {module_name}: {e}")
    
    except Exception as e:
        logger.error(f"Error loading modules from {directory_path}: {e}")
    
    return modules


def reload_module(module_name: str) -> Optional[Any]:
    """Reload a module by name."""
    try:
        module = importlib.import_module(module_name)
        importlib.reload(module)
        logger.debug(f"Reloaded module: {module_name}")
        return module
    except Exception as e:
        logger.error(f"Failed to reload module {module_name}: {e}")
        return None


def get_class_from_module(module: Any, class_name: str) -> Optional[Type]:
    """Get a class from a module by name."""
    try:
        return getattr(module, class_name, None)
    except Exception as e:
        logger.error(f"Failed to get class {class_name} from module: {e}")
        return None