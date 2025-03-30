# gui_streamlit.py (Enfoque Rutas + Backend)
import streamlit as st
from pathlib import Path
import sys
import traceback
from typing import Optional, Dict, Any, List, Set, Tuple

# Importar lógica COMPLETA de nuevo
import file_handler
import tree_generator
import formatter
import prompt_handler
import config_handler
try:
    from main import generate_prompt_core, DEFAULT_PLACEHOLDERS, generate_hierarchical_tags
except ImportError as e:
    st.error(f"Error crítico al importar desde main: {e}")
    st.stop()

st.set_page_config(layout="wide")
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
        except ValueError as e:
            error_msg = f"Error al cargar plantilla '{template_name}': {e}"
        except Exception as e:
             error_msg = f"Error inesperado al cargar plantilla '{template_name}': {e}"

    if error_msg:
        st.error(error_msg)
    st.text_area(
        "Contenido Plantilla Seleccionada", content, height=150, disabled=True, key="template_preview_area_routes"
    )

def validate_and_get_targets(target_input_str: str, vault_path: Path) -> Tuple[List[str], List[str]]:
    """Valida las rutas ingresadas y las devuelve como relativas."""
    raw_targets = [p.strip().replace('"', '') for p in target_input_str.split('\n') if p.strip()] # Limpiar comillas
    valid_relative_targets = []
    invalid_targets = []

    for raw_target in raw_targets:
        try:
            target_path = Path(raw_target)
            # Intentar resolverla relativa a la bóveda si no es absoluta ya
            if not target_path.is_absolute():
                abs_path = (vault_path / target_path).resolve()
            else:
                abs_path = target_path.resolve()

            # Verificar que existe y está dentro de la bóveda
            if abs_path.exists() and abs_path.is_relative_to(vault_path.resolve()):
                 # Obtener ruta relativa para pasarla a la lógica core
                 relative_path_str = abs_path.relative_to(vault_path.resolve()).as_posix()
                 valid_relative_targets.append(relative_path_str)
            else:
                 invalid_targets.append(raw_target)
        except Exception as e:
            print(f"Error validando target '{raw_target}': {e}", file=sys.stderr)
            invalid_targets.append(raw_target)

    return valid_relative_targets, invalid_targets


# --- Carga Inicial y Estado ---
# ...(Sin cambios respecto a la versión anterior con navegador)...
if 'config_loaded' not in st.session_state:
    st.session_state.config = config_handler.load_config()
    st.session_state.saved_vaults = config_handler.get_vaults()
    st.session_state.available_templates = prompt_handler.get_available_templates()
    last_vault_info = config_handler.get_last_vault()
    st.session_state.last_vault_name = last_vault_info[0] if last_vault_info else None
    st.session_state.config_loaded = True
    if 'selected_vault_name' not in st.session_state:
         st.session_state.selected_vault_name = st.session_state.last_vault_name
    if 'selected_template_name' not in st.session_state:
        default_prefs = ["Generar Nota Completa (Original)", "Generar Nota Simple", "Resumir Contenido"]
        templates_keys = list(st.session_state.available_templates.keys())
        st.session_state.selected_template_name = next((t for t in default_prefs if t in st.session_state.available_templates), templates_keys[0] if templates_keys else None)

