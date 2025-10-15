# Reglas de la Base de Conocimiento (Knowledge Base)

Este documento describe las reglas probabilísticas (CPDs) y las variables
usadas en `sistema_experto/base_conocimiento.py`.

## Resumen

La base de conocimiento está modelada como una red bayesiana donde el nodo
objetivo es `correo_es_spam` (0 = ham / legítimo, 1 = spam). Todas las
características (evidencias) son hijos directos de `correo_es_spam`.

El prior utilizado:

- `P(correo_es_spam=1) = 0.47` (CPD `cpd_spam`)

## Variables y CPDs (interpretación)

Para cada CPD se indica: variable, estados, matriz `values` y una lectura
rápida de la interpretación. Las matrices siguen el formato usado por
`pgmpy.TabularCPD`: filas = estados de la variable, columnas = estados del
padre (en este caso `correo_es_spam` con columnas [ham, spam]).

### 1) contiene_palabra_spam (cpd_words)
- Estados: 0 = no, 1 = sí
- Values: [[0.99, 0.10], [0.01, 0.90]]
- Interpretación:
  - P(no palabra sospechosa | ham) = 0.99
  - P(sí palabra sospechosa | ham) = 0.01
  - P(no palabra sospechosa | spam) = 0.10
  - P(sí palabra sospechosa | spam) = 0.90
- Comentario: presencia de palabras del vocabulario de spam es muy indicativa.

### 2) link_count (cpd_linkcount)
- Estados: 0 = 0 links, 1 = 1 link, 2 = 2+ links
- Values: [[0.70, 0.20], [0.25, 0.30], [0.05, 0.50]]
- Interpretación:
  - Ham: mayor probabilidad de 0 links (0.70)
  - Spam: mayor probabilidad de 2+ links (0.50)
- Comentario: múltiples enlaces incrementan fuertemente la probabilidad de spam.

### 3) contiene_simbolo_dinero (cpd_money)
- Estados: 0 = no, 1 = sí
- Values: [[0.97, 0.30], [0.03, 0.70]]
- Interpretación: términos/símbolos monetarios son comunes en spam financiero.

### 4) remitente_desconocido (cpd_unknown)
- Estados: 0 = conocido, 1 = desconocido
- Values: [[0.60, 0.05], [0.40, 0.95]]
- Interpretación: remitente desconocido es fuertemente indicativo de spam.

### 5) telefono_o_whatsapp (cpd_phone)
- Estados: 0 = no, 1 = sí
- Values: [[0.97, 0.60], [0.03, 0.40]]
- Interpretación: referencias a teléfonos/WhatsApp aparecen más a menudo en spam.

### 6) terminos_crypto (cpd_crypto)
- Estados: 0 = no, 1 = sí
- Values: [[0.99, 0.50], [0.01, 0.50]]
- Interpretación: términos cripto son raros en ham y relativamente frecuentes en spam.

### 7) dominio_gratis (cpd_free)
- Estados: 0 = no, 1 = sí
- Values: [[0.75, 0.45], [0.25, 0.55]]
- Interpretación: uso de dominios gratuitos tiene ligera correlación con spam.

### 8) mayusculas_excesivas (cpd_caps)
- Estados: 0 = no, 1 = sí
- Values: [[0.98, 0.70], [0.02, 0.30]]
- Interpretación: asuntos en mayúsculas con frecuencia elevan la probabilidad de spam.

### 9) contiene_short_url (cpd_short)
- Estados: 0 = no, 1 = sí
- Values: [[0.98, 0.80], [0.02, 0.20]]
- Interpretación: URLs acortadas son más frecuentes en spam.

### 10) muchas_exclamaciones (cpd_excl)
- Estados: 0 = pocas, 1 = muchas
- Values: [[0.95, 0.75], [0.05, 0.25]]
- Interpretación: uso excesivo de signos de exclamación incrementa la probabilidad de spam.

### 11) subject_largo (cpd_subj)
- Estados: 0 = corto, 1 = largo
- Values: [[0.90, 0.80], [0.10, 0.20]]
- Interpretación: asunto largo aporta evidencia débil hacia spam.

## Listas y patrones usadas en la adquisición de evidencias

- `SPAM_WORDS`: conjunto de palabras clave (oferta, gratis, premio, bitcoin, etc.).
- `SHORT_URL_PATTERNS`: regex para detectar URLs acortadas (bit.ly, tinyurl, t.co, ...).
- `PHONE_PATTERNS`: regex para detectar números y referencias a WhatsApp.
- `CRYPTO_PATTERNS`: regex para detectar términos relacionados con criptomonedas.
- `CONTACTOS_CONOCIDOS`: lista blanca de remitentes considerados 'conocidos'.
- `DOMINIOS_GRATIS`: dominios como gmail.com, yahoo.com, outlook.com.

Todos estos se encuentran definidos en `sistema_experto/base_conocimiento.py` y son
usados por `adquisicion_conocimiento.py` para transformar texto en evidencias.

## Umbral de decisión

- `UMBRAL_SPAM = 0.55` — si P(spam | evidencias) >= umbral → clasificar como spam.

## Notas finales

- Las CPDs reflejan conocimiento experto calibrado; si se desea mejorar el
  rendimiento real, se puede reestimarlas a partir de datos etiquetados.
- Este documento pretende ser una referencia clara para entender qué
  representan las probabilidades en la base de conocimiento.
