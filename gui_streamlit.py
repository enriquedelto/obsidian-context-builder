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

# ... (Configuración de página, título, funciones auxiliares sin cambios) ...
# --- Funciones Auxiliares ---
def display_template_content(template_name: Optional[str]):
    # ... (sin cambios) ...
    content = ""
    error_msg = None
    if template_name:
        try:
            content = prompt_handler.load_template(template_name)
        except ValueError as e:
            error_msg = f"Error: {e}"
        except Exception as e:
             error_msg = f"Error inesperado al cargar plantilla '{template_name}': {e}"

    if error_msg:
        st.error(error_msg)
    st.text_area(
        "Contenido Plantilla Seleccionada", content, height=150, disabled=True, key="template_preview_area_routes"
    )

def validate_and_get_targets(target_input_str: str, vault_path: Path) -> Tuple[List[str], List[str]]:
    # ... (sin cambios) ...
    raw_targets = [p.strip().strip('"') for p in target_input_str.splitlines() if p.strip()]
    valid_relative_targets = []
    invalid_targets = []
    vault_path_resolved = vault_path.resolve()

    for raw_target in raw_targets:
        try:
            target_path = Path(raw_target)
            if not target_path.is_absolute():
                abs_path = (vault_path_resolved / target_path).resolve()
            else:
                abs_path = target_path.resolve()

            if abs_path.exists() and abs_path.is_relative_to(vault_path_resolved):
                 relative_path_str = abs_path.relative_to(vault_path_resolved).as_posix()
                 valid_relative_targets.append(relative_path_str)
            else:
                 reason = "no existe" if not abs_path.exists() else "fuera de la bóveda"
                 print(f"Target inválido '{raw_target}' ({reason}): {abs_path}", file=sys.stderr)
                 invalid_targets.append(raw_target)
        except Exception as e:
            print(f"Error validando target '{raw_target}': {e}", file=sys.stderr)
            invalid_targets.append(raw_target)

    return valid_relative_targets, invalid_targets


# --- Carga Inicial y Estado de Sesión ---
if 'config_loaded' not in st.session_state:
    # ... (lógica de carga inicial sin cambios, pero añadir estado para modo selección) ...
    st.session_state.config = config_handler.load_config()
    st.session_state.saved_vaults = config_handler.get_vaults()
    st.session_state.available_templates = prompt_handler.get_available_templates()
    last_vault_info = config_handler.get_last_vault()
    st.session_state.last_vault_name = last_vault_info[0] if last_vault_info else None
    st.session_state.config_loaded = True
    if 'selected_vault_name' not in st.session_state:
         st.session_state.selected_vault_name = st.session_state.last_vault_name
    if 'selected_template_name' not in st.session_state:
        templates_keys = list(st.session_state.available_templates.keys())
        default_prefs = ["Archivo: GenerarNota", "Archivo: EnriquecerNota", "Archivo: ResumenConceptosClave"]
        st.session_state.selected_template_name = next((t for t in default_prefs if t in templates_keys), templates_keys[0] if templates_keys else None)
    # <<< NUEVO: Estado para el modo de selección de bóveda >>>
    if 'vault_selection_mode' not in st.session_state:
        st.session_state.vault_selection_mode = "Guardada" # Por defecto
    if 'manual_vault_path' not in st.session_state:
        st.session_state.manual_vault_path = ""


