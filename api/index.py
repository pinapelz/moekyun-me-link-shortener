from flask import Flask, render_template, request, abort, jsonify, redirect
from flask_cors import CORS
import configparser
import string
import random
import secrets
import psycopg2
import redis
import os
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)
CORS(app)


# Site Configurations
SITE_URL = "http://127.0.0.1:5000"
MOE_IMAGE = "https://files.catbox.moe/bqtys4.webp"
MOE_QUOTE = "Have a moe day today!"
CUSTOM_URL_REQUIRE_AUTH = False



parser = configparser.ConfigParser()
parser.read("config.ini")
STORAGE_MODE = "postgres"
CUSTOM_URL_REQUIRE_AUTH = True if os.environ.get("CUSTOM_URL_REQUIRE_AUTH") == "True" else False
MOE_IMAGE = os.environ.get("MOE_IMAGE")
MOE_QUOTE = os.environ.get("MOE_QUOTE")
SITE_URL = os.environ.get("SITE_URL")

corner_graphics = os.environ.get("CORNER_GRAPHICS")
try:
    corner_graphics = corner_graphics.split(",")
except:
    corner_graphics = [
        "https://files.catbox.moe/zciyt2.png",
        "https://files.catbox.moe/zawgke.webp",
        "https://files.catbox.moe/2aioik.webp"
    ]

#######################################
#          POSTGRES HANDLER           #
#######################################

class PostgresHandler:
    def __init__(self,
                 username: str,
                 password: str,
                 host_name: str,
                 port: int,
                 database: str
                 ):
        db_params = {
            "dbname": database,
            "user": username,
            "password": password,
            "host": host_name,
            "port": port
        }
        self._connection = psycopg2.connect(**db_params)
        print("[PGHandler] Handler Initialized")

    def create_table(self, name: str, column: str):
        cursor = self._connection.cursor()
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {name} ({column})")
        self._connection.commit()
        cursor.close()

    def check_row_exists(self, table_name: str, column_name: str, value: str):
        cursor = self._connection.cursor()
        query = f"SELECT 1 FROM {table_name} WHERE {column_name} = %s"
        cursor.execute(query, (value,))
        result = cursor.fetchone()
        cursor.close()

        if result is not None:
            return True
        else:
            return False

    def insert_row(self, table_name, column, data):
        try:
            cursor = self._connection.cursor()
            placeholders = ', '.join(['%s'] * len(data))
            query = f"""INSERT INTO {table_name}({column})
                            VALUES ({placeholders})"""
            cursor.execute(query, data)
            self._connection.commit()
            print("Data Inserted:", data)
        except psycopg2.Error as err:
            self._connection.rollback()
            print("Error inserting data")
            print(err)
            if "duplicate key" not in str(err).lower():
                return False
        return True

    def get_rows(self, table_name: str, column: str, value: str):
        try:
            cursor = self._connection.cursor()
            query = f"SELECT * FROM {table_name} WHERE {column} = %s"
            cursor.execute(query, (value,))
            result = cursor.fetchall()
            return result
        except psycopg2.Error as e:
            self._connection.rollback()
            print(f"Failed to fetch row from {table_name} WHERE {column} is {value}")
            print(e)
            return False

    def close_connection(self):
        self._connection.close()



def create_postgres_connection():
    if os.environ.get("POSTGRES_USER") is not None:
        hostname = os.environ.get("POSTGRES_HOST")
        user = os.environ.get("POSTGRES_USER")
        password = os.environ.get("POSTGRES_PASSWORD")
        port = int(os.environ.get("POSTGRES_PORT"))
        database = os.environ.get("POSTGRES_DATABASE")
    else:
        parser = configparser.ConfigParser()
        parser.read("config.ini")
        CONFIG = parser
        hostname = CONFIG.get("postgres", "pg_host")
        user = CONFIG.get("postgres", "pg_user")
        password = CONFIG.get("postgres", "pg_password")
        database = CONFIG.get("postgres", "pg_database")
        port = CONFIG.get("postgres", "pg_port")
    return PostgresHandler(host_name=hostname,
                           username=user,
                           password=password,
                           database=database,
                           port=port)



