# sistema_experto/modulo_explicacion.py
import numpy as np

def generar_explicacion(modelo, evidencias_observadas):
    """
    Calcula el Likelihood Ratio (LR) para cada evidencia observada
    y lo devuelve como un reporte ordenado para explicar la decisión.
    """
    lr_list = []
    for var, val in evidencias_observadas.items():
        if var == "correo_es_spam": continue
        
        cpd = modelo.get_cpds(var)
        if cpd is None or cpd.get_evidence() != ['correo_es_spam']: continue
        
        state = int(val)
        p_ham  = max(float(cpd.values[state, 0]), 1e-9)
        p_spam = max(float(cpd.values[state, 1]), 1e-9)
        lr = p_spam / p_ham
        lr_list.append({"variable": var, "valor": val, "lr": lr, "log_lr": np.log10(lr)})
        
    lr_list.sort(key=lambda x: abs(x["log_lr"]), reverse=True)
    return lr_list