from pathlib import Path
from typing import List, Dict, Any, Tuple

def generate_tree_string(file_paths: List[Path], vault_path: Path) -> str:
    """
    Genera una representación de árbol de los archivos y directorios dados.

    Args:
        file_paths: Lista de rutas absolutas a los archivos a incluir en el árbol.
        vault_path: Ruta absoluta a la raíz de la bóveda para calcular rutas relativas.

    Returns:
        Un string multi-línea representando la estructura de árbol.
    """
    if not file_paths:
        return " (No se encontraron archivos relevantes para mostrar en el árbol)"

    tree: Dict[str, Any] = {}
    processed_dirs: set[Path] = set()

    # Construir la estructura jerárquica (diccionario anidado)
    for file_path in file_paths:
        try:
            relative_path = file_path.relative_to(vault_path)
        except ValueError:
             # Esto no debería ocurrir si find_relevant_files funciona bien
             print(f"Advertencia: {file_path} no parece estar dentro de {vault_path}", file=sys.stderr)
             continue

        parts = relative_path.parts
        current_level = tree
        # Crear nodos para directorios padres
        for i, part in enumerate(parts[:-1]): # Iterar sobre los directorios
            current_dir_path = vault_path.joinpath(*parts[:i+1])
            if current_dir_path not in processed_dirs:
                 if part not in current_level:
                     current_level[part] = {} # Crear sub-diccionario si no existe
                 processed_dirs.add(current_dir_path)
            current_level = current_level[part]

        # Añadir el archivo al nivel correspondiente
        filename = parts[-1]
        current_level[filename] = True # Marcar como archivo (podría ser el Path si se necesita)


    # Función recursiva para construir las líneas del árbol
    def build_lines(node: Dict[str, Any], prefix: str = "") -> List[str]:
        lines: List[str] = []
        # Obtener items ordenados (directorios primero, luego archivos)
        items = sorted(node.items(), key=lambda item: (isinstance(item[1], dict), item[0]))
        pointers = {i: "├── " for i in range(len(items) - 1)}
        pointers[len(items) - 1] = "└── "

        for i, (name, value) in enumerate(items):
            pointer = pointers[i]
            lines.append(prefix + pointer + name)

            if isinstance(value, dict): # Es un directorio
                extension = "│   " if i < len(items) - 1 else "    "
                lines.extend(build_lines(value, prefix + extension))
        return lines

    # Añadir la raíz de la bóveda (o los puntos de entrada si hay targets)
    # Para simplificar, empezamos desde la estructura generada
    tree_lines = build_lines(tree)

    # Determinar el prefijo inicial (nombre de la bóveda o '.')
    # root_display_name = vault_path.name if vault_path.name else '.'
    # return root_display_name + "\n" + "\n".join(tree_lines)
    # Por ahora, devolvemos solo el árbol relativo interno
    return "\n".join(tree_lines)