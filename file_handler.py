# file_handler.py
import os
from pathlib import Path
from typing import List, Optional, Set # Añadir Optional si no estaba
import sys

def find_relevant_files(
    vault_path: Path,
    target_paths: List[str],
    extensions: List[str],
    excluded_extensions: List[str] = [], # <--- NUEVO PARÁMETRO con default
) -> List[Path]:
    """
    Encuentra archivos dentro de la bóveda que coincidan con las extensiones
    incluidas, no coincidan con las excluidas, y estén dentro de las rutas objetivo.

    Args:
        vault_path: Ruta absoluta al directorio raíz de la bóveda.
        target_paths: Lista de rutas relativas (strings) dentro de la bóveda.
                      Vacía para buscar en toda la bóveda.
        extensions: Lista de extensiones a incluir (ej: ['.md', '.txt']).
        excluded_extensions: Lista de extensiones a excluir (ej: ['.log', '.tmp']).

    Returns:
        Una lista ordenada de objetos Path apuntando a los archivos relevantes.
    """
    relevant_files: List[Path] = []
    # Normalizar extensiones incluidas
    normalized_extensions = {f".{ext.lower().lstrip('.')}" for ext in extensions if ext}
    # Normalizar extensiones excluidas
    normalized_excluded_extensions = {f".{ext.lower().lstrip('.')}" for ext in excluded_extensions if ext} # <--- NUEVO

    resolved_target_paths: Set[Path] = set()
    is_vault_search = not target_paths

    if not vault_path.is_dir():
        print(f"Error: La ruta de la bóveda no es válida: {vault_path}", file=sys.stderr)
        return []

    # Resolver targets
    if not is_vault_search:
        # ... (lógica de resolución de targets sin cambios) ...
        for target in target_paths:
             try:
                 abs_target = (vault_path / target).resolve()
                 abs_target.relative_to(vault_path.resolve()) # Verificar que esté dentro
                 resolved_target_paths.add(abs_target)
             except ValueError: print(f"Advertencia: Target '{target}' fuera de bóveda o inválido. Ignorando.", file=sys.stderr)
             except Exception as e: print(f"Advertencia: Error procesando target '{target}': {e}. Ignorando.", file=sys.stderr)
        if not resolved_target_paths:
            print("Advertencia: Ninguna ruta objetivo válida. Buscando en toda la bóveda.", file=sys.stderr)
            is_vault_search = True

    # Mensajes de búsqueda
    print(f"\nBuscando archivos con extensiones incluidas: {', '.join(normalized_extensions) or 'Ninguna'}", file=sys.stderr)
    if normalized_excluded_extensions: # <--- NUEVO log
        print(f"Excluyendo extensiones: {', '.join(normalized_excluded_extensions)}", file=sys.stderr)
    if not is_vault_search: print(f"Dentro de los objetivos: {', '.join(p.name for p in resolved_target_paths)}", file=sys.stderr)
    else: print("En toda la bóveda.", file=sys.stderr)

    files_processed_count = 0
    try:
        for item in vault_path.rglob('*'):
            if item.is_file():
                files_processed_count += 1
                item_suffix_lower = item.suffix.lower()

                # Comprobar INCLUSIÓN Y EXCLUSIÓN
                passes_inclusion = not normalized_extensions or item_suffix_lower in normalized_extensions
                passes_exclusion = item_suffix_lower not in normalized_excluded_extensions # <--- Lógica de exclusión

                if passes_inclusion and passes_exclusion: # <--- Ambas deben cumplirse
                    # Comprobar si está en los targets (si aplica)
                    if is_vault_search:
                        relevant_files.append(item)
                    else:
                        try:
                            item_resolved = item.resolve()
                            is_relevant = False
                            for target in resolved_target_paths:
                                # El archivo es un target directo O está dentro de un directorio target
                                if item_resolved == target or (target.is_dir() and item_resolved.is_relative_to(target)):
                                     is_relevant = True
                                     break
                            if is_relevant:
                                relevant_files.append(item)
                        except Exception as e: print(f"Advertencia: Error procesando ruta de archivo {item}: {e}", file=sys.stderr)

    except PermissionError: print(f"Error: Permiso denegado al acceder a {vault_path} o subdirectorios.", file=sys.stderr)
    except Exception as e: print(f"Error inesperado buscando archivos: {e}", file=sys.stderr)

    relevant_files.sort()
    print(f"Archivos procesados: {files_processed_count}", file=sys.stderr)
    print(f"Archivos relevantes encontrados: {len(relevant_files)}", file=sys.stderr)
    return relevant_files

def read_file_content(file_path: Path) -> Optional[str]:
    """
    Lee el contenido de un archivo, intentando con codificación UTF-8 y fallback a latin-1.

    Args:
        file_path: Ruta al archivo a leer.

    Returns:
        El contenido del archivo como string, o None si ocurre un error irrecuperable.
    """
    try:
        return file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        print(f"Advertencia: No se pudo decodificar {file_path.name} como UTF-8. Intentando con 'latin-1'.", file=sys.stderr)
        try:
            return file_path.read_text(encoding='latin-1')
        except Exception as e_latin:
             print(f"Error: Falló también la lectura con 'latin-1' para {file_path.name}: {e_latin}", file=sys.stderr)
             return None
    except FileNotFoundError:
        print(f"Error: Archivo no encontrado al intentar leer: {file_path}", file=sys.stderr)
        return None
    except IOError as e_io:
        print(f"Error de E/S al leer el archivo {file_path}: {e_io}", file=sys.stderr)
        return None
    except Exception as e_other:
         print(f"Error inesperado al leer {file_path}: {e_other}", file=sys.stderr)
         return None