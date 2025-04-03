# core.py
from pathlib import Path
import sys
from typing import List, Optional, Dict, Tuple

# Importar módulos necesarios para la lógica central
import file_handler
import tree_generator
import formatter
import prompt_handler # Para inject_context_multi

# Definir constantes compartidas
DEFAULT_PLACEHOLDERS: Dict[str, str] = {
    "contexto_extraido": "{contexto_extraido}",
    "ruta_destino": "{ruta_destino}",
    "etiqueta_jerarquica_1": "{etiqueta_jerarquica_1}",
    "etiqueta_jerarquica_2": "{etiqueta_jerarquica_2}",
    "etiqueta_jerarquica_3": "{etiqueta_jerarquica_3}",
    "etiqueta_jerarquica_4": "{etiqueta_jerarquica_4}",
    "etiqueta_jerarquica_5": "{etiqueta_jerarquica_5}",
}
DEFAULT_EXTENSIONS = ['.md']

# --- Funciones de Lógica Central ---

def generate_hierarchical_tags(relative_note_path: Optional[Path]) -> List[str]:
    """Extrae etiquetas jerárquicas de una ruta relativa a la bóveda. Devuelve lista vacía si la ruta es None."""
    if relative_note_path is None:
        return []
    tags = []
    current_parts = []
    # Usar parent para obtener solo la ruta del directorio, no el archivo
    # Asegurarse de que parts no incluya '.' si la ruta es solo el nombre de archivo
    clean_parts = [p for p in relative_note_path.parent.parts if p and p != '.']
    for part in clean_parts:
        # Reemplazar espacios y guiones para formato de etiqueta común
        cleaned_part = part.replace(" ", "_").replace("-", "_").replace(".", "_") # Reemplazar puntos también
        # Evitar partes vacías después de la limpieza
        if not cleaned_part:
            continue
        current_parts.append(cleaned_part)
        tags.append("/".join(current_parts))
    # Devolver en orden de más específico a más general
    return list(reversed(tags)) # _1 = padre directo, _2 = abuelo, etc.


