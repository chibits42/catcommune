from replit import db
import hashlib
from flask import Flask, request, render_template, send_file, redirect, url_for, make_response
import time

app = Flask(__name__)

# db["accounts"] = []
# db["posts"] = []
# db["recentposts"] = []

# print(db["accounts"])
# for i, a in enumerate(db["accounts"]):
#     if a["username"] == "sirq3 ":
#         del db["accounts"][i]
#     elif not a["username"].isascii():
#         del db["accounts"][i]
        

test_dict = dict(db["accounts"])

# for sub in test_dict:
#     print(sub)
#     for sub_nest in test_dict[sub]:
#         print(sub_nest, ':', test_dict[sub][sub_nest])

print(db["accounts"])

def register(username, password):
    acc = {
        "username": username,
        "passwd": hashlib.sha512(password.encode()).hexdigest()
    }

    db["accounts"].append(acc)

    return acc

def post(nickname, nickIP, title, post):

    _time = time.time()

    if nickname == "Anonymous":
        nickid = hashlib.sha256((nickIP).encode()).hexdigest()[:10]
    else:
        nickid = hashlib.sha256((nickname).encode()).hexdigest()[:10]
        
    postid = f"{nickname}.{nickid}.{title}.{post}.{_time}".encode()

    postjson = {
        "id": hashlib.sha256(postid).hexdigest(),
        "topic": title,
        "posted": _time,
        "posturl": f"https://catcommune.jort57.repl.co/render/{hashlib.sha256(postid).hexdigest()}",
        "post": post,
        "author": nickname,
        "last_update": 0,
    }

    db["posts"].append(postjson)

    post = post.replace("\n", "\n\t")

    with open(f"posts/{hashlib.sha256(postid).hexdigest()}.txt", "w") as f:
        f.write(
            f"[{hashlib.sha256(postid).hexdigest()}]\n'{title}'\n-----------------------------\n\n{nickname} ({nickid}):\n\t{post}\n\n-----------------------------"
        )

    return hashlib.sha256(postid).hexdigest()


def append(postid, nick, nickIP, post):
    post = post.replace("\n", "\n\t")
    postj = {}
    postidx = None

    for i, item in enumerate(db["posts"]):
        if item['id'] == postid:
            postj = item
            postidx = i
            break
        else:
            postj = None


    if nick == "Anonymous":
        nickid = hashlib.sha256((nickIP).encode()).hexdigest()[:10]
    else:
        nickid = hashlib.sha256((nick).encode()).hexdigest()[:10]
        
    postfmt = f"\n\n{nick} ({nickid}):\n\t{post}\n\n-----------------------------"

    with open(f"posts/{postid}.txt", "a") as f:
        f.write(postfmt)

    db["posts"][postidx]["last_update"] = time.time()


@app.route('/')
def index():
    apost = []

    for p in db["posts"]:
        if p["last_update"] == 0:
            continue
        else:
            apost.append(p)

    if sorted(apost, key=lambda x: x["last_update"])[::-1] == None:
        print("nun")
        apost = []
        print(apost)
    else:
        apost = sorted(apost, key=lambda x: x["last_update"])[::-1][:20]

    # print(sorted(db["posts"], key=lambda x: x["posted"])[::-1])

    # print(db["posts"])

    if sorted(db["posts"], key=lambda x: x["posted"])[::-1] == None: _posts = []
    else: _posts = sorted(db["posts"], key=lambda x: x["posted"])[::-1]
            
    return render_template(
        "home.html",
        posts=_posts,
        aposts=apost,
        logged_in = request.cookies.get("logged_in"), username = request.cookies.get("username")
    )


@app.route('/post', methods=("GET", "POST"))
def serv_post():
    if request.method == 'POST':
        if request.cookies.get('logged_in') == "true":
            nick = request.cookies.get('username')
        else:
            nick = "Anonymous"
        id = post(nick, str(request.remote_addr),
                  request.form["title"], request.form["post"])

        return redirect(url_for('render_post', postid=id))

    return render_template('postform.html')


@app.route('/render/<postid>', methods=("GET", "POST"))
def render_post(postid):
    id = postid
    with open(f"posts/{postid}.txt", 'r') as f:
        post = f.read()

    if request.method == 'POST':
        if request.cookies.get('logged_in') == "true":
            nick = request.cookies.get('username')
        else:
            nick = "Anonymous"

        append(postid, nick, str(request.remote_addr),
               request.form["post"])
        
        return redirect(url_for('render_post', postid=id))

    return render_template("render.html", postid=postid, content=post)


# @app.route("/setnick", methods=("GET", "POST"))
# def setnick():
#     if request.method == 'POST':
#         resp = make_response(render_template("setnicksuccess.html")) 
#         print(request.form["nick"])
#         resp.set_cookie('nick', str(request.form["nick"]))
#         return resp
        
#     return render_template("setnick.html")

@app.route("/register", methods=("GET", "POST"))
def serv_register():
    if request.method == 'POST':
        resp = make_response(render_template("registersuccess.html"))

        username = request.form["username"].strip().lower()

        if not username.isascii():
            return "only ascii pls :3"

        if request.cookies.get("logged_in") == "true":
            return f'you are already logged in as {request.cookies.get("username")}'
        
        for i in db["accounts"]:
            if str(request.form["username"]) == i["username"]:
                return 'could not make account: username already in use'

        if str(username) == "Anonymous":
            return 'you cant do that'

        register(str(request.form["username"]), str(request.form["password"]))
        resp.set_cookie('username', str(username))
        resp.set_cookie('password', str(hashlib.sha512(request.form["password"].encode()).hexdigest()))
        resp.set_cookie('logged_in', "true")
        return resp
    
    return render_template("register.html")

@app.route("/logout", methods=("POST", "GET"))
def logout():
    resp = make_response(render_template("logout.html"))
    resp.set_cookie('username', "")
    resp.set_cookie('password', "")
    resp.set_cookie('logged_in', "false")

    return resp

@app.route("/login", methods=("POST", "GET"))
def login():
    if request.method == 'POST':
        resp = make_response(render_template("loginsuccess.html"))

        if request.cookies.get("logged_in") == "true":
            return f'you are already logged in as {request.cookies.get("username")}'

        if str(request.form["username"]) == "Anonymous":
            return 'you cant do that'

        inp_user = str(request.form["username"])
        inp_passwd = str(hashlib.sha512(request.form["password"].encode()).hexdigest())

        auth = False

        for a in db["accounts"]:
            if a["username"] == inp_user:
                if a["passwd"] == inp_passwd:
                    auth = True

        if not auth:
            return "cannot login: incorrect credentials"
        else:
            resp.set_cookie('username', str(request.form["username"]))
            resp.set_cookie('password', str(hashlib.sha512(request.form["password"].encode()).hexdigest()))
            resp.set_cookie('logged_in', "true")
        return resp

    return render_template("login.html")


app.run(host='0.0.0.0', port=81)
del db["key"]
del db["key"]
del db["key"]
del db["key"]
del db["accounts"]
