from pathlib import Path
from typing import Optional, List
import sys # Para mensajes de error

# Reutilizamos la función de lectura de file_handler
from file_handler import read_file_content

# Constante para los separadores
SEPARATOR = "-" * 80

def format_file_content(file_path: Path, vault_path: Path) -> Optional[str]:
    """
    Lee el contenido de un archivo, lo formatea con números de línea y encabezado.

    Args:
        file_path: Ruta absoluta al archivo.
        vault_path: Ruta absoluta a la raíz de la bóveda.

    Returns:
        Un string con el contenido formateado, o None si hubo un error de lectura.
    """
    content = read_file_content(file_path)
    if content is None:
        # El error ya fue impreso por read_file_content
        return f"\n{SEPARATOR}\n/{file_path.relative_to(vault_path).as_posix()}:\n{SEPARATOR}\n *** Error al leer el archivo *** \n{SEPARATOR}\n"


    try:
        relative_path = file_path.relative_to(vault_path).as_posix()
    except ValueError:
        relative_path = file_path.name # Fallback si algo va mal
        print(f"Advertencia: No se pudo calcular la ruta relativa para {file_path} respecto a {vault_path}", file=sys.stderr)

    header = f"\n{SEPARATOR}\n/{relative_path}:\n{SEPARATOR}\n"
    footer = f"\n{SEPARATOR}\n"

    lines = content.splitlines()
    if not lines:
        return header + " (Archivo vacío)\n" + footer

    max_line_num_width = len(str(len(lines))) # Ancho para padding de números

    formatted_lines: List[str] = []
    for i, line in enumerate(lines):
        line_num_str = str(i + 1).rjust(max_line_num_width)
        formatted_lines.append(f"{line_num_str} | {line}")

    return header + "\n".join(formatted_lines) + footer