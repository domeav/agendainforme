# Reprise de l'Agenda Informe

## Contexte

https://agendainforme.htg0.com est en perdition, ceci est un effort pour :

- récupérer les données
- proposer un remplacement

## Initialiser l'environnement

- python -m venv py-dist
- source py-dist/bin/activate
- pip install -r requirements.txt

## Configuration locale

- cp settings-template.py settings.py
- éditer settings.py

## Copier les données depuis le site original

- ./import.py

## Démarrer un serveur local

- flask --app agenda run --debug

## Utilisation

- aller à /login pour accéder aux fonctionnalités
  d'administration. L'utilisateur doit préalablement avoir été
  renseigné dans settings.py