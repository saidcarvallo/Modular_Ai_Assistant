from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from app.config import settings
from app.core.assistant import AetherAssistant
from app.memory.database import init_db
from app.memory.models import Note, Reminder, Task
from app.tools.documents import DocumentTool

init_db()

st.set_page_config(page_title="Aether AI Assistant", page_icon="✨", layout="wide")

if "aether_assistant" not in st.session_state:
    st.session_state["aether_assistant"] = AetherAssistant(provider_name=settings.active_provider)
assistant = st.session_state["aether_assistant"]

st.title("Aether AI Personal Assistant")

with st.sidebar:
    st.subheader("Configuración")
    st.caption(f"Proveedor activo: {assistant.provider_name}")
    st.caption(f"Modelo Gemini: {settings.gemini_model}")
    st.caption(f"Modelo Ollama: {settings.ollama_model}")
    st.caption(f"Base de datos: {settings.database_url}")

    provider_choice = st.selectbox("Proveedor", ["gemini", "ollama"], index=0 if assistant.provider_name == "gemini" else 1)
    if st.button("Aplicar proveedor"):
        assistant.provider_name = provider_choice
        assistant.provider_manager.active_provider = provider_choice
        st.session_state["provider_notice"] = f"Proveedor activo: {provider_choice}"

    if "provider_notice" in st.session_state:
        st.success(st.session_state["provider_notice"])

    if st.button("Ver resumen de memoria"):
        st.session_state["memory_summary"] = assistant.get_memory_summary()

    if "memory_summary" in st.session_state:
        st.json(st.session_state["memory_summary"])

st.subheader("Resumen rápido")
metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
with metrics_col1:
    st.metric("Tareas", assistant.memory.session.query(Task).count())
with metrics_col2:
    st.metric("Notas", assistant.memory.session.query(Note).count())
with metrics_col3:
    st.metric("Recordatorios", assistant.memory.session.query(Reminder).count())

chat_tab, tasks_tab, notes_tab, reminders_tab, documents_tab, providers_tab = st.tabs(["Chat", "Tareas", "Notas", "Recordatorios", "Documentos", "Proveedores"])

