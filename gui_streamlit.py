# gui_streamlit.py (Corregido - Duplicación eliminada)
import streamlit as st
from pathlib import Path
import sys
import traceback
from typing import Optional, Dict, Any, List, Set, Tuple
import fnmatch

# Importar lógica
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

# --- Constantes ---
IGNORE_PATTERNS = ['.git', '.obsidian', '.trash', '__pycache__', '*.pyc', '*_config.json']

# --- Funciones del Navegador de Archivos ---
# (build_file_tree, display_file_tree, get_selected_targets - SIN CAMBIOS, deben estar aquí o importadas)
@st.cache_data(ttl=300)
def build_file_tree(vault_root: Path) -> Dict[str, Any]:
    """Construye una estructura de diccionario anidado del árbol de archivos/carpetas."""
    tree = {}
    if not vault_root or not vault_root.is_dir():
        return tree
    items_to_process = []
    try:
        for item in vault_root.rglob('*'):
            ignore = False
            try:
                relative_parts = item.relative_to(vault_root).parts
            except ValueError:
                continue
            for pattern in IGNORE_PATTERNS:
                if fnmatch.fnmatch(item.name, pattern):
                    ignore = True
                    break
                for part in relative_parts:
                     if fnmatch.fnmatch(part, pattern):
                          ignore = True
                          break
                if ignore:
                     break
            if not ignore:
                items_to_process.append(item)
    except Exception as e:
        st.error(f"Error al listar archivos en {vault_root}: {e}")
        return tree
    for item_path in sorted(items_to_process):
         try:
            relative_path = item_path.relative_to(vault_root)
            parts = relative_path.parts
            current_level = tree
            for i, part in enumerate(parts):
                is_last_part = (i == len(parts) - 1)
                if is_last_part:
                    current_level[part] = relative_path.as_posix() if item_path.is_file() else {}
                else:
                    current_level = current_level.setdefault(part, {})
                    if not isinstance(current_level, dict):
                         print(f"Conflicto en árbol: {part} no es un directorio", file=sys.stderr)
                         break
         except Exception as e:
              print(f"Error procesando item {item_path} para árbol: {e}", file=sys.stderr)
    return tree

def display_file_tree(node: Dict[str, Any], base_path: str = "", level: int = 0):
    """Renderiza recursivamente el árbol con checkboxes en Streamlit."""
    indent = "    " * level # Indentación HTML
    sorted_items = sorted(node.items(), key=lambda item: (not isinstance(item[1], dict), item[0].lower()))

    for name, value in sorted_items:
        current_rel_path = f"{base_path}/{name}" if base_path else name
        unique_key = f"cb_{current_rel_path}"

        # Asegurar que el estado existe antes de renderizar el widget
        if unique_key not in st.session_state:
            st.session_state[unique_key] = False

        item_col1, item_col2 = st.columns([0.1, 0.9])

        with item_col1:
             # CORRECCIÓN AQUÍ: Solo renderizar. Streamlit gestiona el estado vía 'key'.
             st.checkbox(" ", key=unique_key, label_visibility="collapsed")

        with item_col2:
            if isinstance(value, dict): # Carpeta
                is_empty = not bool(value)
                label_text = f"{indent}📁 {name}" + (" (Vacía)" if is_empty else "")
                if not is_empty:
                    # El expander no necesita key si no interactuamos programáticamente con su estado
                    with st.expander(label_text):
                        display_file_tree(value, current_rel_path, level + 1)
                else:
                    st.markdown(label_text, unsafe_allow_html=True) # Mostrar carpeta vacía
            elif isinstance(value, str): # Archivo
                st.markdown(f"{indent}📄 {name}", unsafe_allow_html=True)

def get_selected_targets() -> List[str]:
    # ...(sin cambios)...
    selected = []
    for key, value in st.session_state.items():
        if key.startswith("cb_") and value is True:
            relative_path = key[3:]
            selected.append(relative_path)
    return selected

st.set_page_config(layout="wide")
st.title("Obsidian Context Builder 🔨")
st.caption("Genera prompts para LLMs usando el contexto de tu bóveda Obsidian.")

# --- Funciones Auxiliares para la GUI ---
def display_template_content(template_name: Optional[str]):
    """Muestra el contenido de la plantilla seleccionada."""
    # ...(igual que antes)...
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
        "Contenido Plantilla Seleccionada",
        content,
        height=150,
        disabled=True,
        key="template_preview_area"
    )

