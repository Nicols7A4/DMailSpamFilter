from flask import Flask, render_template, request, redirect, url_for, flash, session
from conexion import obtener_conexion
import json
from sistema_experto.filtro import analizar_correo

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
        remitente_email = session['email'] # Necesitamos el email del remitente para el análisis

        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                # 1. Buscar el ID del destinatario
                cursor.execute("SELECT id FROM usuarios WHERE email = %s", (destinatario_email,))
                destinatario = cursor.fetchone()

                if not destinatario:
                    flash("El correo del destinatario no existe.", "error")
                    return redirect(url_for('redactar'))

                destinatario_id = destinatario['id']
                
                # --- ¡AQUÍ OCURRE LA MAGIA! ---
                # 2. Llamar al sistema experto para analizar el correo ANTES de guardarlo
                resultado_analisis = analizar_correo(
                    asunto=asunto,
                    cuerpo=cuerpo,
                    remitente_email=remitente_email
                )
                
                # 3. Extraer los resultados del análisis
                es_spam = resultado_analisis['es_spam']
                explicacion_reporte = resultado_analisis['reporte']
                
                # Convertimos el reporte (lista de diccionarios) a un string JSON para guardarlo en la BD
                explicacion_json_str = json.dumps(explicacion_reporte)

                # 4. Insertar el correo en la base de datos CON LOS RESULTADOS DEL ANÁLISIS
                sql = "INSERT INTO correos (remitente_id, destinatario_id, asunto, cuerpo, es_spam, explicacion_json) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (remitente_id, destinatario_id, asunto, cuerpo, es_spam, explicacion_json_str))
            
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
            # --- LÓGICA MODIFICADA ---
            # Ahora permite ver el correo si el usuario es el remitente O el destinatario
            sql = """
                SELECT c.asunto, c.cuerpo, c.fecha_envio, u_remitente.email AS remitente_email, u_destinatario.email AS destinatario_email
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
    finally:
        conexion.close()

    # Pasamos el user_id a la plantilla para saber si somos el remitente
    return render_template('correo.html', correo=correo, current_user_id=user_id)


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

if __name__ == '__main__':
    app.run(debug=True)