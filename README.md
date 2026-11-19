# -Projet-TCP-IP
# Système de Partage de Fichiers P2P (Peer-to-Peer)

Ce projet est une application distribuée de partage et de transfert de fichiers en P2P s'appuyant sur un serveur centralisé pour la gestion des utilisateurs et l'indexation. Il a été développé dans le cadre du module **Programmation IP / Réseaux**.

---

##  Architecture du Système

Le système est composé de deux briques principales :

1. **Serveur Centralisé :**
   * **Authentification sécurisée :** Inscription et connexion des utilisateurs sans faire circuler les mots de passe en clair sur le réseau (utilisation du hachage/chiffrement).
   * **Gestion des sessions actives :** Suivi des hôtes connectés et mise à jour dynamique de la liste des fichiers partagés.
   * **Indexation & Recherche :** Recherche par mots-clés dans les descriptions textuelles transmises par les clients, renvoyant l'adresse IP/hostname et le nom des fichiers correspondants.
   * **Détection des déconnexions :** Prise en compte du départ d'un serveur distant (par avertissement direct ou mécanisme de heartbeat).

2. **Hôtes Utilisateurs (P2P Node) :**
   * **Serveur FTP / Fichiers :** Écoute les demandes entrantes des autres utilisateurs et assure l'envoi (`download`) des fichiers locaux partagés.
   * **Client FTP / Fichiers :** Permet à l'utilisateur de s'authentifier auprès du serveur central, d'envoyer la liste/description de ses fichiers, de rechercher des fichiers par mots-clés et de se connecter directement à d'autres hôtes pour extraire les fichiers distants.

---

##  Spécifications Techniques

* **Langage :** Python (ou C / Java selon l'implémentation)
* **Protocole Transport :** TCP (sockets stream) pour assurer la fiabilité des transferts et des requêtes
* **Concurrence :** Gestion des connexions simultanées via **Threads** (un thread par client/connexion)
* **Format des descriptions :** Fichiers texte associés contenant le nom du fichier et son descriptif (ex: `MP3.txt` avec métadonnées)

---

##  Guide d'Installation et d'Exécution

### 1. Prérequis
* Environnement UNIX / Linux recommandé
* Compilateur C / Interprète Python (selon le langage choisi)

### 2. Démarrage du Serveur Centralisé
Lancer le serveur centralisé en précisant le port d'écoute :
```bash
python3 server_central.py <port_serveur>
```

Le port par défaut est `5000` :

```bash
python3 server_central.py
```

### 3. Inscription d'un utilisateur

```bash
python3 peer_node.py \
  --username alice \
  --password secret \
  --central-host 127.0.0.1 \
  --central-port 5000 \
  --register
```

### 4. Connexion et publication des fichiers

Le nœud démarre son serveur de fichiers, se connecte au serveur central et
publie le contenu de `shared/` :

```bash
python3 peer_node.py \
  --username alice \
  --password secret \
  --shared-dir shared-alice \
  --peer-port 6001 \
  --login
```

Lancer chaque utilisateur avec un port pair différent.

Le dossier partagé est parcouru récursivement : les fichiers placés dans des
sous-dossiers sont également publiés. Dans l'interface Peer, utilisez
**Actualiser les fichiers** après avoir ajouté ou supprimé un fichier.

### 5. Recherche et téléchargement

Une recherche renvoie le nom du fichier ainsi que l'adresse du peer :

```bash
python3 peer_node.py \
  --username bob \
  --password secret \
  --central-port 5000 \
  --search musique
```

Pour afficher tous les fichiers publiés sans mot-clé :

```bash
python3 peer_node.py \
  --username bob \
  --password secret \
  --central-port 5000 \
  --list
```

Le fichier peut ensuite être téléchargé directement depuis le peer :

```bash
python3 peer_node.py \
  --username bob \
  --password secret \
  --download-host 127.0.0.1 \
  --download-port 6001 \
  --download-file chanson.mp3 \
  --output downloads/chanson.mp3
```

Le protocole de transfert utilise une réponse JSON contenant la taille du
fichier, suivie des octets du fichier sur la même connexion TCP.

Pour une connexion entre deux ordinateurs, remplacez `127.0.0.1` par
l'adresse IP locale de l'ordinateur qui héberge le peer et autorisez les ports
`5000` et `6001` dans le pare-feu.

## Structure des fichiers

* `server_central.py` : authentification, sessions, index et recherche.
* `peer_node.py` : serveur de fichiers et client du serveur central.
* `common.py` : protocole JSON préfixé par la taille et utilitaires partagés.
* `shared/` : fichiers publiés par défaut.
* `logs/` : emplacement réservé aux journaux.

## Fonctionnement du heartbeat

Après sa connexion, un peer envoie automatiquement un heartbeat au serveur
central toutes les 30 secondes. Un peer qui n'envoie plus de heartbeat pendant
90 secondes est retiré de l'index.

## Vérification

Le projet ne dépend d'aucune bibliothèque externe. Les tests utilisent le
module `unittest` inclus avec Python :

```bash
python3 -m unittest discover -v
```

## Interfaces graphiques

L'application fournit une interface Tkinter moderne avec un lanceur unique :

```bash
python3 app.py
```

Les interfaces peuvent aussi être démarrées séparément :

```bash
python3 central_gui.py
python3 peer_gui.py
```

