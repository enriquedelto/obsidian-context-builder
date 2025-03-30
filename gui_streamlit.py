# gui_streamlit.py (Modificado Completo)
import streamlit as st
from pathlib import Path
import sys
import traceback

# Importar lógica
import file_handler
import tree_generator
import formatter
import prompt_handler
import config_handler # <-- NUEVO
from main import generate_prompt_core, DEFAULT_PLACEHOLDERS # Importar la función core

st.set_page_config(layout="wide") # Usar layout ancho
st.title("Obsidian Context Builder 🔨")
st.caption("Genera prompts para LLMs usando el contexto de tu bóveda Obsidian.")

# --- Carga Inicial de Configuración ---
config = config_handler.load_config()
saved_vaults = config_handler.get_vaults()
available_templates = prompt_handler.get_available_templates()

# --- Estado de la Sesión (para mantener selecciones) ---
if 'last_vault_name' not in st.session_state:
    last_vault_info = config_handler.get_last_vault()
    st.session_state.last_vault_name = last_vault_info[0] if last_vault_info else None

if 'selected_vault_name' not in st.session_state:
    st.session_state.selected_vault_name = st.session_state.last_vault_name

if 'selected_template_name' not in st.session_state:
     # Intentar poner un default razonable si existe
     default_template_prefs = ["Generar Nota Completa (Original)", "Generar Nota Simple"]
     st.session_state.selected_template_name = next((t for t in default_template_prefs if t in available_templates), list(available_templates.keys())[0] if available_templates else None)


# --- Barra Lateral para Configuración Principal ---
with st.sidebar:
    st.header("Configuración Principal")

    # --- Selección de Bóveda ---
    vault_names = list(saved_vaults.keys())
    last_vault_index = vault_names.index(st.session_state.selected_vault_name) if st.session_state.selected_vault_name in vault_names else 0
    if not vault_names:
        st.warning("No hay bóvedas guardadas. Añade una en 'Gestionar Bóvedas'.")
        selected_vault_name = None
    else:
         selected_vault_name = st.selectbox(
             "Selecciona la Bóveda Obsidian",
             options=vault_names,
             index=last_vault_index,
             key='sb_vault_select', # Key para acceder al valor
             help="Selecciona una bóveda previamente guardada."
         )
         st.session_state.selected_vault_name = selected_vault_name # Actualizar estado


    # --- Selección de Plantilla ---
    template_names = list(available_templates.keys())
    if not template_names:
        st.warning("No hay plantillas disponibles (ni predeterminadas ni en /templates).")
        selected_template_name = None
    else:
        # Intentar encontrar el índice del último seleccionado o el default
        try:
            current_template_index = template_names.index(st.session_state.selected_template_name) if st.session_state.selected_template_name in template_names else 0
        except ValueError:
             current_template_index = 0 # Fallback si el estado tenía algo inválido

        # Limpiar nombre de archivo para mostrar en selectbox
        template_display_names = {
             name: (f"Archivo: {Path(available_templates[name]).name}" if name.startswith("Archivo:") else name)
             for name in template_names
        }
        display_list = [template_display_names[name] for name in template_names]

        selected_display_name = st.selectbox(
             "Selecciona la Plantilla de Prompt",
             options=display_list,
             index=current_template_index,
             help="Elige una plantilla predefinida o un archivo de la carpeta /templates."
         )
        # Encontrar el nombre original basado en el display name seleccionado
        selected_template_name = next((name for name, display in template_display_names.items() if display == selected_display_name), None)
        st.session_state.selected_template_name = selected_template_name # Actualizar estado

    # --- Ruta de Nota Destino ---
    output_note_path_str = st.text_input(
        "Ruta Relativa Nota Destino",
        placeholder="Carpeta/Subcarpeta/NotaNueva.md",
        help="Ruta dentro de la bóveda para la nota a generar/analizar (obligatorio)."
    )

# --- Área Principal para Detalles y Salida ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Contexto Específico")
    target_paths_str = st.text_area("Rutas Objetivo (relativas, una por línea)", height=100, help="Deja vacío para usar toda la bóveda seleccionada.")
    extensions_str = st.text_input("Extensiones", ".md", help="Separadas por espacio, ej: .md .canvas")
    output_mode = st.selectbox("Modo de Contexto", ['both', 'tree', 'content'], index=0, help="Qué incluir en {contexto_extraido}")

with col2:
    st.subheader("Salida del Prompt")
    output_file_str = st.text_input("Guardar Prompt en Archivo (opcional)", placeholder="/ruta/completa/prompt.txt")
    # Previsualización de Plantilla Seleccionada
    st.caption("Plantilla Seleccionada:")
    current_template_content = ""
    if selected_template_name:
         try:
            current_template_content = prompt_handler.load_template(selected_template_name)
            st.text_area("Contenido Plantilla", current_template_content, height=150, disabled=True, key="template_preview")
         except ValueError as e:
             st.error(f"Error al cargar plantilla '{selected_template_name}': {e}")
    else:
        st.text("Ninguna plantilla seleccionada.")


st.divider()

