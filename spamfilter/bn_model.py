from pgmpy.models import NaiveBayes
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination
from flask import current_app as app

# Variables binarias: 0/1
model = NaiveBayes()
model.add_nodes_from(["Spam","SenderKnown","Keywords","Links","LengthShort"])
model.add_edges_from([("Spam","SenderKnown"),("Spam","Keywords"),("Spam","Links"),("Spam","LengthShort")])

# Priori de Spam
cpd_spam = TabularCPD("Spam", 2, [[0.6],[0.4]])  # P(Spam=0)=0.6, P(Spam=1)=0.4 (ajustable)

# CPDs condicionales de features dado Spam
cpd_sender = TabularCPD("SenderKnown", 2, [[0.2, 0.8], [0.8, 0.2]], evidence=["Spam"], evidence_card=[2])
# Interpretación (columnas Spam=0, Spam=1):
# P(SenderKnown=0|Spam=0)=0.2, P(SenderKnown=0|Spam=1)=0.8  (spam suele NO ser conocido)
# P(SenderKnown=1|Spam=0)=0.8, P(SenderKnown=1|Spam=1)=0.2

cpd_keywords = TabularCPD("Keywords", 2, [[0.4, 0.1], [0.6, 0.9]], evidence=["Spam"], evidence_card=[2])
cpd_links    = TabularCPD("Links",    2, [[0.5, 0.2], [0.5, 0.8]], evidence=["Spam"], evidence_card=[2])
cpd_length   = TabularCPD("LengthShort", 2, [[0.6, 0.4], [0.4, 0.6]], evidence=["Spam"], evidence_card=[2])

model.add_cpds(cpd_spam, cpd_sender, cpd_keywords, cpd_links, cpd_length)
model.check_model()
infer = VariableElimination(model)

def infer_bn(features: dict):
    ev = {k: int(v) for k, v in features.items() if k in {"SenderKnown","Keywords","Links","LengthShort"}}
    q = infer.query(variables=["Spam"], evidence=ev, show_progress=False)
    p_spam = float(q.values[1])  # index 1 == Spam=1
    label = "spam" if p_spam >= float(app.config.get("SPAM_THRESHOLD", 0.5)) else "no_spam"

    # Explicación heurística (pro/contra)
    pro = []
    contra = []
    if ev.get("Keywords")==1: pro.append(f"Palabras sospechosas: {', '.join(features['_meta']['hit_words']) or 'sí'}")
    else: contra.append("Sin palabras típicas de spam")
    if ev.get("Links")==1: pro.append(f"Contiene enlaces ({features['_meta']['links_count']})")
    else: contra.append("Sin enlaces")
    if ev.get("SenderKnown")==1: contra.append("Remitente en lista de confianza")
    else: pro.append("Remitente no reconocido")
    if ev.get("LengthShort")==1: pro.append("Mensaje muy corto (parecido a spam)")
    else: contra.append("Longitud normal")

    rationale = {"pros": pro, "cons": contra, "threshold": float(app.config["SPAM_THRESHOLD"])}
    return {"label": label, "score": p_spam, "rationale": rationale}
