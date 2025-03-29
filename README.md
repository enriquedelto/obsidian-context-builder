# Obsidian Context Builder

**Obsidian Context Builder** es un script de Python diseñado para automatizar la creación de prompts para Modelos de Lenguaje Grandes (LLMs). Extrae información específica (estructura de directorios y/o contenido de archivos) de tu bóveda de Obsidian, la formatea y la inyecta en plantillas de prompt predefinidas.

Esto te permite generar rápidamente prompts contextualizados para tareas como:

*   Resumir notas existentes.
*   Generar contenido para nuevas notas basadas en el contexto circundante.
*   Identificar conexiones entre temas.
*   Crear preguntas de estudio sobre un conjunto de notas.
*   ¡Y mucho más!

## Características Principales

*   **Exploración Flexible:** Recorre tu bóveda de Obsidian (o cualquier directorio).
*   **Filtrado Preciso:** Selecciona el contexto basándote en:
    *   **Directorios/Archivos Específicos (`--target`):** Enfoca el análisis solo en las partes relevantes de tu bóveda.
    *   **Extensiones de Archivo (`--ext`):** Extrae información de archivos `.md`, `.canvas`, o cualquier otra extensión que necesites (por defecto: `.md`).
*   **Extracción de Contexto:** Genera automáticamente:
    *   Una representación visual de la **estructura de directorios** (`tree`).
    *   El **contenido formateado** de los archivos seleccionados, con numeración de líneas.
*   **Modo de Salida Configurable (`--output-mode`):** Elige qué incluir en el contexto inyectado: solo la estructura (`tree`), solo el contenido (`content`), o ambos (`both`).
*   **Inyección en Plantillas:** Carga tus plantillas de prompt (desde un archivo o directamente en la línea de comandos) y reemplaza placeholders específicos con la información extraída.
*   **Placeholders Múltiples:** Soporta varios placeholders para inyectar no solo el contexto principal, sino también metadatos como la ruta de la nota destino o etiquetas jerárquicas derivadas.
*   **Salida Flexible:** Imprime el prompt final en la consola o guárdalo directamente en un archivo (`--output`).

## Requisitos

*   **Python:** Versión 3.7 o superior.
*   **Bibliotecas Externas:** Actualmente no se requieren bibliotecas externas (solo la biblioteca estándar de Python).

## Instalación

1.  **Clona el repositorio** (o descarga los archivos):
    ```bash
    git clone https://github.com/enriquedelto/obsidian-context-builder.git # Reemplaza con tu URL real si es diferente
    cd obsidian-context-builder
    ```
2.  (Opcional) Crea y activa un entorno virtual:
    ```bash
    python -m venv venv
    source venv/bin/activate # En Linux/macOS
    # venv\Scripts\activate # En Windows
    ```

## Uso Básico

El script se ejecuta desde la línea de comandos usando `python main.py`. La estructura general es:

```bash
python main.py --vault <ruta_a_tu_boveda> [opciones] <opcion_de_plantilla>
```

## Argumentos de Línea de Comandos

*   `--vault PATH`: **(Obligatorio)** Ruta al directorio raíz de tu bóveda de Obsidian.
*   `--target RUTA_RELATIVA`: (Opcional) Ruta relativa dentro de la bóveda para incluir en el contexto. Puedes usar este argumento varias veces para incluir múltiples carpetas o archivos. Si no se especifica, se procesa toda la bóveda.
*   `--ext .EXTENSION`: (Opcional) Extensión de archivo a incluir (ej: `.md`, `.canvas`). Puedes usarlo varias veces. Si no se especifica, por defecto es `.md`.
*   `--prompt-template "PLANTILLA"`: (Obligatorio, si no usas `--prompt-file`) La plantilla del prompt como una cadena de texto. Debe contener los placeholders que el script reemplazará.
*   `--prompt-file RUTA_ARCHIVO_PLANTILLA`: (Obligatorio, si no usas `--prompt-template`) Ruta a un archivo de texto (`.txt`) que contiene la plantilla del prompt.
*   `--output-mode {tree,content,both}`: (Opcional) Define qué incluir en el placeholder `{contexto_extraido}`:
    *   `tree`: Solo la estructura del árbol de directorios/archivos.
    *   `content`: Solo el contenido formateado de los archivos.
    *   `both`: Estructura del árbol seguida del contenido (valor por defecto).
