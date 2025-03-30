# prompt_handler.py
from pathlib import Path
# Asegúrate de que Tuple está aquí, junto con los otros tipos necesarios
from typing import Optional, Dict, List, Tuple
import sys
import os

# --- NUEVAS PLANTILLAS PREDETERMINADAS ---
# (El resto del código de plantillas sigue igual)
DEFAULT_TEMPLATES: Dict[str, str] = {
    "Generar Nota Simple": """\
# Rol: Experto en {etiqueta_jerarquica_1}

## Tarea
Genera contenido introductorio para una nueva nota en Obsidian titulada aproximadamente como sugiere la ruta `{ruta_destino}`.

## Contexto Relevante
{contexto_extraido}

## Solicitud
Escribe una definición clara y concisa del concepto principal indicado por la ruta `{ruta_destino}`. Añade una breve explicación de su importancia en el contexto de `{etiqueta_jerarquica_1}`. Incluye enlaces `[[...]]` a conceptos clave mencionados en el contexto si son relevantes. Empieza directamente con el contenido Markdown, sin YAML.
""",
    "Resumir Contenido": """\
# Rol: Asistente de Síntesis

## Tarea
Resume los puntos clave del siguiente contenido extraído de Obsidian.

## Contenido a Resumir
{contexto_extraido}

## Solicitud
Proporciona un resumen conciso (ej. 3-5 puntos bullet) de la información principal presentada en el contexto anterior. Identifica los temas centrales.
""",
    "Generar Preguntas Estudio": """\
# Rol: Tutor Académico

## Tarea
Formula preguntas de estudio basadas en el siguiente material académico extraído de Obsidian.

## Material de Estudio
{contexto_extraido}

## Solicitud
Genera 3-5 preguntas significativas que evalúen la comprensión del material proporcionado. Las preguntas deben fomentar el pensamiento crítico y cubrir los conceptos más importantes.
""",
    # Añade tu plantilla anterior si quieres mantenerla como predeterminada
    "Generar Nota Completa (Original)": """\
# Rol: Experto Académico y Gestor de Conocimiento en Obsidian

Actúa como un experto académico y especialista en gestión del conocimiento, con habilidad para generar contenido educativo estructurado, preciso y optimizado para Obsidian.

---
## Tarea Principal

Generar el contenido completo en formato Markdown (.md) para una *nueva* nota de Obsidian. El tema principal de la nota se deriva de la `Ruta de Archivo Destino` proporcionada. El contenido debe ser académicamente riguroso, bien estructurado para el aprendizaje y altamente interconectado dentro del contexto de la `Estructura y Contenido Existente`.

---
## Contexto Proporcionado

*   **Ruta de Archivo Destino:** `{ruta_destino}`
    *   *Esta ruta define el tema central y la ubicación de la nota a crear.*

*   **Estructura y Contenido Existente:**
    ```
    {contexto_extraido}
    ```
    *   *Usa esta información para identificar notas existentes a las que enlazar y para entender el contexto temático general.*

---
## Requisitos Detallados de Salida

1.  **Generación de Contenido Enfocado:** Crea contenido original y coherente centrado exclusivamente en el tema inferido de la `Ruta de Archivo Destino`. El nivel de detalle debe ser apropiado para un entorno académico (e.g., nivel universitario o de estudio avanzado), proporcionando una visión general sólida o profundizando según sugiera el título/ruta. Evita información no pertinente al tema central definido por la ruta.

2.  **Estructura y Organización Lógica:** Organiza el contenido generado usando encabezados Markdown (`#`, `##`, `###`, etc.). Asegura un flujo claro y pedagógico:
    *   Introducción / Definición clara del concepto.
    *   Desarrollo de Conceptos Clave / Secciones principales.
    *   Ejemplos concretos (si aplica y enriquece la explicación).
    *   Implicaciones / Aplicaciones / Conclusiones (si aplica).
    *   (Opcional) Sección "Véase También" o "Conceptos Relacionados" al final, con enlaces `[[...]]`.

3.  **Formato Markdown:**
    *   Utiliza Markdown estándar de forma efectiva (negrita `** **`, cursiva `* *`, listas `-`, `1.`, citas `>`, etc.).
    *   Usa LaTeX (`$...$` para inline, `$$...$$` para bloques) para notación matemática o científica *solo si el tema lo requiere*.
    *   Usa bloques de código (``` ``` con especificación de lenguaje si es posible) si es pertinente al tema (e.g., algoritmos, ejemplos de código).

4.  **Rigor Académico y Precisión:** Asegúrate de que toda la información generada (definiciones, hechos, teorías, explicaciones) sea precisa, actualizada y consistente con el conocimiento establecido en el dominio temático correspondiente. Cita fuentes si es posible o necesario para el rigor académico, aunque no es obligatorio si se enfoca en la explicación conceptual.

5.  **Interconexión Extensiva con Obsidian (`[[...]]`):** Este es un punto *crucial*. Integra activamente enlaces internos `[[...]]` aprovechando la `Estructura y Contenido Existente`:
    *   **Identifica y Enlaza Proactivamente:** Dentro del contenido generado, identifica términos clave, conceptos, personas, lugares, eventos, teorías u otras ideas relevantes que *probablemente* tengan (o deberían tener) su propia nota en la bóveda según el contexto proporcionado.
    *   **Enlace a Existentes:** Si la `Estructura y Contenido Existente` indica claramente que una nota relacionada ya existe (se ve en el árbol o en el contenido de otras notas), enlaza a ella usando su nombre de archivo exacto (e.g., `[[Concepto Previo Existente]]`).
    *   **Crea Enlaces Placeholder (Implícitos):** Si un concepto importante mencionado *merece* su propia nota pero no parece existir en el contexto proporcionado (o no estás seguro), crea un enlace igualmente. El formato debe ser `[[Nombre Descriptivo del Concepto]]`. **NO** indiques explícitamente que es un placeholder. El objetivo es que todos los conceptos clave sean enlaces, existan o no aún.
    *   **Enlaces a Secciones:** Si es relevante y conoces una sección específica en una nota existente (visible en el contexto), considera enlazar a ella (`[[Nota Relacionada#Sección Específica]]`).
    *   **Objetivo:** Crear una nota que actúe como un nodo densamente conectado dentro de la base de conocimiento, fomentando la navegación y el descubrimiento.

6.  **YAML Frontmatter (Formato Estricto):** Incluye un bloque YAML al inicio del archivo. **Sigue este formato EXACTAMENTE**:
    ```yaml
    ---
    tags:
      - {etiqueta_jerarquica_1} # Derivada de la ruta, e.g., Asignaturas/Sistemas_Operativos/Conceptos
      - {etiqueta_jerarquica_2} # Derivada de la ruta, más general, e.g., Asignaturas/Sistemas_Operativos
      # ... (más etiquetas jerárquicas si la ruta es más profunda)
      - {etiqueta_conceptual_central_1} # Palabra clave principal del tema de la nota
      - {etiqueta_conceptual_central_2} # Otra palabra clave principal
      - {etiqueta_conceptual_relacionada_1} # Concepto secundario pero relevante
      - {etiqueta_conceptual_relacionada_2} # Otro concepto secundario
      # ... (añade más etiquetas conceptuales relevantes y específicas, evitando las muy genéricas)
    ---
    ```
    *   **Derivación de Etiquetas Jerárquicas:** Extrae la estructura de directorios de la `{ruta_destino}`. Cada nivel de directorio se convierte en parte de una etiqueta jerárquica, usando `/` como separador. Si un nombre de carpeta contiene espacios, reemplázalos consistentemente con guiones bajos (`_`) o medios (`-`) en la etiqueta. Incluye etiquetas para la ruta completa y para niveles superiores.
    *   **Etiquetas Conceptuales:** Añade palabras clave (simples o compuestas con `_` o `-`) que describan el *contenido específico* de la nota generada. Sé preciso y relevante. **NO uses `#`** dentro del YAML. Todas las entradas deben ser elementos de lista (`-`).

7.  **Claridad y Tono:** Mantén un tono pedagógico claro, conciso y formal, adecuado para el nivel académico implícito en la ruta. Define términos técnicos la primera vez que aparezcan o, preferiblemente, enlázalos (`[[Término Técnico]]`).

8.  **Completitud y Contextualización:** Asegúrate de que la nota cubra los aspectos esenciales del tema solicitado en `{ruta_destino}`. Si el tema requiere entender conceptos previos, defínelos brevemente o, idealmente, crea enlaces `[[Concepto Prerrequisito]]` (existente o placeholder).

9.  **Síntesis:** Presenta la información de manera sintetizada y bien organizada, no como una simple enumeración de hechos, sino como una explicación coherente y estructurada.

---
## Solicitud Final

Genera el contenido completo en formato Markdown para la **nueva nota** ubicada en `{ruta_destino}`. Cumple estrictamente con todos los requisitos detallados, prestando especial atención a la **interconexión mediante enlaces `[[...]]`** basados en el contexto proporcionado y al **formato exacto del YAML frontmatter** especificado en el punto 6. El resultado debe ser una nota precisa, bien estructurada y profundamente integrada en la estructura de conocimiento de Obsidian. Empieza directamente con el bloque YAML `---`.
"""
}
# --- FIN PLANTILLAS ---