# --- Barra Lateral ---
# ...(Sin cambios respecto a la versión anterior con navegador)...
with st.sidebar:
    st.header("⚙️ Configuración Principal")
    # --- Selección de Bóveda ---
    vault_names = list(st.session_state.saved_vaults.keys())
    current_selection_index = 0
    if st.session_state.selected_vault_name and st.session_state.selected_vault_name in vault_names:
         try: current_selection_index = vault_names.index(st.session_state.selected_vault_name)
         except ValueError: pass
    if not vault_names:
        st.warning("No hay bóvedas guardadas. Añade una abajo."); selected_vault_name = None
    else:
        selected_vault_name = st.selectbox( "Selecciona Bóveda Obsidian", options=vault_names, index=current_selection_index, key='sb_vault_select_ui', help="Selecciona una bóveda guardada." )
        if selected_vault_name != st.session_state.selected_vault_name:
             st.session_state.selected_vault_name = selected_vault_name

    # --- Selección de Plantilla ---
    template_names = list(st.session_state.available_templates.keys())
    current_template_index = 0
    if st.session_state.selected_template_name and st.session_state.selected_template_name in template_names:
         try: current_template_index = template_names.index(st.session_state.selected_template_name)
         except ValueError: pass
    if not template_names:
        st.warning("No hay plantillas disponibles."); selected_template_name = None
    else:
        template_display_names = { name: (f"📄 {Path(st.session_state.available_templates[name]).stem}" if name.startswith("Archivo:") else f"💡 {name}") for name in template_names }
        display_list = [template_display_names[name] for name in template_names]
        selected_display_name = st.selectbox( "Selecciona Plantilla de Prompt", options=display_list, index=current_template_index, key='sb_template_select_ui', help="Elige predefinida (💡) o de /templates (📄)." )
        selected_template_name = next((name for name, display in template_display_names.items() if display == selected_display_name), None)
        if selected_template_name != st.session_state.selected_template_name:
            st.session_state.selected_template_name = selected_template_name

    # --- Ruta Nota Destino ---
    output_note_path_str = st.text_input( "Ruta Relativa Nota Destino*", placeholder="Carpeta/Nota.md", key='input_output_note_path', help="Ruta dentro de la bóveda (obligatorio)." ).strip()

# --- Área Principal ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("🎯 Rutas de Contexto (Targets)")
    # --- TEXT AREA PARA PEGAR RUTAS ---
    target_paths_input_str = st.text_area(
        "Pegar Rutas (1 por línea)",
        height=200, # Altura moderada
        key='input_target_paths_manual',
        placeholder="Ejemplos:\nAsignaturas/Cálculo\nNotas Diarias/2024-01-15.md\nD:\\Obsidian\\MiBoveda\\Proyectos\\ProyectoX.md",
        help="Pega rutas relativas (a la bóveda) o absolutas de carpetas/archivos a incluir. Una por línea."
    )
    # --- FIN TEXT AREA ---

    st.subheader("⚙️ Opciones de Generación")
    extensions_str = st.text_input( "Extensiones a incluir", ".md", key='input_extensions_main', help="Archivos a buscar DENTRO de carpetas target. Separa con espacio." )
    output_mode = st.selectbox( "Modo Contexto", ['both', 'tree', 'content'], index=0, key='select_output_mode_main', help="Qué incluir en {contexto_extraido}" )

with col2:
    st.subheader("📄 Previsualización y Salida")
    output_file_str = st.text_input( "Guardar Prompt en Archivo (opcional)", placeholder="/ruta/completa/prompt.txt", key='input_output_file_main' ).strip()
    display_template_content(st.session_state.get('selected_template_name'))


st.divider()

