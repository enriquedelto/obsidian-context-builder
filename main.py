# main.py
import argparse
from pathlib import Path
import sys
from typing import List, Optional, Dict, Tuple # Añadir Tuple
import os

# Importar módulos propios
import file_handler
import tree_generator
import formatter
import prompt_handler
import config_handler # <-- NUEVO

# Definir los placeholders por defecto
DEFAULT_PLACEHOLDERS: Dict[str, str] = {
    "contexto_extraido": "{contexto_extraido}",
    "ruta_destino": "{ruta_destino}",
    "etiqueta_jerarquica_1": "{etiqueta_jerarquica_1}",
    "etiqueta_jerarquica_2": "{etiqueta_jerarquica_2}",
    "etiqueta_jerarquica_3": "{etiqueta_jerarquica_3}",
    # Añadir más si se necesitan a menudo
    "etiqueta_jerarquica_4": "{etiqueta_jerarquica_4}",
    "etiqueta_jerarquica_5": "{etiqueta_jerarquica_5}",
}
DEFAULT_EXTENSIONS = ['.md']

# --- Función generate_hierarchical_tags (Mejorada) ---
def generate_hierarchical_tags(relative_note_path: Path) -> List[str]:
    """Extrae etiquetas jerárquicas de una ruta relativa a la bóveda."""
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


# --- Función generate_prompt_core (Mejorada para placeholders) ---
def generate_prompt_core(
    vault_path: Path,
    target_paths: List[str],
    extensions: List[str],
    output_mode: str,
    output_note_path: Path, # Ruta relativa a la bóveda
    template_string: str
) -> str:
    """
    Lógica central para generar el prompt final.
    """
    print("--- Iniciando Lógica Core ---", file=sys.stderr)
    print(f"Core - Bóveda: {vault_path}", file=sys.stderr)
    print(f"Core - Targets: {target_paths}", file=sys.stderr)
    print(f"Core - Extensiones: {extensions}", file=sys.stderr)
    print(f"Core - Modo Contexto: {output_mode}", file=sys.stderr)
    print(f"Core - Ruta Nota Destino: {output_note_path}", file=sys.stderr)

    # 1. Encontrar archivos relevantes
    relevant_files: List[Path] = file_handler.find_relevant_files(
        vault_path, target_paths, extensions
    )
    if not relevant_files and output_mode != 'tree':
        print("\nCore - Advertencia: No se encontraron archivos relevantes para incluir contenido.", file=sys.stderr)

    # 2. Generar string del árbol (si aplica)
    tree_string = ""
    if output_mode in ['tree', 'both']:
        print("\nCore - Generando estructura de árbol...", file=sys.stderr)
        tree_string = tree_generator.generate_tree_string(relevant_files, vault_path)
        if not tree_string.strip() or tree_string.startswith(" (No se encontraron"):
             print("Core - Advertencia: No se generó estructura de árbol válida.", file=sys.stderr)
             tree_string = " (No se generó estructura de árbol para los targets especificados)" # Mensaje más claro

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
             content_block_str = "".join(formatted_contents).strip() # Unir con un solo separador final
        else:
             print("\nCore - No hay archivos relevantes para formatear contenido.", file=sys.stderr)
             # Decidir qué poner si no hay contenido: string vacío o un mensaje
             content_block_str = "" # String vacío es más seguro para reemplazar placeholders

    # 4. Construir bloque de contexto final
    print(f"\nCore - Construyendo bloque de contexto (Modo: {output_mode})...", file=sys.stderr)
    context_block = ""
    tree_part = tree_string.strip() if tree_string and not tree_string.startswith(" (No se generó") else ""
    content_part = content_block_str

    if output_mode == 'tree':
        context_block = tree_part if tree_part else "(Estructura de árbol no disponible o vacía)"
    elif output_mode == 'content':
        context_block = content_part if content_part else "(Contenido no disponible o vacío)"
    elif output_mode == 'both':
        if tree_part and content_part:
            context_block = tree_part + "\n\n" + content_part # Separador más claro
        elif tree_part:
            context_block = tree_part
        elif content_part:
            context_block = content_part
        else:
             context_block = "(No se generó ni árbol ni contenido para el contexto)"

    print(f"Core - Contexto generado (primeros 100 chars): {context_block[:100].replace(chr(10), ' ')}...", file=sys.stderr) # Reemplazar saltos para log

    # 5. Preparar valores para reemplazo (placeholders)
    ruta_destino_relativa_str = output_note_path.as_posix()
    hierarchical_tags = generate_hierarchical_tags(output_note_path)

    replacements: Dict[str, Optional[str]] = {
        DEFAULT_PLACEHOLDERS["contexto_extraido"]: context_block,
        DEFAULT_PLACEHOLDERS["ruta_destino"]: ruta_destino_relativa_str,
    }

    # Rellenar placeholders de etiquetas jerárquicas dinámicamente
    # Basado en cuántos placeholders {etiqueta_jerarquica_N} existen en DEFAULT_PLACEHOLDERS
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
            tag_value = hierarchical_tags[i] if i < len(hierarchical_tags) else "" # Usar tag o "" si no hay suficientes niveles
            replacements[placeholder_fmt] = tag_value
            # print(f"Core - Placeholder {placeholder_fmt} = '{tag_value}'") # Debug

    # 6. Inyectar placeholders
    print("\nCore - Inyectando placeholders en la plantilla...", file=sys.stderr)
    final_prompt = prompt_handler.inject_context_multi(template_string, replacements)

    print("--- Fin Lógica Core ---", file=sys.stderr)
    return final_prompt
