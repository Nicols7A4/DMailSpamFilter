# sistema_experto/__init__.py
from pgmpy.inference import VariableElimination

# Importamos los componentes de nuestros módulos
from .base_conocimiento import construir_modelo_bayesiano, UMBRAL_SPAM
from .adquisicion_conocimiento import extraer_evidencias
from .modulo_explicacion import generar_explicacion

# --- INICIALIZACIÓN DEL SISTEMA EXPERTO ---

# 1. Cargar la Base de Conocimiento
MODELO = construir_modelo_bayesiano()

# 2. Inicializar el Motor de Inferencia
MOTOR_INFERENCIA = VariableElimination(MODELO)

print("✅ Sistema Experto cargado y listo (Base de Conocimiento + Motor de Inferencia).")


# --- INTERFAZ DE USUARIO DEL SISTEMA ---

def analizar_correo(asunto, cuerpo, remitente_email):
    """
    Función pública que actúa como interfaz principal para el sistema experto.
    Orquesta el uso de los diferentes módulos.
    """
    # 1. Módulo de Adquisición: Obtener evidencias del correo
    evidencias = extraer_evidencias(texto=cuerpo, asunto=asunto, remitente=remitente_email)
    
    # 2. Motor de Inferencia: Calcular la probabilidad de spam
    prob_spam = float(MOTOR_INFERENCIA.query(variables=["correo_es_spam"], evidence=evidencias).values[1])
    
    # 3. Clasificar usando una regla de la Base de Conocimiento
    es_spam_predicho = prob_spam >= UMBRAL_SPAM
    
    # 4. Módulo de Explicación: Generar el reporte
    explicacion = generar_explicacion(MODELO, evidencias)
    
    # 5. Devolver un resultado estructurado
    return {
        "probabilidad_spam": prob_spam,
        "es_spam": es_spam_predicho,
        "reporte": explicacion,
        "evidencias": evidencias
    }