def get_available_templates() -> Dict[str, str]:
    """Devuelve un diccionario con los nombres de las plantillas disponibles."""
    # (Mismo código que antes)
    available = DEFAULT_TEMPLATES.copy()
    try:
        script_dir = Path(__file__).parent.resolve()
    except NameError:
        script_dir = Path.cwd()
    templates_dir = script_dir / "templates"

    if templates_dir.is_dir():
        for item in templates_dir.iterdir():
            if item.is_file() and item.suffix.lower() == '.txt':
                template_name = f"Archivo: {item.name}"
                # Guardar la ruta absoluta como string para asegurar consistencia
                available[template_name] = str(item.resolve())
    return available


def load_template(template_name_or_path: str) -> str:
    """Carga la plantilla por nombre (predeterminada o de archivo) o ruta directa."""
    # (Mismo código que antes)
    available_templates = get_available_templates()

    if template_name_or_path in available_templates:
        template_source = available_templates[template_name_or_path]
        file_path: Optional[Path] = None
        source_type: str = ""

        if template_source.startswith("Archivo: "):
             # El path viene después del prefijo, hay que limpiarlo
             path_str = template_source.split("Archivo: ", 1)[1]
             file_path = Path(path_str)
             source_type = "archivo (templates/)"
        elif Path(template_source).is_file(): # Comprobar si el valor es una ruta válida directamente
            file_path = Path(template_source)
            source_type = "archivo (ruta directa?)"
        else: # Es predeterminada
            print(f"Usando plantilla predeterminada: '{template_name_or_path}'")
            return template_source

        # Cargar desde archivo si file_path se determinó
        if file_path and file_path.is_file():
            print(f"Usando plantilla desde {source_type}: {file_path.name}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                raise ValueError(f"Error al leer el archivo de plantilla {file_path}: {e}")
        else:
             # Este caso podría darse si la ruta guardada en available_templates dejó de ser válida
             raise ValueError(f"El archivo de plantilla '{template_name_or_path}' referenciado no existe o la ruta no es válida: {file_path}")

    else: # Intentar como ruta directa
        template_path = Path(template_name_or_path)
        if template_path.is_file() and template_path.suffix.lower() == '.txt':
            print(f"Usando plantilla desde ruta directa: {template_path}")
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                raise ValueError(f"Error al leer el archivo de plantilla {template_path}: {e}")
        else:
            available_names = "\n - ".join(available_templates.keys())
            raise ValueError(f"No se encontró la plantilla predeterminada, el archivo en /templates, ni la ruta directa: '{template_name_or_path}'.\nDisponibles:\n - {available_names}")


# inject_context e inject_context_multi permanecen igual
def inject_context(template_string: str, context_block: str, placeholder: str) -> str:
    """Reemplaza el placeholder en la plantilla con el bloque de contexto."""
    if placeholder not in template_string:
        print(f"Advertencia: El placeholder '{placeholder}' no se encontró en la plantilla.", file=sys.stderr)
        return template_string + "\n\n--- CONTEXTO ADICIONAL (Placeholder no encontrado) ---\n" + context_block
    print(f"Inyectando contexto en el placeholder: '{placeholder}'")
    return template_string.replace(placeholder, context_block)


def inject_context_multi(template: str, replacements: dict[str, Optional[str]]) -> str:
    """Inyecta múltiples valores en sus respectivos placeholders."""
    result = template
    found_placeholders = 0
    for placeholder, value in replacements.items():
        # Asegurarse de que el placeholder existe antes de reemplazar
        if placeholder in result:
             # Reemplazar None o string vacío por ""
             replacement_value = value if value is not None else ""
             result = result.replace(placeholder, replacement_value)
             found_placeholders +=1
        # else: # Opcional: Advertir
        #     if placeholder not in ["{contexto_extraido}", "{ruta_destino}"]:
        #          print(f"Advertencia: Placeholder '{placeholder}' definido pero no encontrado.", file=sys.stderr)

    if found_placeholders == 0 and replacements: # Advertir si había algo que reemplazar pero no se encontró nada
         print("Advertencia: No se encontró ningún placeholder conocido para reemplazar en la plantilla.", file=sys.stderr)

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