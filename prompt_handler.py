# prompt_handler.py
from pathlib import Path
from typing import Optional, Dict, List, Tuple # Asegurarse que Tuple está si se usa (aunque select_vault_interactive se fue)
import sys
# import os # <--- ELIMINADO (No usado)

# --- DEFAULT_TEMPLATES ELIMINADO ---

def get_template_folder_path() -> Path:
    """Obtiene la ruta a la carpeta 'templates' relativa al script."""
    try:
        # Usar __file__ para encontrar la carpeta relativa al script actual
        script_dir = Path(__file__).parent.resolve()
    except NameError:
        # Fallback si __file__ no está definido (ej. ejecución interactiva)
        script_dir = Path.cwd()
    return script_dir / "templates"

def get_available_templates() -> Dict[str, str]:
    """Devuelve un diccionario con plantillas encontradas en la carpeta /templates.
       Clave: Nombre descriptivo (ej: "Archivo: MiPlantilla").
       Valor: Ruta absoluta al archivo .txt como string.
    """
    available: Dict[str, str] = {} # Empezar vacío
    templates_dir = get_template_folder_path()

    if templates_dir.is_dir():
        try:
            # Iterar solo sobre archivos .txt que no empiecen con punto
            for item in templates_dir.glob('*.txt'):
                if item.is_file() and not item.name.startswith('.'):
                    # Usar un prefijo para indicar que viene de un archivo
                    # y usar 'stem' para obtener el nombre sin la extensión .txt
                    template_name = f"Archivo: {item.stem}"
                    available[template_name] = str(item.resolve()) # Guardar ruta absoluta
        except OSError as e:
            print(f"Advertencia: No se pudo listar la carpeta de plantillas '{templates_dir}': {e}", file=sys.stderr)
        except Exception as e:
             print(f"Advertencia: Error inesperado al buscar plantillas en '{templates_dir}': {e}", file=sys.stderr)

    # else: # Opcional: Informar si la carpeta no existe
    #      print(f"Info: Carpeta '{templates_dir.name}' no encontrada. No se cargarán plantillas personalizadas.", file=sys.stderr)

    return available # Devuelve solo los archivos .txt encontrados

def load_template(template_name_or_path: str) -> str:
    """
    Carga una plantilla por su nombre conocido (de get_available_templates) o por ruta directa.

    Args:
        template_name_or_path: Nombre de la plantilla (ej: "Archivo: MiPlantilla")
                               o ruta completa/relativa a un archivo .txt.

    Returns:
        El contenido de la plantilla como string.

    Raises:
        ValueError: Si el nombre o la ruta no son válidos, el archivo no existe,
                    no es un .txt, o no se puede leer.
    """
    available_templates = get_available_templates() # Obtener las plantillas conocidas de /templates

    # 1. Comprobar si es un nombre conocido de la carpeta /templates
    if template_name_or_path in available_templates:
        file_path_str = available_templates[template_name_or_path]
        file_path = Path(file_path_str)
        source_type = f"archivo conocido '{file_path.name}'"
        print(f"Cargando plantilla desde {source_type}", file=sys.stderr)
        try:
            return file_path.read_text(encoding='utf-8')
        except Exception as e:
            # Error más específico
            raise ValueError(f"Error al leer el archivo de plantilla conocido {file_path}: {e}")

    # 2. Si no es un nombre conocido, intentar tratarlo como ruta directa
    else:
        try:
            # Intentar resolver la ruta (relativa al CWD si no es absoluta)
            template_path = Path(template_name_or_path).resolve()
            source_type = f"ruta directa '{template_name_or_path}'"

            if template_path.is_file() and template_path.suffix.lower() == '.txt':
                print(f"Cargando plantilla desde {source_type}", file=sys.stderr)
                try:
                    return template_path.read_text(encoding='utf-8')
                except Exception as e:
                    raise ValueError(f"Error al leer el archivo de plantilla {template_path}: {e}")
            # Si no es un archivo .txt válido
            elif not template_path.exists():
                 raise ValueError(f"La ruta de plantilla '{template_name_or_path}' no existe.")
            elif not template_path.is_file():
                 raise ValueError(f"La ruta de plantilla '{template_name_or_path}' no es un archivo.")
            else: # Existe y es archivo, pero no .txt
                 raise ValueError(f"El archivo de plantilla '{template_name_or_path}' no tiene la extensión .txt.")

        except Exception as e: # Capturar errores de Path() o resolve()
             # Si ya es un ValueError, relanzarlo. Si no, envolverlo.
             if isinstance(e, ValueError):
                 raise e
             else:
                  raise ValueError(f"Error al procesar la ruta de plantilla '{template_name_or_path}': {e}")

    # Si ninguna de las condiciones anteriores funcionó (aunque no debería llegar aquí)
    # Formatear mensaje de error final indicando qué falló
    available_names_list = sorted(available_templates.keys())
    err_msg = f"Plantilla no encontrada: '{template_name_or_path}'.\n"
    err_msg += f"- No es un nombre conocido en la carpeta '{get_template_folder_path().name}/'.\n"
    err_msg += f"- No es una ruta válida a un archivo .txt existente.\n"
    if available_names_list:
         display_names = [f"📄 {Path(available_templates[name]).stem}" for name in available_names_list]
         err_msg += f"Plantillas disponibles en /templates:\n - " + "\n - ".join(display_names)
    else:
         err_msg += f"No hay plantillas .txt en la carpeta '{get_template_folder_path().name}'."
    raise ValueError(err_msg) # Lanzar el error compilado


