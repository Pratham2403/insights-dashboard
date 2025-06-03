# Centralized utility function for importing modules from file paths
import importlib.util

def import_module_from_file(filepath, module_name):
    """Import a module dynamically from a given file path.

    Args:
        filepath (str): Path to the module file.
        module_name (str): Name to assign to the imported module.

    Returns:
        module: The imported module object.

    Raises:
        ImportError: If the module cannot be loaded.
    """
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    if spec is None:
        raise ImportError(f"Could not load spec for module {module_name} from {filepath}")
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise ImportError(f"Spec loader is None for module {module_name} from {filepath}")
    spec.loader.exec_module(module)
    return module