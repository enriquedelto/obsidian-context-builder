# gui_streamlit.py
import streamlit as st
from pathlib import Path
import sys
import traceback
from typing import Optional, Dict, Any, List, Set, Tuple

# Importar módulos propios
import prompt_handler
import config_handler
import file_handler # Aunque la lógica core lo usa, no se usa directamente aquí
import tree_generator # Ídem
import formatter # Ídem

# Importar lógica central y constantes
try:
    from core import generate_prompt_core, DEFAULT_PLACEHOLDERS, generate_hierarchical_tags, DEFAULT_EXTENSIONS
except ImportError as e:
    st.error(f"Error crítico al importar desde core: {e}. Asegúrate que core.py existe.")
    st.stop()

# --- CONFIGURACIÓN DE PÁGINA Y TÍTULO ---
st.set_page_config(layout="wide", page_title="Obsidian Context Builder")
st.title("Obsidian Context Builder 🔨")
st.caption("Genera prompts para LLMs usando el contexto de tu bóveda Obsidian.")

# --- Funciones Auxiliares ---
def display_template_content(template_name: Optional[str]):
    """Muestra el contenido de la plantilla seleccionada."""
    content = ""
    error_msg = None
    if template_name:
        try:
            content = prompt_handler.load_template(template_name)
        except ValueError as e: # Captura errores específicos de carga
            error_msg = f"Error: {e}" # El error ya está formateado
        except Exception as e:
             error_msg = f"Error inesperado al cargar plantilla '{template_name}': {e}"

    if error_msg:
        st.error(error_msg)
    # Usar un ID único para el área de texto de previsualización
    st.text_area(
        "Contenido Plantilla Seleccionada", content, height=150, disabled=True, key="template_preview_area"
    )

def validate_and_get_targets(target_input_str: str, vault_path: Path) -> Tuple[List[str], List[str]]:
    """Valida las rutas ingresadas y las devuelve como relativas a la bóveda."""
    # Limpiar espacios, comillas y líneas vacías
    raw_targets = [p.strip().strip('"') for p in target_input_str.splitlines() if p.strip()]
    valid_relative_targets = []
    invalid_targets = []
    vault_path_resolved = vault_path.resolve() # Resolver una vez

    for raw_target in raw_targets:
        try:
            target_path = Path(raw_target)
            # Intentar resolverla relativa a la bóveda si no es absoluta ya
            if not target_path.is_absolute():
                abs_path = (vault_path_resolved / target_path).resolve()
            else:
                abs_path = target_path.resolve()

            # Verificar que existe y está dentro de la bóveda resuelta
            if abs_path.exists() and abs_path.is_relative_to(vault_path_resolved):
                 relative_path_str = abs_path.relative_to(vault_path_resolved).as_posix()
                 valid_relative_targets.append(relative_path_str)
            else:
                 # Razón más específica para el log/warning
                 reason = "no existe" if not abs_path.exists() else "fuera de la bóveda"
                 print(f"Target inválido '{raw_target}' ({reason}): {abs_path}", file=sys.stderr)
                 invalid_targets.append(raw_target)
        except Exception as e:
            print(f"Error validando target '{raw_target}': {e}", file=sys.stderr)
            invalid_targets.append(raw_target)

    return valid_relative_targets, invalid_targets

# --- Mapeo de Plantillas a Categorías ---
TEMPLATE_CATEGORIES = {
    # 🔍 Análisis y Diagnóstico
    "AnalizarContenido":        "🔍 Análisis", "ResumenConceptosClave":    "🔍 Análisis",
    "ValidarRigorAcademico":    "🔍 Análisis", "IdentificarNotasHuerfanas":"🔍 Análisis",
    # ✨ Creación de Contenido
    "GenerarNota":              "✨ Creación", "GenerarMOC":               "✨ Creación",
    # 📝 Mejora de Notas
    "EnriquecerNota":           "📝 Mejora",
    # 🔗 Gestión de Enlaces
    "MejorarEnlaces":           "🔗 Enlaces", "SugerirEnlacesEntrantes":  "🔗 Enlaces",
    # 🗂️ Organización y Scripts (¡Precaución!)
    "ReorganizarCarpeta":       "🗂️ Organización (Scripts)", "GenerarScriptCreacionNotas":"🗂️ Organización (Scripts)",
    # 🎓 Utilidades (Estudio/Otros)
    "GenerarPreguntas":         "🎓 Utilidades",
}
DEFAULT_CATEGORY = "❓ Sin Categoría"

