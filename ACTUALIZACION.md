Instrucciones Técnicas para la Mejora del
Asistente de IA de Desarrollo de Software
(webUI)
1. Introducción y Requisitos del Proyecto
Este documento técnico detalla las modificaciones necesarias para mejorar el asistente
de IA webUI , desarrollado por josedcape, con el fin de incorporar funcionalidades
avanzadas de gestión de tareas. El objetivo principal es permitir que el asistente maneje
una cola de tareas, ofrezca la capacidad de pausar y detener tareas en ejecución, y
facilite la interacción continua del usuario sin necesidad de reiniciar la página. Además,
se renombrará la sección "Run Agent" a "Agent Interactivo" para reflejar mejor su nueva
capacidad de interacción dinámica.
1.1. Requisitos Funcionales
Los requisitos funcionales clave para esta mejora son los siguientes:
Gestión de Tareas en Cola: El asistente debe ser capaz de recibir múltiples
solicitudes de tareas del usuario y procesarlas de forma secuencial, manteniendo
una cola de espera para las tareas futuras. Si el agente está ocupado con una tarea,
las nuevas solicitudes deben añadirse a esta cola.
Pausa de Tareas: El usuario debe poder pausar una tarea en ejecución en
cualquier momento. Al pausar, el agente debe detener su actividad actual y retener
su estado para poder reanudarla posteriormente desde el punto de interrupción.
Detención de Tareas: El usuario debe poder detener completamente una tarea en
ejecución o en cola. Al detener una tarea, todos los recursos asociados deben ser
liberados y la tarea debe ser eliminada de la cola o del estado de ejecución.
Interacción Continua del Usuario: El usuario debe poder enviar nuevos mensajes
o comandos al asistente incluso cuando una tarea esté en curso. Estos mensajes
deben ser interpretados como nuevas tareas o instrucciones para la tarea actual
(por ejemplo, para pausar o detener), y deben ser gestionados adecuadamente por
el sistema de cola.
Renombrar Interfaz: La pestaña "Run Agent" en la interfaz de usuario de Gradio
debe ser renombrada a "Agent Interactivo" para reflejar la capacidad mejorada de
interacción y gestión de tareas.
•
•
•
•
•
1.2. Requisitos No Funcionales
Rendimiento: Las modificaciones deben introducir una sobrecarga mínima en el
rendimiento del sistema. La gestión de la cola y las operaciones de pausa/
detención deben ser eficientes.
Usabilidad: La interfaz de usuario para la gestión de tareas (pausar, detener, ver
cola) debe ser intuitiva y fácil de usar.
Robustez: El sistema debe ser robusto frente a errores, asegurando que las tareas
se manejen correctamente incluso en situaciones inesperadas (por ejemplo, fallos
del agente o del navegador).
Persistencia (Opcional): Idealmente, el estado de las tareas en cola y en ejecución
debería poder persistir a través de reinicios de la aplicación, aunque este requisito
puede considerarse para una fase posterior si la complejidad inicial es demasiado
alta.
1.3. Plan de Modificaciones de Alto Nivel
Para implementar estos requisitos, se propone el siguiente plan de modificaciones de
alto nivel:
Modificaciones en la Interfaz de Usuario (Gradio):
Renombrar la pestaña "Run Agent" a "Agent Interactivo".
Añadir botones de "Pausar" y "Detener" en la interfaz del agente.
Implementar un componente visual para mostrar la cola de tareas
pendientes.
Asegurar que el campo de entrada de usuario permanezca activo y receptivo
incluso durante la ejecución de tareas.
Modificaciones en la Lógica de Gestión de Tareas ( WebuiManager ):
Extender la clase WebuiManager para incluir un mecanismo de cola de
tareas.
Implementar métodos para añadir, pausar, reanudar y detener tareas.
Gestionar el estado de las tareas (en ejecución, pausada, en cola, completada,
fallida).
Manejar la comunicación entre la UI y el agente para el control de flujo de
tareas.
Implementación de la Cola de Tareas y el Control de Flujo:
Utilizar una estructura de datos adecuada para la cola (por ejemplo,
asyncio.Queue o collections.deque ).
•
•
•
•
1.
◦
◦
◦
◦
2.
◦
◦
◦
◦
3.
◦
Modificar el bucle principal de ejecución del agente para que procese tareas
de la cola.
Implementar mecanismos de señalización (eventos de asyncio ) para la
pausa y detención de tareas.
Asegurar que la interacción del usuario se pueda encolar o priorizar según sea
necesario.
Este plan se desglosará en secciones más detalladas en las siguientes partes de este
documento.
2. Modificaciones en la Interfaz de Usuario (Gradio)
La interfaz de usuario de webUI está construida con Gradio, lo que facilita la creación
de componentes interactivos y la gestión del flujo de la aplicación. Las modificaciones
en esta sección se centrarán en src/webui/interface.py y los componentes
asociados en src/webui/components/ .
2.1. Renombrar la Pestaña "Run Agent" a "Agent Interactivo"
La primera modificación visual es cambiar el nombre de la pestaña principal donde se
ejecuta el agente. Actualmente, esta pestaña se define en src/webui/interface.py .
Ubicación del Código: src/webui/interface.py
Cambio Propuesto:
Buscar la línea que define la TabItem para "Run Agent":
with gr.TabItem(" Run Agent"):
create_browser_use_agent_tab(ui_manager)
Y modificarla para renombrar la pestaña a "Agent Interactivo":
with gr.TabItem(" Agent Interactivo"):
create_browser_use_agent_tab(ui_manager)
Este cambio es puramente estético pero fundamental para reflejar la nueva
funcionalidad interactiva del agente.
◦
◦
◦
2.2. Añadir Botones de "Pausar" y "Detener" en la Interfaz del Agente
Para permitir al usuario controlar la ejecución de las tareas, se deben añadir botones de
"Pausar" y "Detener" en la interfaz del agente. Estos botones interactuarán con la lógica
de gestión de tareas que se implementará en WebuiManager .
Ubicación del Código: src/webui/components/browser_use_agent_tab.py (o un
nuevo archivo si se crea un componente específico para el control de tareas).
Cambio Propuesto:
Dentro de la función create_browser_use_agent_tab , se deben añadir los
siguientes componentes de Gradio. Se recomienda colocarlos cerca de los controles de
inicio de tarea o en una sección de "Control de Tareas".
with gr.Row():
pause_button = gr.Button(" Pausar Tarea",
interactive=False)
stop_button = gr.Button(" Detener Tarea",
interactive=False)
# Conectar estos botones a las funciones de
WebuiManager (se detallará en la Sección 3)
# Ejemplo (la implementación real usará .click
con funciones en WebuiManager):
#
pause_button.click(fn=ui_manager.pause_current_task, inputs=[],
outputs=[...])
#
stop_button.click(fn=ui_manager.stop_current_task, inputs=[],
outputs=[...])
Inicialmente, estos botones deben estar deshabilitados ( interactive=False ) y solo
activarse cuando una tarea esté en ejecución. La lógica para habilitar/deshabilitar estos
botones se gestionará a través de callbacks de Gradio conectados al estado de la tarea
en WebuiManager .
2.3. Implementar un Componente Visual para Mostrar la Cola de Tareas
Pendientes
Para que el usuario tenga visibilidad sobre las tareas que están en espera, se necesita un
componente que muestre la cola de tareas. Un gr.Textbox o gr.Markdown podría
ser suficiente para una representación simple, o un gr.Dataframe para una vista más
estructurada si se requiere más información por tarea.
Ubicación del Código: src/webui/components/browser_use_agent_tab.py (o un
nuevo componente).
Cambio Propuesto:
Se puede añadir un gr.Textbox en una sección dedicada a la cola de tareas:
with gr.Column():
gr.Markdown("### Cola de Tareas
Pendientes")
task_queue_display = gr.Textbox(
label="Tareas en Cola",
lines=5,
interactive=False,
value="No hay tareas en cola."
)
# Este componente se actualizará mediante
callbacks desde WebuiManager
# Ejemplo:
#
ui_manager.task_queue_updated_event.trigger(task_queue_display.update(valuLa actualización del contenido de task_queue_display se realizará mediante una
función de callback en WebuiManager que se activará cada vez que la cola de tareas
cambie (se añada una tarea, se complete una, etc.).
2.4. Asegurar que el Campo de Entrada de Usuario Permanezca Activo y
Receptivo
Actualmente, es posible que el campo de entrada de usuario se desactive o se bloquee
durante la ejecución de una tarea para evitar interacciones no deseadas. Para permitir la
interacción continua, este campo debe permanecer activo y sus entradas deben ser
encoladas o procesadas como comandos de control.
Ubicación del Código: src/webui/components/browser_use_agent_tab.py (o
donde se defina el campo de entrada de chat/comando).
Cambio Propuesto:
Revisar la definición del gr.Textbox o gr.Chatbot que maneja la entrada del
usuario y asegurarse de que su propiedad interactive esté siempre en True o que
se gestione dinámicamente para permitir la entrada.
Si se utiliza un gr.Chatbot , la entrada de texto asociada ( gr.Textbox que actúa
como entrada del chatbot) debe configurarse para que siempre esté interactiva. La
lógica de procesamiento de esta entrada se trasladará a WebuiManager para
diferenciar entre comandos de control y nuevas tareas para el agente.
# Ejemplo de un campo de entrada de texto que
debe permanecer interactivo
user_input_textbox = gr.Textbox(
label="Enviar mensaje o nueva tarea",
placeholder="Escribe tu mensaje o tarea
aquí...",
interactive=True # Asegurar que siempre
esté interactivo
)
# El botón de envío también debe estar siempre
interactivo
send_button = gr.Button("Enviar",
interactive=True)
# La lógica de lo que sucede al enviar se
manejará en WebuiManager
#
send_button.click(fn=ui_manager.handle_user_input,
inputs=[user_input_textbox], outputs=[...])
La función handle_user_input en WebuiManager será la encargada de analizar la
entrada del usuario y determinar si es un comando de control (pausar, detener) o una
nueva tarea para el agente. Las nuevas tareas se añadirán a la cola de tareas. [1]
2.5. Resumen de Componentes de UI Afectados
La siguiente tabla resume los componentes de la UI de Gradio que serán modificados o
añadidos:
Componente
de UI Archivo Afectado Propósito Estado Inicial Interagr.TabItem interface.py
Renombrar
"Run
Agent" a
"Agent
Interactivo"
N/A N/A
browser_use_agent_tab.py interactive=False
Componente
de UI Archivo Afectado Propósito Estado Inicial Interagr.Button
(Pausar)
Pausar la
tarea
actual
clickui_magr.Button
(Detener)
browser_use_agent_tab.py
Detener la
tarea
actual o en
cola
interactive=False
clickui_magr.Textbox
(Cola de
Tareas)
browser_use_agent_tab.py
Mostrar el
estado de
la cola de
tareas
interactive=False updatgr.Textbox
(Entrada de
Usuario)
browser_use_agent_tab.py
Permitir
entrada
continua
del usuario
interactive=True
submiui_maReferencias:
[1] Gradio Documentation: https://www.gradio.app/docs/
3. Detallar las Modificaciones en la Lógica de Gestión de
Tareas ( WebuiManager )
La clase WebuiManager (ubicada en src/webui/webui_manager.py ) es el corazón
de la lógica de la aplicación, gestionando el estado de la UI y la interacción con los
agentes. Para implementar la gestión de tareas en cola, pausa y detención, esta clase
debe ser significativamente extendida.
3.1. Atributos Adicionales en WebuiManager
Se deben añadir los siguientes atributos a la clase WebuiManager para gestionar las
tareas y su estado:
class WebuiManager:
def __init__(self, settings_save_dir: str = "./tmp/
webui_settings"):
# ... (atributos existentes)
self.task_queue: asyncio.Queue = asyncio.Queue()
# Cola para tareas pendientes
self.current_task_id: Optional[str] = None # ID
de la tarea actualmente en ejecución
self.current_task_future: Optional[asyncio.Future] =
None # Futuro de la tarea en ejecución
self.task_status: Dict[str, str] = {} #
Diccionario para el estado de las tareas (ID -> estado)
self.pause_event: asyncio.Event = asyncio.Event() #
Evento para señalizar la pausa
self.stop_event: asyncio.Event = asyncio.Event() #
Evento para señalizar la detención
self.pause_event.set() # Inicialmente no pausado
# Atributos para actualizar la UI desde el backend
self.task_queue_display_update_event = gr.Event()
self.pause_button_update_event = gr.Event()
self.stop_button_update_event = gr.Event()
task_queue : Una cola asíncrona ( asyncio.Queue ) para almacenar las tareas
que esperan ser ejecutadas. Esto permite un procesamiento secuencial y no
bloqueante.
current_task_id : Almacena el ID único de la tarea que se está ejecutando
actualmente. Será None si no hay ninguna tarea en curso.
current_task_future : Un asyncio.Future que representa la ejecución de la
tarea actual. Esto es crucial para poder cancelar o esperar la finalización de la
tarea.
task_status : Un diccionario que mapea el ID de cada tarea a su estado actual
(ej. "en cola", "ejecutando", "pausada", "detenida", "completada", "fallida").
pause_event : Un asyncio.Event que se utilizará para señalizar si la ejecución
de la tarea actual debe pausarse. Cuando este evento está clear() , la tarea debe
pausarse; cuando está set() , la tarea puede continuar.
stop_event : Un asyncio.Event que se utilizará para señalizar si la tarea actual
debe detenerse por completo. Cuando este evento está set() , la tarea debe
abortar su ejecución.
task_queue_display_update_event , pause_button_update_event ,
stop_button_update_event : Estos serán gr.Event() o mecanismos
similares para enviar actualizaciones a los componentes de la UI desde la lógica del
backend, permitiendo que la UI refleje el estado actual de las tareas y la cola.
•
•
•
•
•
•
•
3.2. Métodos para la Gestión de Tareas
Se deben añadir los siguientes métodos a WebuiManager para manejar el ciclo de vida
de las tareas:
3.2.1.
add_task(task_description: str, task_type: str = "browser_use") ->
str
Este método añadirá una nueva tarea a la cola. Generará un ID único para la tarea y
actualizará su estado.
async def add_task(self, task_description: str, task_type:
str = "browser_use") -> str:
task_id = str(uuid.uuid4())
task_info = {
"id": task_id,
"description": task_description,
"type": task_type,
"status": "en cola",
"timestamp": datetime.now().isoformat()
}
await self.task_queue.put(task_info)
self.task_status[task_id] = "en cola"
await self._update_ui_task_queue()
print(f"Tarea
'{task_description}' ({task_id}) añadida a la cola.")
return task_id
3.2.2. pause_current_task()
Este método será llamado desde la UI para pausar la tarea actualmente en ejecución.
async def pause_current_task(self):
if self.current_task_id and
self.task_status.get(self.current_task_id) == "ejecutando":
self.pause_event.clear() # Señaliza la pausa
self.task_status[self.current_task_id] = "pausada"
await
self._update_ui_buttons(pause_interactive=False,
stop_interactive=True)
print(f"Tarea {self.current_task_id} pausada.")
else:
print("No hay tarea en ejecución para pausar.")
3.2.3. resume_current_task()
Este método será llamado desde la UI para reanudar una tarea pausada.
async def resume_current_task(self):
if self.current_task_id and
self.task_status.get(self.current_task_id) == "pausada":
self.pause_event.set() # Señaliza la reanudación
self.task_status[self.current_task_id] =
"ejecutando"
await
self._update_ui_buttons(pause_interactive=True,
stop_interactive=True)
print(f"Tarea {self.current_task_id} reanudada.")
else:
print("No hay tarea pausada para reanudar.")
3.2.4. stop_task(task_id: Optional[str] = None)
Este método detendrá una tarea específica (si se proporciona task_id ) o la tarea
actual. Si la tarea está en ejecución, intentará cancelarla. Si está en cola, la eliminará de
la cola.
async def stop_task(self, task_id: Optional[str] = None):
if task_id is None: # Detener la tarea actual
if self.current_task_id:
task_to_stop_id = self.current_task_id
if self.current_task_future:
self.stop_event.set() # Señaliza la
detención
# Esperar un corto tiempo para que la tarea
reaccione a la señal de detención
try:
await
asyncio.wait_for(self.current_task_future, timeout=1)
except asyncio.TimeoutError:
print(f"La tarea {task_to_stop_id} no
respondió a la señal de detención, cancelando forzosamente.")
self.current_task_future.cancel() #
Cancelación forzosa si no responde
except asyncio.CancelledError:
print(f"La tarea {task_to_stop_id} fue
cancelada.")
finally:
self.task_status[task_to_stop_id] =
"detenida"
self.current_task_id = None
self.current_task_future = None
self.stop_event.clear() # Limpiar el
evento para futuras tareas
self.pause_event.set() # Asegurarse de
que no esté pausado para la siguiente tarea
await
self._update_ui_buttons(pause_interactive=False,
stop_interactive=False)
await self._update_ui_task_queue()
print(f"Tarea {task_to_stop_id}
detenida.")
else:
print("No hay tarea en ejecución para detener.")
else: # Detener una tarea específica en la cola
# Implementar lógica para eliminar de la cola
(requiere iterar y reconstruir la cola o usar una estructura
diferente)
# Por simplicidad, aquí solo se marcará como
detenida si está en cola
if self.task_status.get(task_id) == "en cola":
self.task_status[task_id] = "detenida"
# En una implementación real, se debería
eliminar de self.task_queue
await self._update_ui_task_queue()
print(f"Tarea {task_id} eliminada de la cola.")
else:
print(f"La tarea {task_id} no está en cola o en
ejecución para detener.")
3.3. Bucle Principal de Procesamiento de Tareas
Se necesita un bucle asíncrono que se ejecute en segundo plano y que sea responsable
de tomar tareas de la cola y ejecutarlas. Este bucle debe estar integrado en el ciclo de
vida de la aplicación Gradio.
async def _task_processor_loop(self):
while True:
task_info = await self.task_queue.get() # Espera
hasta que haya una tarea en la cola
task_id = task_info["id"]
task_description = task_info["description"]
task_type = task_info["type"]
if self.task_status.get(task_id) == "detenida":
# Si la tarea fue detenida mientras estaba en cola
print(f"Saltando tarea detenida: {task_id}")
self.task_queue.task_done()
await self._update_ui_task_queue()
continue
self.current_task_id = task_id
self.task_status[task_id] = "ejecutando"
self.stop_event.clear() # Asegurarse de que el
evento de detención esté limpio para la nueva tarea
self.pause_event.set() # Asegurarse de que el
evento de pausa esté establecido para la nueva tarea
await
self._update_ui_buttons(pause_interactive=True,
stop_interactive=True)
await self._update_ui_task_queue()
print(f"Iniciando tarea: {task_description}
({task_id})")
try:
# Aquí se llamaría a la función real del agente
# Por ejemplo, si task_type == "browser_use":
# self.current_task_future =
asyncio.create_task(self._run_browser_use_agent_task(task_info))
# elif task_type == "deep_research":
# self.current_task_future =
asyncio.create_task(self._run_deep_research_agent_task(task_info))
# Placeholder para la ejecución de la tarea real del agente
self.current_task_future =
asyncio.create_task(self._simulate_agent_work(task_id,
task_description))
await self.current_task_future
if self.task_status.get(task_id) != "detenida":
# Si no fue detenida por el usuario
self.task_status[task_id] = "completada"
print(f"Tarea {task_id} completada.")
except asyncio.CancelledError:
print(f"Tarea {task_id} fue cancelada
externamente.")
self.task_status[task_id] = "detenida"
except Exception as e:
print(f"Error ejecutando tarea {task_id}: {e}")
self.task_status[task_id] = "fallida"
finally:
self.task_queue.task_done()
self.current_task_id = None
self.current_task_future = None
self.stop_event.clear() # Limpiar el evento de
detención
self.pause_event.set() # Asegurarse de que el
evento de pausa esté establecido
await
self._update_ui_buttons(pause_interactive=False,
stop_interactive=False)
await self._update_ui_task_queue()
async def _simulate_agent_work(self, task_id: str,
description: str):
""" Simula el trabajo del agente, incluyendo puntos de
pausa y detención. """
steps = 5
for i in range(steps):
# Comprobar si se ha solicitado la detención
if self.stop_event.is_set():
print(f"Simulación de tarea {task_id} detenida
por solicitud.")
raise
asyncio.CancelledError("Tarea detenida por el usuario")
# Esperar si se ha solicitado la pausa
while not self.pause_event.is_set():
print(f"Simulación de tarea {task_id} pausada.
Esperando reanudación...")
await asyncio.sleep(0.5) # Pequeña espera para
evitar bucle ocupado
if self.stop_event.is_set(): # Comprobar
detención también durante la pausa
print(f"Simulación de tarea {task_id}
detenida durante la pausa.")
raise
asyncio.CancelledError("Tarea detenida por el usuario")
print(f"Tarea {task_id} - Paso {i+1}/{steps}:
{description}")
await asyncio.sleep(2) # Simular trabajo
3.4. Métodos Auxiliares para Actualización de UI
Para que la UI refleje el estado de la cola y los botones, se necesitan métodos auxiliares
que envíen actualizaciones a los componentes de Gradio. Estos métodos se llamarán
desde los métodos de gestión de tareas.
async def _update_ui_task_queue(self):
# Construir una representación de la cola para mostrar
en la UI
queue_contents = []
# La cola real (self.task_queue) no es directamente
iterable sin consumir elementos
# Se podría mantener una lista auxiliar de tareas en
cola para este propósito
# Por ahora, simularemos basándonos en self.task_status
for task_id, status in self.task_status.items():
if status == "en cola":
# Recuperar descripción de la tarea si es
posible, o usar solo el ID
queue_contents.append(f"- Tarea {task_id[:
8]}...: {status}")
elif status == "ejecutando":
queue_contents.append(f"- Tarea {task_id[:
8]}...: {status} (Actual)")
elif status == "pausada":
queue_contents.append(f"- Tarea {task_id[:
8]}...: {status} (Actual)")
display_text = "\n".join(queue_contents) if
queue_contents else "No hay tareas en cola."
# Esto es un placeholder. En una implementación real, se usaría
un gr.Event().trigger
# o se devolverían los componentes actualizados en la
función de callback de Gradio.
# Por ejemplo, si task_queue_display es un gr.Textbox:
# return {task_queue_display:
gr.Textbox.update(value=display_text)}
print(f"Actualización de cola UI: {display_text}")
async def _update_ui_buttons(self, pause_interactive: bool,
stop_interactive: bool):
# Similar al anterior, esto es un placeholder para
actualizar los botones de la UI.
# return {pause_button:
gr.Button.update(interactive=pause_interactive),
# stop_button:
gr.Button.update(interactive=stop_interactive)}
print(f"Actualización de botones UI:
Pausar={pause_interactive}, Detener={stop_interactive}")
3.5. Integración del Bucle de Procesamiento de Tareas
El bucle _task_processor_loop debe iniciarse cuando la aplicación Gradio se lanza.
Esto se puede hacer en la función create_ui en src/webui/interface.py o en la
función launch() de Gradio.
# En src/webui/interface.py, dentro de create_ui o justo antes
de demo.launch()
# Asegúrate de que el bucle se ejecute en el mismo bucle de
eventos que Gradio
ui_manager = WebuiManager()
# Iniciar el bucle de procesamiento de tareas en segundo
plano
# Esto debe hacerse de forma que no bloquee el hilo
principal de Gradio
# Una forma es usar asyncio.create_task si Gradio ya está
ejecutando un bucle de eventos
# o un hilo separado si Gradio no lo hace automáticamente.
# Para Gradio, las funciones asíncronas se manejan bien
con .queue()
# Una forma de iniciar el bucle al lanzar la demo:
# demo.load(ui_manager._task_processor_loop, inputs=[],
outputs=[]) # Esto podría no ser ideal para un bucle infinito
# La mejor práctica es iniciar el bucle de tareas cuando la
aplicación se inicia
# y gestionarlo a través del ciclo de vida de la aplicación
o un hilo dedicado.
# Por ejemplo, si se ejecuta webui.py directamente:
# if __name__ == "__main__":
# manager = WebuiManager()
# asyncio.create_task(manager._task_processor_loop())
# demo = create_ui(manager)
# demo.launch()
3.6. Manejo de la Interacción Continua del Usuario
( handle_user_input )
El método handle_user_input en WebuiManager (que se conectará al campo de
entrada de texto del usuario en la UI) será crucial para diferenciar entre comandos de
control y nuevas tareas.
async def handle_user_input(self, user_message: str) ->
Tuple[str, List[List[str]]]:
# Analizar el mensaje del usuario
user_message_lower = user_message.lower().strip()
if user_message_lower == "pausar":
await self.pause_current_task()
return "Comando de pausa enviado.",
self.bu_chat_history # Devolver mensaje de estado y chat history
elif user_message_lower == "reanudar":
await self.resume_current_task()
return "Comando de reanudación enviado.",
self.bu_chat_history
elif user_message_lower == "detener":
await self.stop_task() # Detener la tarea actual
return "Comando de detención enviado.",
self.bu_chat_history
else:
# Si no es un comando de control, es una nueva tarea para el
agente
task_id = await self.add_task(user_message,
task_type="browser_use")
self.bu_chat_history.append([user_message, f"Tarea
añadida a la cola: {user_message} (ID: {task_id[:8]}...)"])
return "", self.bu_chat_history # Limpiar entrada y
actualizar chat history
Este método debe devolver los valores adecuados para actualizar el gr.Textbox de
entrada (vacío después de enviar) y el gr.Chatbot para mostrar la interacción. La
lógica de bu_chat_history debe ser adaptada para reflejar el estado de la cola y las
interacciones del agente.
3.7. Consideraciones Adicionales para WebuiManager
Sincronización: Es vital asegurar que todas las operaciones que modifican el
estado de las tareas ( task_status , current_task_id , task_queue ) sean
hilo-seguras o asíncronas para evitar condiciones de carrera, especialmente si
Gradio ejecuta callbacks en diferentes hilos o si se usan múltiples agentes.
Manejo de Errores: Implementar un manejo robusto de errores dentro de
_task_processor_loop y las funciones de ejecución de agentes para capturar
excepciones y actualizar el estado de la tarea a "fallida".
Persistencia: Para la persistencia de la cola de tareas y sus estados a través de
reinicios de la aplicación, se podría serializar self.task_queue y
self.task_status a un archivo (por ejemplo, JSON) al cerrar la aplicación y
cargarlos al inicio. Esto es un requisito no funcional opcional pero deseable. [2]
Referencias:
[2] Python asyncio documentation: https://docs.python.org/3/library/asyncio.html
4. Especificar la Implementación de la Cola de Tareas y
el Control de Flujo
La implementación de la cola de tareas y el control de flujo es fundamental para permitir
la gestión avanzada de tareas. Esto implica cómo las tareas son procesadas, cómo se
manejan las señales de pausa y detención, y cómo la interacción continua del usuario se
integra en este sistema.
•
•
•
4.1. El Bucle de Procesamiento de Tareas ( _task_processor_loop )
Como se mencionó en la Sección 3, el método _task_processor_loop en
WebuiManager es el corazón del sistema de gestión de tareas. Este bucle debe
ejecutarse de forma asíncrona y continua, esperando nuevas tareas en
self.task_queue y ejecutándolas secuencialmente.
Detalles de Implementación:
Consumo de Tareas: El bucle utiliza await self.task_queue.get() para
esperar de forma no bloqueante hasta que una tarea esté disponible en la cola.
Una vez que se obtiene una tarea, se marca como "ejecutando" en
self.task_status .
Manejo de Tareas Detenidas en Cola: Antes de ejecutar una tarea, el bucle debe
verificar si la tarea fue marcada como "detenida" mientras estaba en cola (por
ejemplo, si el usuario la detuvo antes de que comenzara a ejecutarse). Si es así, la
tarea se salta y se pasa a la siguiente.
Preparación de Eventos de Control: Para cada nueva tarea, los eventos
self.stop_event y self.pause_event deben ser reiniciados ( clear() para
stop_event y set() para pause_event ) para asegurar que la nueva tarea
comience en un estado no detenido y no pausado.
Actualización de UI: Se deben llamar a los métodos auxiliares
( _update_ui_buttons , _update_ui_task_queue ) para reflejar el estado
actual de la tarea (ejecutando) y la cola en la interfaz de usuario.
Ejecución de la Tarea del Agente: Aquí es donde se invoca la lógica real del agente
(por ejemplo, _run_browser_use_agent_task o
_run_deep_research_agent_task ). Es crucial que la ejecución del agente sea
un asyncio.Task para que pueda ser controlada (cancelada, pausada) desde
fuera. El self.current_task_future almacenará este Task .
Manejo de Excepciones y Finalización: Se utiliza un bloque
try...except...finally para manejar posibles errores durante la ejecución
de la tarea y para asegurar que el estado de la tarea se actualice correctamente
(completada, fallida, detenida) y que los recursos se liberen ( current_task_id =
None , current_task_future = None ).
4.2. Integración de Pausa y Detención en la Lógica del Agente
Para que las señales de pausa y detención funcionen, la lógica interna de los agentes
(por ejemplo, el agente de uso del navegador o el agente de investigación profunda)
debe ser modificada para "escuchar" estos eventos. Esto se logra mediante la
comprobación periódica de self.pause_event y self.stop_event .
1.
2.
3.
4.
5.
6.
Modificaciones en la Lógica del Agente (Ejemplo: _simulate_agent_work ):
Dentro de cualquier función que represente una operación de larga duración del agente,
se deben insertar puntos de control:
async def _simulate_agent_work(self, task_id: str,
description: str):
steps = 5
for i in range(steps):
# 1. Comprobar Detención:
# Este es el punto más crítico. Si
stop_event.is_set() es True, la tarea debe abortar
inmediatamente.
if self.stop_event.is_set():
print(f"Simulación de tarea {task_id} detenida
por solicitud.")
raise
asyncio.CancelledError("Tarea detenida por el usuario")
# 2. Comprobar Pausa:
# Si pause_event.is_set() es False (es decir,
clear()), la tarea debe esperar hasta que se reanude.
while not self.pause_event.is_set():
print(f"Simulación de tarea {task_id} pausada.
Esperando reanudación...")
await asyncio.sleep(0.5) # Pequeña espera para
evitar bucle ocupado y permitir otras operaciones
# Es crucial comprobar también el evento de
detención mientras está pausado
if self.stop_event.is_set():
print(f"Simulación de tarea {task_id}
detenida durante la pausa.")
raise
asyncio.CancelledError("Tarea detenida por el usuario")
# Lógica de trabajo real del agente
print(f"Tarea {task_id} - Paso {i+1}/{steps}:
{description}")
await asyncio.sleep(2) # Simular trabajo
Puntos de Control de Detención: Deben insertarse al inicio de cualquier
operación significativa y antes de cualquier await que pueda bloquear la
ejecución. Si self.stop_event.is_set() es True , la función debe lanzar un
asyncio.CancelledError para que el bucle principal pueda manejar la
cancelación.
Puntos de Control de Pausa: Se implementa un bucle while not
self.pause_event.is_set(): que espera hasta que el evento de pausa se
•
•
establezca ( set() ). Dentro de este bucle de espera, es vital seguir comprobando
self.stop_event para permitir la detención incluso mientras la tarea está
pausada.
Cada función asíncrona dentro de la lógica del agente que pueda tomar un tiempo
considerable debe ser modificada para incluir estos puntos de control. Esto asegura que
el agente sea receptivo a los comandos de pausa y detención en un tiempo razonable.
4.3. Integración de la Interacción Continua del Usuario
La capacidad de interacción continua del usuario se logra mediante la combinación de
dos elementos:
Campo de Entrada de Usuario Siempre Activo: Como se detalló en la Sección 2.4,
el gr.Textbox para la entrada del usuario debe configurarse para que siempre
sea interactivo.
Manejo de Entrada en WebuiManager ( handle_user_input ): El método
handle_user_input en WebuiManager es el punto de entrada para todas las
interacciones del usuario. Este método debe:
Detectar Comandos de Control: Analizar el mensaje del usuario para
identificar comandos predefinidos como "pausar", "reanudar" o "detener". Si
se detecta un comando, se llama al método correspondiente en
WebuiManager (ej. pause_current_task() , stop_task() ).
Encolar Nuevas Tareas: Si el mensaje del usuario no es un comando de
control, se interpreta como una nueva tarea para el agente. Esta nueva tarea
se añade a self.task_queue utilizando self.add_task() . El bucle
_task_processor_loop se encargará de procesarla cuando sea su turno.
Actualización del Chatbot: El gr.Chatbot debe actualizarse para mostrar
tanto los mensajes del usuario como las respuestas del sistema
(confirmaciones de comandos, mensajes de estado de tareas).
Flujo de Interacción:
Cuando el usuario envía un mensaje:
El mensaje llega a handle_user_input .
Si es "pausar", se llama a pause_current_task() . El pause_event se
clear() , y la tarea en ejecución entra en un estado de espera.
Si es "detener", se llama a stop_task() . El stop_event se set() , y la tarea en
ejecución se cancela o la tarea en cola se elimina.
1.
2.
◦
◦
◦
•
•
•
Si es una nueva instrucción (ej. "ve a google y busca noticias"), se llama a
add_task() , y la instrucción se añade a self.task_queue . El usuario recibe
una confirmación de que la tarea ha sido encolada.
Este diseño permite que el usuario envíe comandos y nuevas tareas de forma fluida, sin
interrupciones en la interfaz, mientras el sistema gestiona el flujo de trabajo en segundo
plano. [3]
4.4. Sincronización y Comunicación entre Componentes
La comunicación entre los componentes de Gradio y la lógica de WebuiManager es
crucial. Gradio utiliza un modelo de callbacks para actualizar la UI. Para reflejar el estado
de la cola y los botones, se pueden usar los siguientes enfoques:
Retorno de Componentes Actualizados: Las funciones de callback de Gradio
pueden devolver un diccionario de componentes actualizados. Por ejemplo,
handle_user_input puede devolver el gr.Textbox de entrada vacío y el
gr.Chatbot actualizado.
Eventos de Gradio ( gr.Event ): Para actualizaciones asíncronas desde el
backend (como el cambio de estado de la cola o la habilitación/deshabilitación de
botones), se pueden definir gr.Event() en WebuiManager y luego usar
event.trigger() para activar callbacks en la UI. Esto requiere que los
componentes de la UI estén "escuchando" estos eventos.
Ejemplo de Conexión de Eventos (en create_ui o
create_browser_use_agent_tab ):
# En src/webui/components/browser_use_agent_tab.py
# ... (definición de botones y cola_display)
# Conectar los botones a los métodos de WebuiManager
pause_button.click(
fn=ui_manager.pause_current_task,
inputs=[],
outputs=[pause_button, stop_button] # Los botones se
actualizan a sí mismos
)
resume_button.click(
fn=ui_manager.resume_current_task,
inputs=[],
outputs=[pause_button, stop_button]
)
stop_button.click(
fn=ui_manager.stop_task,
inputs=[],
•
•
•
outputs=[pause_button, stop_button, task_queue_display] #
Stop también actualiza la cola
)
# Conectar la entrada de usuario
user_input_textbox.submit(
fn=ui_manager.handle_user_input,
inputs=[user_input_textbox],
outputs=[user_input_textbox, chatbot_component] # Limpiar
entrada y actualizar chatbot
)
# Conectar actualizaciones de estado desde WebuiManager a la UI
# Esto requiere que WebuiManager exponga eventos o que los
callbacks de Gradio
# se encarguen de consultar el estado de WebuiManager
periódicamente.
# Una forma más robusta sería que WebuiManager tenga un método
que devuelva
# el estado actual de la cola y los botones, y que un gr.Live()
o gr.Timer()
# lo llame periódicamente.
# Ejemplo de actualización periódica (menos eficiente pero más
simple inicialmente):
# demo.load(
# fn=ui_manager.get_ui_state,
# inputs=[],
# outputs=[pause_button, stop_button, task_queue_display],
# every=1 # Actualizar cada segundo
# )
# Donde ui_manager.get_ui_state devolvería algo como:
# return {
# pause_button:
gr.Button.update(interactive=ui_manager.is_pause_button_active()),
# stop_button:
gr.Button.update(interactive=ui_manager.is_stop_button_active()),
# task_queue_display:
gr.Textbox.update(value=ui_manager.get_queue_display_text())
# }
La elección entre gr.Event() y la actualización periódica dependerá de la
complejidad y la necesidad de reactividad. Para una interfaz de usuario fluida, los
eventos son preferibles para actualizaciones inmediatas, mientras que un gr.Timer()
puede ser útil para estados que cambian menos frecuentemente o para una "pulsación"
general del sistema. [4]
Referencias:
[3] Design Patterns for Asynchronous Programming: https://www.oreilly.com/library/
view/design-patterns-for/9781492080103/ [4] Gradio Callbacks and State: https://
www.gradio.app/docs/gradio/blocks#callbacks-and-state
5. Conclusión
Las modificaciones propuestas en este documento transformarán el asistente webUI en
una herramienta más robusta y flexible, capaz de gestionar múltiples tareas de IA de
forma asíncrona y permitir una interacción continua y fluida con el usuario. La
implementación de una cola de tareas, junto con las funcionalidades de pausa y
detención, mejorará significativamente la usabilidad y la eficiencia del agente,
permitiendo a los usuarios un control más granular sobre las operaciones del agente.
La refactorización de WebuiManager para centralizar la lógica de gestión de tareas y la
adaptación de la interfaz de Gradio para reflejar estos nuevos estados son pasos
cruciales. Se recomienda un enfoque de desarrollo iterativo, comenzando con la
implementación de la cola básica y las funcionalidades de pausa/detención, y luego
refinando la interacción de la UI y el manejo de casos de borde.
Este conjunto de instrucciones técnicas proporciona una hoja de ruta clara para la
implementación de estas mejoras, sentando las bases para un asistente de IA de
desarrollo de software más potente y adaptable a las necesidades dinámicas de los
usuarios.
