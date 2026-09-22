from flask import Flask, render_template, request, redirect, session
import requests 
import json

def load_users():
    with open("users.json", "r") as file:
        users = json.load(file)

    return users

def save_users():
    with open("users.json", "w") as file:
        json.dump(users, file, indent=4)

app = Flask(__name__)
app.secret_key = "f1-manager-secret-key"

users = load_users()


def get_data(url):
    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return None

        return response.json()

    except requests.RequestException:
        return None


def get_drivers():
    url = "https://api.jolpi.ca/ergast/f1/current/drivers/"
    data = get_data(url)

    if data is None:
        return []

    return data["MRData"]["DriverTable"]["Drivers"]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        username_exists = False

        for user in users:
            if user["username"] == username:
                username_exists = True
                break

        if username_exists:
            error = "Это имя пользователя уже занято."
        else:
            user = {
                "username": username,
                "password": password
            }

            users.append(user)
            save_users()
            session["username"] = username

            return redirect("/cabinet")

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        logged_in = False

        for user in users:
            if user["username"] == username:
                if user["password"] == password:
                    logged_in = True
                    break

        if logged_in:
            session["username"] = username
            return redirect("/cabinet")
        else:
            error = "Неверное имя пользователя или пароль."

    return render_template("login.html", error=error)


@app.route("/cabinet")
def cabinet():
    if "username" not in session:
        return redirect("/login")

    return render_template("cabinet.html", username=session["username"])


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")


@app.route("/race")
def last_race():
    url = "https://api.jolpi.ca/ergast/f1/current/last/results/"
    data = get_data(url)

    if data is None:
        return render_template("error.html", message="Не удалось получить данные о последней гонке.")

    races = data["MRData"]["RaceTable"]["Races"]

    if not races:
        return render_template("error.html", message="Данные о гонке не найдены.")

    race = races[0]

    return render_template("race.html", race=race)


@app.route("/driver", methods=["GET", "POST"])
def driver():
    driver = None
    error = None

    if request.method == "POST":
        query = request.form["name"].strip().lower()

        for item in get_drivers():
            full_name = f"{item['givenName']} {item['familyName']}".lower()

            if query in full_name:
                driver = item
                break

        if driver is None:
            error = "Гонщик не найден."

    return render_template("driver.html", driver=driver, error=error)


@app.route("/results", methods=["GET", "POST"])
def results():
    results = []
    driver_name = None
    error = None

    if request.method == "POST":
        query = request.form["name"].strip().lower()
        selected_driver = None

        for item in get_drivers():
            full_name = f"{item['givenName']} {item['familyName']}".lower()

            if query in full_name:
                selected_driver = item
                break

        if selected_driver is None:
            error = "Гонщик не найден."
        else:
            driver_name = f"{selected_driver['givenName']} {selected_driver['familyName']}"
            driver_id = selected_driver["driverId"]

            url = f"https://api.jolpi.ca/ergast/f1/drivers/{driver_id}/results/"
            data = get_data(url)

            if data is None:
                error = "Не удалось получить результаты."
            else:
                races = data["MRData"]["RaceTable"]["Races"]

                for race in races:
                    result = race["Results"][0]

                    results.append({
                        "race": race["raceName"],
                        "position": result["position"],
                        "points": result["points"]
                    })

    return render_template(
        "results.html",
        results=results,
        driver_name=driver_name,
        error=error
    )


@app.route("/championship")
def championship():
    url = "https://api.jolpi.ca/ergast/f1/current/driverstandings/"
    data = get_data(url)

    if data is None:
        return render_template("error.html", message="Не удалось получить чемпионат.")

    standings = data["MRData"]["StandingsTable"]["StandingsLists"]

    if not standings:
        return render_template("error.html", message="Таблица чемпионата не найдена.")

    drivers = standings[0]["DriverStandings"]

    return render_template("championship.html", drivers=drivers)


if __name__ == "__main__":
    app.run(debug=True)
