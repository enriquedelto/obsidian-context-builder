import os
from pathlib import Path
from typing import List, Optional, Set
import sys # Para mensajes de error

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
    normalized_extensions = {ext.lower() for ext in extensions if ext.startswith('.')}
    resolved_target_paths: Set[Path] = set()

    if not vault_path.is_dir():
        print(f"Error: La ruta de la bóveda no existe o no es un directorio: {vault_path}", file=sys.stderr)
        return []

    # Resolver targets a rutas absolutas para comparación robusta
    if target_paths:
        for target in target_paths:
            abs_target = (vault_path / target).resolve()
            # Verificación básica de que el target está dentro de la bóveda
            try:
                abs_target.relative_to(vault_path.resolve())
                resolved_target_paths.add(abs_target)
            except ValueError:
                 print(f"Advertencia: La ruta objetivo '{target}' parece estar fuera de la bóveda '{vault_path}'. Ignorando.", file=sys.stderr)


    print(f"Buscando archivos con extensiones: {', '.join(normalized_extensions)}")
    if resolved_target_paths:
         print(f"Dentro de los objetivos: {', '.join(target_paths)}")
    else:
        print("En toda la bóveda.")

    try:
        for item in vault_path.rglob('*'):
            if item.is_file() and item.suffix.lower() in normalized_extensions:
                # Si no hay targets específicos, añadir todos los archivos .md
                if not resolved_target_paths:
                    relevant_files.append(item)
                else:
                    # Verificar si el archivo está dentro de alguno de los directorios objetivo
                    is_within_target = False
                    try:
                        # Comprobar si el *directorio* del archivo es un subdirectorio
                        # o el mismo directorio que uno de los targets.
                        file_dir = item.parent.resolve()
                        for target_dir in resolved_target_paths:
                             if file_dir == target_dir or target_dir in file_dir.parents:
                                 is_within_target = True
                                 break
                    except Exception as e:
                         print(f"Advertencia: Error al procesar la ruta del archivo {item}: {e}", file=sys.stderr)

                    if is_within_target:
                        relevant_files.append(item)

    except PermissionError:
        print(f"Error: Permiso denegado al intentar acceder a {vault_path} o sus subdirectorios.", file=sys.stderr)
    except Exception as e:
         print(f"Error inesperado durante la búsqueda de archivos: {e}", file=sys.stderr)


    relevant_files.sort() # Ordenar alfabéticamente por ruta completa
    print(f"Encontrados {len(relevant_files)} archivos relevantes.")
    return relevant_files

def read_file_content(file_path: Path) -> Optional[str]:
    """
    Lee el contenido de un archivo, intentando con codificación UTF-8.

    Args:
        file_path: Ruta al archivo a leer.

    Returns:
        El contenido del archivo como string, o None si ocurre un error.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Archivo no encontrado al intentar leer: {file_path}", file=sys.stderr)
        return None
    except UnicodeDecodeError:
        print(f"Error: No se pudo decodificar el archivo {file_path} como UTF-8. Intentando con 'latin-1'.", file=sys.stderr)
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
             print(f"Error: Falló también la lectura con 'latin-1' para {file_path}: {e}", file=sys.stderr)
             return None
    except IOError as e:
        print(f"Error de E/S al leer el archivo {file_path}: {e}", file=sys.stderr)
        return None
    except Exception as e:
         print(f"Error inesperado al leer {file_path}: {e}", file=sys.stderr)
         return None