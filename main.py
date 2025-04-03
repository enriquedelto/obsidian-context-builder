# main.py
import argparse
from pathlib import Path
import sys
from typing import List, Optional, Dict, Tuple

# ... (otros imports sin cambios: file_handler, tree_generator, etc.)
import prompt_handler
import config_handler
import core

# ... (funciones select_vault_interactive, select_template_interactive sin cambios) ...

def parse_arguments() -> argparse.Namespace:
    """Define y parsea los argumentos de la línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Generador de Contexto Obsidian para Prompts LLM.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Ejemplos:
  # Usar última bóveda guardada, seleccionar plantilla interactivamente
  python main.py --target "Asignaturas/Cálculo" --output-note-path "Asignaturas/Cálculo/Resumen.md"

  # Usar una bóveda específica guardada por nombre
  python main.py --select-vault "Trabajo" --template "Archivo: ResumenConceptosClave" --target "ProyectosActivos" --output-note-path "ResumenProyectos.md"

  # Usar una ruta de bóveda directamente SIN guardarla
  python main.py --vault-path "/ruta/temporal/a/mi/boveda" --template "Archivo: GenerarNota" --target "Conceptos" --output-note-path "Conceptos/NuevaIdea.md"

  # Añadir/Listar bóvedas y plantillas
  python main.py --add-vault "Principal" "/ruta/completa/a/mi/boveda"
  python main.py --list-vaults --list-templates
"""
    )

    # --- Grupo Mutuamente Excluyente para Selección de Bóveda ---
    vault_selection_group = parser.add_mutually_exclusive_group()
    vault_selection_group.add_argument(
        "--select-vault",
        type=str,
        metavar='NOMBRE',
        help="Nombre de la bóveda guardada a usar."
    )
    vault_selection_group.add_argument(
        "--vault-path",
        type=Path, # Usar Path directamente para validación básica
        metavar='RUTA_DIRECTORIO',
        help="Ruta directa a una bóveda Obsidian a usar para esta ejecución (no se guarda)."
    )

    # --- Argumentos de Gestión de Bóvedas (fuera del grupo exclusivo) ---
    vault_management_group = parser.add_argument_group('Gestión de Bóvedas (ejecutar y salir)')
    vault_management_group.add_argument(
        "--add-vault", nargs=2, metavar=('NOMBRE', 'RUTA'),
        help="Añade o actualiza una bóveda guardada."
    )
    vault_management_group.add_argument(
        "--remove-vault", type=str, metavar='NOMBRE',
        help="Elimina una bóveda guardada."
    )
    vault_management_group.add_argument(
        "--list-vaults", action='store_true',
        help="Muestra las bóvedas guardadas y sale."
    )

    # --- Argumentos de Generación de Prompt ---
    gen_group = parser.add_argument_group('Generación de Prompt')
    gen_group.add_argument(
        "--target", type=str, action='append', default=[], metavar='RUTA_RELATIVA',
        help="Ruta relativa (a la bóveda) para incluir. Repetir para múltiples. Vacío = toda la bóveda."
    )
    gen_group.add_argument(
        "--ext", type=str, action='append', default=[], metavar='EXTENSION',
        help=f"Extensión a incluir (ej: .md). Repetir para múltiples. Default: {core.DEFAULT_EXTENSIONS}"
    )
    gen_group.add_argument(
        "--template", type=str, metavar='NOMBRE_O_RUTA',
        help="Nombre de plantilla de /templates (ej: 'Archivo: GenerarNota') o ruta a .txt."
    )
    gen_group.add_argument(
        "--list-templates", action='store_true',
        help="Muestra las plantillas disponibles y sale."
    )
    gen_group.add_argument(
        "--output-mode", type=str, choices=['tree', 'content', 'both'], default='both',
        help="Qué contexto incluir: 'tree', 'content', 'both'. Default: both"
    )
    gen_group.add_argument(
        "--output-note-path", type=str, metavar='RUTA_RELATIVA',
        help="(Requerido para generar) Ruta relativa (en la bóveda) para la nota objetivo."
    )
    gen_group.add_argument(
        "--output", type=Path, default=None, metavar='ARCHIVO_SALIDA',
        help="Archivo opcional para guardar el prompt. Si no, imprime en consola."
    )

    # --- Otros Argumentos ---
    parser.add_argument(
        '--version', action='version',
        version='%(prog)s 0.7.0' # Incrementar versión
    )

    args = parser.parse_args()

    # Post-procesar extensiones
    ext_set = set(args.ext) if args.ext else set(core.DEFAULT_EXTENSIONS)
    args.ext = [f".{e.lower().lstrip('.')}" for e in ext_set]

    return args