# --- Carga Inicial y Estado de la Sesión ---
if 'config_loaded' not in st.session_state:
    # ...(igual que antes)...
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
with st.sidebar:
    st.header("⚙️ Configuración Principal")

    # --- Selección de Bóveda ---
    vault_names = list(st.session_state.saved_vaults.keys())
    current_selection_index = 0 # Default a la primera
    if st.session_state.selected_vault_name and st.session_state.selected_vault_name in vault_names:
         try:
            current_selection_index = vault_names.index(st.session_state.selected_vault_name)
         except ValueError:
              pass # Mantener índice 0 si el nombre guardado ya no es válido

    if not vault_names:
        st.warning("No hay bóvedas guardadas. Añade una abajo.")
        selected_vault_name = None
    else:
        selected_vault_name = st.selectbox(
            "Selecciona Bóveda Obsidian",
            options=vault_names,
            index=current_selection_index,
            key='sb_vault_select_ui', # Key diferente para el widget
            help="Selecciona una bóveda guardada."
        )
        # Actualizar el estado explícitamente si cambia la selección
        if selected_vault_name != st.session_state.selected_vault_name:
             st.session_state.selected_vault_name = selected_vault_name
             # Opcional: guardar como última usada inmediatamente al seleccionar?
             # config_handler.set_last_vault(selected_vault_name)
             # st.session_state.last_vault_name = selected_vault_name

    # --- Selección de Plantilla ---
    template_names = list(st.session_state.available_templates.keys())
    current_template_index = 0
    if st.session_state.selected_template_name and st.session_state.selected_template_name in template_names:
         try:
            current_template_index = template_names.index(st.session_state.selected_template_name)
         except ValueError: pass
    if not template_names:
        st.warning("No hay plantillas disponibles.")
        selected_template_name = None
    else:
        template_display_names = { name: (f"📄 {Path(st.session_state.available_templates[name]).stem}" if name.startswith("Archivo:") else f"💡 {name}") for name in template_names }
        display_list = [template_display_names[name] for name in template_names]
        selected_display_name = st.selectbox( "Selecciona Plantilla de Prompt", options=display_list, index=current_template_index, key='sb_template_select_ui', help="Elige predefinida (💡) o de /templates (📄)." )
        selected_template_name = next((name for name, display in template_display_names.items() if display == selected_display_name), None)
        if selected_template_name != st.session_state.selected_template_name:
            st.session_state.selected_template_name = selected_template_name

    # --- Ruta Nota Destino ---
    output_note_path_str = st.text_input(
        "Ruta Relativa Nota Destino*",
        placeholder="Carpeta/Nota.md",
        key='input_output_note_path',
        help="Ruta dentro de la bóveda (obligatorio para generar)."
    ).strip() # .strip() para quitar espacios

# --- Área Principal ---

st.subheader("🎯 Selección de Contexto (Targets)")
st.caption("Marca las carpetas/archivos para incluir en el contexto. Nada marcado = bóveda completa.")

# Mostrar el navegador de archivos
selected_vault_path_str = st.session_state.saved_vaults.get(st.session_state.get('selected_vault_name'))
if selected_vault_path_str:
    vault_root_path = Path(selected_vault_path_str)
    if vault_root_path.is_dir():
        file_tree_data = build_file_tree(vault_root_path) # Usa la función cacheada
        if not file_tree_data:
            st.warning(f"'{st.session_state.selected_vault_name}' vacía o ilegible.")
        else:
            with st.container(height=400, border=True): # Añadir borde y altura
                display_file_tree(file_tree_data)
    else:
        st.error(f"Ruta inválida para bóveda '{st.session_state.selected_vault_name}'.")
else:
    st.info("Selecciona una bóveda en la barra lateral para ver el navegador.")

st.divider()

col_opts1, col_opts2 = st.columns(2)

with col_opts1:
    st.subheader("⚙️ Opciones Adicionales")
    extensions_str = st.text_input(
        "Extensiones a incluir", ".md", key='input_extensions_main', # Key diferente
        help="Archivos a buscar DENTRO de los targets. Separa con espacio."
    )
    output_mode = st.selectbox(
        "Modo Contexto", ['both', 'tree', 'content'], index=0, key='select_output_mode_main', # Key diferente
        help="Qué incluir en {contexto_extraido}"
    )

with col_opts2:
    st.subheader("📄 Previsualización y Salida")
    output_file_str = st.text_input(
        "Guardar Prompt en Archivo (opcional)", placeholder="/ruta/completa/prompt.txt", key='input_output_file_main' # Key diferente
    ).strip()
    display_template_content(st.session_state.get('selected_template_name')) # Llamar a la función auxiliar

