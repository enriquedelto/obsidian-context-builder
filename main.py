# main.py
import argparse
from pathlib import Path
import sys
from typing import List, Optional, Dict # Añadir Dict

# Importar funciones de nuestros módulos
import file_handler
import tree_generator
import formatter
import prompt_handler

# Definir los placeholders por defecto (usando Dict ahora)
DEFAULT_PLACEHOLDERS: Dict[str, str] = {
    "contexto_extraido": "{contexto_extraido}",
    "ruta_destino": "{ruta_destino}",
    "etiqueta_jerarquica_1": "{etiqueta_jerarquica_1}", # Asegúrate que coincida con la plantilla
    "etiqueta_jerarquica_2": "{etiqueta_jerarquica_2}",
    "etiqueta_jerarquica_3": "{etiqueta_jerarquica_3}"
    # Añade más si necesitas pre-calcular más etiquetas jerárquicas
}
DEFAULT_EXTENSIONS = ['.md']

def parse_arguments() -> argparse.Namespace:
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

    # Grupo para asegurar que solo se use una opción de plantilla
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

    # --- ¡NUEVO ARGUMENTO! ---
    parser.add_argument(
        "--output-mode",
        type=str,
        choices=['tree', 'content', 'both'],
        default='both',
        help="Especifica qué incluir en el contexto: 'tree' (solo estructura), 'content' (solo contenidos), 'both' (ambos). Default: both"
    )
    # --- FIN NUEVO ARGUMENTO ---

    parser.add_argument(
        "--output-note-path",
        type=str, # Cambiado a str para manejar rutas relativas fácilmente
        required=True, # Mantenido requerido para la plantilla de creación
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
        version='%(prog)s 0.2.0' # Incremento de versión
    )

    args = parser.parse_args()

    # Normalizar extensiones
    if not args.ext:
        args.ext = DEFAULT_EXTENSIONS
    args.ext = [f".{e.lstrip('.')}" for e in args.ext]

    # Resolver ruta de la bóveda a absoluta
    args.vault = args.vault.resolve()

    # Convertir output_note_path a Path relativo a la bóveda para consistencia interna
    # Esto asume que el usuario introduce la ruta relativa desde la bóveda
    args.output_note_path = Path(args.output_note_path)
    if args.output_note_path.is_absolute():
         print("Advertencia: --output-note-path debería ser una ruta relativa a la bóveda. Intentando convertir...", file=sys.stderr)
         try:
            args.output_note_path = args.output_note_path.relative_to(args.vault)
         except ValueError:
             print(f"Error: No se pudo hacer relativa la ruta {args.output_note_path} a la bóveda {args.vault}.", file=sys.stderr)
             sys.exit(1)

    return args

def generate_hierarchical_tags(relative_note_path: Path) -> List[str]:
    """Extrae etiquetas jerárquicas de una ruta relativa a la bóveda."""
    tags = []
    current_parts = []
    # Iterar sobre las partes del directorio padre
    for part in relative_note_path.parent.parts:
        if not part or part == '.': # Ignorar raíz, punto o partes vacías
            continue
        # Limpiar parte (ej: reemplazar espacios con _) - Ajusta tu convención
        cleaned_part = part.replace(" ", "_").replace("-", "_")
        current_parts.append(cleaned_part)
        tags.append("/".join(current_parts))

    # Devolver de más general a más específica (invirtiendo)
    return list(reversed(tags))

