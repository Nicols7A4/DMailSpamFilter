# sistema_experto/base_conocimiento.py

from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.factors.discrete import TabularCPD

# ==============================================================================
# 1. HEURÍSTICAS Y DATOS FÁCTICOS
# Reglas simples y umbrales definidos por el experto.
# ==============================================================================

# Lista blanca de remitentes que no se consideran "desconocidos".
CONTACTOS_CONOCIDOS = {"amigo@email.com", "profesor@universidad.edu"}

# Lista de dominios gratuitos comunes.
DOMINIOS_GRATIS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "proton.me"}

# Umbral de decisión: si la probabilidad de spam es > 55%, se clasifica como tal.
UMBRAL_SPAM = 0.55


# ==============================================================================
# 2. CONOCIMIENTO LINGÜÍSTICO Y ESTRUCTURAL
# El "vocabulario" que el sistema usa para reconocer patrones de spam.
# ==============================================================================

# Palabras clave fuertemente asociadas con marketing, estafas y phishing.
SPAM_WORDS = {
    # Marketing y Ofertas
    "oferta", "gratis", "premio", "descuento", "gana", "click", "clic", "promoción", "bono", "cupón",
    # Urgencia y Miedo
    "urgente", "urgent", "limitado", "actividad sospechosa", "suspendida", "bloqueada", "verificación", "verifique",
    # Financiero y Cripto
    "dinero", "transferencia", "ganador", "lotería", "préstamo", "herencia", "ingresos pasivos",
    "bitcoin", "cripto", "nft", "airdrop", "wallet", "mercado", "valores",
    # Phishing y Marcas Falsas
    "PayPal", "Amazon", "Netflix", "Apple", "desbloquear",
    # Contenido para Adultos (NUEVO)
    "adultos", "citas", "solteros", "perfil", "mensaje", "tímido", "xxx", "natural", "tamaño", "aument"
}

# Patrones de Expresiones Regulares (regex) para características estructurales.
SHORT_URL_PATTERNS = [r"bit\.ly", r"tinyurl", r"t\.co", r"goo\.gl"]
PHONE_PATTERNS = [r"\b\+?\d{7,}\b", r"\b(whatsapp|wa\.me)\b"]
CRYPTO_PATTERNS = [r"\b(bitcoin|btc|eth|usdt|wallet|metamask)\b"]


# ==============================================================================
# 3. CONOCIMIENTO PROBABILÍSTICO (RED BAYESIANA)
# El núcleo del sistema experto que define las relaciones y pesos de cada evidencia.
# ==============================================================================

def construir_modelo_bayesiano():
    """
    Define la estructura de la red y las probabilidades condicionales (CPDs).
    Esta función representa el corazón de la base de conocimiento.
    """
    
    # --- A. ESTRUCTURA DE LA RED (SIN CAMBIOS) ---
    edges = [
        ("correo_es_spam", "contiene_palabra_spam"),
        ("correo_es_spam", "link_count"),
        ("correo_es_spam", "contiene_short_url"),
        ("correo_es_spam", "muchas_exclamaciones"),
        ("correo_es_spam", "contiene_simbolo_dinero"),
        ("correo_es_spam", "remitente_desconocido"),
        ("correo_es_spam", "dominio_gratis"),
        ("correo_es_spam", "mayusculas_excesivas"),
        ("correo_es_spam", "subject_largo"),
        ("correo_es_spam", "telefono_o_whatsapp"),
        ("correo_es_spam", "terminos_crypto"),
    ]
    model = DiscreteBayesianNetwork(edges)

    # --- B. REGLAS PROBABILÍSTICAS (EL CONOCIMIENTO DEL EXPERTO CUANTIFICADO) ---
#     # Cada CPD se define con una matriz de valores con la siguiente estructura:
#     # values = [[ P(Característica=NO | Correo=LEGÍTIMO), P(Característica=NO | Correo=SPAM) ],
#     #           [ P(Característica=SÍ | Correo=LEGÍTIMO), P(Característica=SÍ | Correo=SPAM) ]]
    
    ###
    prior_spam = 0.47
    cpd_spam = TabularCPD("correo_es_spam", 2, [[1 - prior_spam], [prior_spam]])

    # <--- REGLA CLAVE: Hacemos la regla de palabras muy fuerte, pero con un pequeño margen.
    # Es muy improbable (1%) que un correo legítimo tenga estas palabras.
    cpd_words = TabularCPD("contiene_palabra_spam", 2, [[0.99, 0.10], [0.01, 0.90]], ["correo_es_spam"], [2])

    # <--- REGLA CLAVE: Fortalecemos significativamente la regla de enlaces.
    # Tener 2+ enlaces es un indicador muy fuerte de spam.
    cpd_linkcount = TabularCPD(
        "link_count", 3,
        values=[[0.70, 0.20],  # P(0 links | Legítimo/Spam)
                [0.25, 0.30],  # P(1 link  | Legítimo/Spam)
                [0.05, 0.50]], # P(2+ links| Legítimo/Spam)
        evidence=["correo_es_spam"], evidence_card=[2]
    )
    cpd_money = TabularCPD("contiene_simbolo_dinero", 2, [[0.97, 0.30], [0.03, 0.70]], ["correo_es_spam"], [2])
    cpd_unknown = TabularCPD("remitente_desconocido", 2, [[0.60, 0.05], [0.40, 0.95]], ["correo_es_spam"], [2])
    cpd_phone = TabularCPD("telefono_o_whatsapp", 2, [[0.97, 0.60], [0.03, 0.40]], ["correo_es_spam"], [2])
    cpd_crypto = TabularCPD("terminos_crypto", 2, [[0.99, 0.50], [0.01, 0.50]], ["correo_es_spam"], [2])
    cpd_free = TabularCPD("dominio_gratis", 2, [[0.75, 0.45], [0.25, 0.55]], ["correo_es_spam"], [2])
    cpd_caps = TabularCPD("mayusculas_excesivas", 2, [[0.98, 0.70], [0.02, 0.30]], ["correo_es_spam"], [2])
    cpd_short = TabularCPD("contiene_short_url", 2, [[0.98, 0.80], [0.02, 0.20]], ["correo_es_spam"], [2])
    cpd_excl = TabularCPD("muchas_exclamaciones", 2, [[0.95, 0.75], [0.05, 0.25]], ["correo_es_spam"], [2])
    cpd_subj = TabularCPD("subject_largo", 2, [[0.90, 0.80], [0.10, 0.20]], ["correo_es_spam"], [2])

    model.add_cpds(
        cpd_spam, cpd_words, cpd_linkcount, cpd_short, cpd_excl, cpd_money,
        cpd_unknown, cpd_free, cpd_caps, cpd_subj, cpd_phone, cpd_crypto
    )
    
    return model



