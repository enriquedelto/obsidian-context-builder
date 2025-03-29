# gui_streamlit.py (Modificado)
import streamlit as st
from pathlib import Path
import sys
import traceback # Para mostrar errores detallados

# Importar funciones y LA NUEVA LÓGICA CORE
import file_handler
import tree_generator
import formatter
import prompt_handler
from main import generate_prompt_core, DEFAULT_PLACEHOLDERS # Importar la función y placeholders

st.title("Obsidian Context Builder")
st.write("Genera prompts para LLMs usando el contexto de tu bóveda Obsidian.")

# --- Sección de Entradas ---
with st.expander("Configuración de Entradas", expanded=True):
    vault_path_str = st.text_input("Ruta de la Bóveda Obsidian", placeholder="/ruta/a/tu/boveda")

    target_paths_str = st.text_area("Rutas Objetivo (una por línea, relativas a la bóveda)", help="Deja vacío para usar toda la bóveda.")
    extensions_str = st.text_input("Extensiones (separadas por espacio, ej: .md .canvas)", ".md")

    output_mode = st.selectbox("Modo de Contexto", ['both', 'tree', 'content'], index=0, help="Qué incluir en {contexto_extraido}") # Default 'both'
    output_note_path_str = st.text_input("Ruta Relativa Nota Destino", placeholder="Carpeta/Subcarpeta/NombreNota.md", help="Ruta relativa a la bóveda. Usada para tema y etiquetas.")

    prompt_option = st.radio("Fuente de Plantilla", ["Archivo", "Texto Directo"], horizontal=True)
    template_content = ""
    if prompt_option == "Archivo":
        uploaded_file = st.file_uploader("Cargar archivo de plantilla (.txt)", type="txt")
        if uploaded_file is not None:
            try:
                template_content = uploaded_file.read().decode("utf-8")
                st.caption("Plantilla cargada desde archivo.")
            except Exception as e:
                 st.error(f"Error al leer el archivo de plantilla: {e}")
    else: # Texto directo
        template_content = st.text_area("Introduce la plantilla del prompt aquí (usa placeholders como {contexto_extraido}, {ruta_destino})", height=150)

    output_file_str = st.text_input("Archivo de Salida para Prompt (opcional)", placeholder="/ruta/completa/prompt_generado.txt")

# --- Botón de Generación y Lógica ---
if st.button("🚀 Generar Prompt", use_container_width=True):
    # Validaciones
    if not vault_path_str:
        st.error("❌ La ruta de la bóveda es obligatoria.")
    elif not Path(vault_path_str).is_dir():
         st.error(f"❌ La ruta de la bóveda no existe o no es un directorio: {vault_path_str}")
    elif not output_note_path_str:
        st.error("❌ La ruta relativa de la nota destino es obligatoria.")
    elif not template_content:
        st.error("❌ Debes proporcionar una plantilla (desde archivo o texto directo).")
    else:
        try:
            # Preparar parámetros para la lógica core
            vault_path = Path(vault_path_str).resolve()
            targets = [p.strip() for p in target_paths_str.split('\n') if p.strip()]
            # Usar default si está vacío, asegurar punto inicial
            input_extensions = [e.strip() for e in extensions_str.split() if e.strip()]
            extensions = [f".{e.lstrip('.')}" for e in input_extensions] if input_extensions else ['.md']

            # Asegurar que output_note_path es relativo
            output_note_path = Path(output_note_path_str)
            if output_note_path.is_absolute():
                 try:
                     output_note_path = output_note_path.relative_to(vault_path)
                 except ValueError:
                      st.error(f"❌ La ruta de nota destino absoluta ({output_note_path_str}) no está dentro de la bóveda ({vault_path}). Proporciona una ruta relativa.")
                      st.stop() # Detener ejecución

            # --- LLAMADA A LA LÓGICA CORE ---
            with st.spinner("Generando contexto y prompt..."):
                 final_prompt = generate_prompt_core(
                    vault_path=vault_path,
                    target_paths=targets,
                    extensions=extensions,
                    output_mode=output_mode,
                    output_note_path=output_note_path,
                    template_string=template_content
                )
            # --- FIN LLAMADA CORE ---

            st.success("✅ ¡Prompt generado con éxito!")

            st.subheader("Prompt Resultante:")
            st.text_area("Prompt Final", final_prompt, height=400, key="prompt_output_area")
            # Añadir botón de copiar
            # st.code(final_prompt, language=None) # Otra forma de mostrar con botón de copia fácil


            if output_file_str:
                output_path = Path(output_file_str)
                try:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(final_prompt)
                    st.success(f"💾 Prompt guardado en: {output_path.resolve()}")
                except Exception as e:
                    st.error(f"❌ Error al guardar el archivo '{output_file_str}': {e}")

        except Exception as e:
            st.error(f"❌ Ocurrió un error inesperado durante la generación:")
            st.exception(e) # Muestra el error y el traceback en la UI