*   `--output-note-path RUTA_RELATIVA_NOTA`: (Obligatorio para ciertas plantillas, como la de creación de notas) Ruta relativa *dentro* de la bóveda donde se crearía/ubicaría la nota objetivo. Esta ruta se usa para:
    *   Informar al LLM sobre el tema/ubicación de la nota a generar.
    *   Generar automáticamente etiquetas jerárquicas para inyectar en la plantilla.
*   `--output RUTA_ARCHIVO_SALIDA`: (Opcional) Ruta al archivo donde se guardará el prompt final generado. Si no se especifica, el prompt se imprimirá en la consola.
*   `--version`: Muestra la versión del script.
*   `-h`, `--help`: Muestra este mensaje de ayuda y los detalles de los argumentos.

## Placeholders en Plantillas

Las plantillas (`--prompt-template` o `--prompt-file`) deben contener "placeholders" (marcadores de texto) que el script reemplazará con la información generada. Los placeholders estándar son:

*   `{contexto_extraido}`: Será reemplazado por la estructura del árbol, el contenido de los archivos, o ambos, según lo especificado por `--output-mode`.
*   `{ruta_destino}`: Será reemplazado por la ruta relativa proporcionada en `--output-note-path`.
*   `{etiqueta_jerarquica_1}`, `{etiqueta_jerarquica_2}`, `{etiqueta_jerarquica_3}`, ... : Serán reemplazados por las etiquetas jerárquicas extraídas de la ruta `--output-note-path`. El script intenta rellenar tantos placeholders de este tipo como encuentre definidos en `DEFAULT_PLACEHOLDERS` (en `main.py`) y como niveles de directorio existan en la ruta. La etiqueta `_1` suele ser la más específica (el directorio padre directo), `_2` la superior, etc. (el orden exacto depende de la implementación de `generate_hierarchical_tags`).

Puedes definir tus propias plantillas usando estos placeholders.

## Ejemplos de Uso

*   **Generar prompt para crear una nueva nota en `Asignaturas/SO/ConceptosClave.md`, usando contexto de `Asignaturas/SO` y plantilla de archivo:**
    ```bash
    python main.py \
        --vault "/ruta/completa/a/mi/boveda" \
        --target "Asignaturas/Sistemas Operativos" \
        --output-note-path "Asignaturas/Sistemas Operativos/ConceptosClave.md" \
        --prompt-file "templates/crear_nota_template.txt" \
        --output prompt_para_crear_ConceptosClave.txt
    ```

*   **Generar prompt para resumir notas, incluyendo SÓLO la estructura del árbol de la carpeta `Proyectos`:**
    ```bash
    python main.py \
        --vault "/ruta/completa/a/mi/boveda" \
        --target "Proyectos" \
        --output-mode tree \
        --output-note-path "ResumenProyectos.md" \
        --prompt-template "Resume la organización de la carpeta Proyectos basada en esta estructura: {contexto_extraido}"
    ```
    *(Nota: `--output-note-path` todavía se necesita aquí si la plantilla usa `{ruta_destino}` o etiquetas, aunque el contexto sea solo el árbol)*

*   **Generar prompt con SÓLO el contenido de dos notas diarias específicas:**
    ```bash
    python main.py \
        --vault "/ruta/completa/a/mi/boveda" \
        --target "Notas Diarias/2023-11-01.md" \
        --target "Notas Diarias/2023-11-02.md" \
        --ext .md \
        --output-mode content \
        --output-note-path "ResumenNoviembreInicio.md" \
        --prompt-template "Resume los eventos principales de estos días: {contexto_extraido}" \
        --output prompt_resumen_diario.txt
    ```

*   **Procesar toda la bóveda (archivos .md), contexto completo, usando plantilla inline:**
    ```bash
    python main.py \
        --vault "/ruta/completa/a/mi/boveda" \
        --output-note-path "AnalisisGlobal.md" \
        --prompt-template "Analiza las conexiones principales en mi bóveda: {contexto_extraido}. La nota se llamaría {ruta_destino}."
    ```

## Estructura del Proyecto

```
obsidian-context-builder/
│
├── main.py             # Punto de entrada principal, maneja CLI
├── file_handler.py     # Encuentra y lee archivos
├── tree_generator.py   # Genera la estructura de árbol
├── formatter.py        # Formatea el contenido de archivos
├── prompt_handler.py   # Carga plantillas e inyecta contexto
│
├── templates/          # Carpeta opcional para guardar plantillas
│   └── crear_nota_template.txt # Ejemplo
│
├── README.md           # Esta documentación
└── requirements.txt    # Dependencias (actualmente vacío)
```
