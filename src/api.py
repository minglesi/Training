from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from base64 import b64encode
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
    name = db.Column(db.String(30), nullable=False, unique=True)
    race = db.Column(db.String(10), nullable=False)
    profession_id = db.Column(db.Integer, db.ForeignKey('profession.profession_id'), nullable=False)
    profession = db.relationship("Profession", back_populates="Hero")
    icon = db.Column(db.Text, nullable=True)

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


def validate_hero(hero, update=False):
    errors = {}
    if not hero.name or hero.name == '':
        errors['name'] = "Please fill out this field."
    if len(hero.name) > 30:
        errors['name'] = "Sorry the Hero name must be 30 characters max."
    if not update and Hero.query.filter(Hero.name == hero.name).first() is not None:
        errors['name'] = "Name already in use, please choose another one."
    if not hero.race or hero.race == '':
        errors['race'] = "Please select a race."
    elif hero.race not in ["Human", "Orc", "Elf", "Goblin"]:
        errors['race'] = "Sorry the Hero race must be one of: Human, Orc, Elf or Goblin."
    if not hero.profession_id:
        errors['profession'] = "Please select a Profession."
    elif Profession.query.get(hero.profession_id) is None:
        errors['profession'] = "Invalid Profession"
    return errors


def validate_profession(profession):
    errors = {}
    if not profession.profession or profession.profession == '':
        errors['profession'] = "Please fill out this field."
    if Profession.query.filter(Profession.profession == profession.profession).first() is not None:
        errors['profession'] = "Could not create profession, name already exists."
    if len(profession.profession) > 30:
        errors['profession'] = "Sorry the Profession name must be 30 characters max."
    if profession.hp == '':
        errors['hp'] = "Please fill out this field."
    if not profession.hp.isdigit():
        errors['hp'] = "Only numbers allowed"
    elif int(profession.hp) > 500:
        errors['hp'] = "Ups! Max HP is 500"
    if profession.mana == '':
        errors['mana'] = "Please fill out this field."
    if not profession.mana.isdigit():
        errors['mana'] = "Only numbers allowed"
    elif int(profession.mana) > 500:
        errors['mana'] = "Ups! Max Mana is 500"
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
    icon = request.files['icon']
    image = b64encode(icon.read()).decode('ascii')
    profession_id = request.form.get("profession")
    new_hero = Hero(name=name, race=race, profession_id=profession_id, icon=image)

    errors = validate_hero(new_hero)
    if errors:
        professions = Profession.query.all()
        return render_template('hero.html', name=new_hero.name, profession_id=new_hero.profession_id,
                               race=new_hero.race, professions=professions, errors=errors)
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
        profession_id = int(profession_id) if profession_id else hero.profession_id
        professions = Profession.query.all()
        return render_template('hero.html', hero_id=hero_id, name=hero.name, profession_id=profession_id,
                               race=hero.race, professions=professions, icon=hero.icon)


@app.route('/hero/<int:hero_id>', methods=['POST'])
def update_hero(hero_id):
    hero = Hero.query.get(hero_id)
    if hero is None:
        return redirect('/error')
    else:
        hero.profession_id = request.form.get("profession")
        hero.name = request.form.get("name")
        hero.race = request.form.get("race")
        icon = request.files['icon']
        image = b64encode(icon.read()).decode('ascii')
        hero.icon = image
        errors = validate_hero(hero, update=True)

        if errors:
            professions = Profession.query.all()
            return render_template('hero.html', name=hero.name, profession_id=hero.profession_id, professions=professions,
                                   race=hero.race, icon=hero.icon, errors=errors)
        try:
            db.session.commit()
            return redirect("/heroes")
        except Exception as e:
            return f"There was an error adding data: {e}"


@app.route('/hero/<int:hero_id>/delete', methods=['GET', 'POST'])
def delete_hero(hero_id):
    hero = Hero.query.get(hero_id)
    db.session.delete(hero)
    db.session.commit()
    return redirect("/heroes")


@app.route('/heroes', methods=['GET'])
def show_heroes():
    try:
        heroes = Hero.query.all()
        return render_template('heroes.html', heroes=heroes)
    except Exception as e:
        return render_template('error.html', error=e)


@app.route('/heroes/delete', methods=['GET', 'POST'])
def delete_all_heroes():
    db.session.query(Hero).delete()
    db.session.commit()
    return redirect("/heroes")


@app.route('/profession', methods=['POST'])
def add_profession():
    profession = request.form.get("new_profession")
    hp = request.form.get("new_profession_hp")
    mana = request.form.get("new_profession_mana")
    hero_id = request.args.get("hero_id")
    new_profession = Profession(profession=profession, hp=hp, mana=mana)
    errors = validate_profession(new_profession)
    if errors:
        if hero_id:
            return redirect(f"/hero/{hero_id}")
        else:
            professions = Profession.query.all()
            return render_template('hero.html', profession=new_profession.profession, hp=new_profession.hp,
                                   professions=professions, mana=new_profession.mana, errors=errors)
    try:
        db.session.add(new_profession)
        db.session.commit()
        suffix = f"?profession_id={new_profession.profession_id}"
        if hero_id:
            return redirect(f"/hero/{hero_id}" + suffix)
        else:
            return redirect("/hero" + suffix)
    except Exception as e:
        return f"There was an error adding data: {e}"


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
