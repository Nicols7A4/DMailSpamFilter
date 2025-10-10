# sistema_experto/filtro.py
import re
import numpy as np
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination

# ------------------ CONFIGURACIÓN EXPERTA (del archivo filtro3.py) ------------------
CONTACTOS_CONOCIDOS = set(["amigo@email.com", "profesor@universidad.edu"])
DOMINIOS_GRATIS    = set(["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "proton.me"])

SPAM_WORDS = {
    "oferta","gratis","premio","descuento","gana","click","clic","urgente","urgent",
    "felicitaciones","dinero","transferencia","bono","ganador","lotería","promoción",
    "limitado","verifica","verificación","cupón","desbloquear","recarga","préstamo",
    "herencia","bitcoin","cripto","nft","airdrop"
}
SHORT_URL_PATTERNS = [r"bit\.ly", r"tinyurl", r"t\.co", r"goo\.gl", r"ow\.ly", r"is\.gd", r"cutt\.ly"]
PHONE_PATTERNS = [
    r"\b\+?\d{2,3}[-\s]?\d{3}[-\s]?\d{3,4}[-\s]?\d{3,4}\b",
    r"\b(whatsapp|wasap|wa\.me|whats\.app)\b"
]
CRYPTO_PATTERNS = [r"\bbitcoin\b", r"\bbtc\b", r"\beth(ereum)?\b", r"\busdt?\b", r"\bwallet\b", r"\bmetamask\b"]

UMBRAL_SPAM = 0.55

# ------------------ FUNCIONES DE EXTRACCIÓN Y MODELADO (del archivo filtro3.py) ------------------

def normalize_email(from_header: str) -> str:
    if not from_header: return ""
    m = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", from_header)
    return m.group(0).lower() if m else from_header.strip().lower()

def derive_features(text: str, subject: str, from_h: str) -> dict:
    low = (text or "").lower()
    sub = (subject or "")
    low_sub = sub.lower()

    contains_spam_word = int(any(w in low or w in low_sub for w in SPAM_WORDS))
    urls = re.findall(r"https?://[^\s'\"<>)+]+", (text or "") + " " + (subject or ""))
    link_count = 0 if len(urls)==0 else (1 if len(urls)==1 else 2)
    contains_short = int(any(re.search(p, " ".join(urls).lower()) for p in SHORT_URL_PATTERNS))
    many_excl = int((text+subject).count("!") >= 3)
    money = int(bool(re.search(r"[€$]|precio|transferencia|paga|pago|pago inmediato|oferta", low)))
    letters = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", sub)
    caps_ratio = (sum(1 for c in sub if c.isupper()) / len(letters)) if letters else 0
    caps_excess = int(caps_ratio > 0.6 and len(sub) >= 6)
    long_subject = int(len(sub) > 60)
    from_email = normalize_email(from_h)
    domain = from_email.split("@")[-1] if "@" in from_email else ""
    unknown_sender = int(from_email not in CONTACTOS_CONOCIDOS)
    free_domain    = int(domain in DOMINIOS_GRATIS)
    has_phone = int(any(re.search(p, low) for p in PHONE_PATTERNS))
    has_crypto = int(any(re.search(p, low) for p in CRYPTO_PATTERNS))

    return {
        "contiene_palabra_spam": contains_spam_word,
        "link_count": link_count,
        "contiene_short_url": contains_short,
        "muchas_exclamaciones": many_excl,
        "contiene_simbolo_dinero": money,
        "remitente_desconocido": unknown_sender,
        "dominio_gratis": free_domain,
        "mayusculas_excesivas": caps_excess,
        "subject_largo": long_subject,
        # Características simplificadas de filtro3.py para no depender de headers complejos
        "telefono_o_whatsapp": has_phone,
        "terminos_crypto": has_crypto,
    }

def build_bayes_expert_model():
    # Modelo simplificado para no incluir características de headers que no tenemos
    edges = [
        ("correo_es_spam","contiene_palabra_spam"), ("correo_es_spam","link_count"),
        ("correo_es_spam","contiene_short_url"), ("correo_es_spam","muchas_exclamaciones"),
        ("correo_es_spam","contiene_simbolo_dinero"), ("correo_es_spam","remitente_desconocido"),
        ("correo_es_spam","dominio_gratis"), ("correo_es_spam","mayusculas_excesivas"),
        ("correo_es_spam","subject_largo"), ("correo_es_spam","telefono_o_whatsapp"),
        ("correo_es_spam","terminos_crypto"),
    ]
    model = DiscreteBayesianNetwork(edges)
    prior_spam = 0.30
    cpd_spam = TabularCPD("correo_es_spam", 2, [[1-prior_spam],[prior_spam]])
    cpd_words   = TabularCPD("contiene_palabra_spam", 2, [[0.80,0.20],[0.20,0.80]], ["correo_es_spam"], [2])
    cpd_short   = TabularCPD("contiene_short_url",   2, [[0.98,0.35],[0.02,0.65]], ["correo_es_spam"], [2])
    cpd_excl    = TabularCPD("muchas_exclamaciones", 2, [[0.92,0.35],[0.08,0.65]], ["correo_es_spam"], [2])
    cpd_money   = TabularCPD("contiene_simbolo_dinero",2,[[0.95,0.45],[0.05,0.55]], ["correo_es_spam"], [2])
    cpd_unknown = TabularCPD("remitente_desconocido",2,[[0.50,0.10],[0.50,0.90]], ["correo_es_spam"], [2])
    cpd_free    = TabularCPD("dominio_gratis",       2, [[0.75,0.45],[0.25,0.55]], ["correo_es_spam"], [2])
    cpd_caps    = TabularCPD("mayusculas_excesivas", 2, [[0.96,0.25],[0.04,0.75]], ["correo_es_spam"], [2])
    cpd_subj    = TabularCPD("subject_largo",        2, [[0.92,0.40],[0.08,0.60]], ["correo_es_spam"], [2])
    cpd_phone   = TabularCPD("telefono_o_whatsapp",  2, [[0.97,0.60],[0.03,0.40]], ["correo_es_spam"], [2])
    cpd_crypto  = TabularCPD("terminos_crypto",      2, [[0.99,0.60],[0.01,0.40]], ["correo_es_spam"], [2])
    cpd_linkcount = TabularCPD("link_count", 3, [[0.55, 0.15], [0.35, 0.35], [0.10, 0.50]], evidence=["correo_es_spam"], evidence_card=[2])
    
    model.add_cpds(cpd_spam, cpd_words, cpd_linkcount, cpd_short, cpd_excl, cpd_money, cpd_unknown, cpd_free, cpd_caps, cpd_subj, cpd_phone, cpd_crypto)
    return model, VariableElimination(model)

def explain_contributions(model, observed):
    lr_list = []
    for var, val in observed.items():
        if var == "correo_es_spam": continue
        cpd = model.get_cpds(var)
        if cpd is None or cpd.get_evidence() != ['correo_es_spam']: continue
        
        state = int(val)
        p_ham  = max(float(cpd.values[state, 0]), 1e-9)
        p_spam = max(float(cpd.values[state, 1]), 1e-9)
        lr = p_spam / p_ham
        lr_list.append({"variable": var, "valor": val, "lr": lr, "log_lr": np.log10(lr)})
        
    lr_list.sort(key=lambda x: abs(x["log_lr"]), reverse=True)
    return lr_list

# ------------------ FUNCIÓN PRINCIPAL DE INTERFAZ ------------------

# Se construye el modelo UNA SOLA VEZ cuando se inicia la aplicación.
# Esto es mucho más eficiente que construirlo con cada correo.
MODELO, INFERENCIA = build_bayes_expert_model()
print("✅ Modelo Bayesiano cargado y listo para usarse.")

def analizar_correo(asunto, cuerpo, remitente_email):
    """
    Función principal que recibe los datos de un correo y devuelve el análisis.
    """
    # 1. Extraer características
    evidencias = derive_features(text=cuerpo, subject=asunto, from_h=remitente_email)
    
    # 2. Realizar inferencia para obtener la probabilidad de spam
    prob_spam = float(INFERENCIA.query(variables=["correo_es_spam"], evidence=evidencias).values[1])
    
    # 3. Clasificar según el umbral
    es_spam_predicho = prob_spam >= UMBRAL_SPAM
    
    # 4. Generar la explicación de las contribuciones
    explicacion = explain_contributions(MODELO, evidencias)
    
    # 5. Devolver un resultado bien estructurado
    return {
        "probabilidad_spam": prob_spam,
        "es_spam": es_spam_predicho,
        "reporte": explicacion,
        "evidencias": evidencias
    }