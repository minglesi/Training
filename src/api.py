from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import pymysql
import os

db_pass = os.environ.get('DB_PASS')
app = Flask(__name__, template_folder="template")
pymysql.install_as_MySQLdb()
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:' + str(db_pass) + '@localhost:3307/demo'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['EXPLAIN_TEMPLATE_LOADING'] = True
db = SQLAlchemy(app)


class Hero(db.Model):
    hero_id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(30), nullable=False)
    race = db.Column(db.String(10), nullable=False)
    profession_id = db.Column(db.Integer, db.ForeignKey('profession.profession_id'), nullable=False)
    profession = db.relationship("Profession", back_populates="Hero")

    def __repr__(self):
        return '%s, %s' % (self.name, self.race)


class Profession(db.Model):
    profession_id = db.Column(db.Integer, primary_key=True, nullable=False)
    profession = db.Column(db.String(30), nullable=False, unique=True)
    Hero = db.relationship("Hero", back_populates="profession")
    hp = db.Column(db.Integer())
    mana = db.Column(db.Integer())

    def __repr__(self):
        return '%s - %s hp, %s mana' % (self.profession, self.hp, self.mana)


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
    db.drop_all()
    db.create_all()
    return render_template('index.html')


@app.route('/hero', methods=['GET'])
def hero():
    professions = Profession.query.all()
    profession_id = request.args.get("profession_id")
    if profession_id:
        profession_id = int(profession_id)
    return render_template('hero.html', professions=professions, profession_id=profession_id)


@app.route('/hero', methods=['POST'])
def add_hero():
    name = request.form.get("name")
    race = request.form.get("race")
    profession_id = request.form.get("profession")
    new_hero = Hero(name=name, race=race, profession_id=profession_id)
    #errors = validate_hero_profession(new_hero, new_profession)
    #if errors:
    #    return render_template('hero.html', name=Hero.name, profession=Hero.profession, hp=Profession.hp,
    #                           mana=Profession.mana)
    try:
        db.session.add(new_hero)
        db.session.commit()
        return redirect(f"/heroes")
    except Exception as e:
        return f"There was an error adding data: {e}"


@app.route('/hero/<int:hero_id>', methods=['GET'])
def get_hero(hero_id):
    hero = Hero.query.get(hero_id)
    if hero is None:
        return redirect('/error')
    else:
        profession_id = request.args.get("profession_id")
        if profession_id:
            profession_id = int(profession_id)
        else:
            profession_id = hero.profession_id
        professions = Profession.query.all()
        return render_template('hero.html', hero_id=hero_id, name=hero.name, profession_id=profession_id,
                               race=hero.race, professions=professions)


@app.route('/hero/<int:hero_id>', methods=['POST'])
def update_hero(hero_id):
    hero = Hero.query.get(hero_id)
    if hero is None:
        return redirect('/error')
    else:
        hero.profession_id = request.form.get("profession")
        hero.name = request.form.get("name")
        hero.race = request.form.get("race")
        #errors = validate_hero_profession(hero, profession)

        #if errors:
        #    return render_template('hero.html', name=Hero.name, profession=Hero.profession, hp=Profession.hp,
        #                           mana=Profession.mana)
        try:
            db.session.commit()
            return redirect("/heroes")
        except Exception as e:
            return f"There was an error adding data: {e}"


@app.route('/heroes', methods=['GET'])
def show_heroes():
    try:
        heroes = Hero.query.all()
        return render_template('heroes.html', heroes=heroes)
    except Exception as e:
        return render_template('error.html', error=e)


@app.route('/hero/<int:hero_id>/delete', methods=['GET', 'POST'])
def delete_hero(hero_id):
    hero = Hero.query.get(hero_id)                  ##cuándo elimino el heroe, que pasa con la profession? se elimina
    db.session.delete(hero)                         ##solo por la relacion que hay entre hero_id y profession_id o no?
    db.session.commit()
    return redirect("/heroes")


@app.route('/heroes/delete', methods=['GET', 'POST'])
def delete_all_heroes():
    db.session.query(Hero).delete()
    db.session.commit()
    return redirect("/hero")


@app.route('/profession', methods=['POST'])
def add_profession():
    profession = request.form.get("new_profession")
    hp = request.form.get("new_profession_hp")
    mana = request.form.get("new_profession_mana")
    hero_id = request.args.get("hero_id")
    new_profession = Profession(profession=profession, hp=hp, mana=mana)
    professions = Profession.query.all()
    professions_list = [profession.profession for profession in professions]
    if profession not in professions_list:
        db.session.add(new_profession)
    db.session.commit()
    suffix = f"?profession_id={new_profession.profession_id}"
    if hero_id:
        return redirect(f"/hero/{hero_id}" + suffix)
    else:
        return redirect("/hero" + suffix)


@app.route('/professions', methods=['GET'])
def show_professions():
    try:
        professions = list(Profession.query.all)
        return render_template('professions.html', professions=professions)
    except Exception as e:
        return render_template('error.html', error=e)



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

##/heroes GET
##/hero GET/POST
##/hero/{id} GET/POST/PATCH/DELETE

##/professions GET
##/profession GET/POST
##/profession/{id} GET/POST/PATCH/DELETE

