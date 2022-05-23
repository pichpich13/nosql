# %% [markdown]
#  # Problématique: creer un logiciel permettant de gerer une videotech:
#  - location de films
#  - disponibilité
#  - ajouter des films dans le stock
#  - modifier des films du stock

# %% [markdown]
# #### pour se faire nous allons utilisé:
# - [flask] pour le serveur web.
# - [flask-restful] pour creer une api rest
# - [mongoengine] pour gerer la base de données
# - [flask-jwt-extended] pour la gestion des users
# - ainsi que [insomnia] pour envoyer les requetes et tester leur fonctionnement

# %%
from flask import Flask, request, Response
from database.db import initialize_db
from database.models import Movie
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from flask_restful import Api
from database.models import User
from mongoengine.errors import FieldDoesNotExist, NotUniqueError, DoesNotExist, ValidationError, InvalidQueryError
from error import SchemaValidationError, MovieAlreadyExistsError, InternalServerError, \
UpdatingMovieError, DeletingMovieError, MovieNotExistsError, EmailAlreadyExistsError, UnauthorizedError
from error import errors

import json

app = Flask(__name__)
api = Api(app, errors=errors)
app.config.from_envvar('ENV_FILE_LOCATION')
# JWT_SECRET_KEY = 't1NP63m4wnBg6nyHYKfmc2TpCOGI4nss'
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# %%
app.config['MONGODB_SETTINGS'] = {
    'host': 'mongodb://localhost/moviesDB'
}

initialize_db(app)

# %%
@app.route('/movies') # return tout les films
def get_movies():
    movies = Movie.objects().to_json()
    return Response(movies, mimetype="application/json", status=200)



@app.route('/movies', methods=['POST']) # POST ajouter film
@jwt_required()
def post():
    try:
        user_id = get_jwt_identity()
        body = request.get_json()
        user = User.objects.get(id=user_id)
        movie =  Movie(**body, added_by=user)
        movie.save()
        user.update(push__movies=movie)
        user.save()
        id = movie.id
        return {'id': str(id)}, 200
    except (FieldDoesNotExist, ValidationError):
        raise SchemaValidationError
    except NotUniqueError:
        raise MovieAlreadyExistsError
    except Exception as e:
        raise InternalServerError

@app.route('/movies/<id>', methods=['PUT']) # update film
@jwt_required()
def put(id):
    try:
        user_id = get_jwt_identity()
        movie = Movie.objects.get(id=id, added_by=user_id)
        body = request.get_json()
        Movie.objects.get(id=id).update(**body)
        return '', 200
    except InvalidQueryError:
        raise SchemaValidationError
    except DoesNotExist:
        raise UpdatingMovieError
    except Exception:
        raise InternalServerError  

@app.route('/movies/<id>', methods=['DELETE']) # delete film
@jwt_required()
def delete(id):
    try:
        user_id = get_jwt_identity()
        movie = Movie.objects.get(id=id, added_by=user_id)
        movie.delete()
        return '', 200
    except DoesNotExist:
        raise DeletingMovieError
    except Exception:
        raise InternalServerError

@app.route('/movies/<id>') # GET request to get a movie
def get(id):
    try:
        movies = Movie.objects.get(id=id).to_json()
        return Response(movies, mimetype="application/json", status=200)
    except DoesNotExist:
        raise MovieNotExistsError
    except Exception:
        raise InternalServerError

# change la valeur de nbFilm de la base de données
@app.route('/movies/<id>/nbfilm/<nbFilm>', methods=['PUT'])
@jwt_required()
def update_nbFilm(id, nbFilm):
    movie = Movie.objects.get(id=id)
    movie.nbFilm = nbFilm
    movie.save()
    return '', 200

# change la valeur de loc de la base de données
@app.route('/movies/<id>/loc/<loc>', methods=['PUT'])
@jwt_required()
def update_loc(id, loc):
    movie = Movie.objects.get(id=id)
    # si loc est inferieur a nbfilm, on met a jour la valeur de loc sinon on return une erreur
    if (int(movie.loc) + int(loc)) <= movie.nbFilm:
        movie.loc = int(movie.loc) + int(loc)
        movie.save()
        return '', 200
    else:
        return '', 400



# %%
# authentification
import datetime


@app.route('/auth/signup', methods=['POST'])
def postSign():
    try:
        body = request.get_json()
        user =  User(**body)
        user.hash_password()
        user.save()
        id = user.id
        return {'id': str(id)}, 200
    except FieldDoesNotExist:
        raise SchemaValidationError
    except NotUniqueError:
        raise EmailAlreadyExistsError
    except Exception as e:
        raise InternalServerError

@app.route('/auth/login', methods=['POST'])
def postLog():
    try:
        body = request.get_json()
        user = User.objects.get(email=body.get('email'))
        authorized = user.check_password(body.get('password'))
        if not authorized:
            raise UnauthorizedError

        expires = datetime.timedelta(days=7)
        access_token = create_access_token(identity=str(user.id), expires_delta=expires)
        return {'token': access_token}, 200
    except (UnauthorizedError, DoesNotExist):
        raise UnauthorizedError
    except Exception as e:
        raise InternalServerError
    
app.run(debug=True, port=20112)

