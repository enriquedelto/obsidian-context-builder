# prompt_handler.py
from pathlib import Path
# Asegúrate de que Tuple está aquí, junto con los otros tipos necesarios
from typing import Optional, Dict, List, Tuple
import sys
import os

# --- NUEVAS PLANTILLAS PREDETERMINADAS ---
# (El resto del código de plantillas sigue igual)
DEFAULT_TEMPLATES: Dict[str, str] = {}
# --- FIN PLANTILLAS ---

def get_template_folder_path() -> Path:
    """Obtiene la ruta a la carpeta 'templates'."""
    try:
        script_dir = Path(__file__).parent.resolve()
    except NameError:
        script_dir = Path.cwd()
    return script_dir / "templates"

def get_available_templates() -> Dict[str, str]:
    """Devuelve un diccionario con los nombres de las plantillas disponibles
       (SOLO las encontradas en la carpeta /templates)."""
    available = DEFAULT_TEMPLATES.copy() # Empezará vacío ahora
    templates_dir = get_template_folder_path()

    if templates_dir.is_dir():
        try:
            for item in templates_dir.iterdir():
                if item.is_file() and item.suffix.lower() == '.txt' and not item.name.startswith('.'):
                    # Usar un nombre descriptivo que incluya el origen
                    template_name = f"Archivo: {item.stem}" # Nombre sin extensión
                    available[template_name] = str(item.resolve())
        except OSError as e:
            print(f"Advertencia: No se pudo listar la carpeta de plantillas '{templates_dir}': {e}", file=sys.stderr)
    # else: # Opcional: Informar si la carpeta no existe
         # print(f"Info: Carpeta '{templates_dir.name}' no encontrada, no se cargarán plantillas personalizadas.", file=sys.stderr)

    return available # Devolverá solo los archivos encontrados

def load_template(template_name_or_path: str) -> str:
    """
    Carga la plantilla por nombre (SOLO de archivo en /templates) o ruta directa.

    Args:
        template_name_or_path: Nombre de la plantilla de archivo (con prefijo "Archivo: ")
                               o ruta completa a un archivo .txt.

    Returns:
        El contenido de la plantilla como string.

    Raises:
        ValueError: Si el nombre o la ruta no son válidos o el archivo no se puede leer.
    """
    available_templates = get_available_templates() # Ahora solo contiene archivos

    # 1. Comprobar si es un nombre conocido de la carpeta /templates
    if template_name_or_path in available_templates:
        file_path_str = available_templates[template_name_or_path]
        file_path = Path(file_path_str)
        source_type = "archivo (templates/)"
        print(f"Usando plantilla desde {source_type}: {file_path.name}", file=sys.stderr)
        try:
            return file_path.read_text(encoding='utf-8')
        except Exception as e:
            raise ValueError(f"Error al leer el archivo de plantilla {file_path}: {e}")

    # 2. Si no es un nombre conocido, intentar tratarlo como ruta directa
    else:
        template_path = Path(template_name_or_path)
        if template_path.is_file() and template_path.suffix.lower() == '.txt':
            print(f"Usando plantilla desde ruta directa: {template_path}", file=sys.stderr)
            try:
                return template_path.read_text(encoding='utf-8')
            except Exception as e:
                raise ValueError(f"Error al leer el archivo de plantilla {template_path}: {e}")
        else:
            # Error más informativo ahora que no hay predeterminadas
            available_names_list = sorted(available_templates.keys())
            err_msg = f"Plantilla no encontrada: '{template_name_or_path}'.\n"
            err_msg += f"No es un archivo en '{get_template_folder_path().name}/' ni una ruta válida a un archivo .txt.\n"
            if available_names_list:
                 # Mostrar nombres limpios
                 display_names = [f"📄 {Path(available_templates[name]).stem}" for name in available_names_list]
                 err_msg += f"Plantillas disponibles en /templates:\n - " + "\n - ".join(display_names)
            else:
                 err_msg += f"No hay plantillas .txt en la carpeta '{get_template_folder_path().name}'."
            raise ValueError(err_msg)

# inject_context e inject_context_multi permanecen igual
def inject_context(template_string: str, context_block: str, placeholder: str) -> str:
    """Reemplaza el placeholder en la plantilla con el bloque de contexto."""
    if placeholder not in template_string:
        print(f"Advertencia: El placeholder '{placeholder}' no se encontró en la plantilla.", file=sys.stderr)
        return template_string # No añadir contexto si no hay placeholder
    print(f"Inyectando contexto en el placeholder: '{placeholder}'", file=sys.stderr)
    return template_string.replace(placeholder, context_block)