# def construir_modelo_bayesiano():
#     """
#     Define la estructura de la red y las probabilidades condicionales (CPDs).
#     Esta función representa el corazón de la base de conocimiento.
#     """
    
#     # --- A. ESTRUCTURA DE LA RED (LAS RELACIONES CAUSA-EFECTO) ---
#     # Se define que todas las características (evidencias) son un efecto
#     # directo de si el correo es spam o no.
#     edges = [
#         ("correo_es_spam", "contiene_palabra_spam"),
#         ("correo_es_spam", "link_count"),
#         ("correo_es_spam", "contiene_short_url"),
#         ("correo_es_spam", "muchas_exclamaciones"),
#         ("correo_es_spam", "contiene_simbolo_dinero"),
#         ("correo_es_spam", "remitente_desconocido"),
#         ("correo_es_spam", "dominio_gratis"),
#         ("correo_es_spam", "mayusculas_excesivas"),
#         ("correo_es_spam", "subject_largo"),
#         ("correo_es_spam", "telefono_o_whatsapp"),
#         ("correo_es_spam", "terminos_crypto"),
#     ]
#     model = DiscreteBayesianNetwork(edges)

#     # --- B. REGLAS PROBABILÍSTICAS (EL CONOCIMIENTO DEL EXPERTO CUANTIFICADO) ---
#     # Cada CPD se define con una matriz de valores con la siguiente estructura:
#     # values = [[ P(Característica=NO | Correo=LEGÍTIMO), P(Característica=NO | Correo=SPAM) ],
#     #           [ P(Característica=SÍ | Correo=LEGÍTIMO), P(Característica=SÍ | Correo=SPAM) ]]

#     # Probabilidad a priori: Basado en datos, ~47% de los correos globales son spam.
#     prior_spam = 0.47
#     cpd_spam = TabularCPD("correo_es_spam", 2, [[1 - prior_spam], [prior_spam]])

#     # Reglas para cada característica, calibradas tras varias pruebas.
#     #cpd_words = TabularCPD("contiene_palabra_spam", 2, [[0.999, 0.001], [0.001, 0.999]], ["correo_es_spam"], [2])
#     cpd_words = TabularCPD("contiene_palabra_spam", 2, [[0.99, 0.05], [0.02, 0.95]], ["correo_es_spam"], [2])
#     cpd_money = TabularCPD("contiene_simbolo_dinero", 2, [[0.95, 0.25], [0.05, 0.75]], ["correo_es_spam"], [2])
#     cpd_unknown = TabularCPD("remitente_desconocido", 2, [[0.50, 0.10], [0.50, 0.90]], ["correo_es_spam"], [2])
#     cpd_phone = TabularCPD("telefono_o_whatsapp", 2, [[0.97, 0.60], [0.03, 0.40]], ["correo_es_spam"], [2])
#     cpd_crypto = TabularCPD("terminos_crypto", 2, [[0.99, 0.50], [0.01, 0.50]], ["correo_es_spam"], [2])
#     cpd_free = TabularCPD("dominio_gratis", 2, [[0.75, 0.45], [0.25, 0.55]], ["correo_es_spam"], [2])
    
#     # Reglas ajustadas para reducir la penalización por ausencia de la característica.
#     cpd_caps = TabularCPD("mayusculas_excesivas", 2, [[0.98, 0.70], [0.02, 0.30]], ["correo_es_spam"], [2])
#     cpd_short = TabularCPD("contiene_short_url", 2, [[0.98, 0.80], [0.02, 0.20]], ["correo_es_spam"], [2])
#     cpd_excl = TabularCPD("muchas_exclamaciones", 2, [[0.95, 0.75], [0.05, 0.25]], ["correo_es_spam"], [2])
#     cpd_subj = TabularCPD("subject_largo", 2, [[0.90, 0.80], [0.10, 0.20]], ["correo_es_spam"], [2])

#     # Regla para una característica con 3 estados (0, 1, o 2+ enlaces).
#     cpd_linkcount = TabularCPD(
#         "link_count", 3,
#         values=[[0.60, 0.35],  # P(0 links | Legítimo/Spam)
#                 [0.35, 0.35],  # P(1 link  | Legítimo/Spam)
#                 [0.05, 0.30]], # P(2+ links| Legítimo/Spam)
#         evidence=["correo_es_spam"], evidence_card=[2]
#     )
    
#     # Se añaden todas las reglas al modelo para completar la base de conocimiento.
#     model.add_cpds(
#         cpd_spam, cpd_words, cpd_linkcount, cpd_short, cpd_excl, cpd_money,
#         cpd_unknown, cpd_free, cpd_caps, cpd_subj, cpd_phone, cpd_crypto
#     )
    
#     return model