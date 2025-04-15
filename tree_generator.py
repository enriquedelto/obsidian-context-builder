# tree_generator.py
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set # Añadir Set
import sys # Añadir sys para stderr

def generate_tree_string(file_paths: List[Path], vault_path: Path) -> str:
    """
    Genera una representación de árbol de los archivos y directorios dados,
    mostrando solo los directorios que contienen archivos relevantes o son
    ancestros de estos.

    Args:
        file_paths: Lista de rutas absolutas a los archivos a incluir en el árbol.
        vault_path: Ruta absoluta a la raíz de la bóveda.

    Returns:
        Un string multi-línea representando la estructura de árbol.
    """
    if not file_paths:
        # Ser más específico si la lista original estaba vacía
        return " (No se encontraron archivos relevantes para generar el árbol)"

    tree: Dict[str, Any] = {}
    # Guardar todos los directorios padres de los archivos relevantes
    relevant_dirs: Set[Path] = set()
    for file_path in file_paths:
        try:
            # Obtener la ruta relativa y añadir todos sus directorios padres
            relative_path = file_path.relative_to(vault_path)
            parent = relative_path.parent
            # Añadir todos los ancestros hasta la raíz de la bóveda
            relevant_dirs.add(vault_path / parent)
            for ancestor in parent.parents:
                if ancestor != Path('.'): # Evitar añadir el directorio actual '.'
                     relevant_dirs.add(vault_path / ancestor)
        except ValueError:
            print(f"Advertencia: {file_path.name} no parece estar dentro de {vault_path}, se omitirá del árbol.", file=sys.stderr)
            continue
        except Exception as e:
             print(f"Advertencia: Error procesando ruta para árbol {file_path.name}: {e}", file=sys.stderr)
             continue


    # Construir la estructura jerárquica solo con dirs/files relevantes
    processed_paths: set[Path] = set() # Para evitar duplicados

    all_paths_to_process = sorted(list(relevant_dirs) + file_paths) # Ordenar todo junto

    for item_path in all_paths_to_process:
         if item_path in processed_paths:
              continue

         try:
            relative_path = item_path.relative_to(vault_path)
         except ValueError:
              continue # Ya se advirtió antes

         parts = relative_path.parts
         current_level = tree
         path_accumulator = vault_path

         # Navegar/crear directorios en el árbol
         for i, part in enumerate(parts[:-1]): # Iterar sobre los directorios
             path_accumulator = path_accumulator / part
             # Solo añadir si es un directorio relevante o un ancestro necesario
             if path_accumulator in relevant_dirs or any(rd.is_relative_to(path_accumulator) for rd in relevant_dirs):
                 if part not in current_level:
                     current_level[part] = {}
                 # Verificar que sea un diccionario antes de descender
                 if isinstance(current_level[part], dict):
                      current_level = current_level[part]
                 else:
                      # Conflicto: un archivo tiene el mismo nombre que un directorio padre? Raro.
                      print(f"Advertencia: Conflicto de nombre en árbol para '{part}'", file=sys.stderr)
                      break # No se puede continuar por esta rama
                 processed_paths.add(path_accumulator)
             else:
                 # Directorio no relevante, no seguir por esta rama
                 current_level = None # Marcar para salir del bucle interno
                 break

         if current_level is None: # Si se interrumpió el bucle anterior
              continue

         # Añadir el archivo o el directorio final (si es relevante)
         if not parts:
            continue
         
         final_part = parts[-1]
         if item_path.is_file() and item_path in file_paths:
             current_level[final_part] = True # Marcar como archivo
             processed_paths.add(item_path)
         elif item_path.is_dir() and item_path in relevant_dirs:
              # Asegurar que el directorio se cree si no existe (por si era un target directo)
              if final_part not in current_level:
                   current_level[final_part] = {}
              processed_paths.add(item_path)

    # --- Función interna para construir las líneas (sin cambios) ---
    def build_lines(node: Dict[str, Any], prefix: str = "") -> List[str]:
        lines: List[str] = []
        items = sorted(node.items(), key=lambda item: (not isinstance(item[1], dict), item[0].lower())) # Dirs primero, case-insensitive
        pointers = {i: "├── " for i in range(len(items) - 1)}
        pointers[len(items) - 1] = "└── "

        for i, (name, value) in enumerate(items):
            pointer = pointers[i]
            lines.append(prefix + pointer + name)

            if isinstance(value, dict): # Es un directorio
                # No añadir extensión si es el último item O si el directorio está vacío
                is_last = (i == len(items) - 1)
                extension = "    " if is_last else "│   "
                # Evitar recursión infinita en diccionarios vacíos que pudieron quedar
                if value:
                    lines.extend(build_lines(value, prefix + extension))
                # else: # Opcional: indicar directorio vacío?
                #    if not is_last: lines.append(prefix + extension)
        return lines
    # --- Fin función interna ---

    if not tree:
         # Si después de procesar, el árbol está vacío (quizás solo archivos en la raíz?)
         # Reintentar solo con los archivos
         if file_paths:
              for file_path in file_paths:
                   try:
                        relative_path = file_path.relative_to(vault_path)
                        if not relative_path.parent.parts: # Archivo en la raíz
                            tree[relative_path.name] = True
                   except ValueError: continue
         if not tree: # Aún vacío
             return " (No se pudo generar una estructura de árbol con los elementos proporcionados)"


    tree_lines = build_lines(tree)

    # Añadir un prefijo indicando la raíz (puede ser útil)
    # root_prefix = f"{vault_path.name}/\n" if vault_path.name else "./\n"
    # return root_prefix + "\n".join(tree_lines)
    # O simplemente devolver el árbol relativo
    return "\n".join(tree_lines)