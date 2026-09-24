# 📖 Boutique Carlo Acutis Foundation — Cahier Journal & Caisse

Application web complète développée en **Python** pour la gestion quotidienne de la caisse, des recettes (entrées) et des dépenses (sorties) de la **Boutique Carlo Acutis Foundation** (services de photocopie, impression, vente de livrets, fournitures et abonnements).

---

## 🌟 Fonctionnalités Principales

### 1. 👥 Gestion des Rôles & Sécurité
- **Secrétaire de Caisse** :
  - Saisie rapide des recettes (Entrées) et des dépenses (Sorties).
  - Choix de l'opération dans la liste déroulante officielle.
  - Consultation libre des comptes et des totaux.
  - 🔒 **Protection stricte** : Une fois enregistrée, la ligne d'écriture est verrouillée. La secrétaire **ne peut plus modifier ni supprimer** l'opération.
- **Directeur Général (DG)** :
  - Consultation globale en temps réel (au jour le jour, par mois, par an, sur période donnée).
  - ✏️ **Droit de correction et modification** : En cas d'erreur de saisie de la secrétaire, le DG a la main pour corriger le montant, la date, l'opération ou la description.
  - 🗑️ Suppression d'écritures erronées.
  - ⚙️ **Gestion de la liste déroulante** : Ajout de nouvelles opérations/catégories à volonté.
- **DG Adjoint** :
  - Même niveau de contrôle et d'assistance de gestion que le DG (consultation, correction et administration).

---

### 2. 📒 Cahier Journal Fidèle à l'Excel
- **Code couleur identique au registre physique/Excel** :
  - 🔵 **Entrée (Bleu)** : Montants des recettes (photocopies, impressions, reliures, ventes).
  - 🟡 **Sortie (Jaune)** : Montants des dépenses (achats rames papier, encre, cash power, loyer, etc.).
  - 🟢 **Solde (Vert)** : Calcul automatique du solde cumulé progressif (en direct, ligne par ligne).
- Détection intelligente : Lorsque la secrétaire choisit une prestation (ex: *Photocopie*), l'application sélectionne automatiquement **Entrée** ; lorsqu'elle choisit une dépense (ex: *Achat de papier ram*), l'application bascule automatiquement sur **Sortie**.

---

### 3. 📊 Filtres & Rapports Financiers
- 📅 **Comptes de chaque jour** : Visualisation instantanée des opérations du jour sélectionné avec totaux.
- 📆 **Comptes du mois en cours** : Vue par défaut pour suivre le mois en temps réel.
- 🗓️ **Comptes par mois** : Sélecteur mois + année (ex: Septembre 2026).
- 📈 **Comptes par an** : Bilan annuel complet avec graphique d'évolution mensuelle.
- 🔍 **Période personnalisée** : Du ... Au ... avec filtre par mot-clé (ex: chercher toutes les "Photocopies" ou tous les achats de "Papier").
- 📊 **Tableaux de bord graphiques** :
  - Graphique à barres comparant Entrées vs Sorties.
  - Diagramme circulaire des prestations les plus rentables.

---

### 4. 📑 Export & Impression
- 📥 **Export Excel officiel (.xlsx)** : Génération d'un classeur Excel propre avec en-têtes officiels, couleurs bleu/jaune/vert et formules de calcul.
- 🖨️ **Impression PDF / Papier** : Vue adaptée prête à l'impression avec cadres de visa pour la secrétaire et la Direction Générale.

---

### 5. 🎨 Identité Visuelle
- Portrait de **Saint Carlo Acutis** avec sa célèbre citation :
  > *« Tous naissent comme des originaux, mais beaucoup meurent comme des photocopies. »*
- Visuel haute définition des photocopieuses professionnelles.
- Interface moderne, élégante et 100% responsive (fonctionne sur ordinateur, tablette et smartphone).

---

## 🔐 Identifiants de Connexion

| Rôle | Nom d'utilisateur | Code PIN | Droits d'accès |
| :--- | :--- | :--- | :--- |
| **Directeur Général (DG)** | `dg` | `12345` | Contrôle total, corrections d'erreurs, suppression, gestion catégories |
| **DG Adjoint** | `dg_adjoint` | `23456` | Supervision, corrections d'erreurs, gestion catégories |
| **Secrétaire de Caisse** | `secretaire` | `4231` | Saisie des flux & consultation (non modifiable après saisie) |

---

## 🚀 Démarrage Rapide

### Sur Windows (en 1 clic) :
Double-cliquez simplement sur le fichier :
```text
demarrer.bat
```
Le serveur démarrera automatiquement et votre navigateur s'ouvrira sur `http://localhost:8000`.

### Via la ligne de commande Python :
```bash
# 1. Aller dans le dossier du projet
cd carlo_acutis_journal

# 2. Initialiser la base de données (si première fois)
python database.py

# 3. Lancer l'application web
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Ouvrez ensuite votre navigateur sur : [http://localhost:8000](http://localhost:8000)

---

## 🌐 Déploiement en Ligne (Mise en Ligne sur Internet)

Pour rendre l'application accessible en ligne à distance au DG, au DG Adjoint et à la Secrétaire depuis n'importe où (téléphone ou ordinateur) :

### Option 1 : Render.com ou Railway.app (Recommandé & Gratuit / Économique)
1. Créez un compte sur [Render.com](https://render.com) ou [Railway.app](https://railway.app).
2. Déposez ce dossier sur GitHub (privé ou public).
3. Connectez votre dépôt Git sur Render / Railway en sélectionnant **Web Service**.
4. Spécifiez :
   - **Build Command** : `pip install -r requirements.txt && python database.py`
   - **Start Command** : `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. L'application aura instantanément une adresse sécurisée en HTTPS (ex: `https://cahier-carlo-acutis.onrender.com`).

### Option 2 : PythonAnywhere
1. Uploadez les fichiers sur [PythonAnywhere](https://www.pythonanywhere.com/).
2. Créez une Web App ASGI (FastAPI) pointant vers `main:app`.

### Option 3 : Docker
Un `Dockerfile` est déjà inclus à la racine :
```bash
docker build -t carlo-acutis-journal .
docker run -p 8000:8000 carlo-acutis-journal
```

---

## 📋 Catégories Incluses par Défaut (28 Opérations)

1. Abonnement Wifi *(Sortie)*
2. Achat d'articles *(Sortie)*
3. Achat d'encre *(Sortie)*
4. Achat de cash power *(Sortie)*
5. Achat de papier ram *(Sortie)*
6. Conception *(Entrée)*
7. Coupe *(Entrée)*
8. Déplacement *(Sortie)*
9. Entretien des machines *(Sortie)*
10. Frais d'électricité *(Sortie)*
11. Impression *(Entrée)*
12. Lamination *(Entrée)*
13. Loyer *(Sortie)*
14. Photo passeport *(Entrée)*
15. Photocopie *(Entrée)*
16. Reliure *(Entrée)*
17. Reliure de livrets de bénédiction *(Entrée)*
18. Saisie *(Entrée)*
19. Scanner *(Entrée)*
20. Vente d'articles *(Entrée)*
21. Vente d'image *(Entrée)*
22. Vente de livres Anecdotes Mgr *(Entrée)*
23. Vente de livret de bénédiction *(Entrée)*
24. Vente de livret de confirmation *(Entrée)*
25. Vente de livret de rosaire *(Entrée)*
26. Vente de livret Esprit Saint *(Entrée)*
27. Vente de Wifi *(Entrée)*
28. Confection de tampon *(Entrée)*
*(Le DG et le DG Adjoint peuvent en ajouter autant qu'ils veulent depuis l'onglet « Catégories »).*
