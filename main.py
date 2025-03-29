import argparse
from pathlib import Path
import sys
from typing import List, Optional

# Importar funciones de nuestros módulos
import file_handler
import tree_generator
import formatter
import prompt_handler

# Definir el placeholder por defecto
DEFAULT_PLACEHOLDER = "{contexto_extraido}"
DEFAULT_EXTENSIONS = ['.md']

def parse_arguments() -> argparse.Namespace:
    """Define y parsea los argumentos de la línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Generador de Contexto Obsidian para Prompts LLM.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Ejemplos:
  # Procesar toda la bóveda (solo .md) y usar plantilla inline
  python main.py --vault "/path/to/vault" --prompt-template "Contexto: {contexto_extraido} Pregunta: ..."

  # Procesar carpetas específicas (md y canvas) y usar plantilla de archivo
  python main.py --vault "/path/to/vault" --target "Proyectos/Activos" --target "Notas Diarias" --ext .md .canvas --prompt-file "templates/mi_plantilla.txt"

  # Guardar el prompt final en un archivo
  python main.py --vault "." --prompt-template "Resumen: {contexto_extraido}" --output final_prompt.txt
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
        action='append', # Permite múltiples --target
        default=[],
        metavar='RUTA_RELATIVA',
        help="Ruta relativa dentro de la bóveda para incluir. Repetir para múltiples targets. Si no se usa, procesa toda la bóveda."
    )
    parser.add_argument(
        "--ext",
        type=str,
        action='append', # Permite múltiples --ext
        default=[],
        metavar='EXTENSION',
        help=f"Extensión de archivo a incluir (ej: .md, .canvas). Repetir para múltiples extensiones. Por defecto: {DEFAULT_EXTENSIONS}"
    )

    # Grupo para asegurar que solo se use una opción de plantilla
    template_group = parser.add_mutually_exclusive_group(required=True)
    template_group.add_argument(
        "--prompt-template",
        type=str,
        help="La plantilla del prompt como string directo. Debe contener el placeholder."
    )
    template_group.add_argument(
        "--prompt-file",
        type=Path,
        help="Ruta a un archivo de texto que contiene la plantilla del prompt."
    )

    parser.add_argument(
        "--placeholder",
        type=str,
        default=DEFAULT_PLACEHOLDER,
        help=f"El texto exacto a reemplazar en la plantilla con el contexto. Por defecto: '{DEFAULT_PLACEHOLDER}'"
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
        version='%(prog)s 0.1.0' # Versión simple
    )

    args = parser.parse_args()

    # Normalizar extensiones y usar default si no se proporcionan
    if not args.ext:
        args.ext = DEFAULT_EXTENSIONS
    # Asegurar que las extensiones empiecen con punto
    args.ext = [f".{e.lstrip('.')}" for e in args.ext]

    # Resolver ruta de la bóveda a absoluta
    args.vault = args.vault.resolve()

    return args

def main():
    """Función principal que orquesta el proceso."""
    args = parse_arguments()

    print("--- Iniciando Generador de Contexto Obsidian ---")
    print(f"Bóveda: {args.vault}")

    # 1. Encontrar archivos relevantes
    relevant_files: List[Path] = file_handler.find_relevant_files(
        args.vault, args.target, args.ext
    )

    if not relevant_files:
        print("\nNo se encontraron archivos relevantes que coincidan con los criterios. Saliendo.")
        sys.exit(0) # Salida normal, no es un error

    # 2. Generar string del árbol
    print("\nGenerando estructura de árbol...")
    tree_string = tree_generator.generate_tree_string(relevant_files, args.vault)
    # print("\n--- Estructura ---")
    # print(tree_string) # Opcional: imprimir árbol para debug

    # 3. Formatear contenido de cada archivo
    print("\nFormateando contenido de archivos...")
    formatted_contents: List[str] = []
    for file_path in relevant_files:
        # print(f" - Procesando: {file_path.relative_to(args.vault)}") # Verboso
        formatted = formatter.format_file_content(file_path, args.vault)
        if formatted:
            formatted_contents.append(formatted)

    # 4. Combinar árbol y contenidos
    # El formato ya incluye los separadores, solo necesitamos unirlos.
    # Añadimos la estructura del árbol al principio.
    context_block = tree_string + "\n" + "".join(formatted_contents) # Usar "" si format_file_content ya tiene saltos de línea

    # print("\n--- Bloque de Contexto Combinado ---")
    # print(context_block[:1000] + "...") # Imprimir muestra para debug

    # 5. Cargar plantilla
    try:
        template_string = prompt_handler.load_template(args.prompt_template, args.prompt_file)
    except ValueError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

    # 6. Inyectar contexto en la plantilla
    final_prompt = prompt_handler.inject_context(template_string, context_block, args.placeholder)

    # 7. Mostrar o guardar resultado
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(final_prompt)
            print(f"\n--- Prompt Final Guardado ---")
            print(f"El prompt completo ha sido guardado en: {args.output.resolve()}")
        except IOError as e:
            print(f"\nError: No se pudo guardar el prompt en el archivo {args.output}: {e}", file=sys.stderr)
            print("\n--- Prompt Final (salida a consola como fallback) ---")
            print(final_prompt)
            sys.exit(1)
    else:
        print("\n--- Prompt Final (salida a consola) ---")
        print(final_prompt)

    print("\n--- Proceso Completado ---")

if __name__ == "__main__":
    main()