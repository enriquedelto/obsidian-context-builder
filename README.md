# Obsidian Context Builder

**Obsidian Context Builder** es una herramienta de Python con doble interfaz (CLI y GUI) diseñada para ayudarte a crear prompts para Modelos de Lenguaje Grandes (LLMs) usando información de tu bóveda de Obsidian.

*   **Modo CLI (Línea de Comandos):** Extrae automáticamente la estructura de directorios y/o el contenido de archivos específicos de tu bóveda basándose en las rutas objetivo que proporciones, los formatea y los inyecta en plantillas de prompt predefinidas. Ideal para análisis contextual automatizado y scripting.
*   **Modo GUI (Interfaz Gráfica - Streamlit):** Ofrece una interfaz visual para seleccionar plantillas (categorizadas por acción), gestionar bóvedas guardadas (o usar una ruta manual), y configurar opciones de contexto. El usuario identifica los archivos/carpetas relevantes y pega sus rutas (relativas o absolutas) en un área de texto. La herramienta genera automáticamente el contexto (árbol y/o contenido) y lo inyecta en la plantilla seleccionada. Ideal para un flujo de trabajo más interactivo y visual.

Esto te permite generar rápidamente prompts contextualizados para tareas como:

*   Resumir notas existentes.
*   Generar contenido para nuevas notas basadas en contexto circundante.
*   Identificar conexiones entre temas.
*   Crear preguntas de estudio sobre un conjunto de notas.
*   Enriquecer notas existentes con más información o enlaces.
*   Analizar la estructura y contenido de tu bóveda.
*   ¡Y mucho más!

## ¿Por Qué Usar Obsidian Context Builder?

Preparar manualmente el contexto para un LLM copiando estructuras de directorios y pegando contenido de múltiples archivos puede ser tedioso, lento y propenso a errores.

**Obsidian Context Builder soluciona estos problemas:**

*   **Automatiza la Recolección:** Extrae y formatea automáticamente la estructura y el contenido basándose en rutas objetivo y filtros de extensión.
*   **Simplifica la Selección:** La GUI permite pegar fácilmente rutas relevantes o usar bóvedas guardadas. La selección de plantillas está categorizada.
*   **Inyección Inteligente:** Inserta el contexto generado y metadatos (ruta destino, etiquetas) en placeholders de tus plantillas reutilizables.
*   **Consistencia:** Asegura un formato uniforme para el contexto.
*   **Ahorro de Tiempo:** Reduce drásticamente la preparación manual de prompts.
*   **Menos Errores:** Minimiza errores de copiado y pegado.
*   **Gestión Centralizada:** Permite guardar y reutilizar rutas de bóvedas.

## Características Principales

*   **Doble Interfaz:** Línea de comandos (`main.py`) y aplicación web local (`gui_streamlit.py`).
*   **Gestión de Bóvedas (CLI & GUI):**
    *   Guarda y selecciona bóvedas por nombre (`--add-vault`, `--select-vault`, GUI).
    *   Usa una ruta de bóveda directamente sin guardar (`--vault-path`, GUI Manual).
    *   Recuerda la última bóveda guardada utilizada.
*   **Gestión de Plantillas (CLI & GUI):**
    *   Carga plantillas `.txt` desde la carpeta `/templates`.
    *   Permite listar las disponibles (`--list-templates`, GUI categorizada).
*   **Contexto Automático (Basado en Rutas):**
    *   **Exploración Flexible:** Recorre la bóveda a partir de rutas objetivo (`--target` / Input GUI). Si no hay targets, usa toda la bóveda.
    *   **Filtrado Preciso:** Selecciona contexto por:
        *   Directorios/archivos específicos (`--target` / Input GUI).
        *   Extensiones a **incluir** (`--ext` / Input GUI).
        *   Extensiones a **excluir** (`--exclude-ext` / Input GUI).
    *   **Extracción de Contexto:** Genera estructura de directorios (`tree`) y/o contenido formateado (`content`).
    *   **Modo Configurable (`--output-mode`):** Elige qué incluir (`tree`, `content`, `both`).
*   **Inyección en Plantillas:** Reemplaza placeholders (`{contexto_extraido}`, `{ruta_destino}`, `{etiqueta_jerarquica_N}`) en la plantilla.
*   **Etiquetas Jerárquicas:** Genera etiquetas (`#tag/subtag`) automáticamente si se proporciona `--output-note-path`.
*   **Salida Flexible:** Imprime el prompt final o guárdalo en archivo (`--output`).

## Requisitos

*   Python: 3.7+
*   Bibliotecas: `streamlit` (para GUI - ver `requirements.txt`)

## Instalación

1.  **Clona:** `git clone <url_repo>` y `cd obsidian-context-builder`
2.  **(Recomendado) Entorno Virtual:** `python -m venv venv` y actívalo (`source venv/bin/activate` o `venv\Scripts\activate`).
3.  **Instala Dependencias:** `pip install -r requirements.txt`

## Uso (CLI)

```bash
python main.py [opciones...]
```

### Argumentos de Línea de Comandos

**Selección de Bóveda (Elige UNA):**