# --- FIN FUNCIÓN CORE ---


# --- NUEVAS FUNCIONES PARA GESTIÓN INTERACTIVA (CLI) ---
def select_vault_interactive(vaults: Dict[str, str]) -> Optional[Tuple[str, Path]]:
    """Permite al usuario seleccionar una bóveda de una lista numerada."""
    if not vaults:
        print("No hay bóvedas guardadas. Use --add-vault para añadir una.", file=sys.stderr)
        return None

    print("\nBóvedas guardadas:")
    vault_list = list(vaults.items())
    for i, (name, path) in enumerate(vault_list):
        print(f"  {i+1}. {name} ({path})")

    while True:
        try:
            choice_str = input(f"Seleccione el número de la bóveda (1-{len(vault_list)}) o 'q' para salir: ").strip()
            if choice_str.lower() == 'q':
                return None
            if not choice_str.isdigit():
                 print("Entrada inválida. Por favor, introduzca un número o 'q'.")
                 continue
            index = int(choice_str) - 1
            if 0 <= index < len(vault_list):
                name, path_str = vault_list[index]
                path_obj = Path(path_str)
                if path_obj.is_dir():
                    return name, path_obj
                else:
                    print(f"Error: La ruta para '{name}' ({path_str}) no es válida. Inténtelo de nuevo.")
            else:
                print(f"Selección fuera de rango (1-{len(vault_list)}).")
        except ValueError: # Captura int() fallando si no es número
            print("Entrada inválida. Por favor, introduzca un número o 'q'.")
        except KeyboardInterrupt:
            print("\nSelección cancelada.")
            return None
        except EOFError: # Si se redirige la entrada y se acaba
             print("\nEntrada finalizada inesperadamente.")
             return None

def select_template_interactive(templates: Dict[str, str]) -> Optional[str]:
    """Permite al usuario seleccionar una plantilla de una lista numerada."""
    if not templates:
        print("No hay plantillas disponibles (ni predeterminadas ni en ./templates).", file=sys.stderr)
        return None

    print("\nPlantillas disponibles:")
    template_list = list(templates.keys()) # Nombres de las plantillas
    for i, name in enumerate(template_list):
         # Mostrar nombre más limpio
         display_name = name
         if name.startswith("Archivo: "):
             try:
                display_name = f"📄 {Path(templates[name]).name}"
             except Exception: # Por si la ruta guardada es inválida
                 display_name = f"📄 {name.split('Archivo: ')[1]} (ruta inválida?)"
         else:
              display_name = f"💡 {name}"
         print(f"  {i+1}. {display_name}")

    while True:
        try:
            choice_str = input(f"Seleccione el número de la plantilla (1-{len(template_list)}) o 'q' para salir: ").strip()
            if choice_str.lower() == 'q':
                return None
            if not choice_str.isdigit():
                 print("Entrada inválida. Por favor, introduzca un número o 'q'.")
                 continue
            index = int(choice_str) - 1
            if 0 <= index < len(template_list):
                return template_list[index] # Devolver el nombre original (key del dict)
            else:
                print(f"Selección fuera de rango (1-{len(template_list)}).")
        except ValueError:
            print("Entrada inválida. Por favor, introduzca un número o 'q'.")
        except KeyboardInterrupt:
            print("\nSelección cancelada.")
            return None
        except EOFError:
             print("\nEntrada finalizada inesperadamente.")
             return None