# --- Barra Lateral (Configuración Principal) ---
with st.sidebar:
    st.header("⚙️ Configuración Principal")

    # --- Selección de Modo: Bóveda Guardada o Manual ---
    st.session_state.vault_selection_mode = st.radio(
        "Fuente de la Bóveda:",
        options=["Guardada", "Manual"],
        key='vault_mode_radio',
        horizontal=True,
        index=0 if st.session_state.vault_selection_mode == "Guardada" else 1
    )

    # --- Selección de Bóveda (Condicional) ---
    if st.session_state.vault_selection_mode == "Guardada":
        st.session_state.manual_vault_path = "" # Limpiar ruta manual si se cambia a guardada
        vault_names = list(st.session_state.saved_vaults.keys())
        current_selection_index = 0
        if st.session_state.selected_vault_name and st.session_state.selected_vault_name in vault_names:
             try: current_selection_index = vault_names.index(st.session_state.selected_vault_name)
             except ValueError: st.session_state.selected_vault_name = None

        selected_vault_name_from_selectbox = st.selectbox(
            "Selecciona Bóveda Guardada",
            options=vault_names,
            index=current_selection_index if vault_names else 0,
            key='sb_vault_select_ui',
            help="Selecciona una bóveda previamente guardada.",
            placeholder="Añade una bóveda abajo...",
            disabled=not vault_names
        )
        # Actualizar estado SOLO si cambia y es válido
        if vault_names and selected_vault_name_from_selectbox != st.session_state.get('selected_vault_name'):
             st.session_state.selected_vault_name = selected_vault_name_from_selectbox

    # --- Entrada de Ruta Manual (Condicional) ---
    elif st.session_state.vault_selection_mode == "Manual":
        st.session_state.selected_vault_name = None # Limpiar selección guardada
        st.session_state.manual_vault_path = st.text_input(
            "Introduce la Ruta Completa a la Bóveda",
            value=st.session_state.manual_vault_path, # Mantener valor entre reruns
            key='sb_manual_vault_path_input',
            placeholder="Ej: C:\\Obsidian\\TemporalVault",
            help="Pega la ruta absoluta al directorio raíz de la bóveda a usar."
        ).strip()

    # --- Selección de Plantilla (sin cambios en su lógica) ---
    # ... (código de selección de plantilla sin cambios) ...
    template_names = list(st.session_state.available_templates.keys())
    current_template_index = 0
    template_display_names = { name: f"📄 {Path(st.session_state.available_templates[name]).stem}" for name in template_names if name.startswith("Archivo:") }
    display_list = list(template_display_names.values())
    name_to_display_map = {v: k for k, v in template_display_names.items()}
    current_display_name = template_display_names.get(st.session_state.selected_template_name)
    if current_display_name and current_display_name in display_list:
         try: current_template_index = display_list.index(current_display_name)
         except ValueError: st.session_state.selected_template_name = None
    selected_display_name = st.selectbox( "Selecciona Plantilla de Prompt", options=display_list, index=current_template_index if display_list else 0, key='sb_template_select_ui', help="Elige plantilla de /templates.", placeholder="No hay plantillas .txt en /templates...", disabled=not display_list )
    selected_template_name_real = name_to_display_map.get(selected_display_name) if selected_display_name else None
    if selected_template_name_real and selected_template_name_real != st.session_state.get('selected_template_name'):
        st.session_state.selected_template_name = selected_template_name_real


    # --- Ruta Nota Destino (sin cambios) ---
    output_note_path_str = st.text_input(
        "Ruta Relativa Nota Destino*",
        placeholder="Carpeta/Subcarpeta/MiNuevaNota.md",
        key='input_output_note_path',
        help="Ruta dentro de la bóveda donde se crearía/ubicaría la nota (obligatorio)."
    ).strip()

# --- Área Principal (Entrada y Salida) ---
# ... (col1 y col2 sin cambios: target_paths_input_str, extensions_str, output_mode, output_file_str, display_template_content) ...
col1, col2 = st.columns(2)
with col1:
    st.subheader("🎯 Rutas de Contexto (Targets)")
    target_paths_input_str = st.text_area( "Pegar Rutas (1 por línea)", height=200, key='input_target_paths_manual', placeholder="Ejemplos:\nAsignaturas/Cálculo\nNotas Diarias/2024-01-15.md\nD:\\Obsidian\\MiBoveda\\Proyectos\\ProyectoX.md\n\n(Dejar vacío para usar toda la bóveda)", help="Pega rutas relativas (a la bóveda) o absolutas de carpetas/archivos a incluir. Una por línea. Vacío = toda la bóveda." )
    st.subheader("⚙️ Opciones de Generación")
    extensions_str = st.text_input( "Extensiones a incluir", " ".join(DEFAULT_EXTENSIONS), key='input_extensions_main', help="Extensiones a buscar DENTRO de carpetas target. Separa con espacio (ej: .md .canvas)." )
    output_mode = st.selectbox( "Modo Contexto", ['both', 'tree', 'content'], index=0, key='select_output_mode_main', help="Qué incluir en {contexto_extraido}" )
with col2:
    st.subheader("📄 Previsualización y Salida")
    output_file_str = st.text_input( "Guardar Prompt en Archivo (opcional)", placeholder="/ruta/completa/o/relativa/prompt.txt", key='input_output_file_main' ).strip()
    display_template_content(st.session_state.get('selected_template_name'))


st.divider()

# --- Botón de Generación y Lógica Principal ---
# Determinar si hay una bóveda válida seleccionada o introducida para habilitar el botón
vault_ready = False
if st.session_state.vault_selection_mode == "Guardada":
    vault_ready = st.session_state.get('selected_vault_name') is not None