def inject_context_multi(template: str, replacements: dict[str, Optional[str]]) -> str:
    """Inyecta múltiples valores en sus respectivos placeholders."""
    result = template
    placeholders_found = set()

    # Usar directamente los placeholders definidos globalmente si es necesario
    # desde donde se llame a esta función (por ejemplo, desde main.py)
    # o pasarlos como argumento si se prefiere desacoplar.
    # Asumiendo que DEFAULT_PLACEHOLDERS está disponible (importado en main)
    # y que `replacements` usa las llaves correctas (ej. "{contexto_extraido}")

    for placeholder_fmt, value_to_inject in replacements.items():
        # Usar los placeholders definidos en DEFAULT_PLACEHOLDERS como referencia
        # (Aunque los reemplazos ya vienen con el formato {placeholder})

        # Asegurarse de que el placeholder existe antes de reemplazar
        if placeholder_fmt in result:
             replacement_value = value_to_inject if value_to_inject is not None else ""
             result = result.replace(placeholder_fmt, replacement_value)
             placeholders_found.add(placeholder_fmt)

    if not placeholders_found and replacements and any(replacements.values()):
         print("Advertencia: No se reemplazó ningún placeholder conocido en la plantilla. ¿Es correcta la plantilla o los placeholders?", file=sys.stderr)

    return result

# --- FUNCIONES INTERACTIVAS ---
# Si la función `select_vault_interactive` estaba aquí, necesita el import
# Es MÁS probable que esta función deba estar en main.py o gui_streamlit.py
# ya que `prompt_handler` no debería necesitar lógica interactiva generalmente.
# Revisando el traceback, parece que SÍ la pusiste aquí. Añadimos el import.

def select_vault_interactive(vaults: Dict[str, str]) -> Optional[Tuple[str, Path]]:
    """Permite al usuario seleccionar una bóveda de una lista numerada."""
    if not vaults:
        print("No hay bóvedas guardadas. Use --add-vault para añadir una.")
        return None

    print("\nBóvedas guardadas:")
    vault_list = list(vaults.items())
    for i, (name, path) in enumerate(vault_list):
        print(f"  {i+1}. {name} ({path})")

    while True:
        try:
            choice = input(f"Seleccione el número de la bóveda (1-{len(vault_list)}) o 'q' para salir: ")
            if choice.lower() == 'q':
                return None
            index = int(choice) - 1
            if 0 <= index < len(vault_list):
                name, path_str = vault_list[index]
                path_obj = Path(path_str)
                if path_obj.is_dir():
                    return name, path_obj
                else:
                    print(f"Error: La ruta para '{name}' ({path_str}) no es válida. Inténtelo de nuevo.")
            else:
                print("Selección inválida.")
        except ValueError:
            print("Entrada inválida. Por favor, introduzca un número o 'q'.")
        except KeyboardInterrupt:
            print("\nSelección cancelada.")
            return None