*   `--select-vault NOMBRE`: Usa una bóveda guardada por su nombre.
*   `--vault-path RUTA_DIRECTORIO`: Usa una bóveda directamente por su ruta (no se guarda).
*   (Si no se especifica ninguna, usa la última guardada o pide selección interactiva)

**Gestión (Se ejecutan y el script termina):**

*   `--add-vault NOMBRE RUTA`: Añade o actualiza una bóveda guardada.
*   `--remove-vault NOMBRE`: Elimina una bóveda guardada.
*   `--list-vaults`: Muestra bóvedas guardadas.
*   `--list-templates`: Muestra plantillas disponibles en /templates.

**Generación de Prompt:**

*   `--target RUTA_RELATIVA`: Ruta (relativa a bóveda) a incluir. Repetir para múltiples. Default: toda la bóveda.
*   `--ext .EXTENSION`: Extensión a incluir. Repetir para múltiples. Default: .md.
*   `--exclude-ext .EXTENSION`: Extensión a excluir. Repetir para múltiples. Default: ninguna.
*   `--template NOMBRE_O_RUTA`: Nombre de plantilla (Archivo:Nombre) o ruta a .txt. Si no, pregunta.
*   `--output-mode {tree,content,both}`: Qué contexto generar. Default: both.
*   `--output-note-path RUTA_RELATIVA`: (Opcional) Ruta relativa para la nota objetivo. Necesaria para placeholders `{ruta_destino}` y `{etiqueta_jerarquica_N}`.
*   `--output RUTA_ARCHIVO_SALIDA`: (Opcional) Guarda el prompt en un archivo.

**Otros:**

*   `--version`: Muestra la versión.
*   `-h, --help`: Muestra ayuda detallada.

### Placeholders en Plantillas

*   `{contexto_extraido}`: Reemplazado por el árbol/contenido generado.
*   `{ruta_destino}`: Reemplazado por `--output-note-path` (si se proporciona).
*   `{etiqueta_jerarquica_1...5}`: Etiquetas generadas desde `--output-note-path` (si se proporciona).

### Ejemplos de Uso (CLI)

*   Usar bóveda guardada 'Estudios', plantilla 'EnriquecerNota', contexto de carpeta 'SO', nota objetivo, guardar prompt:
    ```bash
    python main.py --select-vault "Estudios" --template "Archivo:EnriquecerNota" --target "Asignaturas/Sistemas Operativos" --output-note-path "Asignaturas/Sistemas Operativos/Conceptos/Multiprogramacion.md" --output prompt_enriquecer.txt
    ```

*   Usar ruta directa, plantilla 'GenerarPreguntas', solo contenido de una nota, excluir PDFs:
    ```bash
    python main.py --vault-path "D:\Obsidian\Personal" --template "Archivo:GenerarPreguntas" --output-mode content --target "AreaX/NotaImportante.md" --exclude-ext .pdf --output-note-path "Repasos/Preguntas_AreaX.md"
    ```

*   Analizar estructura de carpeta (sin nota objetivo), usando última bóveda:
    ```bash
    python main.py --template "Archivo:AnalizarContenido" --target "Proyectos/ProyectoZ" --output-mode tree
    ```

## Uso (GUI)

Ejecuta la interfaz gráfica con Streamlit:

```bash
streamlit run gui_streamlit.py
```

La interfaz te permitirá:

1.  **Seleccionar Bóveda:** Elegir entre "Guardada" (menú desplegable) o "Manual" (campo de texto para ruta).
2.  **Seleccionar Plantilla:** Elegir primero una Categoría y luego la Plantilla Específica de esa categoría.
3.  **Pegar Rutas Objetivo:** Área de texto para rutas (relativas/absolutas) a incluir. Vacío = toda la bóveda.
4.  **Configurar Opciones:**
    *   Extensiones a incluir.
    *   Extensiones a excluir.
    *   Modo de salida del contexto (tree, content, both).
5.  **Especificar Ruta Destino (Opcional):** Ruta relativa para nota objetivo (necesaria para placeholders relacionados).
6.  **Generar:** Pulsa el botón.
7.  **Ver/Guardar:** Revisa el prompt y cópialo o guárdalo en archivo.
8.  **(Opcional) Gestionar Bóvedas:** Añade/elimina bóvedas guardadas desde el expander.

## Estructura del Proyecto

```
obsidian-context-builder/
│
├── main.py             # Punto de entrada CLI
├── gui_streamlit.py    # Punto de entrada GUI
├── core.py             # <<< Lógica central compartida
│
├── config_handler.py   # Gestión config JSON
├── file_handler.py     # Búsqueda/lectura archivos
├── tree_generator.py   # Generación árbol
├── formatter.py        # Formateo contenido
├── prompt_handler.py   # Carga/inyección plantillas
│
├── templates/          # Carpeta para plantillas .txt
│   ├── AnalizarContenido.txt
│   └── ...
│
├── obsidian_context_builder_config.json # Config auto-generada
├── README.md           # Esta documentación
├── requirements.txt    # Dependencias
└── .gitignore          # Ignora __pycache__
```