# --- FIN NUEVAS FUNCIONES INTERACTIVAS ---


def parse_arguments() -> argparse.Namespace:
    """Define y parsea los argumentos de la línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Generador de Contexto Obsidian para Prompts LLM.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Ejemplos:
  # Usar última bóveda, seleccionar plantilla interactivamente, target específico
  python main.py --target "Asignaturas/Cálculo" --output-note-path "Asignaturas/Cálculo/Resumen.md"

  # Añadir una nueva bóveda
  python main.py --add-vault "Principal" "/ruta/completa/a/mi/boveda"

  # Listar bóvedas y plantillas
  python main.py --list-vaults --list-templates

  # Seleccionar bóveda y plantilla específicas, guardar prompt
  python main.py --select-vault "Trabajo" --template "Resumir Contenido" --target "ProyectosActivos" --output-note-path "ResumenProyectos.md" --output mi_resumen.txt
"""
    )

    # --- Argumentos de Gestión de Bóvedas ---
    vault_group = parser.add_argument_group('Gestión de Bóvedas')
    vault_group.add_argument(
        "--select-vault",
        type=str,
        metavar='NOMBRE',
        help="Nombre de la bóveda guardada a usar para esta ejecución."
    )
    vault_group.add_argument(
        "--add-vault",
        nargs=2, # Espera 2 argumentos: nombre y ruta
        metavar=('NOMBRE', 'RUTA'),
        help="Añade o actualiza una bóveda con un nombre y ruta específicos."
    )
    vault_group.add_argument(
        "--remove-vault",
        type=str,
        metavar='NOMBRE',
        help="Elimina una bóveda guardada por su nombre."
    )
    vault_group.add_argument(
        "--list-vaults",
        action='store_true',
        help="Muestra las bóvedas guardadas y sale."
    )

    # --- Argumentos de Generación de Prompt ---
    gen_group = parser.add_argument_group('Generación de Prompt')
    # El --vault original ya no es necesario como argumento obligatorio
    gen_group.add_argument(
        "--target",
        type=str,
        action='append',
        default=[],
        metavar='RUTA_RELATIVA',
        help="Ruta relativa dentro de la bóveda para incluir. Repetir para múltiples targets. Si no se usa, procesa toda la bóveda."
    )
    gen_group.add_argument(
        "--ext",
        type=str,
        action='append',
        default=[],
        metavar='EXTENSION',
        help=f"Extensión de archivo a incluir (ej: .md, .canvas). Repetir para múltiples extensiones. Por defecto: {DEFAULT_EXTENSIONS}"
    )
    gen_group.add_argument(
        "--template", # Argumento unificado para plantillas
        type=str,
        metavar='NOMBRE_O_RUTA',
        help="Nombre de la plantilla predefinida/guardada o ruta a un archivo .txt de plantilla."
    )
    gen_group.add_argument(
        "--list-templates",
        action='store_true',
        help="Muestra las plantillas disponibles (predeterminadas y en /templates) y sale."
    )
    gen_group.add_argument(
        "--output-mode",
        type=str,
        choices=['tree', 'content', 'both'],
        default='both',
        help="Especifica qué incluir en el contexto: 'tree' (solo estructura), 'content' (solo contenidos), 'both' (ambos). Default: both"
    )
    gen_group.add_argument(
        "--output-note-path",
        type=str,
        metavar='RUTA_RELATIVA',
        # No lo hacemos required aquí, lo validaremos después si no hay acción de gestión
        help="(Requerido para generar prompt) Ruta relativa (desde la bóveda) donde se crearía/ubicaría la nueva nota."
    )
    gen_group.add_argument(
        "--output",
        type=Path,
        default=None,
        metavar='ARCHIVO_SALIDA',
        help="Archivo opcional donde guardar el prompt final generado. Si no se especifica, se imprime en la consola."
    )

    # --- Otros Argumentos ---
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.3.0' # Versión incrementada
    )

    args = parser.parse_args()

    # Post-procesar extensiones si se proporcionaron
    # Usar un set para eliminar duplicados y luego convertir a lista
    ext_set = set(args.ext) if args.ext else set(DEFAULT_EXTENSIONS)
    args.ext = [f".{e.lower().lstrip('.')}" for e in ext_set]

    return args


