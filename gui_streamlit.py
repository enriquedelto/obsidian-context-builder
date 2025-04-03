# gui_streamlit.py
import streamlit as st
from pathlib import Path
import sys
import traceback
from typing import Optional, Dict, Any, List, Set, Tuple

# ... (otros imports sin cambios: file_handler, tree_generator, etc.)
import prompt_handler
import config_handler
try:
    from core import generate_prompt_core, DEFAULT_PLACEHOLDERS, generate_hierarchical_tags, DEFAULT_EXTENSIONS
except ImportError as e:
    st.error(f"Error crítico al importar desde core: {e}. Asegúrate que core.py existe.")
    st.stop()

# --- CONFIGURACIÓN DE PÁGINA Y TÍTULO ---
st.set_page_config(layout="wide")
st.title("Obsidian Context Builder 🔨")
st.caption("Genera prompts para LLMs usando el contexto de tu bóveda Obsidian.")

# --- Funciones Auxiliares ---
def display_template_content(template_name: Optional[str]):
    # ... (sin cambios) ...
    content = ""
    error_msg = None
    if template_name:
        try: content = prompt_handler.load_template(template_name)
        except ValueError as e: error_msg = f"Error: {e}"
        except Exception as e: error_msg = f"Error inesperado al cargar plantilla '{template_name}': {e}"
    if error_msg: st.error(error_msg)
    st.text_area( "Contenido Plantilla Seleccionada", content, height=150, disabled=True, key="template_preview_area_routes" )

def validate_and_get_targets(target_input_str: str, vault_path: Path) -> Tuple[List[str], List[str]]:
    # ... (sin cambios) ...
    raw_targets = [p.strip().strip('"') for p in target_input_str.splitlines() if p.strip()]
    valid_relative_targets = []; invalid_targets = []
    vault_path_resolved = vault_path.resolve()
    for raw_target in raw_targets:
        try:
            target_path = Path(raw_target)
            if not target_path.is_absolute(): abs_path = (vault_path_resolved / target_path).resolve()
            else: abs_path = target_path.resolve()
            if abs_path.exists() and abs_path.is_relative_to(vault_path_resolved):
                 relative_path_str = abs_path.relative_to(vault_path_resolved).as_posix()
                 valid_relative_targets.append(relative_path_str)
            else: invalid_targets.append(raw_target)
        except Exception as e: invalid_targets.append(raw_target); print(f"Error validando target '{raw_target}': {e}", file=sys.stderr)
    return valid_relative_targets, invalid_targets


# <<< Mapeo de Plantillas a Categorías sin cambios >>>
TEMPLATE_CATEGORIES = {
    "AnalizarContenido":        "🔍 Análisis", "ResumenConceptosClave":    "🔍 Análisis",
    "ValidarRigorAcademico":    "🔍 Análisis", "IdentificarNotasHuerfanas":"🔍 Análisis",
    "GenerarNota":              "✨ Creación", "GenerarMOC":               "✨ Creación",
    "EnriquecerNota":           "📝 Mejora",
    "MejorarEnlaces":           "🔗 Enlaces", "SugerirEnlacesEntrantes":  "🔗 Enlaces",
    "ReorganizarCarpeta":       "🗂️ Organización (Scripts)", "GenerarScriptCreacionNotas":"🗂️ Organización (Scripts)",
    "GenerarPreguntas":         "🎓 Utilidades",
}
DEFAULT_CATEGORY = "❓ Sin Categoría"

# --- Función auxiliar para obtener detalles de plantillas categorizadas ---
def get_categorized_templates(available_templates: Dict[str, str]) -> Tuple[List[str], Dict[str, List[Dict[str, str]]]]:
    """
    Procesa las plantillas disponibles y devuelve una lista ordenada de categorías
    y un diccionario de categorías a listas de detalles de plantillas.
    """
    category_map: Dict[str, List[Dict[str, str]]] = {} # category -> list of {"key": ..., "stem": ...}
    for key, _ in available_templates.items():
        if key.startswith("Archivo: "):
            stem = key.split("Archivo: ", 1)[1]
            category = TEMPLATE_CATEGORIES.get(stem, DEFAULT_CATEGORY)
            if category not in category_map:
                category_map[category] = []
            category_map[category].append({"key": key, "stem": stem})

    # Ordenar plantillas dentro de cada categoría por stem
    for category in category_map:
        category_map[category].sort(key=lambda x: x["stem"])

    # Ordenar categorías
    sorted_categories = sorted(category_map.keys())

    return sorted_categories, category_map