# --- Botón de Generación ---
if st.button("🚀 Generar Prompt", type="primary", use_container_width=True):
    # --- Recoger y Validar ---
    final_vault_name = st.session_state.get('selected_vault_name')
    final_template_name = st.session_state.get('selected_template_name')
    vault_path: Optional[Path] = Path(st.session_state.saved_vaults[final_vault_name]).resolve() if final_vault_name and final_vault_name in st.session_state.saved_vaults else None

    validation_ok = True
    if not (final_vault_name and vault_path and vault_path.is_dir()):
        st.error("❌ Selecciona una bóveda válida."); validation_ok = False
    if not final_template_name:
        st.error("❌ Selecciona una plantilla válida."); validation_ok = False
    if not output_note_path_str:
        st.error("❌ 'Ruta Relativa Nota Destino' es obligatoria."); validation_ok = False
    # No necesitamos validar target_paths_input_str como obligatorio, lista vacía significa toda la bóveda

    if validation_ok:
        try:
            # --- Validar y Procesar Targets ---
            valid_targets, invalid_targets = validate_and_get_targets(target_paths_input_str, vault_path)
            if invalid_targets:
                 st.warning(f"Se ignoraron las siguientes rutas objetivo inválidas o fuera de la bóveda:")
                 for invalid in invalid_targets:
                     st.code(invalid)
            # Si no quedan targets válidos y el usuario puso algo, advertir
            if not valid_targets and target_paths_input_str:
                 st.warning("Ninguna de las rutas objetivo proporcionadas era válida. Se usará toda la bóveda como contexto.")
            # --- FIN Validar Targets ---

            template_content = prompt_handler.load_template(final_template_name)
            input_extensions = [e.strip() for e in extensions_str.split() if e.strip()]
            extensions = [f".{e.lstrip('.')}" for e in input_extensions] if input_extensions else DEFAULT_EXTENSIONS

            # Validar y convertir output_note_path
            output_note_path = Path(output_note_path_str)
            if output_note_path.is_absolute():
                try: output_note_path = output_note_path.relative_to(vault_path)
                except ValueError: st.error(f"❌ Ruta nota destino absoluta no en bóveda."); st.stop()

            # --- LLAMADA A CORE ---
            with st.spinner("⚙️ Generando contexto y prompt..."):
                final_prompt = generate_prompt_core(
                    vault_path=vault_path,
                    target_paths=valid_targets, # Pasar las rutas validadas
                    extensions=extensions,
                    output_mode=output_mode,
                    output_note_path=output_note_path,
                    template_string=template_content
                )

            st.success("✅ ¡Prompt generado!")
            st.subheader("Resultado")
            st.text_area("", final_prompt, height=400, key="prompt_output_area_gui_result")

            if output_file_str:
                try:
                    output_path = Path(output_file_str).resolve()
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(final_prompt, encoding='utf-8')
                    st.success(f"💾 Prompt guardado en: `{output_path}`")
                except Exception as e: st.error(f"❌ Error al guardar archivo: {e}")
            if final_vault_name:
                config_handler.set_last_vault(final_vault_name)
                st.session_state.last_vault_name = final_vault_name

        except ValueError as ve: st.error(f"❌ Error config/validación: {ve}")
        except Exception as e: st.error("❌ Error inesperado:"); st.exception(e)

st.divider()

# --- Sección de Gestión de Bóvedas ---
# ...(Sin cambios aquí)...
with st.expander("⚙️ Gestionar Bóvedas Guardadas"):
    st.subheader("Añadir/Actualizar Bóveda")
    col_add1, col_add2 = st.columns([1,2])
    with col_add1: new_vault_name = st.text_input("Nombre Corto*", key='add_vault_name')
    with col_add2: new_vault_path_str = st.text_input("Ruta Completa al Directorio*", key='add_vault_path')
    if st.button("💾 Guardar Bóveda", key='add_vault_button'):
        if not new_vault_name: st.error("Nombre obligatorio.")
        elif not new_vault_path_str: st.error("Ruta obligatoria.")
        elif not Path(new_vault_path_str).is_dir(): st.error("Ruta inválida.")
        else:
            if config_handler.add_vault(new_vault_name, new_vault_path_str):
                 st.success(f"Bóveda '{new_vault_name}' guardada."); st.session_state.saved_vaults = config_handler.get_vaults(); st.rerun()
            else: st.error("No se pudo guardar.")
    st.subheader("Eliminar Bóveda Guardada")
    vaults_to_display = st.session_state.get('saved_vaults', {})
    if not vaults_to_display: st.caption("No hay bóvedas guardadas.")
    else:
        vault_to_remove = st.selectbox("Selecciona bóveda a eliminar", options=list(vaults_to_display.keys()), index=None, placeholder="Elige...", key='remove_vault_select')
        if vault_to_remove:
            if st.button(f"🗑️ Eliminar '{vault_to_remove}'", key=f'remove_btn_{vault_to_remove}', type="secondary"):
                if config_handler.remove_vault(vault_to_remove):
                    st.success(f"Bóveda '{vault_to_remove}' eliminada."); st.session_state.saved_vaults = config_handler.get_vaults()
                    if st.session_state.selected_vault_name == vault_to_remove: st.session_state.selected_vault_name = None; st.session_state.last_vault_name = None
                    st.rerun()
                else: st.error("No se pudo eliminar.")

st.caption(f"Obsidian Context Builder - v0.5.1") # Incrementar versión