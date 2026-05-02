import pyrebase

config = {
    "apiKey": "AIzaSyAXsK0qsx4RuLSA9C8IPSWd0eQ67HVHuJY",
    "authDomain": "firestorm-9d3db.firebaseapp.com",
    "databaseURL": "https://firestorm-9d3db-default-rtdb.firebaseio.com",
    "storageBucket": "firestorm-9d3db.appspot.com",
    "projectId": "firestorm-9d3db"
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()

email = "TK757567@pwnsec.xyz"

# Remplace cette valeur par le mot de passe obtenu avec Frida
password = "C7_dotpsC7t7f_._In_i.IdttpaofoaIIdIdnndIfC"

try:
    user = auth.sign_in_with_email_and_password(email, password)
    print("[+] Connexion réussie. Token obtenu.")

    db = firebase.database()

    flag_data = db.get(user['idToken'])

    print("[+] FLAG récupéré :")
    print(flag_data.val())

except Exception as e:
    print("[-] Erreur pendant l'authentification ou la récupération du flag :")
    print(e)