def main():
    """Función principal que orquesta el proceso CLI."""
    args = parse_arguments()
    config = config_handler.load_config()
    vaults = config_handler.get_vaults() # Obtener bóvedas válidas

    # --- Manejar acciones de gestión y salir ---
    # Comprobar si ALGUNA acción de gestión fue solicitada
    is_management_action = args.list_vaults or args.list_templates or args.add_vault or args.remove_vault

    if args.list_vaults:
        print("\nBóvedas Guardadas:")
        if vaults:
            # Ordenar por nombre para consistencia
            for name, path in sorted(vaults.items()):
                print(f"  - {name}: {path}")
        else:
            print("  (No hay bóvedas guardadas)")
        # No salimos aún si hay otras acciones de gestión

    if args.list_templates:
        print("\nPlantillas Disponibles:")
        available_templates = prompt_handler.get_available_templates()
        if available_templates:
            # Ordenar por nombre para consistencia
            for name in sorted(available_templates.keys()):
                 display_name = name
                 if name.startswith("Archivo: "):
                     try:
                        display_name = f"📄 {Path(available_templates[name]).name}"
                     except Exception:
                         display_name = f"📄 {name.split('Archivo: ')[1]} (?)"
                 else:
                      display_name = f"💡 {name}"
                 print(f"  - {display_name}")
        else:
            print("  (No se encontraron plantillas)")
        # No salimos aún si hay otras acciones de gestión

    if args.add_vault:
        name, path_str = args.add_vault
        config_handler.add_vault(name, path_str)
        # No salimos aún, podríamos querer listar después

    if args.remove_vault:
        config_handler.remove_vault(args.remove_vault)
        # No salimos aún

    # Salir SI Y SOLO SI se realizó una acción de gestión
    if is_management_action:
        print("\nAcción(es) de gestión completada(s).")
        sys.exit(0)

    # --- Lógica principal de generación de prompt (si no hubo acción de gestión) ---
    print("--- Iniciando Generación de Prompt ---")

    # 1. Determinar la bóveda a usar
    selected_vault_path: Optional[Path] = None
    selected_vault_name: Optional[str] = None

    if args.select_vault:
        if args.select_vault in vaults:
            selected_vault_name = args.select_vault
            selected_vault_path = Path(vaults[selected_vault_name]).resolve()
            # Doble chequeo por si la ruta se invalidó entre carga y uso
            if not selected_vault_path.is_dir():
                 print(f"Error: La ruta para la bóveda '{selected_vault_name}' ({selected_vault_path}) ya no es válida.", file=sys.stderr)
                 sys.exit(1)
            print(f"Usando bóveda seleccionada por argumento: '{selected_vault_name}'")
        else:
            print(f"Error: El nombre de bóveda '{args.select_vault}' no se encontró.", file=sys.stderr)
            if vaults:
                 print("Bóvedas disponibles:", ", ".join(sorted(vaults.keys())))
            else:
                 print("No hay bóvedas configuradas. Use --add-vault.")
            sys.exit(1)
    else:
        last_vault_info = config_handler.get_last_vault()
        if last_vault_info:
            selected_vault_name, selected_vault_path = last_vault_info
            print(f"Usando la última bóveda guardada: '{selected_vault_name}'")
        else:
            print("INFO: No se especificó bóveda (--select-vault) ni hay una última válida.")
            vault_choice = select_vault_interactive(vaults)
            if vault_choice:
                selected_vault_name, selected_vault_path = vault_choice
                print(f"Bóveda seleccionada interactivamente: '{selected_vault_name}'")
            else:
                print("No se seleccionó ninguna bóveda. Abortando.", file=sys.stderr)
                sys.exit(1)

    # 2. Validar argumentos restantes para generación
    if not selected_vault_path: # Seguridad
        print("Error fatal: No se pudo determinar una ruta de bóveda válida.", file=sys.stderr)
        sys.exit(1)
    if not args.output_note_path:
         print("Error: El argumento --output-note-path es requerido para generar el prompt.", file=sys.stderr)
         sys.exit(1)

    # 3. Validar y convertir output_note_path
    output_note_path_relative: Path
    try:
        temp_path = Path(args.output_note_path)
        if temp_path.is_absolute():
             # Intentar hacerla relativa
             output_note_path_relative = temp_path.relative_to(selected_vault_path)
             print(f"Advertencia: Ruta de nota destino absoluta convertida a relativa: {output_note_path_relative}", file=sys.stderr)
        else:
             # Asegurarse de que no empiece con / o \ si es relativa
             if args.output_note_path.startswith(('/', '\\')):
                  print(f"Advertencia: La ruta relativa '{args.output_note_path}' empieza con separador. Se usará tal cual.", file=sys.stderr)
             output_note_path_relative = temp_path
    except ValueError:
         print(f"Error: La ruta de nota destino absoluta '{args.output_note_path}' no parece estar dentro de la bóveda '{selected_vault_path}'.", file=sys.stderr)
         sys.exit(1)
    except Exception as e:
         print(f"Error procesando la ruta de nota destino '{args.output_note_path}': {e}", file=sys.stderr)
         sys.exit(1)

    # 4. Determinar la plantilla a usar
    template_string: Optional[str] = None
    if args.template:
        try:
            template_string = prompt_handler.load_template(args.template)
            print(f"Plantilla '{args.template}' cargada.")
        except ValueError as e:
            print(f"\nError: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("\nINFO: No se especificó plantilla (--template). Seleccione una:")
        available_templates = prompt_handler.get_available_templates()
        template_choice_name = select_template_interactive(available_templates)
        if template_choice_name:
            try:
                template_string = prompt_handler.load_template(template_choice_name)
                print(f"Plantilla seleccionada interactivamente: '{template_choice_name}'")
            except ValueError as e:
                 print(f"\nError al cargar plantilla seleccionada: {e}", file=sys.stderr)
                 sys.exit(1)
        else:
            print("No se seleccionó ninguna plantilla. Abortando.", file=sys.stderr)
            sys.exit(1)

    if not template_string: # Seguridad
         print("Error fatal: No se pudo cargar ninguna plantilla.", file=sys.stderr)
         sys.exit(1)

    # 5. Llamar a la lógica core
    try:
        print("\n--- Ejecutando Generación Core ---")
        final_prompt = generate_prompt_core(
            vault_path=selected_vault_path,
            target_paths=args.target,
            extensions=args.ext,
            output_mode=args.output_mode,
            output_note_path=output_note_path_relative,
            template_string=template_string
        )
    except Exception as e:
         print(f"\nError durante la generación del prompt: {e}", file=sys.stderr)
         import traceback
         traceback.print_exc()
         sys.exit(1)

    # 6. Mostrar o guardar resultado
    if args.output:
        try:
            output_file = args.output.resolve() # Resolver ruta absoluta
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(final_prompt, encoding='utf-8')
            print(f"\n--- Prompt Final Guardado ---")
            print(f"Ruta: {output_file}")
        except Exception as e:
            print(f"\nError: No se pudo guardar el prompt en {args.output}: {e}", file=sys.stderr)
            print("\n--- Prompt Final (salida a consola como fallback) ---")
            print(final_prompt)
            # No salir con error necesariamente, el prompt se generó
    else:
        print("\n--- Prompt Final (salida a consola) ---")
        print(final_prompt)

    # 7. Guardar la bóveda usada como la última
    if selected_vault_name:
        config_handler.set_last_vault(selected_vault_name)

    print("\n--- Proceso CLI Completado ---")

if __name__ == "__main__":
    main()