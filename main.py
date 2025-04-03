# main.py
import argparse
from pathlib import Path
import sys
from typing import List, Optional, Dict, Tuple
# import os # Eliminado, no parece usarse

# Importar módulos propios necesarios para CLI
import prompt_handler # Para selección/carga de plantillas
import config_handler # Para gestión de bóvedas
import core           # <<< NUEVO: Importar la lógica central

# --- FUNCIONES INTERACTIVAS (Permanecen aquí) ---
def select_vault_interactive(vaults: Dict[str, str]) -> Optional[Tuple[str, Path]]:
    """Permite al usuario seleccionar una bóveda de una lista numerada."""
    if not vaults: print("No hay bóvedas guardadas. Use --add-vault.", file=sys.stderr); return None
    print("\nBóvedas guardadas:"); vault_list = list(vaults.items())
    for i, (name, path) in enumerate(vault_list): print(f"  {i+1}. {name} ({path})")
    while True:
        try:
            choice_str = input(f"Seleccione bóveda (1-{len(vault_list)}) o 'q': ").strip()
            if choice_str.lower() == 'q': return None
            if not choice_str.isdigit(): print("Número inválido."); continue
            index = int(choice_str) - 1
            if 0 <= index < len(vault_list):
                name, path_str = vault_list[index]; path_obj = Path(path_str)
                if path_obj.is_dir(): return name, path_obj
                else: print(f"Ruta inválida para '{name}'.")
            else: print("Selección fuera de rango.")
        except (ValueError, EOFError, KeyboardInterrupt): print("\nSelección cancelada."); return None

def select_template_interactive(templates: Dict[str, str]) -> Optional[str]:
    """Permite al usuario seleccionar una plantilla de una lista numerada."""
    if not templates: print("No hay plantillas en ./templates.", file=sys.stderr); return None
    print("\nPlantillas disponibles (./templates):"); template_list = list(templates.keys())
    for i, name in enumerate(template_list):
         display_name = name
         if name.startswith("Archivo: "):
             try: display_name = f"📄 {Path(templates[name]).stem}"
             except: display_name = f"📄 {name.split('Archivo: ')[1]} (?)"
         print(f"  {i+1}. {display_name}")
    while True:
        try:
            choice_str = input(f"Seleccione plantilla (1-{len(template_list)}) o 'q': ").strip()
            if choice_str.lower() == 'q': return None
            if not choice_str.isdigit(): print("Número inválido."); continue
            index = int(choice_str) - 1
            if 0 <= index < len(template_list): return template_list[index]
            else: print("Selección fuera de rango.")
        except (ValueError, EOFError, KeyboardInterrupt): print("\nSelección cancelada."); return None

# --- FIN FUNCIONES INTERACTIVAS ---