def main():
    """Función principal que orquesta el proceso CLI."""
    args = parse_arguments()
    vaults = config_handler.get_vaults() # Obtener bóvedas válidas al inicio

    # --- Manejar acciones de gestión y salir ---
    is_management_action = args.list_vaults or args.list_templates or args.add_vault or args.remove_vault

    # ... (Lógica de gestión --list-vaults, --list-templates, --add-vault, --remove-vault sin cambios)...

    if is_management_action:
        print("\nAcción(es) de gestión completada(s).")
        sys.exit(0)

    # --- Lógica principal de generación de prompt ---
    print("--- Iniciando Generación de Prompt ---")

    # 1. Determinar la bóveda a usar
    selected_vault_path: Optional[Path] = None
    selected_vault_name: Optional[str] = None
    used_manual_path = False # Flag para saber si se usó ruta manual

    # Prioridad 1: Ruta manual directa
    if args.vault_path:
        try:
            manual_path = args.vault_path.resolve()
            if not manual_path.is_dir():
                print(f"Error: La ruta manual proporcionada (--vault-path) no es un directorio válido: {args.vault_path}", file=sys.stderr)
                sys.exit(1)
            selected_vault_path = manual_path
            selected_vault_name = f"(Ruta Manual: {args.vault_path.name})" # Nombre descriptivo temporal
            used_manual_path = True
            print(f"Usando bóveda de ruta manual directa: '{selected_vault_path}'")
        except Exception as e:
            print(f"Error al procesar la ruta manual (--vault-path) '{args.vault_path}': {e}", file=sys.stderr)
            sys.exit(1)

    # Prioridad 2: Selección por nombre guardado
    elif args.select_vault:
        if args.select_vault in vaults:
            selected_vault_name = args.select_vault
            try:
                selected_vault_path = Path(vaults[selected_vault_name]).resolve()
                if not selected_vault_path.is_dir():
                    print(f"Error: La ruta guardada para '{selected_vault_name}' ({selected_vault_path}) ya no es un directorio válido.", file=sys.stderr)
                    sys.exit(1)
                print(f"Usando bóveda seleccionada por argumento: '{selected_vault_name}'")
            except Exception as e:
                print(f"Error al procesar la ruta para '{selected_vault_name}': {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Error: El nombre de bóveda '{args.select_vault}' no se encontró.", file=sys.stderr)
            if vaults: print("Bóvedas disponibles:", ", ".join(sorted(vaults.keys())))
            else: print("No hay bóvedas configuradas. Use --add-vault.")
            sys.exit(1)

    # Prioridad 3: Última bóveda guardada (válida)
    else:
        last_vault_info = config_handler.get_last_vault()
        if last_vault_info:
            selected_vault_name, selected_vault_path = last_vault_info
            print(f"Usando la última bóveda guardada: '{selected_vault_name}'")
        else:
            # Prioridad 4: Selección interactiva
            print("INFO: No se especificó bóveda (--select-vault/--vault-path) ni hay una última válida.")
            vault_choice = select_vault_interactive(vaults)
            if vault_choice:
                selected_vault_name, selected_vault_path = vault_choice
                print(f"Bóveda seleccionada interactivamente: '{selected_vault_name}'")
            else:
                print("No se seleccionó ninguna bóveda. Abortando.", file=sys.stderr)
                sys.exit(1)

    # 2. Validar argumentos restantes para generación
    # ... (validación de output_note_path sin cambios) ...
    if not selected_vault_path: # Seguridad
        print("Error fatal: No se pudo determinar una ruta de bóveda válida.", file=sys.stderr)
        sys.exit(1)
    if not args.output_note_path:
         print("Error: El argumento --output-note-path es requerido para generar el prompt.", file=sys.stderr)
         sys.exit(1)

    # 3. Validar y convertir output_note_path
    # ... (lógica de conversión a relativo sin cambios) ...
    output_note_path_relative: Path
    try:
        temp_path = Path(args.output_note_path)
        if temp_path.is_absolute():
             output_note_path_relative = temp_path.relative_to(selected_vault_path.resolve())
             print(f"Advertencia: Ruta de nota destino absoluta convertida a relativa: {output_note_path_relative}", file=sys.stderr)
        else:
             clean_relative_str = args.output_note_path.lstrip('/\\')
             if clean_relative_str != args.output_note_path:
                  print(f"Advertencia: Limpiando separador inicial de la ruta relativa '{args.output_note_path}' a '{clean_relative_str}'", file=sys.stderr)
             output_note_path_relative = Path(clean_relative_str)
    except ValueError:
         print(f"Error: La ruta de nota destino absoluta '{args.output_note_path}' no parece estar dentro de la bóveda '{selected_vault_path}'.", file=sys.stderr)
         sys.exit(1)
    except Exception as e:
         print(f"Error procesando la ruta de nota destino '{args.output_note_path}': {e}", file=sys.stderr)
         sys.exit(1)


    # 4. Determinar la plantilla a usar
    # ... (lógica de selección de plantilla, interactiva o por argumento, sin cambios) ...
    template_string: Optional[str] = None
    if args.template:
        try:
            template_string = prompt_handler.load_template(args.template)
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
    # ... (llamada a core.generate_prompt_core sin cambios) ...
    try:
        print("\n--- Ejecutando Generación Core ---")
        final_prompt = core.generate_prompt_core(
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
    # ... (lógica de guardar o imprimir sin cambios) ...
    if args.output:
        try:
            output_file = args.output.resolve()
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(final_prompt, encoding='utf-8')
            print(f"\n--- Prompt Final Guardado ---")
            print(f"Ruta: {output_file}")
        except Exception as e:
            print(f"\nError: No se pudo guardar el prompt en {args.output}: {e}", file=sys.stderr)
            print("\n--- Prompt Final (salida a consola como fallback) ---")
            print(final_prompt)
    else:
        print("\n--- Prompt Final (salida a consola) ---")
        print(final_prompt)


    # 7. Guardar la bóveda usada como la última (¡SOLO SI NO SE USÓ RUTA MANUAL!)
    if selected_vault_name and not used_manual_path:
        config_handler.set_last_vault(selected_vault_name)
    elif used_manual_path:
        print("INFO: No se actualiza la última bóveda usada (se usó --vault-path).", file=sys.stderr)


    print("\n--- Proceso CLI Completado ---")

if __name__ == "__main__":
    main()