## Especificación original del proyecto Aether AI Personal Assistant

> Este documento conserva los objetivos iniciales del proyecto. No implica que todas las funciones descritas estén implementadas; consulta el README para el estado y las limitaciones actuales.

1. Descripción general del proyecto

Quiero desarrollar una aplicación llamada Aether AI Personal Assistant, un asistente personal inteligente desarrollado principalmente con Python.

El proyecto debe ser modular, extensible y gratuito en su configuración inicial, utilizando modelos de lenguaje existentes (LLM).

El objetivo NO es entrenar un modelo de inteligencia artificial ni crear simplemente un chatbot. Quiero construir una aplicación propia que se conecte a modelos de IA externos o locales y les proporcione acceso a herramientas, memoria, información y funcionalidades implementadas por nosotros.

El asistente deberá ser capaz de interpretar instrucciones en lenguaje natural, determinar qué herramientas necesita utilizar y solicitar su ejecución mediante un backend controlado desarrollado en Python.

Este proyecto está destinado principalmente al aprendizaje, experimentación y construcción de un portfolio para GitHub, no a la comercialización.

Requisito fundamental: no quiero pagar por APIs, suscripciones, acceso a modelos ni alojamiento. Toda la funcionalidad inicial debe depender de planes gratuitos o modelos ejecutados localmente.

2. PROVEEDORES DE IA Y SELECCIÓN DE MODELOS

La aplicación debe admitir múltiples proveedores de modelos LLM.

Proveedor principal: Google Gemini API

Utilizar Google Gemini API mediante Google AI Studio.

Motivos:

Dispone de un nivel gratuito con límites de utilización.

Admite Function Calling.

Tiene buenas capacidades de seguimiento de instrucciones.

Es adecuado para ejecutar herramientas y tareas de varios pasos.

No requiere una GPU potente en nuestra computadora.

Para la implementación inicial, utilizar el modelo Gemini Flash más adecuado que esté disponible en el nivel gratuito y admita Function Calling.

Modelo sugerido: Gemini Flash.

El identificador exacto del modelo debe configurarse mediante variables de entorno y nunca quedar repartido por el código.

Ejemplo:

GEMINI_MODEL=identificador_del_modelo

Antes de implementar la integración, verificar los identificadores de modelos disponibles, sus capacidades y las restricciones del nivel gratuito mediante la documentación oficial.

Recursos oficiales:

https://ai.google.dev/

https://aistudio.google.com/

Proveedor secundario: Ollama

Ollama debe proporcionar una alternativa de ejecución local.

Su objetivo es permitir que la aplicación continúe funcionando sin depender de las cuotas de APIs externas.

Modelo sugerido para investigar: Qwen3 en una configuración cuantizada de tamaño reducido, siempre que admita las funcionalidades de uso de herramientas necesarias.

Recurso oficial:

https://ollama.com/

Consideraciones:

La ejecución local debe ser opcional.

La aplicación debe seguir funcionando aunque Ollama no esté instalado.

No asumir que el usuario dispone de una GPU dedicada.

Evaluar el consumo de RAM y los requisitos de hardware antes de recomendar un modelo.

Otros proveedores para futuras versiones

La arquitectura debe permitir incorporar posteriormente:

Groq API.

OpenRouter.

Anthropic Claude API.

OpenAI API.

Estas integraciones serán opcionales y no deberán ser necesarias para ejecutar la primera versión.

Independencia del proveedor

Crear una interfaz común para todos los proveedores.

El AI Core no debe depender directamente de un proveedor específico.

El resto de la aplicación debe comunicarse mediante una interfaz común, sin importar directamente los SDK de Gemini, Ollama u otros proveedores.

3. SISTEMA DE GESTIÓN DE PROVEEDORES Y MODELOS

Una de las funcionalidades principales será un administrador de proveedores de IA.

El usuario debe poder:

Agregar proveedores.

Configurar sus API keys.

Seleccionar modelos.

Cambiar el proveedor activo.

Configurar un modelo principal.

Configurar modelos alternativos.

Comprobar la disponibilidad de cada proveedor.

Consultar errores y estadísticas de uso.

Activar o desactivar proveedores.

Sistema de cambio automático (Fallback)

Implementar un mecanismo de fallback.

Ejemplo de funcionamiento:

La aplicación intenta utilizar Gemini.

Gemini devuelve un error por límite de solicitudes.

La aplicación identifica el tipo de error.

Comprueba si existe otro proveedor configurado y disponible.