def parse_arguments() -> argparse.Namespace:
    """Define y parsea los argumentos de la línea de comandos."""
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <<<    Se usa core.DEFAULT_EXTENSIONS y se actualiza la versión y ayuda    >>>
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    parser = argparse.ArgumentParser(
        description="Generador de Contexto Obsidian para Prompts LLM.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Ejemplos:
  # Usar última bóveda guardada, seleccionar plantilla interactiva
  python main.py --target "Asignaturas/Cálculo" --output-note-path "Asignaturas/Cálculo/Resumen.md"

  # Usar una bóveda específica guardada por nombre y plantilla
  python main.py --select-vault "Trabajo" --template "Archivo:ResumenConceptosClave" --target "ProyectosActivos" --output-note-path "ResumenProyectos.md"

  # Usar una ruta de bóveda directa SIN guardarla
  python main.py --vault-path "/ruta/temporal/boveda" --template "Archivo:GenerarNota" --target "Conceptos" --output-note-path "Conceptos/NuevaIdea.md"

  # Excluir extensiones
  python main.py --target "NotasVarias" --exclude-ext .pdf --exclude-ext .png

  # Sin ruta de nota (para plantillas que no la necesiten)
  python main.py --template "Archivo:AnalizarContenido" --target "CarpetaAnalisis" --output-mode tree

  # Gestión
  python main.py --add-vault "Principal" "/ruta/a/boveda"
  python main.py --list-vaults --list-templates
"""
    )

    vault_selection_group = parser.add_mutually_exclusive_group()
    vault_selection_group.add_argument( "--select-vault", type=str, metavar='NOMBRE', help="Nombre de la bóveda guardada a usar." )
    vault_selection_group.add_argument( "--vault-path", type=Path, metavar='RUTA_DIRECTORIO', help="Ruta directa a una bóveda (no se guarda)." )

    vault_management_group = parser.add_argument_group('Gestión de Bóvedas (ejecutar y salir)')
    vault_management_group.add_argument( "--add-vault", nargs=2, metavar=('NOMBRE', 'RUTA'), help="Añade o actualiza una bóveda guardada." )
    vault_management_group.add_argument( "--remove-vault", type=str, metavar='NOMBRE', help="Elimina una bóveda guardada." )
    vault_management_group.add_argument( "--list-vaults", action='store_true', help="Muestra bóvedas guardadas y sale." )

    gen_group = parser.add_argument_group('Generación de Prompt')
    gen_group.add_argument( "--target", type=str, action='append', default=[], metavar='RUTA_RELATIVA', help="Ruta relativa (a bóveda) a incluir. Repetir. Vacío = toda la bóveda." )
    gen_group.add_argument( "--ext", type=str, action='append', default=[], metavar='EXTENSION', help=f"Extensión a INCLUIR (ej: .md). Default: {core.DEFAULT_EXTENSIONS}" ) # Usa core.
    gen_group.add_argument( "--exclude-ext", type=str, action='append', default=[], metavar='EXTENSION', help="Extensión a EXCLUIR (ej: .log)." )
    gen_group.add_argument( "--template", type=str, metavar='NOMBRE_O_RUTA', help="Nombre plantilla ('Archivo:Nombre') o ruta a .txt." )
    gen_group.add_argument( "--list-templates", action='store_true', help="Muestra plantillas disponibles y sale." )
    gen_group.add_argument( "--output-mode", type=str, choices=['tree', 'content', 'both'], default='both', help="Qué contexto incluir. Default: both" )
    gen_group.add_argument( "--output-note-path", type=str, metavar='RUTA_RELATIVA', help="Ruta relativa (en bóveda) para nota objetivo. Opcional, pero necesaria para placeholders {ruta_destino} y {etiqueta_jerarquica_N}." )
    gen_group.add_argument( "--output", type=Path, default=None, metavar='ARCHIVO_SALIDA', help="Archivo opcional para guardar prompt." )

    parser.add_argument( '--version', action='version', version='%(prog)s 1.0.0' ) # Versión actualizada

    args = parser.parse_args()

    # Post-procesar extensiones incluidas y excluidas
    args.ext = [f".{e.lower().lstrip('.')}" for e in (set(args.ext) if args.ext else set(core.DEFAULT_EXTENSIONS)) if e.strip()]
    args.exclude_ext = [f".{e.lower().lstrip('.')}" for e in set(args.exclude_ext) if e.strip()]

    return args

def main():
    """Función principal que orquesta el proceso CLI."""
    args = parse_arguments()
    vaults = config_handler.get_vaults()

    # --- Manejar acciones de gestión y salir ---
    is_management_action = args.list_vaults or args.list_templates or args.add_vault or args.remove_vault
    if is_management_action:
        if args.list_vaults:
            print("\nBóvedas Guardadas:")
            if vaults:
                for name, path in sorted(vaults.items()): print(f"  - {name}: {path}")
            else: print("  (No hay bóvedas guardadas)")
        if args.list_templates:
            print("\nPlantillas Disponibles (./templates):")
            available_templates = prompt_handler.get_available_templates()
            if available_templates:
                for name in sorted(available_templates.keys()):
                    display_name = name
                    if name.startswith("Archivo: "):
                        try: display_name = f"📄 {Path(available_templates[name]).stem}"
                        except: display_name = f"📄 {name.split('Archivo: ')[1]} (?)"
                    print(f"  - {display_name}")
            else: print("  (No se encontraron plantillas .txt)")
        if args.add_vault: config_handler.add_vault(args.add_vault[0], args.add_vault[1])
        if args.remove_vault: config_handler.remove_vault(args.remove_vault)
        print("\nAcción(es) de gestión completada(s).")
        sys.exit(0)

    # --- Lógica principal de generación de prompt ---
    print("--- Iniciando Generación de Prompt ---")

    # 1. Determinar la bóveda a usar
    selected_vault_path: Optional[Path] = None; selected_vault_name: Optional[str] = None; used_manual_path = False
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <<<           Lógica de selección de bóveda sin cambios aquí                >>>
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    if args.vault_path:
        try:
            manual_path = args.vault_path.resolve()
            if not manual_path.is_dir(): print(f"Error: Ruta manual inválida: {args.vault_path}", file=sys.stderr); sys.exit(1)
            selected_vault_path = manual_path; selected_vault_name = f"(Ruta Manual: {args.vault_path.name})"; used_manual_path = True
            print(f"Usando bóveda de ruta manual: '{selected_vault_path}'")
        except Exception as e: print(f"Error procesando ruta manual '{args.vault_path}': {e}", file=sys.stderr); sys.exit(1)
    elif args.select_vault:
        if args.select_vault in vaults:
            selected_vault_name = args.select_vault
            try:
                selected_vault_path = Path(vaults[selected_vault_name]).resolve()
                if not selected_vault_path.is_dir(): print(f"Error: Ruta guardada para '{selected_vault_name}' inválida.", file=sys.stderr); sys.exit(1)
                print(f"Usando bóveda seleccionada: '{selected_vault_name}'")
            except Exception as e: print(f"Error procesando ruta para '{selected_vault_name}': {e}", file=sys.stderr); sys.exit(1)
        else:
            print(f"Error: Bóveda '{args.select_vault}' no encontrada.", file=sys.stderr)
            if vaults: print("Disponibles:", ", ".join(sorted(vaults.keys())))
            else: print("No hay bóvedas guardadas. Use --add-vault.")
            sys.exit(1)
    else:
        last_vault_info = config_handler.get_last_vault()
        if last_vault_info:
            selected_vault_name, selected_vault_path = last_vault_info
            print(f"Usando última bóveda guardada: '{selected_vault_name}'")
        else:
            print("INFO: No se especificó bóveda. Seleccione una:")
            vault_choice = select_vault_interactive(vaults)
            if vault_choice: selected_vault_name, selected_vault_path = vault_choice; print(f"Bóveda seleccionada: '{selected_vault_name}'")
            else: print("No se seleccionó bóveda. Abortando.", file=sys.stderr); sys.exit(1)

    # 2. Validar argumentos restantes para generación (output_note_path es opcional)
    if not selected_vault_path: print("Error fatal: No se pudo determinar ruta de bóveda válida.", file=sys.stderr); sys.exit(1)

    # 3. Validar y convertir output_note_path SI SE PROPORCIONÓ
    output_note_path_relative: Optional[Path] = None
    if args.output_note_path:
        try:
            temp_path = Path(args.output_note_path)
            if temp_path.is_absolute():
                 output_note_path_relative = temp_path.relative_to(selected_vault_path.resolve())
            else:
                 output_note_path_relative = Path(args.output_note_path.lstrip('/\\'))
        except ValueError: print(f"Error: Ruta nota destino absoluta '{args.output_note_path}' no en bóveda.", file=sys.stderr); sys.exit(1)
        except Exception as e: print(f"Error procesando ruta nota destino: {e}", file=sys.stderr); sys.exit(1)

    # 4. Determinar la plantilla a usar
    template_string: Optional[str] = None
    if args.template:
        try: template_string = prompt_handler.load_template(args.template)
        except ValueError as e: print(f"\nError: {e}", file=sys.stderr); sys.exit(1)
    else:
        print("\nINFO: No se especificó plantilla (--template). Seleccione una:")
        available_templates = prompt_handler.get_available_templates()
        template_choice_name = select_template_interactive(available_templates)
        if template_choice_name:
            try: template_string = prompt_handler.load_template(template_choice_name)
            except ValueError as e: print(f"\nError cargando plantilla: {e}", file=sys.stderr); sys.exit(1)
        else: print("No se seleccionó plantilla. Abortando.", file=sys.stderr); sys.exit(1)
    if not template_string: print("Error fatal: No se pudo cargar plantilla.", file=sys.stderr); sys.exit(1)

    # 5. Llamar a la lógica core
    try:
        print("\n--- Ejecutando Generación Core ---")
        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # <<<                LLAMADA A LA FUNCIÓN EN core.py                        >>>
        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        final_prompt = core.generate_prompt_core(
            vault_path=selected_vault_path,
            target_paths=args.target,
            extensions=args.ext,
            output_mode=args.output_mode,
            output_note_path=output_note_path_relative, # Puede ser None
            template_string=template_string,
            excluded_extensions=args.exclude_ext # Pasar exclusiones (necesita implementación en file_handler)
        )
    except Exception as e:
         print(f"\nError durante la generación: {e}", file=sys.stderr)
         import traceback; traceback.print_exc(); sys.exit(1)

    # 6. Mostrar o guardar resultado
    if args.output:
        try:
            output_file = args.output.resolve()
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(final_prompt, encoding='utf-8')
            print(f"\n--- Prompt Final Guardado ---"); print(f"Ruta: {output_file}")
        except Exception as e:
            print(f"\nError guardando prompt en {args.output}: {e}", file=sys.stderr)
            print("\n--- Prompt Final (salida a consola como fallback) ---"); print(final_prompt)
    else:
        print("\n--- Prompt Final (salida a consola) ---"); print(final_prompt)

    # 7. Guardar la bóveda usada como la última (si no fue manual)
    if selected_vault_name and not used_manual_path:
        config_handler.set_last_vault(selected_vault_name)
    elif used_manual_path:
        print("INFO: No se actualiza última bóveda usada (--vault-path).", file=sys.stderr)

    print("\n--- Proceso CLI Completado ---")

if __name__ == "__main__":
    main()