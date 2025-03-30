# config_handler.py
import json
from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple

CONFIG_FILENAME = "obsidian_context_builder_config.json"

def get_config_path() -> Path:
    """Determina la ruta del archivo de configuración (junto al script)."""
    # Intenta encontrar la ruta del script que se está ejecutando
    try:
        # __file__ es la ruta del script actual
        script_dir = Path(__file__).parent.resolve()
    except NameError:
        # Si se ejecuta interactivamente o empaquetado (donde __file__ no está definido)
        # usar el directorio de trabajo actual como fallback
        script_dir = Path.cwd()
    return script_dir / CONFIG_FILENAME

def load_config() -> Dict:
    """Carga la configuración desde el archivo JSON."""
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Asegurarse de que las claves esperadas existen
                if "vaults" not in config:
                    config["vaults"] = {}
                if "last_vault_name" not in config:
                    config["last_vault_name"] = None
                return config
        except json.JSONDecodeError:
            print(f"Advertencia: El archivo de configuración {config_path} está corrupto. Se creará uno nuevo.", file=sys.stderr)
            return {"vaults": {}, "last_vault_name": None}
        except Exception as e:
            print(f"Error al cargar la configuración desde {config_path}: {e}", file=sys.stderr)
            return {"vaults": {}, "last_vault_name": None}
    else:
        print(f"Archivo de configuración no encontrado en {config_path}. Se creará uno nuevo.")
        return {"vaults": {}, "last_vault_name": None}

def save_config(config: Dict):
    """Guarda la configuración en el archivo JSON."""
    config_path = get_config_path()
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error al guardar la configuración en {config_path}: {e}", file=sys.stderr)

def get_vaults() -> Dict[str, str]:
    """Obtiene el diccionario de bóvedas guardadas (nombre: ruta)."""
    config = load_config()
    return config.get("vaults", {})

def add_vault(name: str, path: str) -> bool:
    """Añade o actualiza una bóveda en la configuración."""
    if not name or not path:
        print("Error: Se requiere un nombre y una ruta para añadir la bóveda.", file=sys.stderr)
        return False
    vault_path = Path(path).resolve()
    if not vault_path.is_dir():
        print(f"Error: La ruta proporcionada no es un directorio válido: {vault_path}", file=sys.stderr)
        return False

    config = load_config()
    config["vaults"][name] = str(vault_path) # Guardar como string
    save_config(config)
    print(f"Bóveda '{name}' añadida/actualizada: {vault_path}")
    return True

def remove_vault(name: str) -> bool:
    """Elimina una bóveda de la configuración."""
    config = load_config()
    if name in config["vaults"]:
        removed_path = config["vaults"].pop(name)
        print(f"Bóveda '{name}' eliminada (ruta: {removed_path}).")
        # Si era la última usada, resetearla
        if config.get("last_vault_name") == name:
            config["last_vault_name"] = None
            print("Era la última bóveda usada, se ha reseteado.")
        save_config(config)
        return True
    else:
        print(f"Error: No se encontró una bóveda con el nombre '{name}'.", file=sys.stderr)
        return False

def get_last_vault() -> Optional[Tuple[str, Path]]:
    """Obtiene el nombre y la ruta (Path) de la última bóveda usada."""
    config = load_config()
    last_name = config.get("last_vault_name")
    vaults = config.get("vaults", {})
    if last_name and last_name in vaults:
        path_str = vaults[last_name]
        path_obj = Path(path_str)
        if path_obj.is_dir():
            return last_name, path_obj
        else:
            # La ruta guardada ya no es válida
            print(f"Advertencia: La ruta para la última bóveda usada '{last_name}' ({path_str}) no es válida. Eliminando la referencia.", file=sys.stderr)
            config["last_vault_name"] = None
            save_config(config)
            return None
    return None

def set_last_vault(name: str):
    """Establece la última bóveda usada por nombre."""
    config = load_config()
    if name in config.get("vaults", {}):
        config["last_vault_name"] = name
        save_config(config)
    else:
        print(f"Advertencia: No se pudo establecer '{name}' como última bóveda porque no existe en la configuración.", file=sys.stderr)