# LAB 18 – FireStorm

**Cours : Sécurité des applications mobiles**

---

## Objectif

L'application Android cible contient une méthode interne qui construit un mot de passe Firebase à partir de ressources statiques et d'une librairie native. Cette méthode n'est jamais invoquée lors du fonctionnement normal de l'application. L'objectif du lab est de forcer son exécution à l'aide de Frida, de récupérer le mot de passe généré, puis de s'authentifier sur Firebase pour extraire le flag stocké dans la base de données.

---

## Environnement utilisé

| Composant         | Détail                              |
|-------------------|-------------------------------------|
| Émulateur Android | Android x86 via AVD (ADB)          |
| Outil d'analyse   | Jadx-GUI                            |
| Outil de hooking  | Frida (frida-tools)                 |
| Langage script    | JavaScript (Frida), Python 3        |
| Bibliothèque      | pyrebase4                           |
| Cible Firebase    | firestorm-9d3db (Realtime Database) |

---

## Arborescence du projet

```
LAB18-FireStorm/
├── README.md
├── apk/
│   └── FireStorm.apk
├── captures/
│   ├── 01_adb_devices.png
│   ├── 02_app_installed.png
│   ├── 03_frida_ps.png
│   ├── 04_jadx_open_apk.png
│   ├── 05_jadx_package_mainactivity.png
│   ├── 06_jadx_mainactivity_oncreate.png
│   ├── 07_jadx_password_method.png
│   ├── 08_jadx_native_function.png
│   ├── 9_jadx_loadlibrary.png
│   ├── 10_strings_firebase.png
│   ├── 11_frida_password_output.png
│   ├── 12_install_pyrebase.png
│   ├── 13_python_get_flag.png
│   ├── 14_flag_result.png
│   └── 15_jadx_manifest.png
└── scripts/
    ├── frida_firestorm.js   # Script Frida pour forcer l'appel de Password()
    └── get_flag.py          # Script Python d'authentification et récupération du flag
```

---

## Architecture du lab

```
┌──────────────────────────────────────────────────────────┐
│                     Émulateur Android                    │
│                                                          │
│  ┌─────────────────────────┐    ┌──────────────────────┐ │
│  │   Application FireStorm │    │    Frida Server      │ │
│  │  com.pwnsec.firestorm   │◄───│  (frida-server-arm)  │ │
│  │                         │    └──────────────────────┘ │
│  │  MainActivity           │                             │
│  │   └─ Password()  ◄──────┼──── Hook Frida             │
│  │       └─ libfirestorm.so│                             │
│  └─────────────────────────┘                             │
└───────────────────────────┬──────────────────────────────┘
                            │ Mot de passe récupéré
                            ▼
              ┌─────────────────────────┐
              │   Script Python         │
              │   (pyrebase4)           │
              │   auth.sign_in(...)     │
              └────────────┬────────────┘
                           │ Authentification réussie
                           ▼
              ┌─────────────────────────┐
              │   Firebase Realtime DB  │
              │   → Lecture du flag     │
              └─────────────────────────┘
```

---

## Étape 1 : Préparation et installation de l'application

L'émulateur Android est démarré et accessible via ADB. On vérifie qu'il est bien reconnu, puis on installe l'APK FireStorm.

```bash
adb devices
adb install FireStorm.apk
```

<p align="center">
  <img src="captures/01_adb_devices.png" width="700">
</p>

<p align="center">
  <img src="captures/02_app_installed.png" width="700">
</p>

---

## Étape 2 : Vérification de Frida

Avant de procéder au hooking, on s'assure que le serveur Frida est bien actif sur l'émulateur et que l'application cible est visible dans la liste des processus.

```bash
frida-ps -U
```

<p align="center">
  <img src="captures/03_frida_ps.png" width="700">
</p>

L'application `com.pwnsec.firestorm` apparaît bien dans la liste, ce qui confirme que Frida peut interagir avec elle.

---

## Étape 3 : Analyse statique avec Jadx

L'APK est ouvert dans Jadx-GUI pour une analyse statique du code décompilé.

<p align="center">
  <img src="captures/04_jadx_open_apk.png" width="700">
</p>

### 3.1 Identification du package et de la classe principale

Le package principal est `com.pwnsec.firestorm` et la classe d'entrée est `MainActivity`.

<p align="center">
  <img src="captures/05_jadx_package_mainactivity.png" width="700">
</p>

### 3.2 Analyse de onCreate()

L'examen de `onCreate()` confirme que la méthode `Password()` n'y est jamais appelée — elle est totalement absente du flux d'exécution normal.

<p align="center">
  <img src="captures/06_jadx_mainactivity_oncreate.png" width="700">
</p>

### 3.3 Méthode Password()

La méthode `Password()` construit le mot de passe Firebase en concaténant plusieurs chaînes issues de `strings.xml` avec une valeur produite par une fonction native.

<p align="center">
  <img src="captures/07_jadx_password_method.png" width="700">
</p>

### 3.4 Fonction native generateRandomString()

La partie dynamique du mot de passe est générée par `generateRandomString()`, une fonction déclarée native et implémentée dans la librairie partagée `libfirestorm.so`.

