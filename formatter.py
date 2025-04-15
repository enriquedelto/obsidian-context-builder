# formatter.py
from pathlib import Path
from typing import Optional, List
import sys

# Reutilizamos la función de lectura de file_handler
from file_handler import read_file_content

# Constante para los separadores
SEPARATOR = "-" * 80 # Ajusta la longitud si lo deseas

def format_file_content(file_path: Path, vault_path: Path) -> Optional[str]:
    """
    Lee el contenido de un archivo, lo formatea con números de línea y encabezado/pie.

    Args:
        file_path: Ruta absoluta al archivo.
        vault_path: Ruta absoluta a la raíz de la bóveda.

    Returns:
        Un string con el contenido formateado, o un mensaje de error formateado si hubo
        un error de lectura. Devuelve None solo si ocurre un error catastrófico aquí.
    """
    # Intentar obtener ruta relativa para el encabezado
    try:
        relative_path = file_path.relative_to(vault_path).as_posix()
    except ValueError:
        # Si está fuera de la bóveda (no debería pasar con find_relevant_files corregido)
        # o si hay problemas de links simbólicos, usar solo el nombre.
        relative_path = file_path.name
        print(f"Advertencia: No se pudo calcular la ruta relativa para {file_path.name} respecto a {vault_path}", file=sys.stderr)
    except Exception as e:
        relative_path = file_path.name
        print(f"Advertencia: Error inesperado al calcular ruta relativa para {file_path.name}: {e}", file=sys.stderr)


    header = f"\n{SEPARATOR}\n/{relative_path}:\n{SEPARATOR}\n"
    footer = f"{SEPARATOR}" # Solo una línea al final

    content = read_file_content(file_path)
    if content is None:
        # read_file_content ya imprimió el error, devolvemos un bloque indicando el fallo
        return f"{header} *** Error al leer el contenido del archivo ***\n{footer}\n"

    lines = content.splitlines()
    if not lines:
        return f"{header} (Archivo vacío)\n{footer}\n"

    # Calcular padding basado en el número total de líneas
    # Asegurar un mínimo de ancho por si acaso (ej. 3)
    max_line_num = len(lines)
    max_line_num_width = max(len(str(max_line_num)), 3)

    formatted_lines: List[str] = []
    for i, line in enumerate(lines):
        line_num_str = str(i + 1).rjust(max_line_num_width)
        # Evitar añadir espacios extra si la línea está vacía
        formatted_line = f"{line_num_str} | {line}" if line.strip() else f"{line_num_str} |"
        formatted_lines.append(formatted_line)

    # Unir todo con saltos de línea consistentes
    return header + "\n".join(formatted_lines) + "\n" + footer + "\n"