# --- inject_context (singular) ELIMINADA ---
# (Asumiendo que solo se usa inject_context_multi desde core.generate_prompt_core)

def inject_context_multi(template: str, replacements: Dict[str, Optional[str]]) -> str:
    """
    Inyecta múltiples valores en sus respectivos placeholders en una plantilla.

    Args:
        template: El string de la plantilla.
        replacements: Un diccionario donde las claves son los placeholders
                      (ej: "{contexto_extraido}") y los valores son los
                      strings a inyectar (o None/"" para eliminar el placeholder).

    Returns:
        El string de la plantilla con los reemplazos hechos.
    """
    result = template
    placeholders_found_count = 0
    placeholders_replaced_count = 0

    for placeholder_fmt, value_to_inject in replacements.items():
        # Comprobar si el placeholder existe en la plantilla *actual*
        if placeholder_fmt in result:
            placeholders_found_count += 1
            # Reemplazar con el valor o con vacío si es None
            replacement_value = value_to_inject if value_to_inject is not None else ""
            # Realizar el reemplazo
            result = result.replace(placeholder_fmt, replacement_value)
            placeholders_replaced_count += 1
            # print(f"Placeholder '{placeholder_fmt}' reemplazado.", file=sys.stderr) # Debug
        # else: # Debug opcional
            # print(f"Placeholder '{placeholder_fmt}' no encontrado en la plantilla.", file=sys.stderr)


    # Advertir solo si se esperaban reemplazos pero no se encontró ninguno
    if placeholders_found_count == 0 and replacements and any(v is not None for v in replacements.values()):
         print(f"Advertencia: Ninguno de los placeholders ({', '.join(replacements.keys())}) fue encontrado en la plantilla. ¿Es correcta?", file=sys.stderr)
    elif placeholders_replaced_count < len(replacements):
         # Advertir si algunos placeholders esperados no estaban
         missing = [p for p in replacements if p not in result and placeholder_fmt not in template] # Comprobar en original por si fue reemplazado antes
         if missing:
              print(f"Advertencia: Los siguientes placeholders no se encontraron en la plantilla: {', '.join(missing)}", file=sys.stderr)


    return result

# --- FUNCIONES INTERACTIVAS y main() ELIMINADAS DE AQUÍ ---
# (Pertenecen a main.py o gui_streamlit.py)