import argparse
from pathlib import Path
import sys
from typing import List, Optional, Dict # Añadir Dict

# Importar funciones de nuestros módulos
import file_handler
import tree_generator
import formatter
import prompt_handler # Asegúrate que prompt_handler también tenga DEFAULT_PLACEHOLDERS o pásalo

# Definir los placeholders por defecto (puede vivir aquí o en prompt_handler)
DEFAULT_PLACEHOLDERS: Dict[str, str] = {
    "contexto_extraido": "{contexto_extraido}",
    "ruta_destino": "{ruta_destino}",
    "etiqueta_jerarquica_1": "{etiqueta_jerarquica_1}",
    "etiqueta_jerarquica_2": "{etiqueta_jerarquica_2}",
    "etiqueta_jerarquica_3": "{etiqueta_jerarquica_3}"
}
DEFAULT_EXTENSIONS = ['.md']


def generate_hierarchical_tags(relative_note_path: Path) -> List[str]:
    """Extrae etiquetas jerárquicas de una ruta relativa a la bóveda."""
    # (Misma función que antes)
    tags = []
    current_parts = []
    for part in relative_note_path.parent.parts:
        if not part or part == '.':
            continue
        cleaned_part = part.replace(" ", "_").replace("-", "_")
        current_parts.append(cleaned_part)
        tags.append("/".join(current_parts))
    return list(reversed(tags))

# --- ¡NUEVA FUNCIÓN REFACTORIZADA! ---
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
    Toma parámetros y devuelve el string del prompt procesado.
    """
    print("--- Iniciando Lógica Core ---")
    print(f"Core - Bóveda: {vault_path}")
    print(f"Core - Targets: {target_paths}")
    print(f"Core - Extensiones: {extensions}")
    print(f"Core - Modo Contexto: {output_mode}")
    print(f"Core - Ruta Nota Destino: {output_note_path}")

    # 1. Encontrar archivos relevantes
    relevant_files: List[Path] = file_handler.find_relevant_files(
        vault_path, target_paths, extensions
    )
    if not relevant_files and output_mode != 'tree':
        print("\nCore - Advertencia: No se encontraron archivos relevantes.")

    # 2. Generar string del árbol (si aplica)
    tree_string = ""
    if output_mode in ['tree', 'both']:
        print("\nCore - Generando estructura de árbol...")
        tree_string = tree_generator.generate_tree_string(relevant_files, vault_path)
        if not tree_string.strip() or tree_string.startswith(" (No se encontraron"):
             print("Core - Advertencia: No se generó estructura de árbol.")

    # 3. Formatear contenido (si aplica)
    formatted_contents: List[str] = []
    if output_mode in ['content', 'both']:
        if relevant_files:
             print("\nCore - Formateando contenido de archivos...")
             for file_path in relevant_files:
                 formatted = formatter.format_file_content(file_path, vault_path)
                 if formatted:
                     formatted_contents.append(formatted)
             if not formatted_contents:
                  print("Core - Advertencia: No se pudo formatear contenido.")
        else:
             print("\nCore - No hay archivos relevantes para formatear contenido.")

    # 4. Construir bloque de contexto
    print(f"\nCore - Construyendo bloque de contexto (Modo: {output_mode})...")
    context_block = ""
    if output_mode == 'tree':
        context_block = tree_string
    elif output_mode == 'content':
        context_block = "".join(formatted_contents).strip()
    elif output_mode == 'both':
        if tree_string.strip() and formatted_contents:
            context_block = tree_string.strip() + "\n" + "".join(formatted_contents).strip()
        elif tree_string.strip():
             context_block = tree_string.strip()
        elif formatted_contents:
             context_block = "".join(formatted_contents).strip()
        else:
             context_block = "(No se generó ni árbol ni contenido para el contexto)"
    print(f"Core - Contexto generado (primeros 100 chars): {context_block[:100]}...")


    # 5. Preparar valores para reemplazo
    ruta_destino_relativa_str = output_note_path.as_posix()
    hierarchical_tags = generate_hierarchical_tags(output_note_path)

    replacements: Dict[str, str] = {
        DEFAULT_PLACEHOLDERS["contexto_extraido"]: context_block,
        DEFAULT_PLACEHOLDERS["ruta_destino"]: ruta_destino_relativa_str,
    }

    num_tags_to_fill = len([k for k in DEFAULT_PLACEHOLDERS if k.startswith("etiqueta_jerarquica_")])
    for i, tag in enumerate(hierarchical_tags[:num_tags_to_fill]):
        placeholder_key = f"etiqueta_jerarquica_{i+1}"
        if placeholder_key in DEFAULT_PLACEHOLDERS:
            replacements[DEFAULT_PLACEHOLDERS[placeholder_key]] = tag

    for i in range(len(hierarchical_tags), num_tags_to_fill):
         placeholder_key = f"etiqueta_jerarquica_{i+1}"
         if placeholder_key in DEFAULT_PLACEHOLDERS:
            replacements[DEFAULT_PLACEHOLDERS[placeholder_key]] = ""

    # 6. Inyectar placeholders
    print("\nCore - Inyectando placeholders en la plantilla...")
    final_prompt = prompt_handler.inject_context_multi(template_string, replacements)

    print("--- Fin Lógica Core ---")
    return final_prompt
# --- FIN NUEVA FUNCIÓN REFACTORIZADA ---


def parse_arguments() -> argparse.Namespace:
    # (Sin cambios aquí)
    """Define y parsea los argumentos de la línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Generador de Contexto Obsidian para Prompts LLM.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Ejemplos:
  # Procesar toda la bóveda (solo .md) y usar plantilla inline
  python main.py --vault "/path/to/vault" --output-note-path "NuevaNota.md" --prompt-template "Contexto: {contexto_extraido} Pregunta: ..."

  # Procesar carpetas específicas (md y canvas), SÓLO árbol, y usar plantilla de archivo
  python main.py --vault "/path/to/vault" --target "Proyectos" --ext .md .canvas --output-mode tree --output-note-path "Proyectos/ResumenProyectos.md" --prompt-file "templates/crear_nota_template.txt"

  # Procesar SÓLO contenido y guardar el prompt final en un archivo
  python main.py --vault "." --output-mode content --output-note-path "Ideas/NuevaIdea.md" --prompt-template "Resumen: {contexto_extraido}" --output final_prompt.txt