# --- Función auxiliar para obtener detalles de plantillas categorizadas ---
def get_categorized_templates(available_templates: Dict[str, str]) -> Tuple[List[str], Dict[str, List[Dict[str, str]]]]:
    """Procesa plantillas disponibles y devuelve categorías ordenadas y mapa categoría -> detalles."""
    category_map: Dict[str, List[Dict[str, str]]] = {}
    for key, _ in available_templates.items():
        if key.startswith("Archivo: "):
            stem = key.split("Archivo: ", 1)[1]
            category = TEMPLATE_CATEGORIES.get(stem, DEFAULT_CATEGORY)
            if category not in category_map: category_map[category] = []
            category_map[category].append({"key": key, "stem": stem})
    for category in category_map: category_map[category].sort(key=lambda x: x["stem"])
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
    st.session_state.setdefault('selected_category', None)
    st.session_state.setdefault('selected_template_name', None)

    sorted_categories, category_map = get_categorized_templates(st.session_state.available_templates)
    if sorted_categories:
        preferred_keys = ["Archivo: GenerarNota", "Archivo: EnriquecerNota"]
        default_template_key = None; found_default = False
        for key in preferred_keys:
             if key in st.session_state.available_templates: default_template_key = key; found_default = True; break
        if not found_default and category_map:
             first_category = sorted_categories[0]
             if category_map.get(first_category): default_template_key = category_map[first_category][0]['key']

        if default_template_key:
            stem = default_template_key.split("Archivo: ", 1)[1]
            st.session_state.selected_category = TEMPLATE_CATEGORIES.get(stem, DEFAULT_CATEGORY)
            st.session_state.selected_template_name = default_template_key
        elif sorted_categories : # Si no hubo default pero sí categorías
            st.session_state.selected_category = sorted_categories[0]
            # La plantilla se seleccionará automáticamente en el primer rerun

    st.session_state.config_loaded = True
    print("--- Session State Initialized ---")

