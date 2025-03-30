# config_handler.py
import json
from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple

# Nombre más específico para evitar conflictos
CONFIG_FILENAME = "obsidian_context_builder_config.json"

def get_config_path() -> Path:
    """Determina la ruta del archivo de configuración (junto al script)."""
    try:
        script_dir = Path(__file__).parent.resolve()
    except NameError:
        # Fallback para ejecución interactiva o empaquetada
        script_dir = Path.cwd()
    return script_dir / CONFIG_FILENAME

def load_config() -> Dict:
    """Carga la configuración desde el archivo JSON."""
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Asegurar estructura mínima
                config.setdefault("vaults", {})
                config.setdefault("last_vault_name", None)
                return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Advertencia: Error al leer {config_path} ({e}). Se usará configuración por defecto.", file=sys.stderr)
            return {"vaults": {}, "last_vault_name": None}
    else:
        # No imprimir nada si no existe, se creará al guardar
        return {"vaults": {}, "last_vault_name": None}

def save_config(config: Dict):
    """Guarda la configuración en el archivo JSON."""
    config_path = get_config_path()
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False) # ensure_ascii=False por si acaso
    except IOError as e:
        print(f"Error: No se pudo guardar la configuración en {config_path}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Error inesperado al guardar configuración: {e}", file=sys.stderr)


def get_vaults() -> Dict[str, str]:
    """Obtiene el diccionario de bóvedas guardadas (nombre: ruta_string)."""
    config = load_config()
    # Filtrar rutas inválidas al obtenerlas
    valid_vaults = {}
    for name, path_str in config.get("vaults", {}).items():
        if Path(path_str).is_dir():
            valid_vaults[name] = path_str
        else:
            print(f"Advertencia: La ruta guardada para '{name}' ({path_str}) ya no es válida. Se ignorará.", file=sys.stderr)
            # Considerar eliminarla aquí si se desea limpieza automática
    return valid_vaults

def add_vault(name: str, path_str: str) -> bool:
    """Añade o actualiza una bóveda en la configuración."""
    if not name or not path_str:
        print("Error: Se requiere un nombre y una ruta para añadir la bóveda.", file=sys.stderr)
        return False

    try:
        # Intentar resolver la ruta y verificar si es directorio
        vault_path = Path(path_str).resolve()
        if not vault_path.is_dir():
            print(f"Error: La ruta proporcionada no es un directorio válido: {vault_path}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"Error al procesar la ruta '{path_str}': {e}", file=sys.stderr)
        return False

    config = load_config()
    # Forzar sobreescritura si el nombre ya existe
    if name in config["vaults"]:
        print(f"Advertencia: Actualizando la ruta para la bóveda existente '{name}'.")
    config["vaults"][name] = str(vault_path) # Siempre guardar como string
    save_config(config)
    print(f"Bóveda '{name}' añadida/actualizada: {vault_path}")
    return True

def remove_vault(name: str) -> bool:
    """Elimina una bóveda de la configuración por nombre."""
    config = load_config()
    if name in config.get("vaults", {}):
        removed_path = config["vaults"].pop(name)
        print(f"Bóveda '{name}' eliminada (ruta: {removed_path}).")
        if config.get("last_vault_name") == name:
            config["last_vault_name"] = None
            print("Era la última bóveda usada, se ha reseteado la preferencia.")
        save_config(config)
        return True
    else:
        print(f"Error: No se encontró una bóveda con el nombre '{name}'.", file=sys.stderr)
        return False

def get_last_vault() -> Optional[Tuple[str, Path]]:
    """Obtiene el nombre y la ruta (Path obj) de la última bóveda usada VÁLIDA."""
    config = load_config()
    last_name = config.get("last_vault_name")
    vaults = config.get("vaults", {}) # Cargar bóvedas actuales

    if last_name and last_name in vaults:
        path_str = vaults[last_name]
        try:
            path_obj = Path(path_str).resolve()
            if path_obj.is_dir():
                return last_name, path_obj
            else:
                # La ruta guardada ya no es válida
                print(f"Advertencia: La ruta para la última bóveda '{last_name}' ({path_str}) no es válida. Reseteando preferencia.", file=sys.stderr)
                config["last_vault_name"] = None
                save_config(config) # Guardar el reseteo
                return None
        except Exception as e:
             print(f"Error al procesar ruta de última bóveda '{path_str}': {e}. Reseteando preferencia.", file=sys.stderr)
             config["last_vault_name"] = None
             save_config(config)
             return None
    # Si no había last_name o el nombre ya no está en vaults
    if last_name:
        print(f"Advertencia: La última bóveda usada '{last_name}' ya no existe en la configuración. Reseteando preferencia.", file=sys.stderr)
        config["last_vault_name"] = None
        save_config(config)

    return None # No hay última bóveda válida

def set_last_vault(name: str):
    """Establece la última bóveda usada por su nombre (verifica que exista)."""
    config = load_config()
    if name in config.get("vaults", {}):
        if Path(config["vaults"][name]).is_dir(): # Verificar validez antes de guardar
            current_last = config.get("last_vault_name")
            if current_last != name:
                config["last_vault_name"] = name
                save_config(config)
                # print(f"'{name}' establecida como última bóveda usada.") # Opcional: Mensaje de confirmación
        else:
             print(f"Advertencia: No se pudo establecer '{name}' como última bóveda porque su ruta no es válida.", file=sys.stderr)
    else:
        print(f"Advertencia: No se pudo establecer '{name}' como última bóveda porque no existe.", file=sys.stderr)