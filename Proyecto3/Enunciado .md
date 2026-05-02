Título del Proyecto:
Park-Guard 2.0
PONDERACIÓN: 25 pts
Tiempo estimado: 30 hrs

2. Resumen Ejecutivo
El proyecto Park-Guard 2.0: Sistema IoT Inteligente de Gestión y Analítica de Parqueos
se desarrolla dentro del curso de Arquitectura de Computadoras y Ensambladores 2 como
una evolución del sistema automatizado local hacia una arquitectura distribuida basada en
tecnologías IoT.
La problemática abordada no solo se limita a la gestión ineficiente de espacios de parqueo,
sino también a la ausencia de sistemas integrados que permitan monitoreo remoto, análisis
histórico de ocupación, detección automática de eventos críticos y generación de
información estratégica para la toma de decisiones.
La propuesta consiste en diseñar e implementar un sistema físico de control de acceso y
monitoreo de espacios que transmita datos en tiempo real mediante el protocolo MQTT
hacia una arquitectura backend compuesta por un consumer en Python, una base de datos
NoSQL y una API REST. Estos datos serán visualizados en un dashboard web interactivo
que permitirá supervisión en tiempo real, consulta histórica y análisis de patrones de uso.
El sistema integrará sensores de ocupación, RFID para autenticación, sensores ambientales
de seguridad y actuadores como talanqueras y alarmas. Además, registrará eventos
operativos tales como accesos autorizados, intentos denegados, activaciones de
emergencia y estadísticas de ocupación.
Con esta implementación, el proyecto trasciende la automatización local para convertirse en
un sistema IoT escalable, orientado a eventos y preparado para simulaciones de entornos
de ciudad inteligente.
3. Enunciado del Proyecto
3.1 Descripción del problema a resolver
En Guatemala, la gestión de parqueos en centros educativos, comerciales y empresariales
suele realizarse de forma manual o con sistemas básicos que no ofrecen control en tiempo
real sobre la disponibilidad de espacios, el acceso de usuarios ni las condiciones de
seguridad del área. Esta situación provoca congestionamientos, pérdida de tiempo, errores
humanos en el control de ingreso y salida, así como una baja capacidad de respuesta ante
situaciones de emergencia como incendios, acumulación de gases o fallas operativas.
La ausencia de arquitecturas conectadas limita la capacidad de supervisión centralizada,
impide detectar patrones de alta demanda, dificulta la generación de reportes operativos y
reduce la capacidad de respuesta ante emergencias como acumulación de gases, incendios
o fallos en los sistemas de acceso.
Desde una perspectiva tecnológica, muchos sistemas actuales funcionan como soluciones
cerradas, sin comunicación distribuida, sin procesamiento de eventos y sin almacenamiento
estructurado de información. Esto impide la implementación de modelos predictivos,
auditorías digitales y escalabilidad hacia múltiples zonas o sedes

Ante esta problemática, surge la necesidad de evolucionar el sistema Park-Guard hacia una
arquitectura IoT moderna, donde los sensores y actuadores físicos no solo ejecuten
acciones locales, sino que también publiquen eventos hacia una infraestructura de
mensajería MQTT. Esta arquitectura permitirá el procesamiento en backend,
almacenamiento en bases de datos NoSQL y visualización mediante dashboards web
interactivos.
El nuevo enfoque transforma el parqueo en un sistema inteligente conectado, capaz de:
● Supervisar ocupación en tiempo real, de forma local.
● Registrar y consultar eventos históricos.
● Detectar condiciones de riesgo y generar alertas automáticas.
● Analizar patrones de uso para optimizar la gestión del espacio.
● Registrar nuevos usuarios en base a un identificador.
● Simular un modelo escalable aplicable a entornos de ciudad inteligente.
De esta forma, el proyecto no solo fortalece los principios de automatización y control
embebido, sino que integra conceptos avanzados de sistemas distribuidos, arquitecturas
orientadas a eventos y análisis de datos aplicados a infraestructura urbana.
3.2 Alcance del proyecto
El proyecto consiste en la evolución del sistema físico automatizado hacia una arquitectura
IoT distribuida basada en contenedores, donde todos los servicios del sistema estarán
desacoplados, dockerizados y comunicados mediante el protocolo MQTT.
El sistema integrará:
● Nodo físico (Arduino + ESP32 o Raspberry Pi)
● Broker MQTT
● Consumer en Python
● Backend API
● Base de datos NoSQL
● Frontend web
● Sistema de autenticación con JWT
● Generación de reportes
● Manejo dinámico de usuarios RFID
La arquitectura deberá permitir que el sistema sea fácilmente escalable y preparado para
una futura migración a la nube.
El objetivo ya no se limita únicamente al funcionamiento físico de la maqueta, sino a la
integración completa entre hardware y software mediante una infraestructura moderna,
comunicación en tiempo real con MQTT, almacenamiento en base de datos NoSQL y
visualización web segura con autenticación JWT