def main():
    """Función principal que orquesta el proceso CLI."""
    args = parse_arguments()
    config = config_handler.load_config() # Cargar config al inicio
    vaults = config.get("vaults", {})

    # --- Manejar acciones de gestión y salir ---
    exit_after_action = False
    if args.list_vaults:
        print("\nBóvedas Guardadas:")
        if vaults:
            for name, path in vaults.items():
                print(f"  - {name}: {path}")
        else:
            print("  (No hay bóvedas guardadas)")
        exit_after_action = True

    if args.list_templates:
        print("\nPlantillas Disponibles:")
        available_templates = prompt_handler.get_available_templates()
        if available_templates:
            for name in available_templates.keys():
                 # Mostrar de forma más limpia (sin ruta para archivos de /templates)
                 display_name = name
                 if name.startswith("Archivo: "):
                      display_name = f"Archivo: {Path(name.split('Archivo: ')[1]).name}"
                 print(f"  - {display_name}")
        else:
            print("  (No se encontraron plantillas)")
        exit_after_action = True

    if args.add_vault:
        name, path = args.add_vault
        config_handler.add_vault(name, path)
        exit_after_action = True # Salir después de añadir

    if args.remove_vault:
        config_handler.remove_vault(args.remove_vault)
        exit_after_action = True # Salir después de eliminar

    if exit_after_action:
        sys.exit(0) # Salir limpiamente

    # --- Lógica principal de generación de prompt ---

    # Determinar la bóveda a usar
    selected_vault_path: Optional[Path] = None
    selected_vault_name: Optional[str] = None

    if args.select_vault:
        if args.select_vault in vaults:
            path_str = vaults[args.select_vault]
            path_obj = Path(path_str)
            if path_obj.is_dir():
                selected_vault_path = path_obj
                selected_vault_name = args.select_vault
                print(f"Usando bóveda seleccionada por argumento: '{selected_vault_name}' ({selected_vault_path})")
            else:
                print(f"Error: La ruta para la bóveda '{args.select_vault}' ({path_str}) no es válida.", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Error: El nombre de bóveda '{args.select_vault}' no se encontró en la configuración.", file=sys.stderr)
            print("Bóvedas disponibles:")
            for name in vaults.keys(): print(f" - {name}")
            sys.exit(1)
    else:
        # Intentar usar la última bóveda guardada
        last_vault_info = config_handler.get_last_vault()
        if last_vault_info:
            selected_vault_name, selected_vault_path = last_vault_info
            print(f"Usando la última bóveda guardada: '{selected_vault_name}' ({selected_vault_path})")
        else:
            # Si no hay última válida, pedir selección interactiva
            print("No se especificó bóveda y no hay una última válida guardada.")
            vault_choice = select_vault_interactive(vaults)
            if vault_choice:
                selected_vault_name, selected_vault_path = vault_choice
                print(f"Bóveda seleccionada interactivamente: '{selected_vault_name}'")
            else:
                print("No se seleccionó ninguna bóveda. Saliendo.")
                sys.exit(1)

    # Validar argumentos necesarios para generación
    if not selected_vault_path: # Doble chequeo por si acaso
        print("Error fatal: No se pudo determinar una ruta de bóveda válida.", file=sys.stderr)
        sys.exit(1)
    if not args.output_note_path:
         print("Error: El argumento --output-note-path es requerido para generar un prompt.", file=sys.stderr)
         sys.exit(1)

    # Validar y convertir output_note_path a relativa
    output_note_path_relative = Path(args.output_note_path)
    if output_note_path_relative.is_absolute():
         print("Advertencia: --output-note-path debería ser una ruta relativa a la bóveda. Intentando convertir...", file=sys.stderr)
         try:
            output_note_path_relative = output_note_path_relative.relative_to(selected_vault_path)
         except ValueError:
             print(f"Error: No se pudo hacer relativa la ruta {args.output_note_path} a la bóveda {selected_vault_path}.", file=sys.stderr)
             sys.exit(1)

    # Determinar la plantilla a usar
    template_string: Optional[str] = None
    if args.template:
        try:
            template_string = prompt_handler.load_template(args.template)
        except ValueError as e:
            print(f"\nError: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Si no se especificó, pedir selección interactiva
        print("\nNo se especificó plantilla.")
        available_templates = prompt_handler.get_available_templates()
        template_choice_name = select_template_interactive(available_templates)
        if template_choice_name:
            try:
                template_string = prompt_handler.load_template(template_choice_name)
            except ValueError as e:
                 print(f"\nError al cargar plantilla seleccionada: {e}", file=sys.stderr)
                 sys.exit(1)
        else:
            print("No se seleccionó ninguna plantilla. Saliendo.")
            sys.exit(1)

    if not template_string: # Doble chequeo
         print("Error fatal: No se pudo cargar ninguna plantilla.", file=sys.stderr)
         sys.exit(1)

    # --- LLAMAR A LA LÓGICA CORE ---
    try:
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
         traceback.print_exc() # Imprimir traceback para depuración
         sys.exit(1)
    # --- FIN LLAMADA CORE ---

    # Mostrar o guardar resultado
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(final_prompt)
            print(f"\n--- Prompt Final Guardado ---")
            print(f"El prompt completo ha sido guardado en: {args.output.resolve()}")
        except IOError as e:
            print(f"\nError: No se pudo guardar el prompt en el archivo {args.output}: {e}", file=sys.stderr)
            print("\n--- Prompt Final (salida a consola como fallback) ---")
            print(final_prompt)
            sys.exit(1)
        except Exception as e:
             print(f"\nError inesperado al guardar el archivo {args.output}: {e}", file=sys.stderr)
             sys.exit(1)
    else:
        print("\n--- Prompt Final (salida a consola) ---")
        print(final_prompt)

    # Guardar la bóveda usada como la última
    if selected_vault_name:
        config_handler.set_last_vault(selected_vault_name)

    print("\n--- Proceso CLI Completado ---")

if __name__ == "__main__":
    main()