# --- Carga Inicial y Estado de Sesión ---
if 'config_loaded' not in st.session_state:
    print("--- Initializing Session State ---")
    st.session_state.config = config_handler.load_config()
    st.session_state.saved_vaults = config_handler.get_vaults()
    st.session_state.available_templates = prompt_handler.get_available_templates()
    last_vault_info = config_handler.get_last_vault()
    st.session_state.last_vault_name = last_vault_info[0] if last_vault_info else None

    st.session_state.setdefault('selected_vault_name', st.session_state.last_vault_name)
    st.session_state.setdefault('vault_selection_mode', "Guardada")
    st.session_state.setdefault('manual_vault_path', "")

    # --- Inicialización para plantillas y categorías ---
    st.session_state.setdefault('selected_category', None)
    st.session_state.setdefault('selected_template_name', None) # Guardará la key real "Archivo:Stem"

    # Determinar categoría y plantilla por defecto si es posible
    sorted_categories, category_map = get_categorized_templates(st.session_state.available_templates)
    if sorted_categories:
        # Intentar encontrar una plantilla por defecto preferida
        preferred_keys = ["Archivo: GenerarNota", "Archivo: EnriquecerNota"]
        default_template_key = None
        found_default = False
        for key in preferred_keys:
             if key in st.session_state.available_templates:
                 default_template_key = key
                 found_default = True
                 break
        # Si no se encuentra una preferida, usar la primera de la primera categoría
        if not found_default and category_map:
             first_category = sorted_categories[0]
             if category_map[first_category]:
                 default_template_key = category_map[first_category][0]['key']

        # Establecer estado inicial para categoría y plantilla
        if default_template_key:
            stem = default_template_key.split("Archivo: ", 1)[1]
            default_category = TEMPLATE_CATEGORIES.get(stem, DEFAULT_CATEGORY)
            st.session_state.selected_category = default_category
            st.session_state.selected_template_name = default_template_key
        else: # Si incluso la primera categoría está vacía (improbable)
            st.session_state.selected_category = sorted_categories[0] # Seleccionar primera categoría
            # selected_template_name se queda en None

    st.session_state.config_loaded = True
    print("--- Session State Initialized ---")


