"""
motor_inferencia.py
-------------------
Responsable de inicializar el modelo bayesiano (Base de Conocimiento)
y proporcionar una interfaz para realizar inferencias.

NOTA: Este módulo sólo separa la responsabilidad del motor de inferencia
para mejorar la legibilidad. No cambia la lógica ni los valores del modelo.
"""
from pgmpy.inference import VariableElimination
from .base_conocimiento import construir_modelo_bayesiano


# Construcción del modelo y motor (único punto de inicialización)
MODELO = construir_modelo_bayesiano()
MOTOR_INFERENCIA = VariableElimination(MODELO)


def inferir_probabilidad_spam(evidencias: dict) -> float:
    """
    Devuelve P(correo_es_spam | evidencias) como float.
    """
    resultado = MOTOR_INFERENCIA.query(variables=["correo_es_spam"], evidence=evidencias)
    return float(resultado.values[1])
