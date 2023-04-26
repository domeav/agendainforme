from werkzeug.security import generate_password_hash

DB_FILE = "agenda.db"

# Importing archives is much longer
IMPORT_ARCHIVES = False

# login/mdp pour accéder à l'admin de l'Agenda Informe d'origine
IMPORT_USERNAME = 'original_username'
IMPORT_PASSWD = 'original_passwd'


USERS = {
    'new_username': generate_password_hash('new_password')
}

# generate a secret with "python -c 'import secrets; print(secrets.token_hex())'"
SECRET_KEY = 'some secret'
