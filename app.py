from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import os
import pandas as pd

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "viact.db"
)
app.config["JWT_SECRET_KEY"] = "super-secret"  # change this IRL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)


@app.cli.command("db_create")
def db_create():
    db.create_all()
    print("Database created.")


@app.cli.command("db_drop")
def db_drop():
    db.drop_all()
    print("Database dropped.")


@app.cli.command("db_seed")
def db_seed():
    movie_list = Movie(
        movie_id=1,
        movie_name="Spider Man",
        movie_language="Eng",
        movie_genre="Comedy",
        movie_runtime=120,
    )

    db.session.add(movie_list)

    test_user = User(
        first_name="Shapon",
        last_name="Sheikh",
        email="test@test.com",
        password="P@ssword",
    )
    db.session.add(test_user)
    db.session.commit()
    print("Database seeded.")


@app.route("/api/movies", methods=["GET"])
def movies():
    movies_list = Movie.query.all()
    result = movies_schema.dump(movies_list)
    return jsonify(result)


@app.route("/api/authenticate/register", methods=["POST"])
def register():
    email = request.form["email"]
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message="That email already exists."), 409
    else:
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        password = request.form["password"]
        user = User(
            first_name=first_name, last_name=last_name, email=email, password=password
        )
        db.session.add(user)
        db.session.commit()
        return jsonify(message="User created successfully."), 201


@app.route("/api/authenticate/login", methods=["POST"])
def login():
    if request.is_json:
        email = request.json["email"]
        password = request.json["password"]
    else:
        email = request.form["email"]
        password = request.form["password"]

    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message="Login succeeded!", access_token=access_token)
    else:
        return jsonify(message="You entered incorrect email or password"), 401


@app.route("/api/movie_details/<int:movie_id>", methods=["GET"])
def movie_details(movie_id: int):
    movie = Movie.query.filter_by(movie_id=movie_id).first()
    if movie:
        result = movie_schema.dump(movie)
        return jsonify(result)
    else:
        return jsonify(message="That movie does not exist."), 404


@app.route("/api/add_movie", methods=["POST"])
@jwt_required()
def add_movie():
    movie_name = request.form["movie_name"]
    test = Movie.query.filter_by(movie_name=movie_name).first()
    if test:
        return jsonify(message="There is already a movie by that name."), 409
    else:
        movie_type = request.form["movie_type"]
        movie_language = request.form["movie_language"]
        movie_genre = request.form["movie_genre"]
        movie_runtime = request.form["movie_runtime"]

        new_movie = Movie(
            movie_name=movie_name,
            movie_type=movie_type,
            movie_language=movie_language,
            movie_genre=movie_genre,
            movie_runtime=movie_runtime
        )
        db.session.add(new_movie)
        db.session.commit()
        return jsonify(message="You added a movie."), 201


@app.route('/api/upload', methods=['GET', 'POST'])
def upload_csv():
    # if request.method == 'POST':
    csv_upload = {}
    csv_file = pd.read_csv("movies.csv", delimiter=',')
    for row in csv_file:
        row.append(csv_upload)

    uploaded_movie = Movie(
            movie_name=csv_upload[0], 
            movie_type=csv_upload[1],
            movie_language=csv_upload[2],
            movie_genre=csv_upload[3],
            movie_runtime=csv_upload[4]
        )
    db.session.add(uploaded_movie)
    db.session.commit()
    return jsonify(message="Your csv movies has been added."), 201



# database models
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = Column(db.String)
    last_name = Column(db.String)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class UserSchema(ma.Schema):
    class Meta:
        fields = ("id,", "first_name", "last_name", "email", "password")


class Movie(db.Model):
    __tablename__ = 'movies'

    movie_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    movie_name = Column(db.String)
    movie_type = Column(db.String)
    movie_language = Column(db.String)
    movie_genre = Column(db.String)
    movie_runtime = Column(db.String)


class MovieSchema(ma.Schema):
    class Meta:
        fields = (
            "movie_id",
            "movie_name",
            "movie_language",
            "movie_genre",
            "movie_runtime",
        )


user_schema = UserSchema()
users_schema = UserSchema(many=True)

movie_schema = MovieSchema()
movies_schema = MovieSchema(many=True)

if __name__ == "__main__":
    app.run()
