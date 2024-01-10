from flask import Flask, session, render_template, redirect, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from Db import db
from Db.models import users, initiatives
from flask_migrate import Migrate


app = Flask(__name__)


app.secret_key = 'key'  # Ключ для сессий
user_db = "shep"
host_ip = "127.0.0.1"
host_port = "5432"
database_name = "initiativ"
password = "krut"


app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{user_db}:{password}@{host_ip}:{host_port}/{database_name}?options=-c timezone=Asia/Bangkok'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)

migrate = Migrate(app, db)


@app.route('/')
def start():
    return redirect(url_for('main'))


@app.route("/app/index", methods=['GET', 'POST'])
def main():
    username = session.get('username')
    if 'username' not in session:
        return redirect(url_for('registerPage'))
    
    if request.method == 'POST':
        initiative_id = request.form.get('initiative_id')
        vote_type = int(request.form.get('vote_type'))

        user_id = session.get('id')
        voted_key = f'voted_{user_id}_{initiative_id}'
        
        if session.get(voted_key) is None:
            initiative = initiatives.query.get_or_404(initiative_id)


    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    initiatives_list = initiatives.query.slice(offset, offset + per_page).all()

    # Проверка рейтинга и удаление инициативы
    for initiative in initiatives_list:
        if initiative.rating <= -10:
            db.session.delete(initiative)

    db.session.commit()

    return render_template('index.html', initiatives=initiatives_list, current_page=page, per_page=per_page, name=username)


@app.route('/app/register', methods=['GET', 'POST'])
def registerPage():
    errors = []

    if request.method == 'GET':
        return render_template("register.html", errors=errors)

    username = request.form.get("username")
    password = request.form.get("password")

    if not (username or password):
        errors.append("Пожалуйста, заполните все поля")
        print(errors)
        return render_template("register.html", errors=errors)
   
    existing_user = users.query.filter_by(username=username).first()

    if existing_user:
        errors.append('Пользователь с данным именем уже существует')
        return render_template('register.html', errors=errors, resultСur=existing_user)

    hashed_password = generate_password_hash(password)

    new_user = users(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return redirect("/app/login")


@app.route('/app/login', methods=["GET", "POST"])
def loginPage():
    errors = []

    if request.method == 'GET':
        return render_template("login.html", errors=errors)

    username = request.form.get("username")
    password = request.form.get("password")

    if not (username or password):
        errors.append("Пожалуйста, заполните все поля")
        return render_template("login.html", errors=errors)

    user = users.query.filter_by(username=username).first()

    if user is None or not check_password_hash(user.password, password):
        errors.append('Неправильный пользователь или пароль')
        return render_template("login.html", errors=errors)

    session['id'] = user.id
    session['username'] = user.username

    return redirect("/app/index")


@app.route("/app/new_initiative", methods=["GET", "POST"])
def createInitiative():
    errors = []
    username = session.get('username')

    if request.method == 'POST':
        title = request.form.get('title')
        text = request.form.get('text')

        if not (title and text):
            errors.append('Пожалуйста, заполните все поля')
            return render_template('new_initiative.html', errors=errors)

        user = users.query.filter_by(username=username).first()

        if user:
            new_initiative = initiatives(title=title, text=text, user_id=user.id)
            db.session.add(new_initiative)
            db.session.commit()

            return redirect(url_for('all_initiatives'))

    return render_template('new_initiative.html', errors=errors)


@app.route("/app/all_initiatives", methods=['GET', 'POST'])
def all_initiatives():
    username = session.get('username')

    if not username:
        return redirect(url_for('loginPage'))

    user = users.query.filter_by(username=username).first()

    if not user:
        return redirect(url_for('loginPage'))

    if request.method == 'POST':
        initiative_id = request.form.get('delete_initiative')

        if initiative_id:
            initiative = initiatives.query.get(initiative_id)

            if initiative and initiative.user_id == user.id:
                db.session.delete(initiative)
                db.session.commit()

                return redirect(url_for('all_initiatives'))

    user_initiatives = initiatives.query.filter_by(user_id=user.id).all()

    return render_template('all_initiatives.html', user_initiatives=user_initiatives)


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('loginPage'))


@app.route('/vote/<int:initiative_id>/<int:vote_type>', methods=['POST'])
def vote(initiative_id, vote_type):
    user_id = session.get('id')
    voted_key = f'voted_{user_id}_{initiative_id}'

    if session.get(voted_key) is None:
        initiative = initiatives.query.get_or_404(initiative_id)

        if vote_type == 1:
            initiative.rating += 1
        elif vote_type == 0:
            initiative.rating -= 1

        # Сохранение информации о голосе в сессии
        session[voted_key] = True
        db.session.commit()

    return redirect(url_for('main', page=request.args.get('page', 1)))


@app.route("/app/delete_initiative/<int:initiative_id>", methods=["POST"])
def delete_initiative(initiative_id):
    if 'username' not in session or not session['username'] == 'admin':
        return redirect(url_for('login'))  

    initiative = initiatives.query.get_or_404(initiative_id)
    db.session.delete(initiative)
    db.session.commit()

    return redirect(url_for('main'))