elif st.session_state.vault_selection_mode == "Manual":
    vault_ready = st.session_state.get('manual_vault_path') != ""

if st.button("🚀 Generar Prompt", type="primary", use_container_width=True, disabled=not vault_ready):

    # --- Recoger y Validar Entradas ---
    final_vault_name = None
    vault_path: Optional[Path] = None
    used_manual_path = False # Flag

    # Validar Bóveda según el modo seleccionado
    if st.session_state.vault_selection_mode == "Guardada":
        final_vault_name = st.session_state.get('selected_vault_name')
        if not final_vault_name:
            st.error("❌ Selecciona una bóveda guardada válida.")
            st.stop()
        if final_vault_name not in st.session_state.saved_vaults:
             st.error(f"❌ La bóveda guardada '{final_vault_name}' ya no existe en la configuración.")
             st.stop()
        try:
            vault_path = Path(st.session_state.saved_vaults[final_vault_name]).resolve()
            if not vault_path.is_dir():
                st.error(f"❌ La ruta guardada para '{final_vault_name}' ya no es un directorio válido.")
                st.stop()
        except Exception as e:
            st.error(f"❌ Error al procesar ruta de bóveda guardada '{final_vault_name}': {e}")
            st.stop()

    elif st.session_state.vault_selection_mode == "Manual":
        manual_path_str = st.session_state.get('manual_vault_path')
        if not manual_path_str:
             st.error("❌ Introduce la ruta completa a la bóveda manual.")
             st.stop()
        try:
            vault_path = Path(manual_path_str).resolve()
            if not vault_path.is_dir():
                 st.error(f"❌ La ruta manual '{manual_path_str}' no es un directorio válido.")
                 st.stop()
            final_vault_name = f"(Ruta Manual: {vault_path.name})" # Nombre descriptivo
            used_manual_path = True
        except Exception as e:
             st.error(f"❌ Error al procesar la ruta manual '{manual_path_str}': {e}")
             st.stop()

    # Validar otras entradas
    final_template_name = st.session_state.get('selected_template_name')
    validation_ok = True
    if not vault_path: # Ya validado arriba, pero por seguridad
        st.error("❌ No se pudo determinar una bóveda válida."); validation_ok = False
    if not final_template_name:
        st.error("❌ Selecciona una plantilla válida."); validation_ok = False
    if not output_note_path_str:
        st.error("❌ 'Ruta Relativa Nota Destino' es obligatoria."); validation_ok = False

    if validation_ok:
        try:
            # --- Procesar Targets, Cargar Plantilla, Procesar Opciones ---
            # ... (sin cambios: validate_and_get_targets, load_template, extensiones) ...
            valid_targets, invalid_targets = validate_and_get_targets(target_paths_input_str, vault_path)
            if invalid_targets:
                 st.warning(f"Se ignoraron las siguientes rutas objetivo inválidas o fuera de la bóveda:")
                 for invalid in invalid_targets: st.code(invalid)
            if not valid_targets and target_paths_input_str.strip():
                 st.warning("⚠️ Ninguna ruta objetivo válida proporcionada. Se usará toda la bóveda.")
            elif not valid_targets and not target_paths_input_str.strip():
                 st.info("ℹ️ No se especificaron rutas objetivo. Se usará toda la bóveda.")

            template_content = prompt_handler.load_template(final_template_name)
            input_extensions = [e.strip() for e in extensions_str.split() if e.strip()]
            extensions = [f".{e.lstrip('.')}" for e in input_extensions] if input_extensions else DEFAULT_EXTENSIONS

            # --- Validar y Convertir Ruta Destino ---
            # ... (sin cambios: conversión a relativo) ...
            output_note_path_relative: Path
            try:
                temp_path = Path(output_note_path_str)
                if temp_path.is_absolute():
                    output_note_path_relative = temp_path.relative_to(vault_path.resolve())
                    st.info(f"Nota: Ruta destino absoluta convertida a relativa: {output_note_path_relative}")
                else:
                    clean_relative_str = output_note_path_str.lstrip('/\\')
                    if clean_relative_str != output_note_path_str:
                         st.info(f"Nota: Limpiando separador inicial de ruta destino a: {clean_relative_str}")
                    output_note_path_relative = Path(clean_relative_str)
            except ValueError:
                st.error(f"❌ La ruta destino absoluta '{output_note_path_str}' no está dentro de la bóveda '{vault_path}'."); st.stop()
            except Exception as e:
                st.error(f"❌ Error procesando ruta destino '{output_note_path_str}': {e}"); st.stop()


            # --- LLAMADA A CORE ---
            with st.spinner("⚙️ Generando contexto y prompt... Por favor espera."):
                final_prompt = generate_prompt_core(
                    vault_path=vault_path,
                    target_paths=valid_targets,
                    extensions=extensions,
                    output_mode=output_mode,
                    output_note_path=output_note_path_relative,
                    template_string=template_content
                )

            st.success("✅ ¡Prompt generado!")
            st.subheader("Resultado")
            st.text_area("Prompt Final:", final_prompt, height=400, key="prompt_output_area_gui_result")

            # --- Guardar Archivo (Opcional) ---
            # ... (sin cambios) ...
            if output_file_str:
                try:
                    output_path = Path(output_file_str)
                    if not output_path.is_absolute(): output_path = Path.cwd() / output_path
                    output_path = output_path.resolve()
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(final_prompt, encoding='utf-8')
                    st.success(f"💾 Prompt guardado en: `{output_path}`")
                except Exception as e:
                    st.error(f"❌ Error al guardar archivo '{output_file_str}': {e}")


            # --- Actualizar Última Bóveda Usada (¡SOLO SI NO ES MANUAL!) ---
            if not used_manual_path and st.session_state.vault_selection_mode == "Guardada":
                current_selected_vault_name = st.session_state.get('selected_vault_name')
                if current_selected_vault_name: # Asegurarse de que hay un nombre seleccionado
                    config_handler.set_last_vault(current_selected_vault_name)
                    st.session_state.last_vault_name = current_selected_vault_name

        except ValueError as ve:
            st.error(f"❌ Error Config/Validación: {ve}")
        except Exception as e:
            st.error(f"❌ Error Inesperado:")
            st.exception(e)

