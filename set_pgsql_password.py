import keyring
from getpass import getpass

print('Username:', end=' ')
user_name = input()
password = getpass()
keyring.set_password('market_db', user_name, password)