<p align="center">
  <img src="captures/08_jadx_native_function.png" width="700">
</p>

### 3.5 Chargement de la librairie native

Le chargement de `libfirestorm.so` s'effectue via `System.loadLibrary("firestorm")` à l'initialisation de l'activité.

<p align="center">
  <img src="captures/9_jadx_loadlibrary.png" width="700">
</p>

### 3.6 Configuration Firebase dans strings.xml

Le fichier `strings.xml` contient l'ensemble des paramètres Firebase nécessaires : clé API, email du compte, URL de la base de données.

<p align="center">
  <img src="captures/10_strings_firebase.png" width="700">
</p>

### 3.7 AndroidManifest.xml

<p align="center">
  <img src="captures/15_jadx_manifest.png" width="700">
</p>

---

## Étape 4 : Développement du script Frida

Le script Frida cible directement la méthode `Password()` en parcourant les instances actives de `MainActivity` en mémoire. Un délai de 3 secondes est introduit pour garantir que la librairie native est bien chargée avant l'appel.

**frida_firestorm.js**

```javascript
Java.perform(function() {

    function getPassword() {
        console.log("[*] Début de la recherche d'instances de MainActivity...");

        Java.choose('com.pwnsec.firestorm.MainActivity', {

            onMatch: function(instance) {
                console.log("[+] MainActivity instance trouvée : " + instance);

                try {
                    var pass = instance.Password();
                    console.log("[+] Mot de passe Firebase généré : " + pass);
                } catch (e) {
                    console.log("[-] Erreur lors de l'appel de Password() : " + e);
                }
            },

            onComplete: function() {
                console.log("[*] Recherche des instances terminée.");
            }
        });
    }

    console.log("[*] Script chargé. Attente de 3 secondes avant exécution...");
    setTimeout(getPassword, 3000);
});
```

Points clés du script :

- `Java.perform()` initialise le contexte Java de Frida.
- `Java.choose()` parcourt le tas de la JVM pour trouver toutes les instances vivantes de `MainActivity`, sans avoir besoin d'une référence directe.
- `instance.Password()` invoque la méthode directement sur l'objet trouvé, ce qui déclenche également l'appel à la fonction native.
- Le `setTimeout` évite une exécution prématurée avant que `libfirestorm.so` soit initialisée.

---

## Étape 5 : Exécution du script Frida et récupération du mot de passe

Le script est injecté dans l'application en cours d'exécution avec la commande suivante :

```bash
frida -U -f com.pwnsec.firestorm -l frida_firestorm.js --no-pause
```

<p align="center">
  <img src="captures/11_frida_password_output.png" width="700">
</p>

Le mot de passe Firebase est affiché dans la console Frida sous la forme `[+] Mot de passe Firebase généré : ********`. Ce mot de passe est dynamique — il change à chaque lancement en raison de la composante native aléatoire.

---

## Étape 6 : Authentification Firebase avec Python

### 6.1 Installation de pyrebase4

Un environnement virtuel Python est créé et la bibliothèque `pyrebase4` y est installée pour interagir avec Firebase.

<p align="center">
  <img src="captures/12_install_pyrebase.png" width="700">
</p>

### 6.2 Script get_flag.py

Le script s'authentifie sur Firebase avec l'email extrait de `strings.xml` et le mot de passe obtenu via Frida, puis interroge la Realtime Database.

**get_flag.py**

```python
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
password = "MOT_DE_PASSE_OBTENU_VIA_FRIDA"

user = auth.sign_in_with_email_and_password(email, password)
print("Connexion reussie. Token obtenu.")

db = firebase.database()
flag_data = db.get(user['idToken'])
print("FLAG recupere :")
print(flag_data.val())
```

<p align="center">
  <img src="captures/13_python_get_flag.png" width="700">
</p>

Exécution :

```bash
python get_flag.py
```

---

## Étape 7 : Récupération du flag

L'authentification est validée par Firebase, le token d'accès est obtenu, et la base de données retourne le flag.

<p align="center">
  <img src="captures/14_flag_result.png" width="700">
</p>

---

## Résultat final

```
PWNSEC{C0ngr4ts_Th4t_w45_4N_345y_P4$$w0rd_t0_G3t!!!0R!5_!t???}
```

---

## Conclusion

Ce lab illustre une vulnérabilité classique dans les applications Android : la présence de logique sensible dans le code client, même si celle-ci n'est jamais exposée à l'utilisateur. Le fait qu'une méthode ne soit pas appelée dans le flux normal ne la rend pas inaccessible — un attaquant disposant de Frida peut toujours la déclencher en ciblant directement ses instances en mémoire.

Les points à retenir :

- Les informations de configuration (clés API, emails, URLs Firebase) ne doivent jamais être stockées en clair dans les ressources d'une application.
- Une méthode non appelée dans l'interface ne constitue pas une protection : elle reste instrumentable via des outils de hooking.
- Les fonctions natives dans `libfirestorm.so` ne suffisent pas à dissuader une analyse dynamique si la couche Java qui les orchestre reste exposée.
- L'accès à une base de données Realtime Firebase doit être conditionné à des règles de sécurité strictes côté serveur, indépendamment de la robustesse du mot de passe côté client.