def initialize_database():
    sql_handler = create_postgres_connection()
    sql_handler.create_table(
        "shortened_links",
        """
        id SERIAL PRIMARY KEY,
        link VARCHAR(255),
        shortened_link VARCHAR(255) UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        special VARCHAR(255)
        """
    )
    sql_handler.create_table(
        "authentication",
        """id SERIAL PRIMARY KEY,
        authkey VARCHAR(255) UNIQUE
        """
    )
    sql_handler.close_connection()

def generate_random_hash(length=6):
    characters = string.ascii_letters + string.digits
    random_hash = ''.join(secrets.choice(characters) for _ in range(length))
    return random_hash


@app.route('/')
def main_page():
    print(corner_graphics)
    bottom_graphic = random.choice(corner_graphics)
    if os.environ.get("CHECK_SETUP_EACH_VISIT") == "True":
        pass
        # initialize_database()
    return render_template('index.html',
                           moe_image_url=MOE_IMAGE,
                           moe_quote=MOE_QUOTE,
                           graphic=bottom_graphic)

def create_new_shortened_link(requested_link: str,  special: str):
    server = create_postgres_connection()
    if requested_link is None:
        return abort(400, "No link provided")
    if requested_link.strip() == "":
        return abort(400, "Cannot shorten empty link")
    if not requested_link.startswith("http://") \
            and not requested_link.startswith("https://"):
        requested_link = "https://" + requested_link
    hash_value = generate_random_hash()
    while True:
        if server.check_row_exists("shortened_links", "shortened_link",
                                    hash_value):
            hash_value = generate_random_hash()
        else:
            break
    server.insert_row("shortened_links", "link, shortened_link, special",
                        (requested_link, hash_value, special))
    server.close_connection()
    return jsonify(SITE_URL+"/"+hash_value)

@app.route('/api/add_shortened', methods=['POST'])
def new_link():
    requested_link = request.form.get("url")
    special = request.form.get("special")
    return create_new_shortened_link(requested_link, special)


def add_custom_url(requested_link: str,
                   special: str,
                   custom_link: str,
                   password: str):
    server = create_postgres_connection()
    if password is None and CUSTOM_URL_REQUIRE_AUTH:
        return abort(401, "Invalid Authentication")
    authentication_result = False

    if CUSTOM_URL_REQUIRE_AUTH and server.check_row_exists("authentication", "authkey", password):
            authentication_result = True

    if not authentication_result and CUSTOM_URL_REQUIRE_AUTH:
        server.close_connection()
        return abort(401, "Invalid Authentication")
    if requested_link is None:
        return abort(400, "No link provided")
    if requested_link.strip() == "":
        return abort(400, "Cannot shorten empty link")
    if not requested_link.startswith("http://") \
            and not requested_link.startswith("https://"):
        requested_link = "https://" + requested_link
    if custom_link is None:
        return abort(400, "No custom link provided")
    if custom_link.strip() == "":
        return abort(400, "Cannot shorten empty link")
    if server.check_row_exists("shortened_links", "shortened_link",
                                 custom_link):
          server.close_connection()
          return abort(400, "Custom link already exists")
    if special is None or special not in ["VTuber", "None"]:
        special = "None"
    server.insert_row("shortened_links", "link, shortened_link, special",
                        (requested_link, custom_link, special))
    server.close_connection()
    return jsonify(SITE_URL+"/"+custom_link)

@app.route("/api/add_custom", methods=['POST'])
def add_custom():
    requested_link = request.form.get("url")
    special = request.form.get("special")
    custom_link = request.form.get("custom")
    password = request.headers.get('X-AUTHENTICATION')
    return add_custom_url(requested_link, special, custom_link, password)


def fetch_url(path: str):
    server = create_postgres_connection()
    if server.check_row_exists("shortened_links", "shortened_link", path):
        link = server.get_rows("shortened_links", "shortened_link", path)[0][1]
        special = server.get_rows("shortened_links",
                                "shortened_link", path)[0][4]
        server.close_connection()
        return link, special
    server.close_connection()
    return 404, "Not Found"

@app.route('/<path>')
def expand_url(path):
    link, special = fetch_url(path)
    if link == 404:
        return abort(404, "Not Found")
    if special == "VTuber":
        return render_template("auth.html", redirect_url=link)
    else:
        return redirect(link)


if __name__ == '__main__':
    app.run(debug=True)