# --- Barra Lateral (Configuración Principal) ---
with st.sidebar:
    st.header("⚙️ Configuración Principal")

    # --- Selección de Modo Bóveda ---
    # ... (sin cambios) ...
    current_mode_index = 0
    if 'vault_selection_mode' in st.session_state and st.session_state.vault_selection_mode == "Manual": current_mode_index = 1
    st.session_state.vault_selection_mode = st.radio( "Fuente de la Bóveda:", options=["Guardada", "Manual"], key='vault_mode_radio', horizontal=True, index=current_mode_index )

    # --- Selección de Bóveda (Condicional) ---
    # ... (sin cambios) ...
    if st.session_state.vault_selection_mode == "Guardada":
        st.session_state.manual_vault_path = ""; vault_names = list(st.session_state.saved_vaults.keys()); current_selection_index = 0
        if st.session_state.selected_vault_name and st.session_state.selected_vault_name in vault_names:
             try: current_selection_index = vault_names.index(st.session_state.selected_vault_name)
             except ValueError: st.session_state.selected_vault_name = None
        selected_vault_name_from_selectbox = st.selectbox( "Selecciona Bóveda Guardada", options=vault_names, index=current_selection_index if vault_names else 0, key='sb_vault_select_ui', help="Selecciona bóveda guardada.", placeholder="Añade una bóveda abajo...", disabled=not vault_names )
        if vault_names and selected_vault_name_from_selectbox != st.session_state.get('selected_vault_name'):
             st.session_state.selected_vault_name = selected_vault_name_from_selectbox
    elif st.session_state.vault_selection_mode == "Manual":
        st.session_state.selected_vault_name = None
        st.session_state.manual_vault_path = st.text_input( "Introduce Ruta Completa a Bóveda", value=st.session_state.manual_vault_path, key='sb_manual_vault_path_input', placeholder="Ej: C:\\Obsidian\\TemporalVault", help="Pega ruta absoluta." ).strip()

    st.divider()

    # --- Selección de Plantilla en Dos Pasos ---
    st.subheader("Plantilla")
    sorted_categories, category_map = get_categorized_templates(st.session_state.available_templates)

    # 1. Selectbox de Categoría
    # Encontrar índice de la categoría seleccionada actualmente
    category_index = 0
    if st.session_state.selected_category and st.session_state.selected_category in sorted_categories:
        try: category_index = sorted_categories.index(st.session_state.selected_category)
        except ValueError: pass # Si la categoría guardada ya no existe

    selected_category = st.selectbox(
        "Categoría de Plantilla",
        options=sorted_categories,
        index=category_index,
        key='sb_category_select',
        help="Elige el tipo de tarea que quieres realizar.",
        placeholder="No hay plantillas disponibles...",
        disabled=not sorted_categories
    )

    # Actualizar estado si la categoría cambia y resetear plantilla seleccionada
    if selected_category != st.session_state.get('selected_category'):
        st.session_state.selected_category = selected_category
        st.session_state.selected_template_name = None # Resetear plantilla
        # Encontrar y seleccionar la primera plantilla de la nueva categoría automáticamente
        if selected_category in category_map and category_map[selected_category]:
            st.session_state.selected_template_name = category_map[selected_category][0]['key']
        st.rerun() # Necesario para que el segundo selectbox se actualice

    # 2. Selectbox de Plantilla (filtrado por categoría)
    filtered_templates_display = [] # Lista para mostrar ("📄 Stem")
    display_to_key_map = {} # Mapeo para recuperar la key real

    if st.session_state.selected_category and st.session_state.selected_category in category_map:
        for template_detail in category_map[st.session_state.selected_category]:
            display_name = f"📄 {template_detail['stem']}"
            filtered_templates_display.append(display_name)
            display_to_key_map[display_name] = template_detail['key']

    # Encontrar índice de la plantilla actual dentro de las filtradas
    template_index = 0
    current_template_key = st.session_state.get('selected_template_name')
    if current_template_key:
        # Necesitamos encontrar el display_name correspondiente a la key actual
        # para buscarlo en filtered_templates_display
        current_display_name = None
        for disp, key in display_to_key_map.items():
            if key == current_template_key:
                current_display_name = disp
                break
        if current_display_name and current_display_name in filtered_templates_display:
            try: template_index = filtered_templates_display.index(current_display_name)
            except ValueError: pass

    selected_template_display = st.selectbox(
        "Plantilla Específica",
        options=filtered_templates_display,
        index=template_index,
        key='sb_template_select',
        help="Selecciona la plantilla específica para la categoría elegida.",
        placeholder="Selecciona una categoría primero..." if not st.session_state.selected_category else "No hay plantillas en esta categoría...",
        disabled=not filtered_templates_display # Deshabilitar si no hay plantillas en la categoría
    )

    # Obtener la clave real y actualizar estado si cambia
    selected_template_key = display_to_key_map.get(selected_template_display)
    if selected_template_key and selected_template_key != st.session_state.get('selected_template_name'):
        st.session_state.selected_template_name = selected_template_key
        st.rerun() # Actualizar previsualización

    # --- Ruta Nota Destino ---
    st.divider()
    st.subheader("Nota Objetivo")
    output_note_path_str = st.text_input( "Ruta Relativa", placeholder="Carpeta/NotaObjetivo.md", key='input_output_note_path', help="Ruta DENTRO de la bóveda. Necesaria para placeholders {ruta_destino} y {etiqueta_jerarquica_N}." ).strip()


# --- Área Principal (Entrada y Salida) ---
# ... (sin cambios) ...
col1, col2 = st.columns(2)
with col1:
    st.subheader("🎯 Rutas de Contexto (Targets)")
    target_paths_input_str = st.text_area( "Pegar Rutas (1 por línea)", height=200, key='input_target_paths_manual', placeholder="Ejemplos:\nAsignaturas/Cálculo\nNotas Diarias/2024-01-15.md\n\n(Dejar vacío para usar toda la bóveda)", help="Pega rutas relativas/absolutas. Vacío = toda la bóveda." )
    st.subheader("⚙️ Opciones de Generación")
    extensions_str = st.text_input( "Extensiones a INCLUIR", " ".join(DEFAULT_EXTENSIONS), key='input_extensions_main', help="Separar con espacio (ej: .md .canvas)." )
    excluded_extensions_str = st.text_input(
        "Extensiones a EXCLUIR",
        "",
        key='input_excluded_extensions_main',
        placeholder=".log .tmp .bak",
        help="Extensiones a ignorar aunque estén en los targets. Separa con espacio."
    )
    output_mode = st.selectbox( "Modo Contexto", ['both', 'tree', 'content'], index=0, key='select_output_mode_main', help="Qué incluir en {contexto_extraido}" )