"""
    )
    parser.add_argument(
        "--vault",
        type=Path,
        required=True,
        help="Ruta al directorio raíz de la bóveda de Obsidian."
    )
    parser.add_argument(
        "--target",
        type=str,
        action='append',
        default=[],
        metavar='RUTA_RELATIVA',
        help="Ruta relativa dentro de la bóveda para incluir. Repetir para múltiples targets. Si no se usa, procesa toda la bóveda."
    )
    parser.add_argument(
        "--ext",
        type=str,
        action='append',
        default=[],
        metavar='EXTENSION',
        help=f"Extensión de archivo a incluir (ej: .md, .canvas). Repetir para múltiples extensiones. Por defecto: {DEFAULT_EXTENSIONS}"
    )
    template_group = parser.add_mutually_exclusive_group(required=True)
    template_group.add_argument(
        "--prompt-template",
        type=str,
        help="La plantilla del prompt como string directo. Debe contener placeholders."
    )
    template_group.add_argument(
        "--prompt-file",
        type=Path,
        help="Ruta a un archivo de texto que contiene la plantilla del prompt."
    )
    parser.add_argument(
        "--output-mode",
        type=str,
        choices=['tree', 'content', 'both'],
        default='both',
        help="Especifica qué incluir en el contexto: 'tree' (solo estructura), 'content' (solo contenidos), 'both' (ambos). Default: both"
    )
    parser.add_argument(
        "--output-note-path",
        type=str, # Mantenido como str aquí
        required=True,
        help="Ruta relativa (desde la bóveda) donde se crearía/ubicaría la nueva nota (usada para tema y etiquetas)."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Archivo opcional donde guardar el prompt final generado. Si no se especifica, se imprime en la consola."
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.2.0'
    )
    args = parser.parse_args()
    if not args.ext:
        args.ext = DEFAULT_EXTENSIONS
    args.ext = [f".{e.lstrip('.')}" for e in args.ext]
    args.vault = args.vault.resolve()
    # --- Procesamiento de output_note_path se hará dentro de main ---
    return args


def main():
    """Función principal que orquesta el proceso CLI."""
    args = parse_arguments()

    # Validar y convertir output_note_path aquí
    output_note_path_relative = Path(args.output_note_path)
    if output_note_path_relative.is_absolute():
         print("Advertencia: --output-note-path debería ser una ruta relativa a la bóveda. Intentando convertir...", file=sys.stderr)
         try:
            output_note_path_relative = output_note_path_relative.relative_to(args.vault)
         except ValueError:
             print(f"Error: No se pudo hacer relativa la ruta {args.output_note_path} a la bóveda {args.vault}.", file=sys.stderr)
             sys.exit(1)

    # Cargar plantilla desde archivo o string
    try:
        template_string = prompt_handler.load_template(args.prompt_template, args.prompt_file)
    except ValueError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

    # --- LLAMAR A LA LÓGICA CORE ---
    try:
        final_prompt = generate_prompt_core(
            vault_path=args.vault,
            target_paths=args.target,
            extensions=args.ext,
            output_mode=args.output_mode,
            output_note_path=output_note_path_relative, # Usar la relativa
            template_string=template_string
        )
    except Exception as e:
         print(f"\nError durante la generación del prompt: {e}", file=sys.stderr)
         # Podrías imprimir traceback aquí si quieres más detalle
         # import traceback
         # traceback.print_exc()
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

    print("\n--- Proceso CLI Completado ---")

if __name__ == "__main__":
    main()