# --- Barra Lateral (Configuración Principal) ---
with st.sidebar:
    st.header("⚙️ Configuración Principal")

    # --- Selección de Modo Bóveda ---
    current_mode_index = 0
    if 'vault_selection_mode' in st.session_state and st.session_state.vault_selection_mode == "Manual": current_mode_index = 1
    st.session_state.vault_selection_mode = st.radio( "Fuente de la Bóveda:", options=["Guardada", "Manual"], key='vault_mode_radio', horizontal=True, index=current_mode_index )

    # --- Selección de Bóveda (Condicional) ---
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
    category_index = 0
    if st.session_state.selected_category and st.session_state.selected_category in sorted_categories:
        try: category_index = sorted_categories.index(st.session_state.selected_category)
        except ValueError: st.session_state.selected_category = None # Resetear si ya no existe

    selected_category = st.selectbox( "Categoría de Plantilla", options=sorted_categories, index=category_index, key='sb_category_select', help="Elige el tipo de tarea.", placeholder="No hay plantillas...", disabled=not sorted_categories )

    if selected_category and selected_category != st.session_state.get('selected_category'):
        st.session_state.selected_category = selected_category
        st.session_state.selected_template_name = None # Resetear plantilla
        if selected_category in category_map and category_map[selected_category]:
            st.session_state.selected_template_name = category_map[selected_category][0]['key']
        st.rerun()

    # 2. Selectbox de Plantilla (filtrado)
    filtered_templates_display = []; display_to_key_map = {}
    if st.session_state.selected_category and st.session_state.selected_category in category_map:
        for template_detail in category_map[st.session_state.selected_category]:
            display_name = f"📄 {template_detail['stem']}"
            filtered_templates_display.append(display_name)
            display_to_key_map[display_name] = template_detail['key']

    template_index = 0
    current_template_key = st.session_state.get('selected_template_name')
    if current_template_key:
        current_display_name = next((disp for disp, key in display_to_key_map.items() if key == current_template_key), None)
        if current_display_name and current_display_name in filtered_templates_display:
            try: template_index = filtered_templates_display.index(current_display_name)
            except ValueError: pass

    selected_template_display = st.selectbox( "Plantilla Específica", options=filtered_templates_display, index=template_index, key='sb_template_select', help="Selecciona la plantilla específica.", placeholder="Elige categoría..." if not st.session_state.selected_category else "No hay plantillas...", disabled=not filtered_templates_display )

    selected_template_key = display_to_key_map.get(selected_template_display)
    if selected_template_key and selected_template_key != st.session_state.get('selected_template_name'):
        st.session_state.selected_template_name = selected_template_key
        st.rerun() # Actualizar previsualización

    # --- Ruta Nota Destino (Opcional) ---
    st.divider()
    st.subheader("Nota Objetivo")
    output_note_path_str = st.text_input(
        "Ruta Relativa (Opcional)", # <--- Ya no es obligatorio
        placeholder="Carpeta/NotaObjetivo.md",
        key='input_output_note_path',
        help="Ruta DENTRO de la bóveda. Necesaria para placeholders {ruta_destino} y {etiqueta_jerarquica_N}." # <--- Aclaración
    ).strip()

# --- Área Principal (Entrada y Salida) ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("🎯 Rutas de Contexto (Targets)")
    target_paths_input_str = st.text_area( "Pegar Rutas (1 por línea)", height=150, key='input_target_paths_manual', placeholder="Ejemplos:\nAsignaturas/Cálculo\nNotas Diarias/2024-01-15.md\n\n(Dejar vacío para usar toda la bóveda)", help="Pega rutas relativas/absolutas. Vacío = toda la bóveda." )
    st.subheader("⚙️ Opciones de Generación")
    extensions_str = st.text_input( "Extensiones a INCLUIR", " ".join(DEFAULT_EXTENSIONS), key='input_extensions_main', help="Separar con espacio (ej: .md .canvas)." )
    excluded_extensions_str = st.text_input( # <--- NUEVO
        "Extensiones a EXCLUIR", "", key='input_excluded_extensions_main', placeholder=".log .tmp .bak", help="Extensiones a ignorar. Separa con espacio."
    )
    output_mode = st.selectbox( "Modo Contexto", ['both', 'tree', 'content'], index=0, key='select_output_mode_main', help="Qué incluir en {contexto_extraido}" )
with col2:
    st.subheader("📄 Previsualización y Salida")
    output_file_str = st.text_input( "Guardar Prompt en Archivo (opcional)", placeholder="/ruta/prompt.txt", key='input_output_file_main' ).strip()
    display_template_content(st.session_state.get('selected_template_name'))

st.divider()

# --- Botón de Generación y Lógica Principal ---
vault_ready = False
if st.session_state.vault_selection_mode == "Guardada": vault_ready = st.session_state.get('selected_vault_name') is not None
elif st.session_state.vault_selection_mode == "Manual": vault_ready = st.session_state.get('manual_vault_path') != ""

