# Obsidian Context Builder

**Obsidian Context Builder** es una herramienta de Python con doble interfaz (CLI y GUI) diseñada para ayudarte a crear prompts para Modelos de Lenguaje Grandes (LLMs) usando información de tu bóveda de Obsidian.

*   **Modo CLI (Línea de Comandos):** Extrae automáticamente la estructura de directorios y/o el contenido de archivos específicos de tu bóveda, los formatea y los inyecta en plantillas de prompt predefinidas. Ideal para análisis contextual automatizado.
*   **Modo GUI (Interfaz Gráfica - Streamlit):** Ofrece una interfaz visual para seleccionar plantillas y gestionar bóvedas. En este modo, **pegas manualmente** el contexto deseado (que puedes generar con la CLI u otras herramientas) en un área de texto, y la herramienta lo inyecta en la plantilla junto con metadatos derivados de la ruta destino. Ideal para un flujo de trabajo más interactivo donde ya tienes el contexto preparado.

Esto te permite generar rápidamente prompts contextualizados para tareas como:

*   Resumir notas existentes (pegando su contenido en la GUI o usando la CLI).
*   Generar contenido para nuevas notas basadas en contexto circundante (pegándolo en la GUI o usando la CLI).
*   Identificar conexiones entre temas.
*   Crear preguntas de estudio sobre un conjunto de notas.
*   ¡Y mucho más!

## Características Principales

*   **Doble Interfaz:** Funciona como script de línea de comandos (`main.py`) o como aplicación web local (`gui_streamlit.py`).
*   **Gestión de Bóvedas (CLI & GUI):** Guarda y selecciona fácilmente entre múltiples rutas de bóvedas de Obsidian. Recuerda la última utilizada para ejecuciones posteriores (tanto en CLI como en GUI).
*   **Gestión de Plantillas (CLI & GUI):** Utiliza plantillas predefinidas para tareas comunes o carga las tuyas desde archivos `.txt` ubicados en la carpeta `templates/`.
*   **Contexto Automático (CLI):**
    *   **Exploración Flexible:** Recorre tu bóveda de Obsidian seleccionada.
    *   **Filtrado Preciso (`--target`, `--ext`):** Selecciona el contexto basándote en directorios/archivos específicos y extensiones.
    *   **Extracción de Contexto:** Genera automáticamente la estructura de directorios (`tree`) y/o el contenido formateado (`content`).
    *   **Modo de Salida Configurable (`--output-mode`):** Elige qué incluir (`tree`, `content`, `both`).
*   **Contexto Manual (GUI):** Permite pegar directamente el texto del contexto (árbol, contenido, etc.) en un área dedicada.
*   **Inyección en Plantillas:** Reemplaza placeholders (`{contexto_extraido}`, `{ruta_destino}`, `{etiqueta_jerarquica_N}`) en la plantilla seleccionada con la información correspondiente.
*   **Etiquetas Jerárquicas:** Genera automáticamente etiquetas basadas en la ruta de la nota destino para usar en el YAML frontmatter o en el prompt.
*   **Salida Flexible:** Imprime el prompt final en la consola (CLI) o en el área de texto (GUI), y opcionalmente guárdalo en un archivo.

## Requisitos

*   **Python:** Versión 3.7 o superior.
*   **Bibliotecas Externas:**
    *   `streamlit` (solo para la interfaz gráfica `gui_streamlit.py`)

## Instalación

1.  **Clona el repositorio** (o descarga los archivos):
    ```bash
    git clone https://github.com/tu_usuario/obsidian-context-builder.git # Reemplaza con tu URL
    cd obsidian-context-builder
    ```
2.  (Opcional pero recomendado) Crea y activa un entorno virtual:
    ```bash
    python -m venv venv
    # Linux/macOS:
    source venv/bin/activate
    # Windows:
    # venv\Scripts\activate
    ```
3.  Instala las dependencias (necesario para la GUI):
    ```bash
    pip install -r requirements.txt
    ```

## Uso (CLI)

El script se ejecuta desde la línea de comandos usando `python main.py`.

```bash
python main.py [opciones_gestion] [opciones_generacion]
```

### Argumentos de Línea de Comandos

**Gestión de Bóvedas:** (Se ejecutan y el script termina)