El sistema deberá componerse de varios servicios desacoplados, ejecutándose en
contenedores Docker independientes. La comunicación entre el nodo físico (Arduino +
ESP32 o Raspberry Pi) y el backend se realizará exclusivamente mediante el protocolo
MQTT, utilizando un broker desplegado en Docker. A su vez, los datos recibidos serán
procesados por un consumer en Python, almacenados en una base de datos NoSQL
también contenerizada y expuestos a través de una API REST segura.
El backend y el consumer deberán construirse como imágenes Docker personalizadas,
publicarse en Docker Hub y utilizarse directamente desde dicha plataforma el día de la
presentación. Este requisito tiene como finalidad garantizar que el proyecto esté preparado
para su despliegue en la nube en la siguiente fase del curso. Durante la evaluación se
solicitará una demostración en vivo del levantamiento del sistema utilizando
docker-compose, evidenciando el dominio técnico del entorno de contenedores.
Desde el punto de vista funcional, el sistema deberá conservar la maqueta física
desarrollada previamente, incluyendo los espacios de parqueo, las talanqueras automáticas,
sensores de ocupación, sensor de gas o humo, ventilador, buzzer y pantalla LCD. Sin
embargo, la lógica de validación de tarjetas RFID cambia: las tarjetas autorizadas ya no
podrán estar definidas directamente en el código de Arduino o Raspberry. En esta fase, los
usuarios y sus tarjetas deberán almacenarse en la base de datos y gestionarse
dinámicamente desde el frontend.
Esto implica que el sistema deberá permitir registrar nuevas tarjetas, editar información de
usuarios, activar o desactivar accesos y visualizar el listado completo de tarjetas
registradas. Toda validación de acceso deberá consultar la base de datos a través del
backend, reforzando el enfoque distribuido del proyecto.
Adicionalmente, el sistema deberá registrar y almacenar eventos operativos tales como
ingresos autorizados, intentos denegados, salidas, ocupación y desocupación de espacios,
activaciones de emergencia, encendido de ventilador y cambios de estado relevantes. Estos
registros permitirán la generación de reportes descargables en formato PDF, incluyendo
estadísticas básicas de uso y actividad del parqueo.
El frontend deberá desarrollarse utilizando React, Vue o Angular, incorporando autenticación
mediante JWT para garantizar un acceso seguro. Todas las rutas protegidas deberán
requerir token válido, y el backend deberá validar correctamente cada solicitud autenticada.
La visualización en tiempo real será un componente fundamental de esta fase. Utilizando
MQTT con WebSockets en el frontend y la librería P5.js, se deberá representar
gráficamente el estado de los espacios de parqueo, el nivel de gas ambiental, el estado de
las talanqueras y los eventos recientes del sistema. Esta vista deberá actualizarse en
tiempo real conforme se reciban mensajes del broker.
Desde el dashboard también se deberá permitir la ejecución de acciones remotas, como
activar el ventilador o activar el sistema de emergencia, publicando los mensajes
correspondientes al tópico MQTT adecuado. De esta forma, el sistema demuestra
comunicación bidireccional completa entre interfaz web y dispositivo físico.


El proyecto también deberá incluir un mecanismo básico de detección de actividad
sospechosa asociada a tarjetas RFID, por ejemplo, múltiples intentos de ingreso en un
rango corto de tiempo. Estos eventos deberán registrarse en la base de datos y visualizarse
como alertas en el sistema.
Asimismo, se deberá permitir la gestión administrativa de los espacios de parqueo,
habilitando o deshabilitando espacios por mantenimiento u otras causas, reflejando estos
cambios tanto en la base de datos como en la visualización en tiempo real.
En conjunto, esta fase busca que el estudiante integre conocimientos de automatización,
sistemas distribuidos, bases de datos NoSQL, seguridad mediante autenticación con
tokens, comunicación orientada a eventos y despliegue contenerizado. El resultado
esperado es un sistema IoT funcional, modular, escalable y preparado para ser migrado a
infraestructura en la nube en la siguiente etapa del proyecto

Alcance opcional:
Podrá incorporarse funcionalidades adicionales para hacer del sistema un prototipo
completo:
● Incorporación de LEDs por espacio, indicando libre u ocupado
● Contador de ingresos y salidas
● Posible expansión futura hacía comunicación inalámbrica o monitoreo remoto.
● Utilización de una interfaz gráfica utilizando processing