def generate_prompt_core(
    vault_path: Path,
    target_paths: List[str],
    extensions: List[str],
    output_mode: str,
    output_note_path: Optional[Path], # Ruta relativa a la bóveda
    template_string: str,
    excluded_extensions: Optional[List[str]] = None # <--- NUEVO PARÁMETRO
) -> str:
    """
    Lógica central para generar el prompt final.
    """
    print("--- Iniciando Lógica Core ---", file=sys.stderr)
    print(f"Core - Bóveda: {vault_path}", file=sys.stderr)
    print(f"Core - Targets: {target_paths}", file=sys.stderr)
    print(f"Core - Extensiones: {extensions}", file=sys.stderr)
    print(f"Core - Modo Contexto: {output_mode}", file=sys.stderr)
    print(f"Core - Ruta Nota Destino: {output_note_path if output_note_path else 'No especificada'}", file=sys.stderr)
    print(f"Core - Excluir Extensiones: {excluded_extensions if excluded_extensions else 'Ninguna'}", file=sys.stderr)

    # 1. Encontrar archivos relevantes
    relevant_files: List[Path] = file_handler.find_relevant_files(
        vault_path,
        target_paths,
        extensions,
        excluded_extensions or [] # Pasar lista vacía si es None
    )
    if not relevant_files and output_mode != 'tree':
        print("\nCore - Advertencia: No se encontraron archivos relevantes (considerando inclusiones/exclusiones) para incluir contenido.", file=sys.stderr)

    # 2. Generar string del árbol (si aplica)
    tree_string = ""
    if output_mode in ['tree', 'both']:
        print("\nCore - Generando estructura de árbol...", file=sys.stderr)
        # Pasar copia de la lista por si la función la modifica internamente (aunque no debería)
        tree_string = tree_generator.generate_tree_string(list(relevant_files), vault_path)
        if not tree_string.strip() or tree_string.startswith(" (No se encontraron"):
             print("Core - Advertencia: No se generó estructura de árbol válida.", file=sys.stderr)
             tree_string = " (No se generó estructura de árbol para los targets/extensiones especificados)" # Mensaje más claro

    # 3. Formatear contenido (si aplica)
    formatted_contents: List[str] = []
    content_block_str = ""
    if output_mode in ['content', 'both']:
        if relevant_files:
             print("\nCore - Formateando contenido de archivos...", file=sys.stderr)
             for file_path in relevant_files:
                 formatted = formatter.format_file_content(file_path, vault_path)
                 if formatted:
                     formatted_contents.append(formatted)
             if not formatted_contents:
                  print("Core - Advertencia: No se pudo formatear contenido de los archivos encontrados.", file=sys.stderr)
             content_block_str = "".join(formatted_contents).strip() # Unir sin separadores extra
        else:
             print("\nCore - No hay archivos relevantes para formatear contenido.", file=sys.stderr)
             content_block_str = "" # String vacío es más seguro para reemplazar placeholders

    # 4. Construir bloque de contexto final
    print(f"\nCore - Construyendo bloque de contexto (Modo: {output_mode})...", file=sys.stderr)
    context_block = ""
    # Asegurarse de que tree_part no sea solo el mensaje de error
    tree_part = tree_string.strip() if tree_string and not tree_string.startswith(" (No se generó") else ""
    content_part = content_block_str

    if output_mode == 'tree':
        context_block = tree_part if tree_part else "(Estructura de árbol no disponible o vacía)"
    elif output_mode == 'content':
        context_block = content_part if content_part else "(Contenido no disponible o vacío)"
    elif output_mode == 'both':
        if tree_part and content_part:
            # Añadir un separador visual claro entre árbol y contenido si ambos existen
            separator = "\n" + ("-" * 40) + " CONTENIDO " + ("-" * 40) + "\n\n"
            context_block = tree_part + separator + content_part
        elif tree_part:
            context_block = tree_part
        elif content_part:
            context_block = content_part
        else:
             context_block = "(No se generó ni árbol ni contenido para el contexto)"

    print(f"Core - Contexto generado (primeros 100 chars): {context_block[:100].replace(chr(10), ' ')}...", file=sys.stderr)

    # 5. Preparar valores para reemplazo (placeholders)
    ruta_destino_relativa_str = output_note_path.as_posix() if output_note_path else "" # Vacío si no hay ruta
    hierarchical_tags = generate_hierarchical_tags(output_note_path)

    replacements: Dict[str, Optional[str]] = {
        DEFAULT_PLACEHOLDERS["contexto_extraido"]: context_block,
        DEFAULT_PLACEHOLDERS["ruta_destino"]: ruta_destino_relativa_str,
    }

    # Rellenar placeholders de etiquetas jerárquicas dinámicamente
    max_tag_level = 0
    for key in DEFAULT_PLACEHOLDERS:
        if key.startswith("etiqueta_jerarquica_"):
            try:
                level = int(key.split("_")[-1])
                max_tag_level = max(max_tag_level, level)
            except ValueError:
                pass # Ignorar si no tiene número al final

    for i in range(max_tag_level):
        level = i + 1
        placeholder_fmt = DEFAULT_PLACEHOLDERS.get(f"etiqueta_jerarquica_{level}")
        if placeholder_fmt:
            # Usar tag o "" si no hay suficientes niveles en la ruta
            tag_value = hierarchical_tags[i] if i < len(hierarchical_tags) else ""
            replacements[placeholder_fmt] = tag_value

    # 6. Inyectar placeholders usando la función de prompt_handler
    print("\nCore - Inyectando placeholders en la plantilla...", file=sys.stderr)
    final_prompt = prompt_handler.inject_context_multi(template_string, replacements)

    # Advertir si placeholders clave están vacíos porque faltó la ruta
    if not ruta_destino_relativa_str and DEFAULT_PLACEHOLDERS["ruta_destino"] in template_string:
        print(f"Core - Advertencia: El placeholder {{ruta_destino}} está presente en la plantilla pero no se proporcionó Ruta Nota Destino.", file=sys.stderr)
    if not hierarchical_tags and any(DEFAULT_PLACEHOLDERS.get(f"etiqueta_jerarquica_{i+1}") in template_string for i in range(max_tag_level)):
         print(f"Core - Advertencia: Hay placeholders {{etiqueta_jerarquica_N}} en la plantilla pero no se proporcionó Ruta Nota Destino para generarlas.", file=sys.stderr)


    print("--- Fin Lógica Core ---", file=sys.stderr)
    return final_prompt