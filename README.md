# Obsidian Context Builder

**Filosofía:**

*   **Modularidad:** Separar las responsabilidades en diferentes archivos (módulos) para que el código sea más fácil de entender, probar y mantener.
*   **Claridad:** Usar nombres descriptivos para variables, funciones y archivos.
*   **Robustez:** Manejar posibles errores (p. ej., rutas no encontradas, problemas de permisos, errores de codificación).
*   **Configurabilidad:** Usar argumentos de línea de comandos para que el script sea flexible.

**Estructura de Carpetas y Archivos Propuesta:**

```
obsidian-context-builder/
│
├── main.py                     # Punto de entrada principal, maneja CLI y orquesta el flujo
├── file_handler.py             # Funciones para encontrar y leer archivos
├── tree_generator.py           # Lógica para generar la estructura de árbol
├── formatter.py                # Funciones para formatear el contenido de los archivos
├── prompt_handler.py           # Funciones para manejar la plantilla del prompt
│
├── templates/                  # (Opcional) Carpeta para guardar plantillas de prompt
│   └── example_template.txt
│
├── README.md                   # Documentación: cómo instalar, usar, ejemplos
└── requirements.txt            # (Inicialmente vacío o con librerías si añadimos alguna)
```

**Descripción de cada Archivo/Módulo:**

1.  **`main.py`:**
    *   **Responsabilidad:** Orquestar todo el proceso.
    *   **Tareas:**
        *   Importar funciones de los otros módulos.
        *   Definir y parsear los argumentos de línea de comandos (CLI) usando `argparse`:
            *   `--vault` (ruta a la bóveda, obligatorio).
            *   `--target` (ruta relativa objetivo, opcional, puede aparecer varias veces).
            *   `--ext` (extensión a incluir, opcional, por defecto '.md', puede aparecer varias veces).
            *   `--prompt-template` (plantilla como string, opcional).
            *   `--prompt-file` (ruta a archivo de plantilla, opcional, alternativa al anterior).
            *   `--placeholder` (el texto a reemplazar en la plantilla, opcional, default `"{contexto_extraido}"`).
            *   `--output` (ruta a archivo de salida para el prompt final, opcional, si no, imprime a consola).
        *   Llamar a `file_handler.find_relevant_files` para obtener la lista de archivos a procesar.
        *   Llamar a `tree_generator.generate_tree_string` para crear el árbol.
        *   Iterar sobre los archivos relevantes, llamando a `formatter.format_file_content` para cada uno.
        *   Combinar el árbol y los contenidos formateados en `contexto_combinado`.
        *   Llamar a `prompt_handler.load_template` para obtener la plantilla.
        *   Llamar a `prompt_handler.inject_context` para generar el prompt final.
        *   Imprimir el prompt final en consola o guardarlo en el archivo de salida.
        *   Manejar errores generales y mostrar mensajes informativos al usuario.

2.  **`file_handler.py`:**
    *   **Responsabilidad:** Interactuar con el sistema de archivos.
    *   **Funciones:**
        *   `find_relevant_files(vault_path, target_paths, extensions)`:
            *   Usa `pathlib.Path(vault_path).rglob('*')` o `os.walk` para recorrer la bóveda.
            *   Filtra por las `extensions` especificadas.
            *   Si `target_paths` no está vacío, filtra los archivos para que estén dentro de al menos uno de esos targets (comparando rutas relativas).
            *   Devuelve una lista ordenada de objetos `pathlib.Path` de los archivos relevantes.
        *   `read_file_content(file_path)`:
            *   Abre y lee el contenido de un archivo.
            *   Maneja la codificación (intentar UTF-8 por defecto, quizás con fallback).
            *   Maneja `FileNotFoundError` y otros `IOError`.
            *   Devuelve el contenido como una única cadena de texto.

