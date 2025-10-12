from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from conexion import obtener_conexion
import json
# from sistema_experto.filtro import analizar_correo
from sistema_experto import analizar_correo
import json

app = Flask(__name__)

app.secret_key = 'tu_clave_secreta_muy_dificil' 

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('bandeja'))
    return redirect(url_for('login'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'] # Se guarda la contraseña en texto plano
        
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                # Comprobar si el email ya existe
                cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash("El correo electrónico ya está registrado.", "error")
                    return redirect(url_for('registro'))
                
                # Insertar nuevo usuario con la contraseña sin encriptar
                cursor.execute("INSERT INTO usuarios (email, password) VALUES (%s, %s)", (email, password))
            conexion.commit()
            flash("¡Registro exitoso! Por favor, inicia sesión.", "success")
            return redirect(url_for('login'))
        finally:
            conexion.close()
            
    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
                usuario = cursor.fetchone()
                
                if usuario and password == usuario['password']:
                    session['user_id'] = usuario['id']
                    session['email'] = usuario['email']
                    return redirect(url_for('bandeja'))
                else:
                    flash("Correo o contraseña incorrectos.", "error")
                    return redirect(url_for('login'))
        finally:
            conexion.close()
            
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('email', None)
    flash("Has cerrado sesión.", "success")
    return redirect(url_for('login'))

# --- Rutas de la Aplicación ---

@app.route('/bandeja')
def bandeja():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Consulta para correos NORMALES recibidos (es_spam = 0)
            sql_normal = """
                SELECT c.id, c.asunto, c.fecha_envio, u.email AS remitente_email
                FROM correos c JOIN usuarios u ON c.remitente_id = u.id
                WHERE c.destinatario_id = %s AND c.es_spam = 0
                ORDER BY c.fecha_envio DESC
            """
            cursor.execute(sql_normal, (user_id,))
            correos_normales = cursor.fetchall()

            # Consulta para correos SPAM recibidos (es_spam = 1)
            sql_spam = """
                SELECT c.id, c.asunto, c.fecha_envio, u.email AS remitente_email
                FROM correos c JOIN usuarios u ON c.remitente_id = u.id
                WHERE c.destinatario_id = %s AND c.es_spam = 1
                ORDER BY c.fecha_envio DESC
            """
            cursor.execute(sql_spam, (user_id,))
            correos_spam = cursor.fetchall()

            # --- NUEVA CONSULTA PARA CORREOS ENVIADOS ---
            sql_enviados = """
                SELECT c.id, c.asunto, c.fecha_envio, u.email AS destinatario_email
                FROM correos c JOIN usuarios u ON c.destinatario_id = u.id
                WHERE c.remitente_id = %s
                ORDER BY c.fecha_envio DESC
            """
            cursor.execute(sql_enviados, (user_id,))
            correos_enviados = cursor.fetchall()

    finally:
        conexion.close()

    # Añadimos la nueva lista al render_template
    return render_template('bandeja.html', 
                           correos_normales=correos_normales, 
                           correos_spam=correos_spam,
                           correos_enviados=correos_enviados)


@app.route('/redactar', methods=['GET', 'POST'])
def redactar():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        destinatario_email = request.form['destinatario']
        asunto = request.form['asunto']
        cuerpo = request.form['cuerpo']
        remitente_id = session['user_id']
        remitente_email = session['email']

        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT id FROM usuarios WHERE email = %s", (destinatario_email,))
                destinatario = cursor.fetchone()

                if not destinatario:
                    flash("El correo del destinatario no existe.", "error")
                    return redirect(url_for('redactar'))

                destinatario_id = destinatario['id']
                
                # 1. Llamar al sistema experto
                resultado_analisis = analizar_correo(asunto, cuerpo, remitente_email)
                
                # 2. Extraer todos los resultados del análisis
                es_spam = resultado_analisis['es_spam']
                prob_spam = resultado_analisis['probabilidad_spam'] # <-- DATO NUEVO
                explicacion_reporte = resultado_analisis['reporte']
                explicacion_json_str = json.dumps(explicacion_reporte)

                # 3. Guardar el correo CON LA PROBABILIDAD
                sql = """
                    INSERT INTO correos 
                    (remitente_id, destinatario_id, asunto, cuerpo, es_spam, explicacion_json, probabilidad_spam) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (remitente_id, destinatario_id, asunto, cuerpo, es_spam, explicacion_json_str, prob_spam))
            
            conexion.commit()
            flash("Correo enviado y analizado exitosamente.", "success")
            return redirect(url_for('bandeja'))
        finally:
            conexion.close()

    return render_template('redactar.html')


@app.route('/correo/<int:correo_id>')
def ver_correo(correo_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Consulta que trae toda la info del correo
            sql = """
                SELECT c.*, u_remitente.email AS remitente_email, u_destinatario.email AS destinatario_email
                FROM correos c
                JOIN usuarios u_remitente ON c.remitente_id = u_remitente.id
                JOIN usuarios u_destinatario ON c.destinatario_id = u_destinatario.id
                WHERE c.id = %s AND (c.destinatario_id = %s OR c.remitente_id = %s)
            """
            cursor.execute(sql, (correo_id, user_id, user_id))
            correo = cursor.fetchone()

            if not correo:
                flash("Correo no encontrado o no tienes permiso para verlo.", "error")
                return redirect(url_for('bandeja'))
            
            # Cargamos el reporte JSON para pasarlo a la plantilla
            reporte = json.loads(correo['explicacion_json']) if correo['explicacion_json'] else None

    finally:
        conexion.close()

    return render_template('correo.html', correo=correo, reporte=reporte)

@app.route('/explicacion/<int:correo_id>')
def explicacion(correo_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Buscamos el correo y nos aseguramos de que le pertenezca al usuario en sesión
            sql = "SELECT explicacion_json, asunto FROM correos WHERE id = %s AND destinatario_id = %s"
            cursor.execute(sql, (correo_id, session['user_id']))
            correo = cursor.fetchone()

            if not correo or not correo['explicacion_json']:
                flash("Reporte no encontrado o el correo no es spam.", "error")
                return redirect(url_for('bandeja'))
            
            # El JSON se guarda como string, lo convertimos de nuevo a un objeto de Python
            reporte = json.loads(correo['explicacion_json'])
            asunto = correo['asunto']

    finally:
        conexion.close()
    
    return render_template('explicacion.html', reporte=reporte, asunto=asunto)





# =====================================================================
# API PARA PRUEBAS RÁPIDAS
# =====================================================================

@app.route('/api/analizar', methods=['POST'])
def api_analizar_correos():
    """
    Endpoint para analizar una lista de correos en batch.
    Espera un JSON con la clave "correos", que es una lista de objetos.
    Cada objeto debe tener: "asunto", "cuerpo", "remitente".
    """
    datos = request.get_json()
    if not datos or 'correos' not in datos:
        return jsonify({"error": "Formato de JSON inválido. Se esperaba una clave 'correos'."}), 400

    resultados = []
    for correo in datos['correos']:
        asunto = correo.get('asunto', '')
        cuerpo = correo.get('cuerpo', '')
        remitente = correo.get('remitente', 'desconocido@test.com')
        
        # Llama a nuestro sistema experto
        analisis = analizar_correo(asunto, cuerpo, remitente)
        resultados.append(analisis)
        
    return jsonify(resultados)


@app.route('/api/registrar', methods=['POST'])
def api_registrar_y_analizar_correos():
    """
    Endpoint que analiza una lista de correos Y LOS GUARDA en la base de datos.
    Espera un JSON con "correos". Cada correo debe tener:
    "asunto", "cuerpo", "remitente_email", "destinatario_email".
    """
    datos = request.get_json()
    if not datos or 'correos' not in datos:
        return jsonify({"error": "Formato de JSON inválido."}), 400

    correos_a_procesar = datos['correos']
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            for correo in correos_a_procesar:
                remitente_email = correo.get('remitente_email')
                destinatario_email = correo.get('destinatario_email')
                asunto = correo.get('asunto', '')
                cuerpo = correo.get('cuerpo', '')

                # --- 1. Validar que los usuarios existan y obtener sus IDs ---
                cursor.execute("SELECT id FROM usuarios WHERE email = %s", (remitente_email,))
                remitente_user = cursor.fetchone()
                cursor.execute("SELECT id FROM usuarios WHERE email = %s", (destinatario_email,))
                destinatario_user = cursor.fetchone()

                if not remitente_user or not destinatario_user:
                    # Si un usuario no existe, saltamos este correo y continuamos con el siguiente
                    print(f"ADVERTENCIA: No se pudo registrar el correo de {remitente_email} a {destinatario_email} porque uno de los usuarios no existe.")
                    continue
                
                remitente_id = remitente_user['id']
                destinatario_id = destinatario_user['id']
                
                # --- 2. Llamar al sistema experto para el análisis ---
                analisis = analizar_correo(asunto, cuerpo, remitente_email)
                
                # --- 3. Guardar el correo en la BD con los resultados ---
                sql = """
                    INSERT INTO correos 
                    (remitente_id, destinatario_id, asunto, cuerpo, es_spam, explicacion_json, probabilidad_spam) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    remitente_id,
                    destinatario_id,
                    asunto,
                    cuerpo,
                    analisis['es_spam'],
                    json.dumps(analisis['reporte']),
                    analisis['probabilidad_spam']
                ))

        conexion.commit()
        return jsonify({"mensaje": f"{len(correos_a_procesar)} correos procesados y registrados exitosamente."}), 201
    
    except Exception as e:
        conexion.rollback()
        return jsonify({"error": f"Ocurrió un error en la base de datos: {str(e)}"}), 500
    finally:
        conexion.close()


@app.route('/api/correos', methods=['GET'])
def api_obtener_correos():
    """
    Endpoint para obtener los correos ya guardados en la base de datos.
    Acepta un parámetro de consulta `filtro`.
    Valores posibles para ?filtro= : 'spam', 'nospam', 'todos' (defecto)
    """
    filtro = request.args.get('filtro', 'todos').lower()
    
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Construimos la consulta base
            sql = "SELECT id, asunto, cuerpo, es_spam, probabilidad_spam, fecha_envio FROM correos"
            
            # Añadimos el filtro si es necesario
            if filtro == 'spam':
                sql += " WHERE es_spam = 1"
            elif filtro == 'nospam':
                sql += " WHERE es_spam = 0"
            
            sql += " ORDER BY fecha_envio DESC"
            
            cursor.execute(sql)
            correos_db = cursor.fetchall()
            
            # Convertimos los resultados a un formato compatible con JSON
            # (las fechas deben ser convertidas a string)
            correos_json = []
            for correo in correos_db:
                correo['fecha_envio'] = correo['fecha_envio'].isoformat()
                correos_json.append(correo)
                
            return jsonify(correos_json)
    finally:
        conexion.close()



if __name__ == '__main__':
    app.run(debug=True)