# --- Botón de Generación y Lógica ---
if st.button("🚀 Generar Prompt", type="primary", use_container_width=True):
    # --- Validaciones ---
    vault_path = Path(saved_vaults[selected_vault_name]) if selected_vault_name and selected_vault_name in saved_vaults else None

    if not selected_vault_name or not vault_path:
        st.error("❌ Debes seleccionar una bóveda válida en la barra lateral.")
    elif not vault_path.is_dir():
        st.error(f"❌ La ruta de la bóveda seleccionada ('{selected_vault_name}': {vault_path}) no es válida.")
    elif not selected_template_name:
        st.error("❌ Debes seleccionar una plantilla válida en la barra lateral.")
    elif not output_note_path_str:
        st.error("❌ La ruta relativa de la nota destino es obligatoria.")
    elif not current_template_content: # Verificar que la plantilla se cargó bien
        st.error("❌ No se pudo cargar el contenido de la plantilla seleccionada.")
    else:
        # --- Preparar Parámetros ---
        try:
            vault_path = vault_path.resolve() # Asegurar ruta absoluta
            targets = [p.strip() for p in target_paths_str.split('\n') if p.strip()]
            input_extensions = [e.strip() for e in extensions_str.split() if e.strip()]
            extensions = [f".{e.lstrip('.')}" for e in input_extensions] if input_extensions else DEFAULT_EXTENSIONS

            output_note_path = Path(output_note_path_str)
            if output_note_path.is_absolute():
                 try:
                     output_note_path = output_note_path.relative_to(vault_path)
                 except ValueError:
                      st.error(f"❌ La ruta de nota destino absoluta ({output_note_path_str}) no está dentro de la bóveda ({vault_path}). Proporciona una ruta relativa.")
                      st.stop()

            # --- LLAMADA A LA LÓGICA CORE ---
            with st.spinner("⚙️ Generando contexto y prompt..."):
                 final_prompt = generate_prompt_core(
                    vault_path=vault_path,
                    target_paths=targets,
                    extensions=extensions,
                    output_mode=output_mode,
                    output_note_path=output_note_path,
                    template_string=current_template_content # Usar el contenido cargado
                )
            # --- FIN LLAMADA CORE ---

            st.success("✅ ¡Prompt generado con éxito!")

            st.subheader("Prompt Resultante:")
            st.text_area("Prompt Final", final_prompt, height=400, key="prompt_output_area_gui")
            # st.code(final_prompt, language=None) # Alternativa con copia fácil

            # Guardar archivo si se especificó
            if output_file_str:
                output_path = Path(output_file_str)
                try:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(final_prompt)
                    st.success(f"💾 Prompt guardado en: {output_path.resolve()}")
                except Exception as e:
                    st.error(f"❌ Error al guardar el archivo '{output_file_str}': {e}")

            # Guardar la bóveda usada como la última en la configuración
            if selected_vault_name:
                config_handler.set_last_vault(selected_vault_name)
                st.session_state.last_vault_name = selected_vault_name # Actualizar estado para la UI

        except Exception as e:
            st.error(f"❌ Ocurrió un error inesperado durante la generación:")
            st.exception(e)

st.divider()

# --- Sección de Gestión de Bóvedas ---
with st.expander("⚙️ Gestionar Bóvedas Guardadas"):
    st.subheader("Añadir Nueva Bóveda")
    with st.form("add_vault_form", clear_on_submit=True):
        new_vault_name = st.text_input("Nombre Corto para la Bóveda")
        new_vault_path_str = st.text_input("Ruta Completa a la Bóveda")
        submitted_add = st.form_submit_button("Añadir Bóveda")
        if submitted_add:
            if not new_vault_name:
                st.error("El nombre no puede estar vacío.")
            elif not new_vault_path_str:
                 st.error("La ruta no puede estar vacía.")
            elif not Path(new_vault_path_str).is_dir():
                st.error(f"La ruta '{new_vault_path_str}' no es un directorio válido.")
            elif new_vault_name in saved_vaults:
                st.warning(f"Ya existe una bóveda con el nombre '{new_vault_name}'. Se actualizará la ruta.")
                if config_handler.add_vault(new_vault_name, new_vault_path_str):
                     st.success(f"Ruta de la bóveda '{new_vault_name}' actualizada.")
                     st.rerun() # Recargar para actualizar selectbox
                else:
                     st.error("No se pudo actualizar la bóveda.") # El error ya se imprimió en consola
            else:
                if config_handler.add_vault(new_vault_name, new_vault_path_str):
                     st.success(f"Bóveda '{new_vault_name}' añadida.")
                     st.rerun() # Recargar para actualizar selectbox
                else:
                    st.error("No se pudo añadir la bóveda.")

    st.subheader("Eliminar Bóveda Guardada")
    if not saved_vaults:
        st.caption("No hay bóvedas guardadas para eliminar.")
    else:
        vault_to_remove = st.selectbox("Selecciona bóveda a eliminar", options=list(saved_vaults.keys()), index=None, placeholder="Elige una bóveda...")
        if vault_to_remove:
            if st.button(f"Eliminar '{vault_to_remove}'", type="secondary"):
                if config_handler.remove_vault(vault_to_remove):
                    st.success(f"Bóveda '{vault_to_remove}' eliminada.")
                    # Limpiar selección si era la eliminada
                    if st.session_state.selected_vault_name == vault_to_remove:
                        st.session_state.selected_vault_name = None
                        st.session_state.last_vault_name = None # Asegurar que se limpie
                    st.rerun() # Recargar
                else:
                    st.error(f"No se pudo eliminar la bóveda '{vault_to_remove}'.")