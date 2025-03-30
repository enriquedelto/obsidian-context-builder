# Obsidian Context Builder
... (introducción existente) ...

## Características Principales

*   **Gestión de Bóvedas:** Guarda y selecciona fácilmente entre múltiples rutas de bóvedas. Recuerda la última utilizada.
*   **Gestión de Plantillas:** Utiliza plantillas predefinidas para tareas comunes o carga las tuyas desde archivos `.txt`.
*   **Exploración Flexible:** ... (resto de características existentes) ...
*   ...

## Requisitos

*   **Python:** Versión 3.7 o superior.
*   **Bibliotecas Externas:**
    *   `streamlit` (solo para la interfaz gráfica `gui_streamlit.py`)

## Instalación

1.  **Clona el repositorio** ... (igual) ...
2.  (Opcional pero recomendado para GUI) Crea y activa un entorno virtual: ... (igual) ...
3.  (Opcional pero recomendado para GUI) Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```

## Uso (CLI)

El script se ejecuta desde la línea de comandos usando `python main.py`.

```bash
python main.py [opciones_gestion] [opciones_generacion]
```

### Argumentos de Línea de Comandos

**Gestión de Bóvedas:**

*   `--select-vault NOMBRE`: Especifica qué bóveda guardada usar. Si no se usa, se intenta la última usada o se pide interactivamente.
*   `--add-vault NOMBRE RUTA`: Añade o actualiza una bóveda con un nombre corto y su ruta completa.
*   `--remove-vault NOMBRE`: Elimina una bóveda guardada por su nombre.
*   `--list-vaults`: Muestra las bóvedas guardadas y sale.

**Generación de Prompt:** (Se usan *después* de seleccionar una bóveda)

*   `--target RUTA_RELATIVA`: (Opcional) Ruta relativa para incluir. Repetir para múltiples. Default: toda la bóveda seleccionada.
*   `--ext .EXTENSION`: (Opcional) Extensión a incluir. Repetir para múltiples. Default: `.md`.
*   `--template NOMBRE_O_RUTA`: (Requerido si no se selecciona interactivamente) Nombre de una plantilla predefinida/guardada (ver `--list-templates`) o ruta a un archivo `.txt`.
*   `--list-templates`: Muestra las plantillas disponibles y sale.
*   `--output-mode {tree,content,both}`: (Opcional) Qué incluir en `{contexto_extraido}`. Default: `both`.
*   `--output-note-path RUTA_RELATIVA_NOTA`: (Requerido para generar) Ruta relativa *dentro* de la bóveda donde se crearía/ubicaría la nota objetivo.
*   `--output RUTA_ARCHIVO_SALIDA`: (Opcional) Guarda el prompt final en un archivo. Default: imprime en consola.

**Otros:**

*   `--version`: Muestra la versión.
*   `-h`, `--help`: Muestra ayuda detallada.

... (Placeholders - sin cambios) ...

### Ejemplos de Uso (CLI)

*   **Añadir tu bóveda principal:**
    ```bash
    python main.py --add-vault "Principal" "D:\Obsidian\MiBoveda"
    ```

*   **Listar bóvedas y plantillas:**
    ```bash
    python main.py --list-vaults --list-templates
    ```

*   **Generar nota usando la bóveda 'Principal', plantilla 'Generar Nota Simple', contexto de 'Ideas', guardando el prompt:**
    ```bash
    python main.py --select-vault "Principal" --template "Generar Nota Simple" --target "Ideas" --output-note-path "Ideas/Nueva Idea Sobre AI.md" --output prompt_idea_ai.txt
    ```

*   **Usar la última bóveda (o seleccionar interactivamente), usar plantilla desde archivo, SÓLO contenido:**
    ```bash
    python main.py --template "templates/mi_plantilla_resumen.txt" --output-mode content --target "Notas Diarias/2024-01" --output-note-path "Resumen Enero 2024.md"
    ```

## Uso (GUI)

Ejecuta la interfaz gráfica con Streamlit:

```bash
streamlit run gui_streamlit.py
```

La interfaz te permitirá:
*   Seleccionar una bóveda guardada de un desplegable.
*   Gestionar tus bóvedas (añadir/eliminar) en una sección expandible.
*   Seleccionar una plantilla (predeterminada o de tu carpeta `templates/`) de un desplegable.
*   Configurar las rutas objetivo, extensiones, modo de contexto, etc.
*   Generar el prompt y verlo en pantalla.
*   Opcionalmente, especificar un archivo para guardar el prompt generado.

... (Estructura del proyecto - actualizar si es necesario) ...