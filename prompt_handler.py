from pathlib import Path
from typing import Optional
import sys

def load_template(template_str: Optional[str], template_file: Optional[Path]) -> str:
    """
    Carga la plantilla de prompt desde un string o un archivo.

    Args:
        template_str: La plantilla como string directo.
        template_file: Ruta al archivo que contiene la plantilla.

    Returns:
        El contenido de la plantilla como string.

    Raises:
        ValueError: Si no se proporciona ni string ni archivo válido,
                    o si el archivo no se puede leer.
    """
    if template_file:
        if template_file.is_file():
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    print(f"Usando plantilla desde archivo: {template_file}")
                    return f.read()
            except Exception as e:
                raise ValueError(f"Error al leer el archivo de plantilla {template_file}: {e}")
        else:
            raise ValueError(f"El archivo de plantilla especificado no existe: {template_file}")
    elif template_str:
        print("Usando plantilla desde argumento --prompt-template.")
        return template_str
    else:
        # Podríamos tener una plantilla por defecto aquí, o requerir una.
        # Por ahora, lanzamos error si no hay plantilla.
        raise ValueError("Se requiere una plantilla. Usa --prompt-template o --prompt-file.")


def inject_context(template_string: str, context_block: str, placeholder: str) -> str:
    """
    Reemplaza el placeholder en la plantilla con el bloque de contexto.

    Args:
        template_string: La plantilla completa.
        context_block: El string que contiene el árbol y el contenido formateado.
        placeholder: El marcador de texto a reemplazar (ej: "{contexto_extraido}").

    Returns:
        El prompt final con el contexto inyectado.
    """
    if placeholder not in template_string:
        print(f"Advertencia: El placeholder '{placeholder}' no se encontró en la plantilla.", file=sys.stderr)
        # Devolvemos la plantilla tal cual, añadiendo el contexto al final como fallback
        return template_string + "\n\n--- CONTEXTO ADICIONAL (Placeholder no encontrado) ---\n" + context_block

    print(f"Inyectando contexto en el placeholder: '{placeholder}'")
    return template_string.replace(placeholder, context_block)


def inject_context_multi(template: str, replacements: dict[str, str]) -> str:
    """
    Inyecta múltiples valores en sus respectivos placeholders en la plantilla.
    
    Args:
        template: String con múltiples placeholders
        replacements: Diccionario de placeholders y sus valores
    
    Returns:
        String con todos los reemplazos realizados
    """
    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    return result