def main():
    """Función principal que orquesta el proceso."""
    args = parse_arguments()

    print("--- Iniciando Generador de Contexto Obsidian ---")
    print(f"Bóveda: {args.vault}")
    print(f"Modo de Salida Contexto: {args.output_mode}")
    print(f"Ruta Nota Destino (para tema/tags): {args.output_note_path}")

    # 1. Encontrar archivos relevantes
    relevant_files: List[Path] = file_handler.find_relevant_files(
        args.vault, args.target, args.ext
    )

    if not relevant_files and args.output_mode != 'tree': # Si no hay archivos y pedimos contenido, advertir
        print("\nAdvertencia: No se encontraron archivos relevantes que coincidan con los criterios.")
        # Podríamos salir, pero quizás sólo queremos el árbol (si aplica) o generar una nota sin contexto de contenido
        # sys.exit(0)

    # --- LÓGICA CONDICIONAL PARA GENERACIÓN ---
    tree_string = ""
    if args.output_mode in ['tree', 'both']:
        print("\nGenerando estructura de árbol...")
        # Pasamos sólo los archivos encontrados, incluso si está vacío,
        # para que tree_generator pueda devolver el mensaje adecuado.
        tree_string = tree_generator.generate_tree_string(relevant_files, args.vault)
        if not tree_string.strip() or tree_string.startswith(" (No se encontraron"):
             print("Advertencia: No se generó estructura de árbol (posiblemente no hay archivos o directorios relevantes).")


    formatted_contents: List[str] = []
    if args.output_mode in ['content', 'both']:
        if relevant_files: # Solo formatear si hay archivos
             print("\nFormateando contenido de archivos...")
             for file_path in relevant_files:
                 # print(f" - Procesando: {file_path.relative_to(args.vault)}") # Verboso
                 formatted = formatter.format_file_content(file_path, args.vault)
                 if formatted:
                     formatted_contents.append(formatted)
             if not formatted_contents:
                  print("Advertencia: No se pudo formatear contenido (archivos vacíos o con errores de lectura).")
        else:
             print("\nNo hay archivos relevantes para formatear contenido.")
    # --- FIN LÓGICA CONDICIONAL ---


    # 4. Construir el bloque de contexto según el modo
    print(f"\nConstruyendo bloque de contexto (Modo: {args.output_mode})...")
    context_block = ""
    if args.output_mode == 'tree':
        context_block = tree_string
    elif args.output_mode == 'content':
        context_block = "".join(formatted_contents).strip() # Unir contenidos, quitar espacios extra
    elif args.output_mode == 'both':
        # Unir árbol y contenido, asegurando un salto de línea si ambos existen
        if tree_string.strip() and formatted_contents:
            context_block = tree_string.strip() + "\n" + "".join(formatted_contents).strip()
        elif tree_string.strip():
             context_block = tree_string.strip()
        elif formatted_contents:
             context_block = "".join(formatted_contents).strip()
        else: # Ambos vacíos o con errores
             context_block = "(No se generó ni árbol ni contenido)"

    # print("\n--- Bloque de Contexto Combinado (muestra) ---")
    # print(context_block[:500] + "..." if len(context_block) > 500 else context_block) # Imprimir muestra

    # 5. Cargar plantilla
    try:
        template_string = prompt_handler.load_template(args.prompt_template, args.prompt_file)
    except ValueError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

    # 6. Preparar valores para los placeholders
    # Ruta destino relativa desde la bóveda
    ruta_destino_relativa_str = args.output_note_path.as_posix()
    # Calcular etiquetas jerárquicas (usando la función mejorada)
    hierarchical_tags = generate_hierarchical_tags(args.output_note_path)

    # Crear diccionario de reemplazos dinámico
    replacements: Dict[str, str] = {
        DEFAULT_PLACEHOLDERS["contexto_extraido"]: context_block,
        DEFAULT_PLACEHOLDERS["ruta_destino"]: ruta_destino_relativa_str,
    }

    # Añadir etiquetas jerárquicas disponibles a los placeholders {etiqueta_jerarquica_X}
    # Asegúrate que los nombres coinciden con los de DEFAULT_PLACEHOLDERS y la plantilla
    num_tags_to_fill = len([k for k in DEFAULT_PLACEHOLDERS if k.startswith("etiqueta_jerarquica_")])
    for i, tag in enumerate(hierarchical_tags[:num_tags_to_fill]):
        placeholder_key = f"etiqueta_jerarquica_{i+1}"
        if placeholder_key in DEFAULT_PLACEHOLDERS:
            replacements[DEFAULT_PLACEHOLDERS[placeholder_key]] = tag
        else:
             print(f"Advertencia: Placeholder '{placeholder_key}' no definido en DEFAULT_PLACEHOLDERS.", file=sys.stderr)

    # Rellenar placeholders de etiquetas restantes (si los hay) con string vacío o un marcador
    for i in range(len(hierarchical_tags), num_tags_to_fill):
         placeholder_key = f"etiqueta_jerarquica_{i+1}"
         if placeholder_key in DEFAULT_PLACEHOLDERS:
            replacements[DEFAULT_PLACEHOLDERS[placeholder_key]] = "" # O un texto como "(no disponible)"


    # 6. Inyectar todos los placeholders
    print("\nInyectando contexto y metadatos en la plantilla...")
    final_prompt = prompt_handler.inject_context_multi(template_string, replacements)

    # 7. Mostrar o guardar resultado
    if args.output:
        try:
            # Asegurarse que el directorio de salida exista (si args.output incluye carpetas)
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

    print("\n--- Proceso Completado ---")

if __name__ == "__main__":
    main()