Requerimientos técnicos:
El proyecto deberá implementarse como un sistema IoT distribuido, desacoplado y
contenerizado, integrando hardware físico y servicios backend bajo una arquitectura
orientada a eventos.
El sistema deberá garantizar coherencia entre las acciones físicas de la maqueta y su
representación digital en tiempo real, manteniendo sincronización constante mediante el
protocolo MQTT.
El sistema deberá ejecutarse bajo una arquitectura basada en contenedores Docker.
Deberán ejecutarse en contenedores independientes:
● Broker MQTT
● Base de datos NoSQL
● Backend API
● Consumer MQTT
● Frontend
El backend, consumer y frontend deberán:
● Contener su propio Dockerfile.
● Construir una imagen personalizada.
● Publicarse en Docker Hub.
● Descargarse desde Docker Hub el día de la presentación.
● Integrarse mediante docker-compose.
Se evaluará el correcto uso de redes internas, variables de entorno y orquestación básica.
Durante la presentación se realizará una demostración en vivo del levantamiento del
sistema completo utilizando Docker.
Comunicación en tiempo real
Toda la comunicación entre el nodo físico y el sistema deberá realizarse exclusivamente
mediante MQTT.
No se permitirá comunicación directa HTTP entre el dispositivo físico y el backend.
El frontend deberá suscribirse a tópicos MQTT para visualización en tiempo real y publicar
comandos cuando se activen acciones remotas como:
● Activación de ventilador.
● Activación de emergencia.
● Habilitar o deshabilitar parqueos


Documentación Obligatoria de Topics MQTT
El documento técnico deberá incluir una sección formal donde se describan:
● Lista completa de topics utilizados.
● Estructura jerárquica de los mismos.
● Formato JSON de cada mensaje.
● Descripción funcional de cada topic.
● Qué componente publica.
● Qué componente se suscribe.
Se evaluará la coherencia y organización del diseño de mensajería.
Diseño de Base de Datos NoSQL
Como mínimo deberán existir colecciones para:
● Usuarios RFID.
● Eventos.
● Espacios de parqueo.
● Logs del sistema.
● Estadísticas generadas.
Las tarjetas RFID no podrán estar almacenadas en el microcontrolador. La validación
deberá realizarse consultando la base de datos a través del backend.
Seguridad - Autenticación JWT
El sistema deberá implementar autenticación mediante JSON Web Tokens (JWT).
Se requiere:
● Login obligatorio.
● Manejo seguro de credenciales.
Diseño de la Interfaz Web
El frontend deberá desarrollarse utilizando React, Vue o Angular. La interfaz deberá estar
organizada en dashboards diferenciados y claramente estructurados:
Dashboard de Visualización en tiempo real
Debe incluir:
● Representación gráfica de los espacios ocupados utilizando P5.js.
● Nivel de gas ambiental.
● Estado del ventilador.
● Estado de emergencia.
● Estado de talanqueras.


● Espacios disponibles.
● Registro en vivo de eventos recientes.
La actualización deberá realizarse mediante suscripción MQTT.
Dashboard de Gestión de Usuarios
Debe permitir:
● Crear usuario con tarjeta RFID.
● Editar usuario.
● Activar o desactivar tarjeta.
● Visualizar historial básico de actividad.
● Identificar actividad sospechosa (múltiples intentos en corto tiempo).
● Manejo de saldo por usuario.
Dashboard de Estadísticas y Reportes
● Gráficas de ingresos y salidas.
● Espacio más utilizado.
● Cantidad de emergencias.
● Activaciones de ventilador.
Desde este dashboard deberá poder generarse un reporte en PDF descargable con las
estadísticas mostradas.
3.3 Entregables
Tipo Descripción
Manual de Usuario
Documento que describa el funcionamiento del sistema web, detallando
funcionalidades y uso.
Documento técnico.
Agregar el diagrama que represente claramente la arquitectura del sistema. Nodo
físico > Broker MQTT > Consumer > Base de Datos NoSQL > Backend API >
Frontend.
Incluir objetivos, alcance, arquitectura, documentación de topics, diseño de base
de datos (esquemas) diseño de dashboards, explicación del flujo completo.
Maqueta Funcional Sistema físico completamente operativo y sincronizado con el sistema IoT
Repositorio Git Mínimo 2 commits por persona, en fechas diferentes.