# --- Sección de Gestión de Bóvedas ---
# ... (sin cambios) ...
with st.expander("⚙️ Gestionar Bóvedas Guardadas"):
    # ... (Código para añadir/eliminar bóvedas guardadas sin cambios) ...
    st.subheader("Añadir/Actualizar Bóveda")
    col_add1, col_add2 = st.columns([1, 2])
    with col_add1: new_vault_name = st.text_input("Nombre Corto*", key='add_vault_name', placeholder="Ej: Personal")
    with col_add2: new_vault_path_str = st.text_input("Ruta Completa al Directorio*", key='add_vault_path', placeholder="Ej: C:\\Users\\Tu\\Obsidian\\Personal")
    if st.button("💾 Guardar Bóveda", key='add_vault_button'):
        error = False
        if not new_vault_name: st.error("Nombre obligatorio."); error = True
        if not new_vault_path_str: st.error("Ruta obligatoria."); error = True
        elif not Path(new_vault_path_str).is_dir(): st.error("Ruta inválida o no es directorio."); error = True
        if not error:
            if config_handler.add_vault(new_vault_name, new_vault_path_str):
                 st.success(f"Bóveda '{new_vault_name}' guardada/actualizada.")
                 st.session_state.saved_vaults = config_handler.get_vaults()
                 st.session_state.selected_vault_name = new_vault_name # Seleccionar la nueva
                 st.session_state.vault_selection_mode = "Guardada" # Cambiar a modo guardada
                 st.rerun()
    st.divider()
    st.subheader("Eliminar Bóveda Guardada")
    vaults_to_display_remove = st.session_state.get('saved_vaults', {})
    if not vaults_to_display_remove: st.caption("No hay bóvedas guardadas.")
    else:
        vault_to_remove = st.selectbox("Selecciona bóveda a eliminar", options=list(vaults_to_display_remove.keys()), index=None, placeholder="Elige...", key='remove_vault_select')
        if vault_to_remove:
            st.warning(f"¿Seguro que quieres eliminar '{vault_to_remove}'?")
            if st.button(f"🗑️ Sí, Eliminar '{vault_to_remove}'", key=f'remove_btn_{vault_to_remove}', type="secondary"):
                if config_handler.remove_vault(vault_to_remove):
                    st.success(f"Bóveda '{vault_to_remove}' eliminada.")
                    st.session_state.saved_vaults = config_handler.get_vaults()
                    if st.session_state.get('selected_vault_name') == vault_to_remove: st.session_state.selected_vault_name = None
                    if st.session_state.get('last_vault_name') == vault_to_remove: st.session_state.last_vault_name = None
                    # No es necesario tocar el config aquí, remove_vault ya lo hace
                    st.rerun()

st.divider()
st.caption(f"Obsidian Context Builder - v0.7.0") # Versión actualizada