# sistema_experto/base_conocimiento.py
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.factors.discrete import TabularCPD

# --- CONOCIMIENTO EXPLÍCITO DEL EXPERTO ---

# Heurísticas y datos fácticos
CONTACTOS_CONOCIDOS = set(["amigo@email.com", "profesor@universidad.edu"])
DOMINIOS_GRATIS    = set(["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "proton.me"])
UMBRAL_SPAM = 0.55

# Listas de palabras y patrones (conocimiento sobre el lenguaje)
SPAM_WORDS = {
    "oferta","gratis","premio","descuento","gana","click","clic","urgente","urgent",
    "felicitaciones","dinero","transferencia","bono","ganador","lotería","promoción",
    "limitado","verifica","verifique","siguiente","enlace","verificación","cupón","desbloquear","recarga","préstamo",
    "sus","datos","herencia","bitcoin","cripto","nft","airdrop",
    "PayPal","Amazon","Netflix","Apple", "XXX",
    "suspendida","bloqueada","actividad sospechosa","verificar",
    "trabajo desde casa",  "ingresos pasivos", "oportunidad de negocio"
}
SHORT_URL_PATTERNS = [r"bit\.ly", r"tinyurl", r"t\.co", r"goo\.gl", r"ow\.ly", r"is\.gd", r"cutt\.ly"]
PHONE_PATTERNS = [
    r"\b\+?\d{2,3}[-\s]?\d{3}[-\s]?\d{3,4}[-\s]?\d{3,4}\b",
    r"\b(whatsapp|wasap|wa\.me|whats\.app)\b"
]
CRYPTO_PATTERNS = [r"\bbitcoin\b", r"\bbtc\b", r"\beth(ereum)?\b", r"\busdt?\b", r"\bwallet\b", r"\bmetamask\b"]

def construir_modelo_bayesiano():
    """
    Define la estructura de la red y las probabilidades condicionales (CPDs).
    Esta función representa el núcleo de la base de conocimiento.
    """
    edges = [
        ("correo_es_spam","contiene_palabra_spam"), ("correo_es_spam","link_count"),
        ("correo_es_spam","contiene_short_url"), ("correo_es_spam","muchas_exclamaciones"),
        ("correo_es_spam","contiene_simbolo_dinero"), ("correo_es_spam","remitente_desconocido"),
        ("correo_es_spam","dominio_gratis"), ("correo_es_spam","mayusculas_excesivas"),
        ("correo_es_spam","subject_largo"), ("correo_es_spam","telefono_o_whatsapp"),
        ("correo_es_spam","terminos_crypto"),
    ]
    model = DiscreteBayesianNetwork(edges)
    
    # --- PROBABILIDADES DEFINIDAS POR EL EXPERTO (CPDs) ---
    
    # --- PROBABILIDADES DEFINIDAS POR EL EXPERTO (CPDs) ---
    # Adaptado con datos de investigación (Oct 2025)

    # <-- CAMBIO: Ajustado al ~46% del tráfico de correo global.
    prior_spam = 0.47
    cpd_spam = TabularCPD("correo_es_spam", 2, [[1-prior_spam], [prior_spam]])

    # <-- CAMBIO: Reforzado. Es la característica principal del spam de marketing (el más común).
    cpd_words = TabularCPD("contiene_palabra_spam", 2, [[0.98, 0.05], [0.02, 0.95]], ["correo_es_spam"], [2])

    # <-- CAMBIO: Reforzado. Crucial para phishing y marketing.
    # Muchos correos de phishing no usan URLs acortadas.
    cpd_short   = TabularCPD("contiene_short_url",   2, [[0.98, 0.80], [0.02, 0.20]], ["correo_es_spam"], [2])

    # No tener exclamaciones no es una prueba fuerte de legitimidad.
    cpd_excl    = TabularCPD("muchas_exclamaciones", 2, [[0.95, 0.75], [0.05, 0.25]], ["correo_es_spam"], [2])

    # <-- CAMBIO: Reforzado. Característica clave del spam financiero (26.5% del total).
    cpd_money   = TabularCPD("contiene_simbolo_dinero",2,[[0.95, 0.25], [0.05, 0.75]], ["correo_es_spam"], [2])

    cpd_unknown = TabularCPD("remitente_desconocido",2,[[0.50, 0.10], [0.50, 0.90]], ["correo_es_spam"], [2])

    cpd_free    = TabularCPD("dominio_gratis",       2, [[0.75, 0.45], [0.25, 0.55]], ["correo_es_spam"], [2])

    #                                            [P(No Caps|Legítimo), P(No Caps|Spam)] [P(Sí Caps|Legítimo), P(Sí Caps|Spam)]
    cpd_caps    = TabularCPD("mayusculas_excesivas", 2, [[0.98, 0.70], [0.02, 0.30]], ["correo_es_spam"], [2])

    # No tener un asunto largo es normal en ambos tipos de correo.
    cpd_subj    = TabularCPD("subject_largo",        2, [[0.90, 0.80], [0.10, 0.20]], ["correo_es_spam"], [2])

    cpd_phone   = TabularCPD("telefono_o_whatsapp",  2, [[0.97, 0.60], [0.03, 0.40]], ["correo_es_spam"], [2])

    # <-- CAMBIO: Ligeramente reforzado, ya que se solapa con el spam financiero.
    cpd_crypto  = TabularCPD("terminos_crypto",      2, [[0.99, 0.50], [0.01, 0.50]], ["correo_es_spam"], [2])

    # <-- CAMBIO: Reforzado. Los enlaces son fundamentales en marketing y phishing.
    cpd_linkcount = TabularCPD("link_count", 3,
                           values=[[0.60, 0.35],  # P(0 links | ham/spam) <-- Aumentado de 0.10 a 0.35
                                   [0.35, 0.35],  # P(1 link  | ham/spam) <-- Ligeramente aumentado
                                   [0.05, 0.30]], # P(2+ links| ham/spam) <-- Ligeramente reducido
                           evidence=["correo_es_spam"], evidence_card=[2])
        
    model.add_cpds(cpd_spam, cpd_words, cpd_linkcount, cpd_short, cpd_excl, cpd_money, cpd_unknown, cpd_free, cpd_caps, cpd_subj, cpd_phone, cpd_crypto)
    return model