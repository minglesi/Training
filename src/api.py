from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import pymysql
import os

db_pass = os.environ.get('DB_PASS')
app = Flask(__name__, template_folder="template")
pymysql.install_as_MySQLdb()
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:' + str(db_pass) + '@localhost:3306/demo'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['EXPLAIN_TEMPLATE_LOADING'] = True
db = SQLAlchemy(app)


class Hero(db.Model):
    hero_id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(30), nullable=False)
    profession_id = db.Column(db.Integer, db.ForeignKey('profession.profession_id'), nullable=False)
    profession = db.relationship("Profession", back_populates="Hero")

    def __repr__(self):
        return '%s, %s' % (self.name, self.profession)


class Profession(db.Model):
    profession_id = db.Column(db.Integer, primary_key=True, nullable=False)
    profession = db.Column(db.String(30), nullable=False, unique=True)
    Hero = db.relationship("Hero", back_populates="profession")
    hp = db.Column(db.Integer())
    mana = db.Column(db.Integer())

    def __repr__(self):
        return '%s, %s, %s' % (self.profession, self.hp, self.mana)


def validate_hero_profession(hero, profession):
    errors = {}
    if hero.profession_id == '':
        errors['profession'] = "Please fill out this field."
    if len(hero.profession_id) > 20:
        errors['profession'] = "Sorry the Profession name must be 20 characters max."
    if hero.name == '':
        errors['name'] = "Please fill out this field."
    if len(hero.name) > 20:
        errors['name'] = "Sorry the Hero name must be 20 characters max."
    if profession.hp == '':
        errors['hp'] = "Please fill out this field."
    if profession.hp > 500:
        errors['hp'] = "Ups! Max HP is 500"
    if profession.mana == '':
        errors['mana'] = "Please fill out this field."
    if profession.mana > 300:
        errors['mana'] = "Ups! Max Mana is 300"
    return errors


@app.errorhandler(404)
def invalid_route(e):
    return render_template('error.html', e=e)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/profession', methods=['GET', 'POST'])
def add_profession():
    profession = request.form.get("new_profession")
    new_profession = Profession(profession=profession)
    professions = Profession.query.all()
    professions_list = [str(profession) for profession in professions]
    if profession not in professions_list:
        db.session.add(new_profession)
    db.session.commit()
    return redirect("/hero")


@app.route('/professions', methods=['GET'])
def show_professions():
    try:
        professions = list(Profession.query.all)
        return render_template('professions.html', professions=professions)
    except Exception as e:
        return render_template('error.html', error=e)


@app.route('/hero', methods=['GET'])
def all_heroes():
    professions = Profession.query.all()
    return render_template('hero.html', profession=professions)


@app.route('/heroes/<int:hero_id>', methods=['GET'])
def get_hero(hero_id):
    hero = Hero.query.get(hero_id)
    if hero is None:
        return redirect('/error')
    else:
        return render_template('hero.html', name=Hero.name, profession=Hero.profession, hp=Profession.hp,
                               mana=Profession.mana)


@app.route('/heroes/<int:hero_id>', methods=['POST'])
def update_hero_profession(hero_id):
    hero = Hero.query.get(hero_id)
    profession = Profession.query.get(hero_id)
    if hero is None:
        return redirect('/error')
    else:
        Hero.profession_id = request.form.get("profession")
        Hero.name = request.form.get("name")
        Profession.hp = request.form.get("hp")
        Profession.mana = request.form.get("mana")
        errors = validate_hero_profession(hero, profession)

        if errors:
            return render_template('hero.html', name=Hero.name, profession=Hero.profession, hp=Profession.hp,
                                   mana=Profession.mana)
        try:
            db.session.commit()
            return redirect("/hero")
        except Exception as e:
            return f"There was an error adding data: {e}"


@app.route('/heroes/new', methods=['POST'])
def add_hero():
    name = request.form.get("name")
    profession = request.form.get("profession")
    hp = request.form.get("hp")
    mana = request.form.get("mana")
    new_hero = Hero(name=name)
    new_profession = Profession(profession=profession, hp=hp, mana=mana)
    errors = validate_hero_profession(new_hero, new_profession)
    if errors:
        return render_template('hero.html', name=Hero.name, profession=Hero.profession, hp=Profession.hp,
                               mana=Profession.mana)
    try:
        db.session.add(new_hero)
        db.session.add(new_profession)
        db.session.commit()
        return redirect("/todos")
    except Exception as e:
        return f"There was an error adding data: {e}"


@app.route('/heroes', methods=['GET'])
def show_heroes():
    try:
        heroes = list(Hero.query.all)
        return render_template('heroes.html', heroes=heroes)
    except Exception as e:
        return render_template('error.html', error=e)


@app.route('/heroes/<int:hero_id>/delete', methods=['GET', 'POST'])
def delete_hero(hero_id):
    hero = Hero.query.get(hero_id)                  ##cuándo elimino el heroe, que pasa con la profession? se elimina
    db.session.delete(hero)                         ##solo por la relacion que hay entre hero_id y profession_id o no?
    db.session.commit()
    return redirect("/hero")


@app.route('/heroes/delete', methods=['GET', 'POST'])
def delete_all_heroes():
    db.session.query(Hero).delete()
    db.session.commit()
    return redirect("/hero")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

##/heroes GET
##/hero GET/POST
##/hero/{id} GET/POST/PATCH/DELETE

##/professions GET
##/profession GET/POST
##/profession/{id} GET/POST/PATCH/DELETE

