# file_handler.py
import os
from pathlib import Path
from typing import List, Optional, Set
import sys

def find_relevant_files(
    vault_path: Path,
    target_paths: List[str],
    extensions: List[str],
) -> List[Path]:
    """
    Encuentra archivos dentro de la bóveda que coincidan con las extensiones
    y estén dentro de las rutas objetivo especificadas.

    Args:
        vault_path: Ruta absoluta al directorio raíz de la bóveda.
        target_paths: Lista de rutas relativas (strings) dentro de la bóveda
                      para enfocar la búsqueda. Si está vacía, busca en toda la bóveda.
        extensions: Lista de extensiones de archivo a incluir (ej: ['.md', '.txt']).

    Returns:
        Una lista ordenada de objetos Path apuntando a los archivos relevantes.
    """
    relevant_files: List[Path] = []
    # Normalizar extensiones a minúsculas y asegurar que empiecen con '.'
    normalized_extensions = {f".{ext.lower().lstrip('.')}" for ext in extensions}
    resolved_target_paths: Set[Path] = set()
    is_vault_search = not target_paths # True si buscamos en toda la bóveda

    if not vault_path.is_dir():
        print(f"Error: La ruta de la bóveda no existe o no es un directorio: {vault_path}", file=sys.stderr)
        return []

    # Resolver targets a rutas absolutas y verificar que estén dentro de la bóveda
    if not is_vault_search:
        for target in target_paths:
            try:
                # Construir ruta absoluta y resolverla (maneja '..')
                abs_target = (vault_path / target).resolve()
                # Verificar que esté DENTRO de la bóveda resuelta
                abs_target.relative_to(vault_path.resolve())
                resolved_target_paths.add(abs_target)
            except ValueError:
                 print(f"Advertencia: La ruta objetivo '{target}' parece estar fuera de la bóveda '{vault_path}' o no existe. Ignorando.", file=sys.stderr)
            except Exception as e:
                 print(f"Advertencia: Error al procesar la ruta objetivo '{target}': {e}. Ignorando.", file=sys.stderr)
        # Si después de procesar, no queda ningún target válido, actuar como si no se hubieran dado targets
        if not resolved_target_paths:
            print("Advertencia: Ninguna ruta objetivo válida encontrada. Buscando en toda la bóveda.", file=sys.stderr)
            is_vault_search = True


    print(f"\nBuscando archivos con extensiones: {', '.join(normalized_extensions)}", file=sys.stderr)
    if not is_vault_search:
         print(f"Dentro de los objetivos: {', '.join(p.name for p in resolved_target_paths)}", file=sys.stderr)
    else:
        print("En toda la bóveda.", file=sys.stderr)

    files_processed_count = 0
    try:
        for item in vault_path.rglob('*'):
            if item.is_file():
                files_processed_count += 1
                # Comprobar extensión
                if item.suffix.lower() in normalized_extensions:
                    # Si es búsqueda global o el archivo está en un target, añadirlo
                    if is_vault_search:
                        relevant_files.append(item)
                    else:
                        try:
                            item_resolved = item.resolve()
                            # Verificar si el archivo mismo es un target o si está DENTRO de un directorio target
                            is_relevant = False
                            for target in resolved_target_paths:
                                if item_resolved == target: # El archivo es un target directo
                                     is_relevant = True
                                     break
                                if target.is_dir() and item_resolved.parent.is_relative_to(target): # El archivo está en un subdirectorio del target
                                # Simplificado: comprobar si el padre del archivo está "por debajo" del directorio target
                                # Usar is_relative_to es más robusto que mirar parents
                                # if target.is_dir() and target in item_resolved.parents: # Chequeo alternativo menos robusto con links simbólicos
                                     is_relevant = True
                                     break
                            if is_relevant:
                                relevant_files.append(item)
                        except Exception as e:
                             # Errores de resolución de links simbólicos rotos, etc.
                             print(f"Advertencia: Error al procesar la ruta del archivo {item}: {e}", file=sys.stderr)

    except PermissionError:
        print(f"Error: Permiso denegado al intentar acceder a {vault_path} o sus subdirectorios.", file=sys.stderr)
    except Exception as e:
         print(f"Error inesperado durante la búsqueda de archivos: {e}", file=sys.stderr)


    relevant_files.sort() # Ordenar alfabéticamente por ruta completa
    # Usar stderr para mensajes informativos que no son el resultado principal
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
        # Usar 'errors='ignore'' es una opción si fallos de decodificación son frecuentes
        # pero puede perder datos. Mejor intentar con latin-1.
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