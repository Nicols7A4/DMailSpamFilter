# sistema_experto/__init__.py
"""
Paquete sistema_experto reorganizado para mayor claridad.

Componentes:
- base_conocimiento: estructura y CPDs del modelo
- adquisicion_conocimiento: extracción de evidencias desde texto
- modulo_explicacion: generación de reportes interpretables
- motor_inferencia: inicialización y consulta del motor (pgmpy)

La función pública `analizar_correo` conserva exactamente la misma
firma y formato de salida que antes para mantener compatibilidad con
el resto de la aplicación.
"""

from .base_conocimiento import UMBRAL_SPAM
from .procesador_de_evidencias import extraer_evidencias
from .modulo_explicacion import generar_explicacion
from .motor_inferencia import inferir_probabilidad_spam, MODELO

print("✅ Sistema Experto cargado y listo (Base de Conocimiento + Motor de Inferencia).")


def analizar_correo(asunto, cuerpo, remitente_email):
    """
    Interfaz pública. Recibe asunto, cuerpo y remitente. Devuelve:

    {
      "probabilidad_spam": float,
      "es_spam": bool,
      "reporte": list,   # salida de generar_explicacion
      "evidencias": dict # salida de extraer_evidencias
    }
    """
    evidencias = extraer_evidencias(texto=cuerpo, asunto=asunto, remitente=remitente_email)

    prob_spam = inferir_probabilidad_spam(evidencias)
    es_spam_predicho = prob_spam >= UMBRAL_SPAM

    # mantenemos la explicación existente
    explicacion = generar_explicacion(MODELO, evidencias)

    return {
        "probabilidad_spam": float(prob_spam),
        "es_spam": bool(es_spam_predicho),
        "reporte": explicacion,
        "evidencias": evidencias
    }