3.  **`tree_generator.py`:**
    *   **Responsabilidad:** Crear la representación visual del árbol de directorios.
    *   **Funciones:**
        *   `generate_tree_string(file_paths, vault_path)`:
            *   Toma la lista de `pathlib.Path` relevantes y la ruta base de la bóveda.
            *   Calcula las rutas relativas de cada archivo.
            *   Construye la estructura jerárquica (puede ser complejo, quizás usando un diccionario anidado o procesando las rutas ordenadas).
            *   Genera el string del árbol con los prefijos `├──`, `└──`, `│   `.
            *   Asegura el orden correcto.
            *   Devuelve el string multi-línea del árbol.

4.  **`formatter.py`:**
    *   **Responsabilidad:** Dar formato específico al contenido de los archivos y combinarlo con el árbol.
    *   **Funciones:**
        *   `format_file_content(file_path, vault_path)`:
            *   Obtiene la ruta relativa del archivo desde `vault_path`.
            *   Llama a `file_handler.read_file_content` para obtener el texto.
            *   Añade el encabezado con la ruta relativa (p.ej., `/ruta/relativa/archivo.md:\n-----\n`).
            *   Enumera las líneas (` 1 | linea1\n 2 | linea2\n`). Asegurar alineación de números.
            *   Añade el separador final (`\n-----\n`).
            *   Devuelve el bloque de texto formateado para ese archivo.
        *   `combine_context(tree_string, formatted_contents)`:
            *   Toma el string del árbol y una lista (o diccionario) de los contenidos ya formateados por `format_file_content`.
            *   Los une en un solo bloque de texto, usualmente el árbol primero, luego cada contenido de archivo (ordenado por ruta) separado por un espacio o separador adicional si se desea.
            *   Devuelve el string `contexto_combinado` completo.

5.  **`prompt_handler.py`:**
    *   **Responsabilidad:** Gestionar la plantilla del prompt.
    *   **Funciones:**
        *   `load_template(template_str, template_file)`:
            *   Verifica si se proporcionó `template_str` o `template_file`. Da prioridad a uno (p.ej., `template_file` si ambos existen).
            *   Si es `template_file`, lo lee.
            *   Si no hay ninguno, devuelve una plantilla por defecto simple o lanza un error.
            *   Devuelve el contenido de la plantilla como string.
        *   `inject_context(template_string, context_block, placeholder)`:
            *   Realiza el reemplazo del `placeholder` dentro del `template_string` con el `context_block`.
            *   Devuelve el prompt final como string.

6.  **`README.md`:**
    *   Explicación del propósito del script.
    *   Instrucciones de instalación (si hay dependencias).
    *   Instrucciones de uso detalladas con ejemplos de CLI para varios casos (toda la bóveda, targets específicos, diferentes extensiones, uso de plantillas).
    *   Descripción de los argumentos CLI.

**Primeros Pasos Concretos:**

1.  **Crea la estructura de carpetas:** `mkdir obsidian-context-builder && cd obsidian-context-builder && mkdir templates`
2.  **Crea los archivos `.py` vacíos:** `touch main.py file_handler.py tree_generator.py formatter.py prompt_handler.py README.md requirements.txt`
3.  **Empieza por `main.py`:** Define la estructura básica con `argparse` para manejar los argumentos `--vault`, `--ext`, `--target` y `--prompt-template` (puedes añadir los demás después).
4.  **Implementa `file_handler.py`:** Céntrate en la función `find_relevant_files`. Usa `pathlib` para esto. Haz pruebas simples imprimiendo la lista de archivos encontrados.
5.  **Continúa con `formatter.py`:** Implementa `format_file_content` (leyendo el archivo y añadiendo números de línea). Puedes probarlo llamándolo desde `main.py` para un archivo específico.
6.  **Aborda `tree_generator.py`:** Esta parte puede requerir más lógica. Busca librerías existentes o implementa tu propia lógica para generar el árbol a partir de una lista de rutas relativas.
7.  **Implementa `prompt_handler.py`:** Funciones relativamente sencillas para leer la plantilla y reemplazar el placeholder.
8.  **Ensambla todo en `main.py`:** Llama a las funciones en el orden correcto y combina los resultados.
9.  **Refina y añade manejo de errores:** Considera casos borde y añade `try...except`.
10. **Escribe el `README.md`**.

Este plan te da una hoja de ruta clara para empezar a construir tu herramienta. ¡Ve paso a paso y prueba cada componente!