import streamlit as st
import serial
import time
import pandas as pd
import os
from datetime import datetime

# =========================================================
# 1. CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="AGRO-INTELLIGENT IoT | Grupo 2",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

PUERTO_ARDUINO = "COM3"
BAUDIOS = 9600


# RUTA BASE DEL PROYECTO
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# CARPETA DE IMÁGENES
CARPETA_IMAGENES = os.path.join(BASE_DIR, "imag")

# RUTAS RELATIVAS DE LAS IMÁGENES
RUTAS = {
    "maranon": os.path.join(CARPETA_IMAGENES, "maranon.jpeg"),
    "arroz": os.path.join(CARPETA_IMAGENES, "arroz.webp"),
    "name": os.path.join(CARPETA_IMAGENES, "ñame.webp"),
    "yuca": os.path.join(CARPETA_IMAGENES, "yuca.jpg"),
    "circuito": os.path.join(CARPETA_IMAGENES, "circuito.jpg")
}


# =========================================================
# 2. DISEÑO VISUAL PROFESIONAL
# =========================================================

st.markdown("""
<style>

/* Fondo general */
.stApp {
    background: #F3F6F2;
}

/* Contenedor principal */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}

/* Tipografía */
h1, h2, h3, h4 {
    color: #173D2C !important;
    font-family: 'Segoe UI', sans-serif;
    font-weight: 750 !important;
}

/* Textos */
p, li, label {
    color: #35463C;
    font-family: 'Segoe UI', sans-serif;
}

/* Barra lateral */
section[data-testid="stSidebar"] {
    background: #173D2C;
    border-right: 1px solid #24563E;
}

section[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}

/* Separadores */
hr {
    border-color: #DCE5DC;
}

/* Tarjetas métricas */
div[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #DDE7DD;
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0 3px 12px rgba(25, 60, 40, 0.06);
}

div[data-testid="stMetricLabel"] {
    color: #627267 !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
}

div[data-testid="stMetricValue"] {
    color: #173D2C !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
}

/* Pestañas */
.stTabs [data-baseweb="tab"] {
    color: #173D2C;
    font-weight: 700;
}

/* Botones */
.stButton > button {
    border-radius: 10px;
    font-weight: 700;
    border: 1px solid #DCE5DC;
    min-height: 42px;
}

.stButton > button:hover {
    border-color: #168B69;
    color: #168B69;
}

/* Imágenes */
img {
    border-radius: 12px;
}

/* Encabezado */
.hero {
    background: linear-gradient(115deg, #173D2C, #28734E);
    padding: 30px;
    border-radius: 18px;
    margin-bottom: 25px;
    color: white;
}

.hero h1 {
    color: white !important;
    font-size: 2.2rem;
    margin-bottom: 8px;
}

.hero p {
    color: #E0F0E4 !important;
    font-size: 1.05rem;
    margin-bottom: 0;
}

/* Tarjetas informativas */
.info-card {
    background: white;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #DDE7DD;
    margin-bottom: 12px;
}

.info-card h4 {
    margin-top: 0;
}

/* Etiquetas */
.section-label {
    color: #168B69;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 1.5px;
}

/* Pie de página */
.footer {
    text-align: center;
    color: #758278;
    font-size: 0.85rem;
    padding: 25px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# 3. CONEXIÓN CON ARDUINO
# =========================================================

@st.cache_resource
def iniciar_serial():
    try:
        conexion = serial.Serial(
            PUERTO_ARDUINO,
            BAUDIOS,
            timeout=0.5
        )

        time.sleep(2)
        conexion.reset_input_buffer()

        return conexion

    except serial.SerialException as error:
        print(f"Error serial: {error}")
        return None


arduino = iniciar_serial()


# =========================================================
# 4. VARIABLES DE MEMORIA
# =========================================================

if "historial" not in st.session_state:
    st.session_state.historial = pd.DataFrame(
        columns=[
            "Hora",
            "Humedad Suelo",
            "Temperatura",
            "Humedad Amb",
            "Distancia"
        ]
    )

valores_iniciales = {
    "last_hum_suelo": 0,
    "last_temp_aire": 0.0,
    "last_hum_amb": 0,
    "last_dist_tanque": 0,
    "last_estado_bomba": "APAGADA",
    "last_modo_sistema": "AUTOMÁTICO",
    "ultima_actualizacion": "Sin lecturas"
}

for clave, valor in valores_iniciales.items():
    if clave not in st.session_state:
        st.session_state[clave] = valor


# =========================================================
# 5. COMUNICACIÓN SERIAL
# =========================================================

def enviar_comando(comando):
    try:
        if arduino is not None and arduino.is_open:
            arduino.write(comando.encode("utf-8"))
            arduino.flush()
        else:
            st.sidebar.error("Arduino desconectado.")

    except Exception as error:
        st.sidebar.error(f"Error de comunicación: {error}")


def leer_datos_arduino():
    try:
        if arduino is None or not arduino.is_open:
            return

        # Leer las líneas disponibles sin bloquear el panel
        if arduino.in_waiting > 0:
            linea = arduino.readline().decode(
                "utf-8",
                errors="ignore"
            ).strip()

            datos = linea.split(",")

            if len(datos) != 6:
                return

            hum_suelo = int(datos[0])
            temp_aire = float(datos[1])
            hum_amb = int(datos[2])
            distancia = int(datos[3])

            estado_bomba = (
                "ACTIVADA" if datos[4].strip() == "1"
                else "APAGADA"
            )

            modo = (
                "MANUAL" if datos[5].strip() == "1"
                else "AUTOMÁTICO"
            )

            # Validación básica de rangos
            if not 0 <= hum_suelo <= 100:
                return

            if not 0 <= hum_amb <= 100:
                return

            if temp_aire < -50 or temp_aire > 100:
                return

            # Guardar valores
            st.session_state.last_hum_suelo = hum_suelo
            st.session_state.last_temp_aire = temp_aire
            st.session_state.last_hum_amb = hum_amb
            st.session_state.last_dist_tanque = distancia
            st.session_state.last_estado_bomba = estado_bomba
            st.session_state.last_modo_sistema = modo

            ahora = datetime.now()

            st.session_state.ultima_actualizacion = (
                ahora.strftime("%H:%M:%S")
            )

            registro = pd.DataFrame(
                [[
                    ahora.strftime("%H:%M:%S"),
                    hum_suelo,
                    temp_aire,
                    hum_amb,
                    distancia
                ]],
                columns=[
                    "Hora",
                    "Humedad Suelo",
                    "Temperatura",
                    "Humedad Amb",
                    "Distancia"
                ]
            )

            st.session_state.historial = pd.concat(
                [
                    st.session_state.historial,
                    registro
                ],
                ignore_index=True
            ).tail(100)

    except (ValueError, TypeError) as error:
        print(f"Lectura inválida: {error}")

    except Exception as error:
        print(f"Error de lectura Arduino: {error}")


# =========================================================
# 6. BARRA LATERAL Y NAVEGACIÓN
# =========================================================

st.sidebar.markdown(
    """
    <div style="text-align:center; padding:15px 5px;">
        <div style="font-size:45px;">🌿</div>
        <h2 style="margin-bottom:0;">AGRO-INTELLIGENT</h2>
        <p style="font-size:12px;">SMART AGRICULTURE IoT</p>
        <hr>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("### MENÚ PRINCIPAL")

seccion = st.sidebar.radio(
    "Navegación",
    [
        "🏠 Panel principal",
        "📊 Monitoreo de sensores",
        "🎛️ Control de electrobomba",
        "🌱 Información de cultivos",
        "🔌 Ingeniería del circuito",
        "📈 Historial de mediciones"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")

st.sidebar.markdown("### CONECTIVIDAD")

if arduino is not None and arduino.is_open:
    st.sidebar.success("Arduino conectado")
else:
    st.sidebar.error("Arduino desconectado")

st.sidebar.caption(f"Puerto: {PUERTO_ARDUINO}")
st.sidebar.caption(f"Velocidad: {BAUDIOS} baudios")

st.sidebar.markdown("---")

st.sidebar.markdown("### MODO DE OPERACIÓN")

col_m1, col_m2 = st.sidebar.columns(2)

with col_m1:
    if st.button("🤖 AUTO", use_container_width=True):
        enviar_comando("A")

with col_m2:
    if st.button("👨‍💻 MANUAL", use_container_width=True):
        enviar_comando("M")

st.sidebar.markdown("---")

st.sidebar.markdown("### CONTROL DE BOMBA")

if st.button(
    "🟢 ENCENDER BOMBA",
    use_container_width=True
):
    enviar_comando("1")

if st.button(
    "🔴 APAGAR BOMBA",
    use_container_width=True
):
    enviar_comando("0")

st.sidebar.markdown("---")

st.sidebar.caption(
    "Proyecto académico de ingeniería electrónica"
)


# =========================================================
# 7. ENCABEZADO PRINCIPAL
# =========================================================

st.markdown(
    """
    <div class="hero">
        <div style="font-size:13px; letter-spacing:2px;">
            SMART AGRICULTURE TECHNOLOGY
        </div>
        <h1>🌿 AGRO-INTELLIGENT IoT</h1>
        <p>
            Sistema inteligente de monitoreo agrícola,
            análisis ambiental y gestión hídrica sostenible.
        </p>
        <p style="margin-top:15px; font-size:13px;">
            GRUPO N.º 2 | INGENIERÍA ELECTRÓNICA
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 8. ACTUALIZACIÓN EN TIEMPO REAL
# =========================================================

@st.fragment(run_every=0.5)
def actualizar_panel():

    leer_datos_arduino()

    if seccion in [
        "🏠 Panel principal",
        "📊 Monitoreo de sensores",
        "🎛️ Control de electrobomba"
    ]:

        st.caption(
            f"Última actualización: "
            f"{st.session_state.ultima_actualizacion}"
        )

        if seccion == "🏠 Panel principal":

            st.markdown("### RESUMEN GENERAL DEL SISTEMA")

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.metric(
                    "💧 HUMEDAD DEL SUELO",
                    f"{st.session_state.last_hum_suelo}%"
                )

            with c2:
                st.metric(
                    "🌡️ TEMPERATURA",
                    f"{st.session_state.last_temp_aire} °C"
                )

            with c3:
                st.metric(
                    "☁️ HUMEDAD AMBIENTAL",
                    f"{st.session_state.last_hum_amb}%"
                )

            with c4:
                st.metric(
                    "📡 DISTANCIA AL AGUA",
                    f"{st.session_state.last_dist_tanque} cm"
                )

            st.markdown("---")

            izquierda, derecha = st.columns([1.3, 1])

            with izquierda:

                st.markdown("### 📈 Comportamiento del suelo")

                if not st.session_state.historial.empty:

                    grafico = st.session_state.historial[
                        ["Hora", "Humedad Suelo"]
                    ].set_index("Hora")

                    st.line_chart(
                        grafico,
                        use_container_width=True
                    )

                else:
                    st.info(
                        "Esperando las primeras mediciones de Arduino."
                    )

            with derecha:

                st.markdown("### ⚙️ Estado de los actuadores")

                if st.session_state.last_modo_sistema == "MANUAL":
                    st.info("👨‍💻 Modo de operación: MANUAL")
                else:
                    st.success("🤖 Modo de operación: AUTOMÁTICO")

                if st.session_state.last_estado_bomba == "ACTIVADA":
                    st.success("🌊 Electrobomba ACTIVADA")
                else:
                    st.error("🛑 Electrobomba APAGADA")

                st.markdown("### 🛢️ Sensor ultrasónico")

                st.metric(
                    "Distancia medida",
                    f"{st.session_state.last_dist_tanque} cm"
                )

                st.caption(
                    "Lectura de distancia entre el sensor "
                    "y la superficie del agua. No representa "
                    "directamente el porcentaje del tanque."
                )

        elif seccion == "📊 Monitoreo de sensores":

            st.markdown("### 📊 MONITOREO DE VARIABLES AMBIENTALES")

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Humedad del suelo",
                f"{st.session_state.last_hum_suelo}%"
            )

            c2.metric(
                "Temperatura",
                f"{st.session_state.last_temp_aire} °C"
            )

            c3.metric(
                "Humedad ambiental",
                f"{st.session_state.last_hum_amb}%"
            )

            c4.metric(
                "Distancia ultrasónica",
                f"{st.session_state.last_dist_tanque} cm"
            )

            st.markdown("---")

            st.markdown("### Evolución de las variables")

            if not st.session_state.historial.empty:

                h = st.session_state.historial.set_index("Hora")

                tab1, tab2, tab3 = st.tabs([
                    "💧 Humedad del suelo",
                    "🌡️ Temperatura",
                    "☁️ Humedad ambiental"
                ])

                with tab1:
                    st.line_chart(h[["Humedad Suelo"]])

                with tab2:
                    st.line_chart(h[["Temperatura"]])

                with tab3:
                    st.line_chart(h[["Humedad Amb"]])

            else:
                st.info("No hay datos suficientes para generar gráficos.")

        elif seccion == "🎛️ Control de electrobomba":

            st.markdown("### 🎛️ CENTRO DE CONTROL DE ELECTROBOMBA")

            col1, col2 = st.columns(2)

            with col1:

                st.markdown("#### Modo de funcionamiento")

                st.info(
                    f"Modo actual: "
                    f"{st.session_state.last_modo_sistema}"
                )

                if st.button(
                    "🤖 ACTIVAR MODO AUTOMÁTICO",
                    use_container_width=True
                ):
                    enviar_comando("A")

                if st.button(
                    "👨‍💻 ACTIVAR MODO MANUAL",
                    use_container_width=True
                ):
                    enviar_comando("M")

            with col2:

                st.markdown("#### Accionamiento de bomba")

                if st.session_state.last_estado_bomba == "ACTIVADA":
                    st.success("BOMBA EN FUNCIONAMIENTO")
                else:
                    st.error("BOMBA APAGADA")

                if st.button(
                    "🟢 ENCENDER ELECTROBOMBA",
                    use_container_width=True
                ):
                    enviar_comando("1")

                if st.button(
                    "🔴 APAGAR ELECTROBOMBA",
                    use_container_width=True
                ):
                    enviar_comando("0")

            st.warning(
                "Los comandos manuales deben estar habilitados "
                "en el programa Arduino. Verifica el estado real "
                "del actuador y las protecciones eléctricas."
            )


actualizar_panel()


# =========================================================
# 9. INFORMACIÓN DE CULTIVOS
# =========================================================

if seccion == "🌱 Información de cultivos":

    st.markdown("## 🌱 DOCUMENTACIÓN AGRONÓMICA")

    st.write(
        "Cultivos considerados para el análisis de humedad "
        "del suelo y condiciones ambientales."
    )

    tabla_datos = {
        "Cultivo": [
            "Yuca (Manihot esculenta)",
            "Ñame (Dioscorea alata)",
            "Arroz secano",
            "Marañón (Anacardium occidentale)"
        ],
        "Temperatura óptima": [
            "24°C - 30°C",
            "25°C - 30°C",
            "22°C - 33°C",
            "24°C - 28°C"
        ],
        "Humedad relativa": [
            "60% - 80%",
            "70% - 80%",
            "70% - 90%",
            "65% - 80%"
        ],
        "Humedad crítica del suelo": [
            "< 30% - 35%",
            "< 40% - 50%",
            "< 50% - 60%",
            "< 25% - 30%"
        ]
    }

    df_cultivos = pd.DataFrame(tabla_datos)

    st.dataframe(
        df_cultivos,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    st.markdown("### 🌾 CULTIVOS EVALUADOS")

    cultivos = [
        (
            "Marañón",
            "maranon",
            "60% - 70%",
            "Seguimiento de condiciones ambientales "
            "durante las fases de floración."
        ),
        (
            "Arroz secano",
            "arroz",
            "70% - 90%",
            "Monitoreo de humedad durante el desarrollo "
            "del cultivo."
        ),
        (
            "Ñame",
            "name",
            "70% - 80%",
            "Seguimiento de la humedad durante el "
            "desarrollo del tubérculo."
        ),
        (
            "Yuca",
            "yuca",
            "60% - 70%",
            "Monitoreo de humedad durante el crecimiento "
            "y desarrollo de las raíces."
        )
    ]

    columnas = st.columns(4)

    for columna, cultivo in zip(columnas, cultivos):

        nombre, clave, humedad, descripcion = cultivo

        with columna:

            st.markdown(
                f"#### 🌿 {nombre}"
            )

            ruta = RUTAS[clave]

            if os.path.exists(ruta):
                st.image(
                    ruta,
                    caption=f"Cultivo de {nombre}",
                    use_container_width=True
                )
            else:
                st.warning(
                    f"No se encontró la imagen: "
                    f"{os.path.basename(ruta)}"
                )

            st.markdown(
                f"""
                <div class="info-card">
                    <b>Humedad de referencia</b>
                    <h3>{humedad}</h3>
                    <p>{descripcion}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.caption(
        "Los rangos son referencias orientativas. "
        "Deben validarse según variedad, etapa fenológica, "
        "tipo de suelo y método de medición."
    )


# =========================================================
# 10. INGENIERÍA DEL CIRCUITO
# =========================================================

if seccion == "🔌 Ingeniería del circuito":

    st.markdown("## 🔌 INGENIERÍA ELECTRÓNICA")

    st.write(
        "Documentación técnica del sistema de monitoreo "
        "agrícola basado en Arduino UNO R3 SMD."
    )

    tab1, tab2 = st.tabs([
        "📷 Diagrama del circuito",
        "📋 Descripción técnica"
    ])

    with tab1:

        st.markdown("### Diagrama de conexiones")

        if os.path.exists(RUTAS["circuito"]):

            st.image(
                RUTAS["circuito"],
                caption="Diagrama electrónico del sistema Agro-IoT",
                use_container_width=True
            )

        else:

            st.warning(
                "No se encontró circuito.jpg en la carpeta imag."
            )

    with tab2:

        st.markdown("### Arquitectura del sistema")

        st.markdown("""
        **Unidad de procesamiento**

        - Arduino UNO R3 SMD.
        - Lectura y procesamiento de sensores.
        - Comunicación serial con la interfaz.

        **Variables monitoreadas**

        - Humedad del suelo.
        - Temperatura ambiental.
        - Humedad relativa del aire.
        - Distancia mediante sensor ultrasónico.

        **Interfaz de usuario**

        - Plataforma desarrollada en Python y Streamlit.
        - Comunicación mediante puerto USB.
        - Visualización de datos en tiempo real.
        - Control manual y automático de la electrobomba.
        """)


# =========================================================
# 11. HISTORIAL DE MEDICIONES
# =========================================================

if seccion == "📈 Historial de mediciones":

    st.markdown("## 📈 REGISTRO HISTÓRICO")

    st.write(
        "Consulta de los últimos registros recibidos desde Arduino."
    )

    if not st.session_state.historial.empty:

        st.dataframe(
            st.session_state.historial,
            use_container_width=True,
            hide_index=True
        )

        csv = st.session_state.historial.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            "📥 DESCARGAR HISTORIAL CSV",
            data=csv,
            file_name="historial_agro_iot.csv",
            mime="text/csv",
            use_container_width=True
        )

    else:

        st.info(
            "Todavía no existen registros. "
            "Espera a que Arduino envíe sus primeras mediciones."
        )


# =========================================================
# 12. PIE DE PÁGINA
# =========================================================

st.markdown("---")

st.markdown(
    """
    <div class="footer">
        <b>AGRO-INTELLIGENT IoT | GRUPO N.º 2</b><br>
        Sistema inteligente de monitoreo agrícola<br>
        Ingeniería Electrónica · 2026<br>
        Tecnología al servicio de la agricultura sostenible 🌿
    </div>
    """,
    unsafe_allow_html=True
)