Cambia al siguiente proveedor compatible.

Intenta continuar la conversación.

Informa al usuario cuando se produce el cambio.

Ejemplo de orden:

Principal: Gemini.

Alternativa 1: Groq.

Alternativa 2: OpenRouter.

Alternativa 3: Ollama.

Solamente se deben utilizar proveedores configurados y habilitados por el usuario.

Restricciones importantes:

Nunca cambiar automáticamente a un proveedor de pago.

Nunca realizar solicitudes que puedan generar cargos sin autorización explícita.

Diferenciar errores de cuota, autenticación, conectividad y compatibilidad.

Evitar reintentos infinitos.

Informar al usuario cuando se produzca un cambio de proveedor.

Estadísticas de uso

Cuando el proveedor proporcione los datos necesarios, mostrar:

Solicitudes realizadas.

Tokens consumidos.

Uso estimado.

Errores de límite de solicitudes.

Última solicitud exitosa.

Estado del proveedor.

No inventar estadísticas cuando el proveedor no proporcione esa información.

4. FUNCIONALIDADES PRINCIPALES DE LA IA

El asistente debe permitir mantener conversaciones naturales con el usuario.

Funcionalidades iniciales:

Recibir mensajes.

Generar respuestas mediante el LLM seleccionado.

Mantener el contexto de las conversaciones.

Guardar el historial.

Recuperar conversaciones anteriores.

Interpretar instrucciones.

Solicitar herramientas cuando sea necesario.

Recibir los resultados de las herramientas y utilizarlos para responder.

Function Calling / Tool Calling

Esta será una de las funcionalidades fundamentales.

El modelo debe poder solicitar la ejecución de funciones de Python proporcionadas por nuestra aplicación.

Ejemplos:

create_task()
get_tasks()
delete_task()
create_reminder()
search_memory()
save_note()
read_pdf()

El modelo podrá decidir cuándo necesita una herramienta, pero el backend deberá validar y ejecutar la operación.

Nunca permitir que el modelo ejecute código Python arbitrario.

La aplicación debe mantener un registro explícito de las herramientas disponibles.

5. SISTEMA DE MEMORIA

El asistente debe disponer de memoria persistente.

Inicialmente, implementar memoria convencional mediante una base de datos.

El sistema debe poder almacenar:

Historial de conversaciones.

Preferencias del usuario.

Notas guardadas.

Tareas.

Recordatorios.

Información relevante proporcionada explícitamente por el usuario.

En etapas posteriores, incorporar memoria semántica mediante embeddings y búsqueda vectorial.

Tecnologías posibles:

ChromaDB.

FAISS.

Sentence Transformers.

La implementación de RAG debe quedar para una etapa posterior y no ser un requisito del MVP.

6. HERRAMIENTAS INICIALES DEL ASISTENTE

Desarrollar progresivamente las siguientes herramientas.

Gestión de tareas

Crear tareas.

Consultar tareas.

Modificar tareas.

Eliminar tareas.

Marcar tareas como completadas.

Gestión de recordatorios

Crear recordatorios.

Consultar recordatorios.

Eliminar recordatorios.

Consultar próximos recordatorios.

Procesamiento de documentos

Leer archivos PDF.

Extraer texto.

Resumir documentos.

Guardar resúmenes.

Gestión de notas

Crear notas.

Buscar notas.

Recuperar información guardada.

Modificar notas.

Integraciones externas (futuras)

APIs meteorológicas.

Búsqueda web.

Integración con calendarios.

Otras APIs útiles.

Cada herramienta debe tener una descripción clara, parámetros validados y un mecanismo de ejecución controlado.

7. TECNOLOGÍAS DEL PROYECTO

Utilizar principalmente las siguientes tecnologías:

Tecnología

Función

Python

Lenguaje principal

FastAPI

Backend

SQLite

Base de datos inicial

SQLAlchemy

ORM y gestión de datos

Pydantic

Validación de datos

Google Gemini API

Modelo de IA principal

Ollama

Modelo local opcional

Streamlit

Interfaz inicial

Pytest

Pruebas automatizadas

Git

Control de versiones

Evitar incorporar frameworks adicionales sin una justificación técnica clara.

LangGraph puede evaluarse en el futuro si los flujos de ejecución de los agentes se vuelven suficientemente complejos.

8. ESTRUCTURA PROPUESTA DEL PROYECTO

Utilizar una estructura modular similar a la siguiente:

aether-ai-assistant/