with col2:
    st.subheader("📄 Previsualización y Salida")
    output_file_str = st.text_input( "Guardar Prompt en Archivo (opcional)", placeholder="/ruta/prompt.txt", key='input_output_file_main' ).strip()
    # Usamos la key real guardada en el estado para la previsualización
    display_template_content(st.session_state.get('selected_template_name'))


st.divider()

# --- Botón de Generación y Lógica Principal ---
# ... (la lógica interna del botón no necesita cambios, usa st.session_state.selected_template_name) ...
vault_ready = False
if st.session_state.vault_selection_mode == "Guardada": vault_ready = st.session_state.get('selected_vault_name') is not None
elif st.session_state.vault_selection_mode == "Manual": vault_ready = st.session_state.get('manual_vault_path') != ""

if st.button("🚀 Generar Prompt", type="primary", use_container_width=True, disabled=not vault_ready):
    # ... (Validaciones y lógica de generación sin cambios significativos, ya que usa
    #      st.session_state.selected_template_name que contiene la key correcta) ...
    final_vault_name = None; vault_path: Optional[Path] = None; used_manual_path = False
    # [Código de validación de bóveda igual que antes]
    if st.session_state.vault_selection_mode == "Guardada":
        final_vault_name = st.session_state.get('selected_vault_name')
        if not final_vault_name: st.error("❌ Selecciona bóveda."); st.stop()
        if final_vault_name not in st.session_state.saved_vaults: st.error(f"❌ Bóveda '{final_vault_name}' no encontrada."); st.stop()
        try: vault_path = Path(st.session_state.saved_vaults[final_vault_name]).resolve(); assert vault_path.is_dir()
        except: st.error(f"❌ Ruta para '{final_vault_name}' inválida."); st.stop()
    elif st.session_state.vault_selection_mode == "Manual":
        manual_path_str = st.session_state.get('manual_vault_path')
        if not manual_path_str: st.error("❌ Introduce ruta manual."); st.stop()
        try: vault_path = Path(manual_path_str).resolve(); assert vault_path.is_dir()
        except: st.error(f"❌ Ruta manual '{manual_path_str}' inválida."); st.stop()
        final_vault_name = f"(Ruta Manual: {vault_path.name})"; used_manual_path = True

    final_template_name = st.session_state.get('selected_template_name') # <-- Key real usada aquí
    validation_ok = True
    if not vault_path: st.error("❌ Bóveda no determinada."); validation_ok = False
    if not final_template_name: st.error("❌ Plantilla no seleccionada."); validation_ok = False

    if validation_ok:
        try:
            # [Procesar targets, cargar plantilla, extensiones, ruta destino - sin cambios]
            valid_targets, invalid_targets = validate_and_get_targets(target_paths_input_str, vault_path)
            if invalid_targets: st.warning(f"Ignorando rutas inválidas: {[inv for inv in invalid_targets]}")
            if not valid_targets and target_paths_input_str.strip(): st.warning("⚠️ Usando toda la bóveda.")
            elif not valid_targets and not target_paths_input_str.strip(): st.info("ℹ️ Usando toda la bóveda.")

            template_content = prompt_handler.load_template(final_template_name)
            input_extensions = [e.strip() for e in extensions_str.split() if e.strip()]
            extensions = [f".{e.lstrip('.')}" for e in input_extensions] if input_extensions else DEFAULT_EXTENSIONS

            input_excluded_extensions = [e.strip() for e in excluded_extensions_str.split() if e.strip()]
            excluded_extensions = [f".{e.lstrip('.')}" for e in input_excluded_extensions]

            output_note_path_relative: Optional[Path] = None
            if output_note_path_str:
                try:
                    temp_path = Path(output_note_path_str)
                    if temp_path.is_absolute(): output_note_path_relative = temp_path.relative_to(vault_path.resolve())
                    else: output_note_path_relative = Path(output_note_path_str.lstrip('/\\'))
                except ValueError: st.error(f"❌ Ruta destino '{output_note_path_str}' no está en bóveda."); st.stop()
                except Exception as e: st.error(f"❌ Error procesando ruta destino: {e}"); st.stop()

            # --- LLAMADA A CORE ---
            with st.spinner("⚙️ Generando contexto y prompt..."):
                final_prompt = core.generate_prompt_core( vault_path=vault_path, target_paths=valid_targets, extensions=extensions, output_mode=output_mode, output_note_path=output_note_path_relative, template_string=template_content, excluded_extensions=excluded_extensions )

            st.success("✅ ¡Prompt generado!")
            st.subheader("Resultado")
            st.text_area("Prompt Final:", final_prompt, height=400, key="prompt_output_area_gui_result")

            # [Guardar Archivo - sin cambios]
            if output_file_str:
                try:
                    output_path = Path(output_file_str); output_path = (Path.cwd() / output_path).resolve() if not output_path.is_absolute() else output_path.resolve()
                    output_path.parent.mkdir(parents=True, exist_ok=True); output_path.write_text(final_prompt, encoding='utf-8')
                    st.success(f"💾 Prompt guardado en: `{output_path}`")
                except Exception as e: st.error(f"❌ Error guardando archivo: {e}")

            # [Actualizar Última Bóveda Usada - sin cambios]
            if not used_manual_path and st.session_state.vault_selection_mode == "Guardada":
                current_selected_vault_name = st.session_state.get('selected_vault_name')
                if current_selected_vault_name:
                    config_handler.set_last_vault(current_selected_vault_name)
                    st.session_state.last_vault_name = current_selected_vault_name

        except ValueError as ve: st.error(f"❌ Error Config/Validación: {ve}")
        except Exception as e: st.error(f"❌ Error Inesperado:"); st.exception(e)


