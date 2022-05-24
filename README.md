# nosql

pour faire marcher le code il suffit d'installer requierement.txt

$ pip install requierement.txt

puis de faire executer tout sur le notebook.

afin de tester les routes d'api, utiliser insmonia ou postman sur la route http://localhost:5000/auth/signup methode post
dans le body, ajouter, en json:
{
    "email": "(your email)",
    "password": "(your password)"
}

pour creer un compte.

une fois cela fait en method post sur la route http://localhost:5000/auth/login
dans le body, ajouter, en json:
{
    "email": "(your email)",
    "password": "(your password)"
}
cette methode renvoie un token d'authentification bearer.
il faut l'ajouter dans les prochaines requetes.