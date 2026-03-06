# Déploiement sur PythonAnywhere — Abaye Elégance

## Étape 1 : Créer un compte PythonAnywhere

1. Aller sur https://www.pythonanywhere.com
2. Créer un compte (gratuit ou payant)
3. Retenir votre **username** (ex: `abayeelegance`)

---

## Étape 2 : Configurer la base de données MySQL

1. Aller dans l'onglet **Databases**
2. Créer une base de données MySQL :
   - Mot de passe MySQL : choisir un mot de passe fort
   - Cliquer sur **Create a MySQL database**
   - Nom de la base : `votre_username$abaye_elegance`
3. Noter les informations :
   - **Host** : `votre_username.mysql.pythonanywhere-services.com`
   - **User** : `votre_username`
   - **Database** : `votre_username$abaye_elegance`

---

## Étape 3 : Uploader le code

### Option A : Via Git (recommandé)
```bash
# Dans la console Bash de PythonAnywhere :
cd ~
git clone https://github.com/Faraleno2022/abayaelegancegn.git abaye_elegance
```

### Option B : Upload manuel
1. Aller dans l'onglet **Files**
2. Créer un dossier `abaye_elegance`
3. Uploader tous les fichiers du projet dans ce dossier

---

## Étape 4 : Créer un virtualenv

Dans la console **Bash** de PythonAnywhere :

```bash
mkvirtualenv --python=/usr/bin/python3.10 abaye_env
pip install -r ~/abaye_elegance/requirements.txt
```

---

## Étape 5 : Configurer les variables d'environnement

Ajouter dans le fichier `~/.bashrc` ou dans le fichier WSGI :

```bash
export PYTHONANYWHERE=1
export DB_NAME='votre_username$abaye_elegance'
export DB_USER='votre_username'
export DB_PASSWORD='votre_mot_de_passe_mysql'
export DB_HOST='votre_username.mysql.pythonanywhere-services.com'
```

---

## Étape 6 : Mettre à jour settings.py

Dans `abaye_elegance/settings.py`, remplacer les valeurs par défaut dans la section MySQL :

```python
'NAME': os.environ.get('DB_NAME', 'votre_username$abaye_elegance'),
'USER': os.environ.get('DB_USER', 'votre_username'),
'PASSWORD': os.environ.get('DB_PASSWORD', 'votre_mot_de_passe'),
'HOST': os.environ.get('DB_HOST', 'votre_username.mysql.pythonanywhere-services.com'),
```

Aussi, mettre à jour :
```python
DEBUG = False
# ALLOWED_HOSTS et CSRF_TRUSTED_ORIGINS sont déjà configurés pour abayaelegancegn.com
# Ajouter aussi le domaine PythonAnywhere si besoin :
ALLOWED_HOSTS = [
    'abayaelegancegn.com',
    'www.abayaelegancegn.com',
    'votre_username.pythonanywhere.com',
]
```

---

## Étape 7 : Migrations et données initiales

```bash
cd ~/abaye_elegance
python manage.py migrate
python manage.py seed_products
python manage.py createsuperuser
# Suivre les instructions pour créer l'admin
python manage.py collectstatic --noinput
```

---

## Étape 8 : Configurer l'application web

1. Aller dans l'onglet **Web**
2. Cliquer **Add a new web app**
3. Choisir **Manual configuration** → **Python 3.10**
4. Configurer :

### Virtualenv
```
/home/votre_username/.virtualenvs/abaye_env
```

### Source code
```
/home/votre_username/abaye_elegance
```

### Fichier WSGI
Cliquer sur le lien du fichier WSGI et remplacer tout le contenu par :

```python
import os
import sys

# Ajouter le projet au path
path = '/home/votre_username/abaye_elegance'
if path not in sys.path:
    sys.path.append(path)

# Variables d'environnement
os.environ['DJANGO_SETTINGS_MODULE'] = 'abaye_elegance.settings'
os.environ['PYTHONANYWHERE'] = '1'
os.environ['DB_NAME'] = 'votre_username$abaye_elegance'
os.environ['DB_USER'] = 'votre_username'
os.environ['DB_PASSWORD'] = 'votre_mot_de_passe_mysql'
os.environ['DB_HOST'] = 'votre_username.mysql.pythonanywhere-services.com'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### Static files (dans la section Web)
| URL | Directory |
|-----|-----------|
| `/static/` | `/home/votre_username/abaye_elegance/staticfiles` |
| `/media/` | `/home/votre_username/abaye_elegance/media` |

---

## Étape 9 : Configurer le nom de domaine personnalisé

1. Dans l'onglet **Web** de PythonAnywhere, section **Domains**
2. Ajouter `abayaelegancegn.com` comme domaine personnalisé
3. Chez votre registrar DNS (là où vous avez acheté le domaine), configurer :
   - **CNAME** : `www` → `votre_username.pythonanywhere.com`
   - **A record** : `@` → l'IP fournie par PythonAnywhere (voir leur doc)
4. Activer le **HTTPS** gratuit via PythonAnywhere (bouton dans la section Web)
5. Cliquer le bouton vert **Reload**
6. Visiter `https://abayaelegancegn.com`

> **Note** : Un compte **payant** PythonAnywhere est requis pour utiliser un nom de domaine personnalisé.

---

## Identifiants Admin

- **URL Admin** : `https://abayaelegancegn.com/admin-panel/login/`
- **Username** : celui créé avec `createsuperuser`
- **Password** : celui choisi

---

## Résumé des URLs

| Page | URL |
|------|-----|
| Accueil | `/` |
| Produit | `/produit/<id>/` |
| À Propos | `/a-propos/` |
| Panier | `/panier/` |
| Admin Login | `/admin-panel/login/` |
| Admin Dashboard | `/admin-panel/` |
| Admin Commandes | `/admin-panel/commandes/` |
| Admin Produits | `/admin-panel/produits/` |
| Django Admin | `/django-admin/` |

---

## Notes importantes

- **Compte gratuit** : le site s'endort après 3 mois sans renouvellement
- **Compte payant** : requis pour le domaine personnalisé `abayaelegancegn.com`
- **Images produits** : les images utilisent des URLs Unsplash, pas besoin d'uploader d'images
- **Sécurité** : changer `SECRET_KEY` en production et mettre `DEBUG = False`