with chat_tab:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Escribe tu mensaje...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        response = assistant.send_message(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

with tasks_tab:
    with st.form("task_form", clear_on_submit=True):
        task_title = st.text_input("Título")
        task_description = st.text_area("Descripción", height=80)
        submitted = st.form_submit_button("Crear tarea")
        if submitted and task_title:
            assistant.memory.add_task(task_title, task_description or None)
            st.success(f"Tarea creada: {task_title}")

    tasks = assistant.memory.session.query(Task).order_by(Task.created_at.desc()).all()
    if not tasks:
        st.info("No hay tareas todavía.")
    else:
        for task in tasks:
            with st.container():
                col_a, col_b, col_c = st.columns([3, 1, 1])
                with col_a:
                    st.write(f"**{task.title}**")
                    if task.description:
                        st.write(task.description)
                    st.caption("Completada" if task.completed else "Pendiente")
                with col_b:
                    if not task.completed:
                        if st.button("Completar", key=f"complete-task-{task.id}"):
                            assistant.memory.complete_task(task.id)
                            st.rerun()
                with col_c:
                    if st.button("Eliminar", key=f"delete-task-{task.id}"):
                        assistant.memory.delete_task(task.id)
                        st.rerun()

with notes_tab:
    with st.form("note_form", clear_on_submit=True):
        note_title = st.text_input("Título de la nota")
        note_body = st.text_area("Contenido", height=120)
        note_submitted = st.form_submit_button("Guardar nota")
        if note_submitted and note_title and note_body:
            assistant.memory.add_note(note_title, note_body)
            st.success(f"Nota guardada: {note_title}")

    notes = assistant.memory.session.query(Note).order_by(Note.created_at.desc()).all()
    if not notes:
        st.info("No hay notas guardadas.")
    else:
        for note in notes:
            with st.expander(f"{note.title}"):
                with st.form(f"edit_note_form_{note.id}"):
                    edited_title = st.text_input(
                        "Título",
                        value=note.title,
                        key=f"edit_note_title_{note.id}",
                    )
                    edited_body = st.text_area(
                        "Contenido",
                        value=note.body,
                        height=160,
                        key=f"edit_note_body_{note.id}",
                    )
                    save_note = st.form_submit_button("Guardar cambios")

                if save_note:
                    if not edited_title.strip() or not edited_body.strip():
                        st.error("El título y el contenido no pueden quedar vacíos.")
                    else:
                        assistant.memory.update_note(note.id, edited_title.strip(), edited_body.strip())
                        st.success("Nota actualizada.")
                        st.rerun()

                if st.button("Eliminar nota", key=f"delete_note_{note.id}"):
                    assistant.memory.delete_note(note.id)
                    st.rerun()

with reminders_tab:
    with st.form("reminder_form", clear_on_submit=True):
        reminder_message = st.text_input("Mensaje")
        reminder_time = st.text_input("Fecha y hora (ISO)", placeholder="2026-11-10T20:00:00")
        reminder_submitted = st.form_submit_button("Crear recordatorio")
        if reminder_submitted and reminder_message:
            assistant.memory.add_reminder(reminder_message, reminder_time or None)
            st.success(f"Recordatorio creado: {reminder_message}")

    reminders = assistant.memory.session.query(Reminder).order_by(Reminder.created_at.desc()).all()
    if not reminders:
        st.info("No hay recordatorios.")
    else:
        for reminder in reminders:
            st.markdown(f"- **{reminder.message}**")
            if reminder.scheduled_for:
                st.caption(f"Programado para: {reminder.scheduled_for}")
            if st.button("Eliminar recordatorio", key=f"delete-reminder-{reminder.id}"):
                assistant.memory.delete_reminder(reminder.id)
                st.rerun()

with documents_tab:
    st.subheader("Documentos")
    uploaded_file = st.file_uploader("Sube un documento para revisarlo", type=["txt", "md", "csv", "json", "pdf"])

    if uploaded_file is not None:
        suffix = Path(uploaded_file.name).suffix or ".txt"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            temp_path = Path(tmp_file.name)

        try:
            document_tool = DocumentTool()
            read_result = document_tool.read_document(str(temp_path))
            summary_result = document_tool.summarize_document(str(temp_path))

            st.write(f"**Archivo:** {uploaded_file.name}")
            if read_result.get("status") == "ok":
                st.caption(f"Palabras: {read_result.get('words', 0)} | Caracteres: {read_result.get('chars', 0)}")
                st.text_area("Vista previa", value=read_result.get("preview", ""), height=180)
            else:
                st.warning(read_result.get("message", "No se pudo leer el archivo."))

            if summary_result.get("status") == "summarized":
                st.markdown("### Resumen extractivo")
                st.write(summary_result.get("summary", ""))
        finally:
            temp_path.unlink(missing_ok=True)

with providers_tab:
    st.subheader("Proveedores")
    st.markdown("### Conectar con Google Gemini")
    st.write(
        "¿Aún no tienes una API key? Ábrela en Google AI Studio y luego vuelve aquí para pegarla."
    )
    st.link_button(
        "Crear API key en Google AI Studio",
        "https://aistudio.google.com/api-keys",
        help="Google puede pedirte iniciar sesión para crear una clave.",
    )
    gemini_server_key_configured = bool(settings.gemini_api_key)
    if gemini_server_key_configured:
        credential_mode = st.radio(
            "Cómo conectar",
            ["Usar la clave configurada automáticamente", "Ingresar mi propia API key"],
            horizontal=True,
            key="gemini_credential_mode",
        )
    else:
        credential_mode = "Ingresar mi propia API key"
        st.info(
            "No hay una clave automática configurada. Puedes conectar Gemini con tu API key "
            "o el administrador puede configurar GEMINI_API_KEY en el archivo .env del servidor."
        )

    with st.form("connect_gemini_form", clear_on_submit=True):
        personal_api_key = ""
        if credential_mode == "Ingresar mi propia API key":
            personal_api_key = st.text_input(
                "API key de Google Gemini",
                type="password",
                placeholder="Pega tu API key",
                help="La clave se mantiene en esta sesión y no se guarda en la base de datos.",
            )
        connect_gemini = st.form_submit_button("Conectar con Google Gemini")

    if connect_gemini:
        api_key = (
            settings.gemini_api_key
            if credential_mode == "Usar la clave configurada automáticamente"
            else personal_api_key.strip()
        )
        if not api_key:
            st.error("Introduce una API key válida o configura GEMINI_API_KEY en el servidor.")
        else:
            assistant.provider_manager.configure_provider(
                "gemini",
                api_key=api_key,
                enabled=True,
            )
            result = assistant.provider_manager.validate_provider("gemini")
            if result["healthy"]:
                assistant.provider_name = "gemini"
                assistant.provider_manager.active_provider = "gemini"
                st.success("Conexión con Google Gemini verificada. Ya puedes usar el chat.")
            else:
                status = result.get("status", {})
                st.error(
                    "No se pudo conectar con Google Gemini: "
                    f"{status.get('last_error') or 'revisa la API key y el modelo configurado.'}"
                )

    st.caption(
        "Las claves personales no se escriben en .env ni en la base de datos. "
        "Una clave automática la configura el administrador en el servidor."
    )
    st.markdown("---")
    provider_report = assistant.provider_manager.health_report()
    provider_list = assistant.provider_manager.list_config()

    for status in provider_report:
        provider_config = next((item for item in provider_list if item["provider"] == status.provider), {})
        state = "Disponible" if status.available else "No disponible"
        with st.container():
            st.markdown(f"### {status.provider.title()}")
            st.caption(f"Modelo: {provider_config.get('model', 'N/D')}")
            st.caption(f"Estado: {state}")
            st.caption(f"Activo: {'Sí' if provider_config.get('active') else 'No'}")
            st.caption(f"Solicitudes: {status.requests}")
            st.caption(f"Último éxito: {status.last_success or 'Ninguno'}")
            st.caption(f"Último error: {status.last_error or 'Ninguno'}")
            if status.available:
                st.success("Proveedor saludable")
            else:
                st.warning("Proveedor requiere atención")
            st.markdown("---")

    st.markdown("---")
    provider_name = st.selectbox("Proveedor a configurar", ["gemini", "ollama"], key="provider_config_name")
    provider_config = assistant.provider_manager.providers[provider_name].config
    model = st.text_input("Modelo", value=provider_config.model, key=f"provider_model_{provider_name}")
    host = st.text_input("Host", value=provider_config.host, key=f"provider_host_{provider_name}")
    enabled = st.checkbox(
        "Habilitado",
        value=provider_config.enabled,
        key=f"provider_enabled_{provider_name}",
    )

    if st.button("Guardar configuración del proveedor"):
        assistant.provider_manager.configure_provider(
            provider_name,
            model=model or None,
            host=host or None,
            enabled=enabled,
        )
        st.success(f"Configuración guardada para {provider_name}")

    if st.button("Validar proveedor"):
        result = assistant.provider_manager.validate_provider(provider_name)
        if result["healthy"]:
            assistant.provider_name = provider_name
            st.success(f"{provider_name} está disponible y responde correctamente.")
        else:
            st.warning(f"{provider_name} no respondió correctamente. Revisa la configuración.")