app/
main.py
config.py

    core/
        assistant.py
        conversation.py
        prompts.py

    providers/
        base.py
        gemini.py
        ollama.py

    model_manager/
        manager.py
        fallback.py
        registry.py
        capabilities.py

    memory/
        manager.py
        database.py
        models.py

    tools/
        registry.py
        tasks.py
        reminders.py
        notes.py
        documents.py

    api/
        routes.py

    ui/
        dashboard.py

tests/

.env.example
.gitignore
requirements.txt
README.md

Se pueden proponer mejoras a esta estructura cuando existan razones arquitectónicas justificadas.

9. SEGURIDAD Y FIABILIDAD

La seguridad es importante incluso tratándose de un proyecto personal.

Implementar:

API keys almacenadas en variables de entorno.

Nunca exponer credenciales al frontend.

Nunca subir secretos a GitHub.

Validación de entradas.

Validación de parámetros de herramientas.

Manejo de excepciones.

Sistema de logging.

Ejecución controlada de herramientas.

Confirmación antes de acciones destructivas o sensibles.

Protección frente a usos no autorizados de herramientas.

El modelo nunca debe disponer de acceso ilimitado al sistema de archivos, al sistema operativo ni a la ejecución arbitraria de Python.

10. METODOLOGÍA DE DESARROLLO

Quiero desarrollar esta aplicación progresivamente.

Actúa como mentor técnico y compañero de desarrollo.

Respeta las siguientes indicaciones:

No generes toda la aplicación en una única respuesta.

Inspecciona el proyecto existente antes de modificar archivos.

Explica la finalidad de cada módulo antes de implementarlo.

Trabaja en un componente a la vez.

Explica los conceptos nuevos.

Prioriza código Python legible y mantenible.

Utiliza anotaciones de tipos cuando corresponda.

Incorpora manejo de errores y pruebas.

Evita dependencias innecesarias.

Explica las decisiones arquitectónicas y sus alternativas.

No reescribas código funcional sin una razón clara.

Mantén la documentación actualizada.

Quiero comprender el código y su funcionamiento, no simplemente copiar y pegar soluciones generadas.

11. HOJA DE RUTA DE DESARROLLO

Fase 1 — Configuración inicial

Crear la estructura del proyecto.

Configurar el entorno de Python.

Configurar variables de entorno.

Conectar Gemini API.

Implementar una interfaz conversacional básica.

Fase 2 — AI Core

Implementar la interfaz común de proveedores LLM.

Implementar la gestión de conversaciones.

Implementar Function Calling.

Crear el registro de herramientas.

Probar la ejecución de herramientas.

Fase 3 — Memoria

Implementar persistencia mediante SQLite.

Guardar conversaciones.

Recuperar el historial.

Implementar memoria básica del usuario.

Fase 4 — Herramientas del asistente

Gestión de tareas.

Recordatorios.

Notas.

Procesamiento de documentos PDF.

Fase 5 — Gestión de proveedores

Implementar el registro de proveedores.

Incorporar Ollama.

Implementar fallback.

Incorporar estado de proveedores.

Implementar estadísticas de uso.

Fase 6 — Interfaz

Desarrollar el dashboard.

Incorporar gestión de conversaciones.

Incorporar configuración de proveedores.

Incorporar gestión de tareas y recordatorios.

Mejorar la experiencia visual.

Fase 7 — Funcionalidades avanzadas

RAG.

Memoria semántica.

Búsqueda web.

Proveedores LLM adicionales.

Interacción por voz.

Flujos de agentes más avanzados.

12. PRIMERA TAREA

Antes de escribir código, analiza esta especificación.

Quiero que:

Identifiques posibles problemas arquitectónicos.

Propongas mejoras.

Determines las dependencias mínimas necesarias.

Verifiques los modelos Gemini disponibles actualmente en el nivel gratuito y su compatibilidad con Function Calling.

Recomiendes un modelo inicial apropiado.

Evalúes los requisitos de hardware para los modelos locales.

Establezcas la estructura inicial de carpetas.

Elabores una hoja de ruta realista de implementación.

No comiences implementando todos los módulos inmediatamente.

Comienza por el análisis arquitectónico y la configuración del entorno.

Objetivo final: desarrollar un asistente personal de IA funcional, modular y extensible, capaz de utilizar múltiples proveedores LLM, ejecutar herramientas controladas en Python, mantener memoria persistente y cambiar automáticamente entre proveedores gratuitos disponibles cuando sea necesario.
