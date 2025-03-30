# Obsidian Context Builder

**Obsidian Context Builder** es una herramienta de Python con doble interfaz (CLI y GUI) diseñada para ayudarte a crear prompts para Modelos de Lenguaje Grandes (LLMs) usando información de tu bóveda de Obsidian.

*   **Modo CLI (Línea de Comandos):** Extrae automáticamente la estructura de directorios y/o el contenido de archivos específicos de tu bóveda basándose en las rutas objetivo que proporciones, los formatea y los inyecta en plantillas de prompt predefinidas. Ideal para análisis contextual automatizado y scripting.
*   **Modo GUI (Interfaz Gráfica - Streamlit):** Ofrece una interfaz visual para seleccionar plantillas y gestionar bóvedas guardadas. El usuario identifica los archivos/carpetas relevantes en su explorador y **pega sus rutas** (relativas a la bóveda o absolutas, ej: `Asignaturas/Cálculo/Funciones` o `D:\Obsidian\Y1Q2\Notas Diarias\2024-01-15.md`) en un área de texto. La herramienta **genera automáticamente el contexto** (árbol y/o contenido) a partir de esas rutas y lo inyecta en la plantilla seleccionada. Ideal para un flujo de trabajo más interactivo y visual.

Esto te permite generar rápidamente prompts contextualizados para tareas como:

*   Resumir notas existentes.
*   Generar contenido para nuevas notas basadas en contexto circundante.
*   Identificar conexiones entre temas.
*   Crear preguntas de estudio sobre un conjunto de notas.
*   Enriquecer notas existentes con más información o enlaces.
*   ¡Y mucho más!

## ¿Por Qué Usar Obsidian Context Builder?

Preparar manualmente el contexto para un LLM copiando estructuras de directorios (quizás usando herramientas como `tree` o scripts personalizados) y pegando el contenido de múltiples archivos en un prompt puede ser **extremadamente tedioso, lento y propenso a errores**, especialmente cuando se trabaja con contextos grandes o se necesita generar prompts frecuentemente.

**Obsidian Context Builder soluciona estos problemas:**

*   **Automatiza la Recolección:** La CLI extrae y formatea automáticamente la estructura y el contenido basándose en simples rutas objetivo.
*   **Simplifica la Selección (GUI):** La GUI permite pegar fácilmente las rutas relevantes, y la herramienta se encarga del resto.
*   **Inyección Inteligente:** Inserta el contexto generado y otros metadatos (como la ruta destino o etiquetas jerárquicas) en los lugares correctos de tus plantillas reutilizables usando placeholders.
*   **Consistencia:** Asegura que el contexto siempre tenga el mismo formato (separadores, numeración de líneas).
*   **Ahorro de Tiempo:** Reduce drásticamente el tiempo dedicado a la preparación manual de prompts.
*   **Menos Errores:** Minimiza los errores de copiado y pegado.
*   **Gestión Centralizada:** Permite guardar y reutilizar rutas de bóvedas y plantillas de prompts.

En resumen, agiliza y estandariza el proceso de creación de prompts ricos en contexto para interactuar con LLMs sobre tu base de conocimiento en Obsidian.

## Características Principales

*   **Doble Interfaz:** Script de línea de comandos (`main.py`) y aplicación web local (`gui_streamlit.py`).
*   **Gestión de Bóvedas (CLI & GUI):** Guarda y selecciona fácilmente entre múltiples rutas de bóvedas. Recuerda la última utilizada.
*   **Gestión de Plantillas (CLI & GUI):** Carga plantillas desde archivos `.txt` ubicados en la carpeta `templates/`. Permite listar las disponibles. *(Nota: Las plantillas predefinidas se eliminaron en favor de archivos externos).*
*   **Contexto Automático (Basado en Rutas):**
    *   **Exploración Flexible (CLI & GUI):** Recorre tu bóveda seleccionada a partir de las rutas objetivo proporcionadas.
    *   **Filtrado Preciso (`--target`/Input GUI, `--ext`):** Selecciona el contexto basándote en directorios/archivos específicos y extensiones.
    *   **Extracción de Contexto:** Genera automáticamente la estructura de directorios (`tree`) y/o el contenido formateado (`content`) de los elementos especificados en las rutas objetivo.
    *   **Modo de Salida Configurable (`--output-mode`):** Elige qué incluir (`tree`, `content`, `both`).
*   **Inyección en Plantillas:** Reemplaza placeholders (`{contexto_extraido}`, `{ruta_destino}`, `{etiqueta_jerarquica_N}`) en la plantilla seleccionada.
*   **Etiquetas Jerárquicas:** Genera automáticamente etiquetas basadas en la ruta de la nota destino.
*   **Salida Flexible:** Imprime el prompt final o guárdalo en un archivo.

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

*   `--add-vault NOMBRE RUTA`: Añade o actualiza una bóveda.
*   `--remove-vault NOMBRE`: Elimina una bóveda guardada.
*   `--list-vaults`: Muestra las bóvedas guardadas.

**Gestión de Plantillas:** (Se ejecuta y el script termina)

