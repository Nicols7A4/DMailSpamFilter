# DMailSpamFilter

Proyecto: sistema de filtrado de spam basado en un sistema experto (red bayesiana).

Este README es intencionalmente simple y se centra en la parte del "sistema experto".

## Resumen

La aplicación es una web en Flask que utiliza un sistema experto para analizar correos y decidir si son spam. El sistema experto está organizado en el paquete `sistema_experto` y se compone de:

- `base_conocimiento.py` — Define la estructura de la red bayesiana y los CPDs (conocimiento cuantificado por el experto).
- `adquisicion_conocimiento.py` — Extrae las evidencias (características) desde el texto del correo (asunto, cuerpo, remitente).
- `modulo_explicacion.py` — Calcula la contribución (likelihood ratio) de cada evidencia para generar explicaciones interpretables.
- `motor_inferencia.py` — Inicializa el modelo bayesiano y el motor de inferencia (VariableElimination) y ofrece una función para consultar P(spam | evidencias).
- `__init__.py` — Interfaz pública: `analizar_correo(asunto, cuerpo, remitente_email)` que devuelve un dict con la decisión y explicación.


## Contrato público principal

Función: `sistema_experto.analizar_correo(asunto: str, cuerpo: str, remitente_email: str) -> dict`

Retorna un diccionario con las claves:

- `probabilidad_spam` (float): probabilidad en [0,1] de que el correo sea spam.
- `es_spam` (bool): decisión binaria comparando `probabilidad_spam` con `UMBRAL_SPAM`.
- `reporte` (list): lista ordenada con la contribución de cada evidencia (variable, valor, LR, log_LR).
- `evidencias` (dict): características extraídas usadas para la inferencia.


## Cómo probar localmente (rápido)

1. Crear un entorno virtual e instalar dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Probar el sistema experto desde Python:

```python
from sistema_experto import analizar_correo
res = analizar_correo('Oferta limitada', 'Gana dinero con bitcoin y visita http://bit.ly/xyz', 'spam@example.com')
print(res)
```

3. Ejecutar la aplicación Flask:

```powershell
python app.py
# Visitar http://127.0.0.1:5000
```


## Notas rápidas y recomendaciones

- El `base_conocimiento.py` contiene las TabularCPD que definen cómo cada característica se comporta condicional al hecho de ser spam o no; ver comentarios en ese archivo para la interpretación por CPD.
- `app.py` guarda explicaciones en la base de datos como JSON (campo `explicacion_json`) junto con `probabilidad_spam` y `es_spam`.
- Seguridad: actualmente hay credenciales y contraseñas sin hashear en el código; se recomienda mover credenciales a variables de entorno y usar hashing (bcrypt) para contraseñas.


## Contacto

Si quieres que documente más en detalle alguna parte (por ejemplo, generar diagramas, tests unitarios o un README más extenso), dime cuál prefieres y lo hago.
