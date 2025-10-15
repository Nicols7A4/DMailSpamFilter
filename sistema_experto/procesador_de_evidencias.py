# sistema_experto/adquisicion_conocimiento.py
import re
from .base_conocimiento import SPAM_WORDS, SHORT_URL_PATTERNS, PHONE_PATTERNS, CRYPTO_PATTERNS, CONTACTOS_CONOCIDOS, DOMINIOS_GRATIS

def _normalize_email(from_header: str) -> str:
    if not from_header: return ""
    m = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", from_header)
    return m.group(0).lower() if m else from_header.strip().lower()

def extraer_evidencias(texto: str, asunto: str, remitente: str) -> dict:
    """
    Toma los datos crudos de un correo y los convierte en un diccionario
    de evidencias (características) para el motor de inferencia.
    """
    low = (texto or "").lower()
    sub = (asunto or "")
    low_sub = sub.lower()

    contains_spam_word = int(any(w in low or w in low_sub for w in SPAM_WORDS))
    urls = re.findall(r"https?://[^\s'\"<>)+]+", (texto or "") + " " + (asunto or ""))
    link_count = 0 if len(urls) == 0 else (1 if len(urls) == 1 else 2)
    contains_short = int(any(re.search(p, " ".join(urls).lower()) for p in SHORT_URL_PATTERNS))
    many_excl = int((texto + asunto).count("!") >= 3)
    money = int(bool(re.search(r"[€$]|precio|transferencia|paga|pago|pago inmediato|oferta", low)))
    letters = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", sub)
    caps_ratio = (sum(1 for c in sub if c.isupper()) / len(letters)) if letters else 0
    caps_excess = int(caps_ratio > 0.6 and len(sub) >= 6)
    long_subject = int(len(sub) > 60)
    from_email = _normalize_email(remitente)
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
        "telefono_o_whatsapp": has_phone,
        "terminos_crypto": has_crypto,
    }