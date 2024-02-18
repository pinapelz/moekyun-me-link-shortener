from flask import Flask, render_template, request, abort, jsonify, redirect
from flask_cors import CORS
import configparser
import string
import random
import secrets
import psycopg2
import redis
import os

app = Flask(__name__)
CORS(app)

# Corner Graphics
corner_graphics = [
    "https://files.catbox.moe/zciyt2.png",
    "https://files.catbox.moe/zawgke.webp",
    "https://files.catbox.moe/2aioik.webp"
]

# Site Configurations
SITE_URL = "https://moekyun.me"
MOE_IMAGE = "https://files.catbox.moe/bqtys4.webp"
MOE_QUOTE = "Have a moe day today!"
CUSTOM_URL_REQUIRE_AUTH = True


#######################################
#          POSTGRES HANDLER           #
#######################################

class PostgresHandler:
    def __init__(self,
                 username: str,
                 password: str,
                 host_name: str,
                 port: int,
                 database: str):
        db_params = {
            "dbname": database,
            "user": username,
            "password": password,
            "host": host_name,
            "port": port
        }
        self._connection = psycopg2.connect(**db_params)
        print("Handler Success")

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


#######################################
#          REDIS HANDLER           #
#######################################

class RedisHandler:
    def __init_


def create_database_connection():
    if os.environ.get("POSTGRES_USER") is not None:
        hostname = os.environ.get("POSTGRES_HOST")
        user = os.environ.get("POSTGRES_USER")
        password = os.environ.get("POSTGRES_PASSWORD")
        port = int(os.environ.get("POSTGRES_PORT"))
        database = os.environ.get("POSTGRES_DATABASE")
        SITE_URL = os.environ.get("SITE_URL")
        MOE_IMAGE = os.environ.get("MOE_IMAGE")
        MOE_QUOTE = os.environ.get("MOE_QUOTE")

    else:
        parser = configparser.ConfigParser()
        parser.read("config.ini")
        CONFIG = parser
        hostname = CONFIG.get("database", "host")
        user = CONFIG.get("database", "user")
        password = CONFIG.get("database", "password")
        database = CONFIG.get("database", "database")
        port = CONFIG.get("database", "port")
    return PostgresHandler(host_name=hostname,
                           username=user,
                           password=password,
                           database=database,
                           port=5432)


def initialize_database():
    sql_handler = create_database_connection()
    sql_handler.create_table(
        "shortened_links",
        """
        id SERIAL PRIMARY KEY,
        link VARCHAR(255),
        shortened_link VARCHAR(255) UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        captcha VARCHAR(255)
        """
    )
    sql_handler.create_table(
        "authentication",
        """id SERIAL PRIMARY KEY,
        authkey VARCHAR(255) UNIQUE
        """"
    )
    sql_handler.close_connection()


def generate_random_hash(length=6):
    characters = string.ascii_letters + string.digits
    random_hash = ''.join(secrets.choice(characters) for _ in range(length))
    return random_hash


@app.route('/')
def main_page():
    bottom_graphic = random.choice(corner_graphics)
    if os.environ.get("CHECK_SETUP_EACH_VISIT") == "True":
        pass
        # initialize_database()
    return render_template('index.html',
                           moe_image_url=MOE_IMAGE,
                           moe_quote=MOE_QUOTE,
                           graphic=bottom_graphic)


@app.route('/api/add_shortened', methods=['POST'])
def new_link():
    server = create_database_connection()
    requested_link = request.form.get("url")
    captcha = request.form.get("captcha")
    if captcha is None or captcha not in ["VTuber", "None"]:
        captcha = "None"
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
    server.insert_row("shortened_links", "link, shortened_link, captcha",
                      (requested_link, hash_value, captcha))
    server.close_connection()
    return jsonify(SITE_URL+"/"+hash_value)


@app.route("/api/add_custom", methods=['POST'])
def add_custom():
    server = create_database_connection()
    requested_link = request.form.get("url")
    captcha = request.form.get("captcha")
    custom_link = request.form.get("custom")
    password = request.headers.get('X-AUTHENTICATION')
    if password is None and CUSTOM_URL_REQUIRE_AUTH:
        return abort(401, "Invalid Authentication")
    if not server.check_row_exists("authentication", "authkey", password) \
            and CUSTOM_URL_REQUIRE_AUTH:
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
    if server.check_row_exists("shortened_links", "shortened_link", custom_link):
        server.close_connection()
        return abort(400, "Custom link already exists")
    if captcha is None or captcha not in ["VTuber", "None"]:
        captcha = "None"
    server.insert_row("shortened_links", "link, shortened_link, captcha", (requested_link, custom_link, captcha))
    server.close_connection()
    return jsonify(SITE_URL+"/"+custom_link)


@app.route('/<path>')
def expand_url(path):
    server = create_database_connection()
    if server.check_row_exists("shortened_links", "shortened_link", path):
        link = server.get_rows("shortened_links", "shortened_link", path)[0][1]
        captcha = server.get_rows("shortened_links",
                                  "shortened_link", path)[0][4]
        server.close_connection()
        if captcha == "VTuber":
            return render_template("auth.html", redirect_url=link)
        else:
            return redirect(link)
    server.close_connection()
    return abort(404, "Link not found")


@app.route("/create/new_auth")
def new_auth():
    return render_template("auth.html")


if __name__ == '__main__':
    app.run(debug=True)