if st.button("🚀 Generar Prompt", type="primary", use_container_width=True, disabled=not vault_ready):
    # --- Recoger y Validar Entradas ---
    final_vault_name = None; vault_path: Optional[Path] = None; used_manual_path = False
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

    final_template_name = st.session_state.get('selected_template_name')
    validation_ok = True
    if not vault_path: st.error("❌ Bóveda no determinada."); validation_ok = False
    if not final_template_name: st.error("❌ Plantilla no seleccionada."); validation_ok = False
    # <<< Ya no se valida output_note_path_str como obligatorio >>>

    if validation_ok:
        try:
            # --- Procesar Targets, Plantilla, Opciones ---
            valid_targets, invalid_targets = validate_and_get_targets(target_paths_input_str, vault_path)
            if invalid_targets: st.warning(f"Ignorando rutas inválidas: {[inv for inv in invalid_targets]}")
            if not valid_targets and target_paths_input_str.strip(): st.warning("⚠️ Usando toda la bóveda.")
            elif not valid_targets and not target_paths_input_str.strip(): st.info("ℹ️ Usando toda la bóveda.")

            template_content = prompt_handler.load_template(final_template_name)
            input_extensions = [e.strip() for e in extensions_str.split() if e.strip()]
            extensions = [f".{e.lstrip('.')}" for e in input_extensions] if input_extensions else core.DEFAULT_EXTENSIONS
            input_excluded_extensions = [e.strip() for e in excluded_extensions_str.split() if e.strip()] # <<< Obtener exclusiones
            excluded_extensions = [f".{e.lstrip('.')}" for e in input_excluded_extensions] # <<< Normalizar exclusiones

            # --- Validar y Convertir Ruta Destino (SI SE PROPORCIONÓ) ---
            output_note_path_relative: Optional[Path] = None # <-- Default None
            if output_note_path_str: # <-- Solo procesar si no está vacío
                try:
                    temp_path = Path(output_note_path_str)
                    if temp_path.is_absolute():
                        output_note_path_relative = temp_path.relative_to(vault_path.resolve())
                    else:
                        output_note_path_relative = Path(output_note_path_str.lstrip('/\\'))
                except ValueError: st.error(f"❌ Ruta destino '{output_note_path_str}' no está en bóveda."); st.stop()
                except Exception as e: st.error(f"❌ Error procesando ruta destino: {e}"); st.stop()
            # No mostrar info aquí, core.py ya advierte si faltan placeholders

            # --- LLAMADA A CORE ---
            with st.spinner("⚙️ Generando contexto y prompt..."):
                final_prompt = core.generate_prompt_core(
                    vault_path=vault_path,
                    target_paths=valid_targets,
                    extensions=extensions,
                    output_mode=output_mode,
                    output_note_path=output_note_path_relative, # <-- Pasa None si no se dio
                    template_string=template_content,
                    excluded_extensions=excluded_extensions # <-- Pasar exclusiones
                )

            st.success("✅ ¡Prompt generado!")
            st.subheader("Resultado")
            st.text_area("Prompt Final:", final_prompt, height=400, key="prompt_output_area_gui_result")

            # --- Guardar Archivo (Opcional) ---
            if output_file_str:
                try:
                    output_path = Path(output_file_str); output_path = (Path.cwd() / output_path).resolve() if not output_path.is_absolute() else output_path.resolve()
                    output_path.parent.mkdir(parents=True, exist_ok=True); output_path.write_text(final_prompt, encoding='utf-8')
                    st.success(f"💾 Prompt guardado en: `{output_path}`")
                except Exception as e: st.error(f"❌ Error guardando archivo: {e}")

            # --- Actualizar Última Bóveda Usada ---
            if not used_manual_path and st.session_state.vault_selection_mode == "Guardada":
                current_selected_vault_name = st.session_state.get('selected_vault_name')
                if current_selected_vault_name:
                    config_handler.set_last_vault(current_selected_vault_name)
                    st.session_state.last_vault_name = current_selected_vault_name

        except ValueError as ve: st.error(f"❌ Error Config/Validación: {ve}")
        except Exception as e: st.error(f"❌ Error Inesperado:"); st.exception(e)

# --- Sección de Gestión de Bóvedas ---
with st.expander("⚙️ Gestionar Bóvedas Guardadas"):
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
# Actualizar versión en el caption
st.caption(f"Obsidian Context Builder - v0.10.0")