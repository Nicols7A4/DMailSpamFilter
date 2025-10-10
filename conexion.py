# conexion.py
import pymysql
import pymysql.cursors
import certifi

# DB_HOST = "127.0.0.1"
# DB_PORT = 3306
# DB_USER = "root"
# DB_PASS = ""
# DB_NAME = "ia_t2_filtrospam"

DB_HOST = "gateway01.us-east-1.prod.aws.tidbcloud.com"
DB_PORT = 4000
DB_USER = "44vvNTE7qqnuCZE.root"
DB_PASS = "h3SDTjU93Y31X4oj"
DB_NAME = "ia_t2_filtrospam"

def obtener_conexion():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
        port=int(DB_PORT),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        # --- 2. AÑADE ESTA LÍNEA PARA HABILITAR SSL ---
        ssl={'ca': certifi.where()}
    )
    # return pymysql.connect(
    #     host=DB_HOST,
    #     port=DB_PORT,
    #     user=DB_USER,
    #     password=DB_PASS,
    #     db=DB_NAME,
    #     charset="utf8mb4",
    #     cursorclass=pymysql.cursors.DictCursor,
    #     autocommit=True
    # )