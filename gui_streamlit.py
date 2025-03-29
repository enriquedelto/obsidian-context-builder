# gui_streamlit.py (simplificado)
import streamlit as st
from pathlib import Path
# Importar funciones de tus otros módulos
import file_handler
import tree_generator
import formatter
import prompt_handler
# Quizás una función refactorizada de main.py
# from main import run_generation 

st.title("Obsidian Context Builder")

# Widgets para obtener entradas
vault_path_str = st.text_input("Ruta de la Bóveda Obsidian", "/ruta/por/defecto") 
# (Mejor sería un selector de carpetas, Streamlit tiene componentes extra para eso)

target_paths_str = st.text_area("Rutas Objetivo (una por línea, relativas a la bóveda)", "Asignaturas/Sistemas Operativos\nEnciclopedia")
extensions_str = st.text_input("Extensiones (separadas por espacio, ej: .md .canvas)", ".md")

output_mode = st.selectbox("Modo de Contexto", ['both', 'tree', 'content'])
output_note_path_str = st.text_input("Ruta Relativa Nota Destino", "Asignaturas/Sistemas Operativos/NuevaNota.md")

prompt_option = st.radio("Fuente de Plantilla", ["Archivo", "Texto Directo"])
template_content = ""
if prompt_option == "Archivo":
    uploaded_file = st.file_uploader("Cargar archivo de plantilla (.txt)", type="txt")
    if uploaded_file is not None:
        template_content = uploaded_file.read().decode("utf-8")
else:
    template_content = st.text_area("Introduce la plantilla del prompt aquí", "Contexto:\n{contexto_extraido}\n\nTarea:")

output_file_str = st.text_input("Archivo de Salida para Prompt (opcional)", "")

if st.button("Generar Prompt"):
    if not vault_path_str or not output_note_path_str or not template_content:
        st.error("Por favor, completa la ruta de la bóveda, la ruta de la nota destino y proporciona una plantilla.")
    else:
        vault_path = Path(vault_path_str)
        # ... (procesar targets, extensions, etc.) ...
        
        # --- Llamar a la lógica principal (refactorizada) ---
        # Necesitarías una función que tome todos estos params y devuelva el final_prompt
        # final_prompt = run_generation(vault_path, targets, extensions, ...) 
        # --- Simulación por ahora ---
        st.info("Generando prompt... (Lógica principal no conectada en este ejemplo)")
        # (Aquí iría la llamada real a tu lógica de main.py adaptada)
        
        # Supongamos que obtenemos el prompt final
        final_prompt_example = f"Plantilla recibida:\n{template_content}\n\n(Contexto iría aquí basado en modo {output_mode})" # Placeholder
        
        st.subheader("Prompt Generado:")
        st.text_area("Resultado", final_prompt_example, height=300)
        
        if output_file_str:
            try:
                output_path = Path(output_file_str)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(final_prompt_example) # Usar el prompt real
                st.success(f"Prompt guardado en: {output_path.resolve()}")
            except Exception as e:
                st.error(f"Error al guardar el archivo: {e}")