Interfaz Dashboards descritos funcionales y con interfaz intuitiva.
Penalizaciones
70% de penalización si no se cumplen las funcionalidades físicas de la Fase 1.
10% de penalización por no cumplir el mínimo de commits.
Penalización si las imágenes no están publicadas en Docker Hub

4. Material de apoyo
Para facilitar el desarrollo del proyecto Park-Guard 2.0: Sistema IoT Distribuido y
Escalable, se recomienda a los estudiantes consultar recursos técnicos orientados a
arquitecturas distribuidas, comunicación basada en eventos, contenerización y desarrollo de
aplicaciones web modernas.
En esta fase, el enfoque ya no se limita únicamente al control embebido con Arduino, sino
que integra conceptos de sistemas IoT, bases de datos NoSQL, seguridad mediante
autenticación con tokens, procesamiento backend y despliegue en contenedores.
Los siguientes materiales permitirán comprender tanto la parte física como la arquitectura
completa del sistema.
Documentación oficial de Arduino — Referencia del lenguaje, manejo de interrupciones y
librerías para sensores.
Raspberry Pi Documentation — Configuración de red, GPIO y conectividad WiFi.
Librerías MQTT para Arduino (PubSubClient u otras).
Documentación oficial de MQTT — Conceptos de publish/subscribe, QoS y estructura de
tópicos.
Eclipse Mosquitto — Configuración y despliegue de broker MQTT.
Guías sobre diseño de jerarquía de topics y mensajes JSON.
5. Metodología
La metodología del proyecto Park-Guard: Sistema automatizado de parqueo se organiza
en fases progresivas que guían al estudiante desde la investigación inicial hasta la
validación del sistema automatizado. Este enfoque busca que los participantes comprendan
no sólo qué deben construir, sino también cómo lograr un resultado funcional y bien
documentado. Cada fase incluye actividades concretas que deberán registrarse mediante
evidencias fotográficas y bitácoras de avance.
6. Recursos y herramientas a utilizar
Para el desarrollo del proyecto Park-Guard: Sistema automatizado de parqueo, los
estudiantes deberán utilizar herramientas tecnológicas que faciliten la programación, el
diseño, la simulación y la documentación del sistema. Los recursos seleccionados buscan
reforzar la comprensión de los procesos de automatización y el trabajo colaborativo dentro
de entornos académicos.
Software
● Arduino IDE: entorno principal para la programación del microcontrolador y la
implementación de los subsistemas de control y seguridad.
● Processing: herramienta de apoyo para el diseño de la interfaz gráfica de
visualización y la comunicación serial con el sistema físico

● TinkerCAD Circuits: simulador en línea para pruebas iniciales de circuitos y
componentes electrónicos.
● Fritzing: programa para elaborar diagramas de conexión eléctricos y esquemas de
montaje.
● Canva o PowerPoint: para la elaboración de presentaciones visuales de avance y
documentación final.
● Microsoft Word o Google Docs: para la redacción de la documentación técnica y la
bitácora de desarrollo.
Plataformas de trabajo y gestión
● UEDI: plataforma institucional para la publicación de actividades, entregas y avisos
del curso.
● GitHub: control de versiones y almacenamiento del código fuente, diagramas y
documentación digital del proyecto.
● Google Drive: espacio para compartir archivos, fotografías y evidencias del trabajo
en equipo

9.2 Resumen de Puntuaciones
Área Puntos Totales Puntos Obtenidos
1. Habilidades
Competencia / Habilidad Puntos Totales Puntos Obtenidos
Uso correcto de Docker y Docker
Compose
10
Imagenes en docker hub y uso de tags 3
Documentación Técnica 5
Manual de usuario claro y funcional 5
Orden del repositorio y mínimo 2
commits en fechas distintas
2
Trabajo y presentación final 5
Subtotal Habilidades 30
2. Conocimiento
Tema / Módulo Puntos Totales Puntos Obtenidos
Broker MQTT dockerizado y
funcional
4
Base de datos NoSQL dockerizada 4
Backend dockerizado con imagen
propia en Docker Hub
4
Consumer dockerizado con imagen
propia en Docker Hub
4
Comunicación correcta vía MQTT
(publish/subscribe)
6
Procesamiento de eventos en consumer 4
Registro correcto de eventos en base
de datos
5
Implementación correcta de JWT 4
Gestión dinámica de usuarios RFID 8


(CRUD completo)
Detección de actividad sospechosa 3
Dashboard en tiempo real con P5.js 10
Dashboard de estadísticas con gráficas 5
Generación de reporte en PDF 4
Activación remota (ventilador /
emergencia, parqueos) vía MQTT
5
Subtotal Conocimiento 70
TOTAL 100