*   `--add-vault NOMBRE RUTA`: Añade o actualiza una bóveda con un nombre corto y su ruta completa.
*   `--remove-vault NOMBRE`: Elimina una bóveda guardada por su nombre.
*   `--list-vaults`: Muestra las bóvedas guardadas.

**Gestión de Plantillas:** (Se ejecuta y el script termina)

*   `--list-templates`: Muestra las plantillas disponibles (predeterminadas y en `/templates`).

**Generación de Prompt:** (Requieren que una bóveda sea seleccionable)

*   `--select-vault NOMBRE`: (Opcional) Especifica qué bóveda guardada usar. Si no se usa, intenta la última recordada o pide selección interactiva.
*   `--target RUTA_RELATIVA`: (Opcional) Ruta relativa (a la bóveda) para incluir en el contexto. Repetir para múltiples. Default: toda la bóveda.
*   `--ext .EXTENSION`: (Opcional) Extensión de archivo a incluir. Repetir para múltiples. Default: `.md`.
*   `--template NOMBRE_O_RUTA`: (Opcional) Nombre de una plantilla (ver `--list-templates`) o ruta a un archivo `.txt`. Si no se usa, pide selección interactiva.
*   `--output-mode {tree,content,both}`: (Opcional) Qué contexto generar automáticamente (`tree`, `content`, o `both`). Default: `both`.
*   `--output-note-path RUTA_RELATIVA_NOTA`: (**Requerido para generar**) Ruta relativa *dentro* de la bóveda donde se crearía/ubicaría la nota objetivo (usada para etiquetas y placeholder `{ruta_destino}`).
*   `--output RUTA_ARCHIVO_SALIDA`: (Opcional) Guarda el prompt final en un archivo. Default: imprime en consola.

**Otros:**

*   `--version`: Muestra la versión.
*   `-h`, `--help`: Muestra ayuda detallada.

### Placeholders en Plantillas

Las plantillas pueden usar los siguientes marcadores:

*   `{contexto_extraido}`: Reemplazado por el árbol/contenido generado (CLI) o el texto pegado (GUI).
*   `{ruta_destino}`: Reemplazado por la `RUTA_RELATIVA_NOTA` proporcionada.
*   `{etiqueta_jerarquica_1}`, `{etiqueta_jerarquica_2}`, ... `{etiqueta_jerarquica_5}`: Reemplazados por etiquetas generadas desde `RUTA_RELATIVA_NOTA` (e.g., `Asignaturas/Sistemas_Operativos` para `_1`, `Asignaturas` para `_2`, si la nota está en `Asignaturas/Sistemas_Operativos/Conceptos.md`).

### Ejemplos de Uso (CLI)

*   **Añadir tu bóveda principal:**
    ```bash
    python main.py --add-vault "Principal" "D:\Obsidian\MiBoveda"
    ```

*   **Listar bóvedas y plantillas:**
    ```bash
    python main.py --list-vaults --list-templates
    ```

*   **Generar prompt para nota (usando la bóveda 'Principal', plantilla predefinida 'Generar Nota Simple', contexto de la carpeta 'Ideas', guardando el prompt):**
    ```bash
    python main.py --select-vault "Principal" --template "Generar Nota Simple" --target "Ideas" --output-note-path "Ideas/Nueva Idea Sobre AI.md" --output prompt_idea_ai.txt
    ```

*   **Generar resumen usando la última bóveda, plantilla de archivo, SÓLO contenido de notas diarias:**
    ```bash
    # Asumiendo que 'templates/mi_plantilla_resumen.txt' existe
    python main.py --template "templates/mi_plantilla_resumen.txt" --output-mode content --target "Notas Diarias/2024-01" --output-note-path "Resumen Enero 2024.md"
    ```
*   **Selección interactiva (si no se especifica bóveda ni plantilla):**
    ```bash
    python main.py --target "Asignaturas/Cálculo" --output-note-path "Asignaturas/Cálculo/Conceptos/NuevoConcepto.md"
    # El script preguntará qué bóveda y qué plantilla usar
    ```

## Uso (GUI)

Ejecuta la interfaz gráfica con Streamlit (asegúrate de haber instalado las dependencias con `pip install -r requirements.txt`):

```bash
streamlit run gui_streamlit.py
```