st.divider()

# --- Botón de Generación ---
if st.button("🚀 Generar Prompt", type="primary", use_container_width=True):
    # --- Recoger y Validar ---
    # (Misma lógica de validación que antes)
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

    if validation_ok:
        try:
            # --- Recoger Targets ---
            selected_target_paths = get_selected_targets() # USA LA NUEVA FUNCIÓN
            print(f"GUI Targets: {selected_target_paths}") # Debug

            template_content = prompt_handler.load_template(final_template_name)
            input_extensions = [e.strip() for e in extensions_str.split() if e.strip()]
            extensions = [f".{e.lstrip('.')}" for e in input_extensions] if input_extensions else DEFAULT_EXTENSIONS
            output_note_path = Path(output_note_path_str)
            if output_note_path.is_absolute():
                output_note_path = output_note_path.relative_to(vault_path)

            # --- LLAMADA A CORE ---
            with st.spinner("⚙️ Generando contexto y prompt..."):
                final_prompt = generate_prompt_core(
                    vault_path=vault_path,
                    target_paths=selected_target_paths, # Pasar los seleccionados
                    extensions=extensions,
                    output_mode=output_mode, # Usar el del selectbox principal
                    output_note_path=output_note_path,
                    template_string=template_content
                )

            st.success("✅ ¡Prompt generado!")
            st.subheader("Resultado")
            st.text_area("", final_prompt, height=400, key="prompt_output_area_gui_result")

            if output_file_str: # Usar el del input principal
                try:
                    output_path = Path(output_file_str).resolve()
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(final_prompt, encoding='utf-8')
                    st.success(f"💾 Prompt guardado en: `{output_path}`")
                except Exception as e:
                    st.error(f"❌ Error al guardar archivo '{output_file_str}': {e}")
            if final_vault_name:
                config_handler.set_last_vault(final_vault_name)
                st.session_state.last_vault_name = final_vault_name

        except ValueError as ve:
             st.error(f"❌ Error de configuración/validación: {ve}")
        except Exception as e:
            st.error("❌ Error inesperado durante la generación:")
            st.exception(e)

st.divider()

# --- Sección de Gestión de Bóvedas ---
with st.expander("⚙️ Gestionar Bóvedas Guardadas"):
    # ...(igual que antes)...
    st.subheader("Añadir/Actualizar Bóveda")
    col_add1, col_add2 = st.columns([1,2])
    with col_add1: new_vault_name = st.text_input("Nombre Corto*", key='add_vault_name')
    with col_add2: new_vault_path_str = st.text_input("Ruta Completa al Directorio*", key='add_vault_path')
    if st.button("💾 Guardar Bóveda", key='add_vault_button'):
        if not new_vault_name: st.error("El nombre es obligatorio.")
        elif not new_vault_path_str: st.error("La ruta es obligatoria.")
        elif not Path(new_vault_path_str).is_dir(): st.error(f"'{new_vault_path_str}' no es un directorio válido.")
        else:
            if config_handler.add_vault(new_vault_name, new_vault_path_str):
                 st.success(f"Bóveda '{new_vault_name}' guardada/actualizada.")
                 st.session_state.saved_vaults = config_handler.get_vaults()
                 st.rerun()
            else: st.error("No se pudo guardar la bóveda.")
    st.subheader("Eliminar Bóveda Guardada")
    vaults_to_display = st.session_state.get('saved_vaults', {})
    if not vaults_to_display: st.caption("No hay bóvedas guardadas.")
    else:
        vault_to_remove = st.selectbox("Selecciona bóveda a eliminar", options=list(vaults_to_display.keys()), index=None, placeholder="Elige una bóveda...", key='remove_vault_select')
        if vault_to_remove:
            if st.button(f"🗑️ Eliminar '{vault_to_remove}'", key=f'remove_btn_{vault_to_remove}', type="secondary"):
                if config_handler.remove_vault(vault_to_remove):
                    st.success(f"Bóveda '{vault_to_remove}' eliminada.")
                    st.session_state.saved_vaults = config_handler.get_vaults()
                    if st.session_state.selected_vault_name == vault_to_remove:
                        st.session_state.selected_vault_name = None
                        st.session_state.last_vault_name = None
                    st.rerun()
                else: st.error(f"No se pudo eliminar '{vault_to_remove}'.")

st.caption(f"Obsidian Context Builder - v0.4.0")