# --- Sección de Gestión de Bóvedas ---
# ... (sin cambios) ...
with st.expander("⚙️ Gestionar Bóvedas Guardadas"):
    # ... (Código añadir/eliminar sin cambios) ...
    st.subheader("Añadir/Actualizar Bóveda"); col_add1, col_add2 = st.columns([1, 2]); new_vault_name = col_add1.text_input("Nombre Corto*", key='add_vault_name', placeholder="Ej: Personal"); new_vault_path_str = col_add2.text_input("Ruta Completa al Directorio*", key='add_vault_path', placeholder="Ej: C:\\Users\\Tu\\Obsidian\\Personal")
    if st.button("💾 Guardar Bóveda", key='add_vault_button'):
        error = False;
        if not new_vault_name: st.error("Nombre."); error=True
        if not new_vault_path_str: st.error("Ruta."); error=True
        elif not Path(new_vault_path_str).is_dir(): st.error("Ruta inválida."); error=True
        if not error:
            if config_handler.add_vault(new_vault_name, new_vault_path_str):
                 st.success(f"Bóveda '{new_vault_name}' guardada."); st.session_state.saved_vaults = config_handler.get_vaults(); st.session_state.selected_vault_name = new_vault_name; st.session_state.vault_selection_mode = "Guardada"; st.rerun()
    st.divider(); st.subheader("Eliminar Bóveda Guardada"); vaults_to_display_remove = st.session_state.get('saved_vaults', {})
    if not vaults_to_display_remove: st.caption("No hay bóvedas.")
    else:
        vault_to_remove = st.selectbox("Selecciona bóveda a eliminar", options=list(vaults_to_display_remove.keys()), index=None, placeholder="Elige...", key='remove_vault_select')
        if vault_to_remove:
            st.warning(f"¿Eliminar '{vault_to_remove}'?")
            if st.button(f"🗑️ Sí, Eliminar '{vault_to_remove}'", key=f'remove_btn_{vault_to_remove}', type="secondary"):
                if config_handler.remove_vault(vault_to_remove):
                    st.success(f"'{vault_to_remove}' eliminada."); st.session_state.saved_vaults = config_handler.get_vaults()
                    if st.session_state.get('selected_vault_name') == vault_to_remove: st.session_state.selected_vault_name = None
                    if st.session_state.get('last_vault_name') == vault_to_remove: st.session_state.last_vault_name = None
                    st.rerun()

st.divider()
st.caption(f"Obsidian Context Builder - v0.9.0") # Incrementar versión