*   `--list-templates`: Muestra las plantillas disponibles en `/templates`.

**Generación de Prompt:** (Requieren que una bóveda sea seleccionable)

*   `--select-vault NOMBRE`: (Opcional) Especifica qué bóveda usar. Si no, usa la última o pregunta.
*   `--target RUTA_RELATIVA`: (Opcional) Ruta relativa (a la bóveda) para incluir. Repetir para múltiples. Default: toda la bóveda.
*   `--ext .EXTENSION`: (Opcional) Extensión a incluir. Repetir para múltiples. Default: `.md`.
*   `--template NOMBRE_ARCHIVO_O_RUTA`: (Opcional) Nombre de plantilla de `/templates` (ej: "Archivo: GenerarNota") o ruta a un archivo `.txt`. Si no, pregunta.
*   `--output-mode {tree,content,both}`: (Opcional) Qué contexto generar. Default: `both`.
*   `--output-note-path RUTA_RELATIVA_NOTA`: (**Requerido**) Ruta relativa *dentro* de la bóveda para la nota objetivo.
*   `--output RUTA_ARCHIVO_SALIDA`: (Opcional) Guarda el prompt en un archivo.

**Otros:**

*   `--version`: Muestra la versión.
*   `-h`, `--help`: Muestra ayuda detallada.

### Placeholders en Plantillas

*   `{contexto_extraido}`: Reemplazado por el árbol/contenido generado automáticamente.
*   `{ruta_destino}`: Reemplazado por la `RUTA_RELATIVA_NOTA`.
*   `{etiqueta_jerarquica_1}`, ..., `{etiqueta_jerarquica_5}`: Etiquetas generadas desde `RUTA_RELATIVA_NOTA`.

### Ejemplos de Uso (CLI)

*   **Añadir bóveda:**
    ```bash
    python main.py --add-vault "Estudios" "D:\Obsidian\Estudios"
    ```
*   **Listar:**
    ```bash
    python main.py --list-vaults --list-templates
    ```
*   **Generar prompt para nota (usando bóveda 'Estudios', plantilla de archivo 'EnriquecerNota', contexto de carpeta 'Asignaturas/SO', guardando):**
    ```bash
    python main.py --select-vault "Estudios" --template "Archivo: EnriquecerNota" --target "Asignaturas/Sistemas Operativos" --output-note-path "Asignaturas/Sistemas Operativos/Conceptos/Multiprogramacion.md" --output prompt_enriquecer_multi.txt
    ```
*   **Usar última bóveda, plantilla 'GenerarPreguntas', SÓLO contenido de una nota:**
    ```bash
    python main.py --template "Archivo: GenerarPreguntas" --output-mode content --target "Asignaturas/Cálculo/Teoremas Clave/Teorema de Bolzano.md" --output-note-path "Repasos/Preguntas_Bolzano.md"
    ```

## Uso (GUI)

Ejecuta la interfaz gráfica con Streamlit:

```bash
streamlit run gui_streamlit.py
```

La interfaz te permitirá:

1.  **Seleccionar Bóveda:** Elige una bóveda guardada previamente.
2.  **Seleccionar Plantilla:** Elige una plantilla de la carpeta `/templates`.
3.  **Pegar Rutas Objetivo:** En el área de texto, pega las rutas (una por línea, relativas o absolutas) de las carpetas/archivos que quieres usar como contexto. Si dejas esto vacío, se usará toda la bóveda seleccionada.
4.  **Configurar Opciones:** Selecciona las extensiones a incluir y el modo de salida del contexto (árbol, contenido o ambos).
5.  **Especificar Ruta Destino:** Indica la ruta relativa donde se ubicaría la nota a generar/modificar (necesario para placeholders).
6.  **Generar:** Pulsa el botón. La herramienta generará el contexto basado en las rutas y lo inyectará en la plantilla.
7.  **Ver/Guardar:** Revisa el prompt resultante y cópialo o guárdalo en un archivo opcionalmente.
8.  **(Opcional) Gestionar Bóvedas:** Añade o elimina bóvedas guardadas.

## Estructura del Proyecto

```
obsidian-context-builder/
│
├── main.py             # Punto de entrada CLI
├── gui_streamlit.py    # Punto de entrada GUI
├── config_handler.py   # Gestión de config (bóvedas, etc.)
├── file_handler.py     # Búsqueda y lectura de archivos
├── tree_generator.py   # Generación de estructura de árbol
├── formatter.py        # Formateo de contenido de archivos
├── prompt_handler.py   # Carga/gestión de plantillas, inyección
│
├── templates/          # CARPETA PARA PLANTILLAS DE USUARIO (.txt)
│   └── GenerarNota.txt # Ejemplo (puedes añadir las otras aquí)
│   └── ...             # Otros archivos .txt de plantillas
│
├── obsidian_context_builder_config.json # Archivo de config (auto-generado)
├── README.md           # Esta documentación
├── requirements.txt    # Dependencias (streamlit)
└── .gitignore          # Ignora __pycache__
```