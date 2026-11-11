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

