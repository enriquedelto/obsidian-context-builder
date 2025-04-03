# prompt_handler.py
from pathlib import Path
from typing import Optional, Dict, List
import sys
# import os # Eliminado - No usado
# from typing import Tuple # Eliminado - No usado (select_vault_interactive se fue)

# --- CONSTANTES Y FUNCIONES OBSOLETAS ELIMINADAS ---
# DEFAULT_TEMPLATES = {}
# inject_context(singular)
# select_vault_interactive()
# main()
# ----------------------------------------------------

def get_template_folder_path() -> Path:
    """Obtiene la ruta a la carpeta 'templates' relativa al script."""
    try:
        script_dir = Path(__file__).parent.resolve()
    except NameError:
        # Fallback si __file__ no está definido
        script_dir = Path.cwd()
    return script_dir / "templates"

def get_available_templates() -> Dict[str, str]:
    """
    Devuelve un diccionario con plantillas encontradas en la carpeta /templates.
    Clave: Nombre descriptivo (ej: "Archivo: MiPlantilla").
    Valor: Ruta absoluta al archivo .txt como string.
    """
    available: Dict[str, str] = {}
    templates_dir = get_template_folder_path()

    if templates_dir.is_dir():
        try:
            for item in templates_dir.glob('*.txt'):
                if item.is_file() and not item.name.startswith('.'):
                    template_name = f"Archivo: {item.stem}"
                    available[template_name] = str(item.resolve())
        except OSError as e:
            print(f"Advertencia: No se pudo listar '{templates_dir}': {e}", file=sys.stderr)
        except Exception as e:
             print(f"Advertencia: Error buscando plantillas en '{templates_dir}': {e}", file=sys.stderr)
    # else:
    #     print(f"Info: Carpeta '{templates_dir.name}' no encontrada.", file=sys.stderr)
    return available

def load_template(template_name_or_path: str) -> str:
    """
    Carga una plantilla por su nombre conocido (de get_available_templates) o por ruta directa.

    Args:
        template_name_or_path: Nombre ("Archivo: Stem") o ruta a archivo .txt.

    Returns:
        El contenido de la plantilla como string.

    Raises:
        ValueError: Si no se encuentra o no se puede leer.
    """
    available_templates = get_available_templates()

    # 1. Comprobar si es un nombre conocido
    if template_name_or_path in available_templates:
        file_path_str = available_templates[template_name_or_path]
        file_path = Path(file_path_str)
        print(f"Cargando plantilla desde archivo conocido: {file_path.name}", file=sys.stderr)
        try:
            return file_path.read_text(encoding='utf-8')
        except Exception as e:
            raise ValueError(f"Error al leer plantilla conocida {file_path}: {e}")

    # 2. Intentar tratarlo como ruta directa
    else:
        try:
            template_path = Path(template_name_or_path).resolve()
            if template_path.is_file() and template_path.suffix.lower() == '.txt':
                print(f"Cargando plantilla desde ruta directa: {template_path}", file=sys.stderr)
                try:
                    return template_path.read_text(encoding='utf-8')
                except Exception as e:
                    raise ValueError(f"Error al leer plantilla {template_path}: {e}")
            # Generar error claro si no es archivo .txt válido
            elif not template_path.exists(): raise ValueError(f"Ruta de plantilla '{template_name_or_path}' no existe.")
            elif not template_path.is_file(): raise ValueError(f"Ruta de plantilla '{template_name_or_path}' no es un archivo.")
            else: raise ValueError(f"Archivo de plantilla '{template_name_or_path}' no tiene extensión .txt.")
        except Exception as e:
             if isinstance(e, ValueError): raise e # Relanzar errores de validación
             else: raise ValueError(f"Error procesando ruta plantilla '{template_name_or_path}': {e}")

    # Fallback - Mensaje si no se encontró por ninguna vía (aunque no debería llegar aquí)
    # available_names_list = sorted(available_templates.keys())
    # err_msg = f"Plantilla no encontrada: '{template_name_or_path}'.\n..." # Ya cubierto arriba
    # raise ValueError(err_msg)


def inject_context_multi(template: str, replacements: Dict[str, Optional[str]]) -> str:
    """
    Inyecta múltiples valores en sus respectivos placeholders en una plantilla.
    Reemplaza con string vacío si el valor es None.
    """
    result = template
    placeholders_found_count = 0
    placeholders_replaced_count = 0
    original_template_placeholders = {p for p in replacements if p in template} # Placeholders presentes originalmente

    for placeholder_fmt, value_to_inject in replacements.items():
        if placeholder_fmt in result: # Comprobar en la versión actual por si hubo reemplazos previos
             placeholders_found_count += 1
             replacement_value = value_to_inject if value_to_inject is not None else ""
             result = result.replace(placeholder_fmt, replacement_value)
             placeholders_replaced_count +=1
             # print(f"Placeholder '{placeholder_fmt}' reemplazado.", file=sys.stderr) # Debug
        # else: # Debug opcional
             # Si el placeholder no está en el resultado ACTUAL, pero sí estaba en el ORIGINAL,
             # puede ser útil saberlo, aunque podría ser ruido.
             # if placeholder_fmt in original_template_placeholders:
             #      print(f"Placeholder '{placeholder_fmt}' no encontrado (ya reemplazado?).", file=sys.stderr)


    # Advertir si no se reemplazó nada útil
    if placeholders_replaced_count == 0 and replacements and any(v is not None for v in replacements.values()):
         print(f"Advertencia: Ninguno de los placeholders proporcionados ({', '.join(replacements.keys())}) fue encontrado en la plantilla.", file=sys.stderr)
    # Advertir si faltaron placeholders que estaban originalmente
    elif placeholders_replaced_count < len(original_template_placeholders):
         missing = original_template_placeholders - set(replacements.keys()) # Placeholders que estaban pero no se intentó reemplazar? Raro
         # O más útil: placeholders que se intentó reemplazar pero no estaban al final
         attempted_but_missing_finally = {p for p in replacements if p in original_template_placeholders and p not in result}
         if attempted_but_missing_finally:
              print(f"Advertencia: Los siguientes placeholders estaban originalmente pero no se encontraron al final (¿reemplazados por error?): {', '.join(attempted_but_missing_finally)}", file=sys.stderr)


    return result