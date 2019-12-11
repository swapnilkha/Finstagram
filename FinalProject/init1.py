 #Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib
import time


#Initialize the app from Flask
app = Flask(__name__, static_folder="static")

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 8889, # change
                       user='root',
                       password='root', # change
                       db='FinalProject', # change
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']
    hashed_password = hashlib.sha256(password.encode("utf-8")).hexdigest()
    #print(hashed_password)
    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'
    cursor.execute(query, (username, password))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']
    f_name = request.form['firstName']
    l_name = request.form['lastName']
    password_hashed = hashlib.sha256(password.encode("utf-8")).hexdigest()
    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO Person(username, password, firstName, lastName) VALUES(%s, %s, %s, %s)'
        cursor.execute(ins, (username, password_hashed, f_name, l_name))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    user = session['username']
    cursor = conn.cursor();

    query = 'SELECT photoID, photoPoster, postingdate, filepath FROM Photo WHERE photoPoster IN \
    (SELECT username_followed FROM Follow WHERE username_follower = %s AND \
    followstatus = true) AND allFollowers = true OR photoPoster IN \
        (SELECT owner_username FROM BelongTo WHERE member_username = %s) ORDER BY \
        postingdate DESC'

    get_tagged = 'SELECT photoID, username, firstName, lastName FROM Photo NATURAL JOIN Tagged \
    NATURAL JOIN Person WHERE photoPoster IN \
    (SELECT username_followed FROM Follow WHERE username_follower = %s AND \
    followstatus = true) AND allFollowers = true OR photoPoster IN \
        (SELECT owner_username FROM BelongTo WHERE member_username = %s) ORDER BY \
        postingdate DESC'

    get_likes = 'SELECT photoID, username, rating FROM Photo NATURAL JOIN Likes \
    NATURAL JOIN Person WHERE photoPoster IN \
    (SELECT username_followed FROM Follow WHERE username_follower = %s AND \
    followstatus = true) AND allFollowers = true OR photoPoster IN \
        (SELECT owner_username FROM BelongTo WHERE member_username = %s) ORDER BY \
        postingdate DESC'

    getgr = 'SELECT groupName FROM Friendgroup WHERE groupOwner = %s'

    cursor.execute(query, (user, user))
    data = cursor.fetchall()
    cursor.execute(getgr, (user))
    groups = cursor.fetchall() 
    cursor.execute(get_tagged, (user, user))
    tagged_people = cursor.fetchall()
    cursor.execute(get_likes, (user, user))
    liked_users = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=user, posts=data, grps=groups, tagged=tagged_people, likes=liked_users)

        
@app.route('/post', methods=['GET', 'POST'])
def post():
    username = session['username']
    cursor = conn.cursor();
    photo_ID = request.form['photoID']
    timestamp = str(time.strftime('%Y-%m-%d %H:%M:%S'))
    caption = request.form['caption']
    fp = request.form['filepath']
    public_bool = int(request.form['public'])
    group_name = request.form.getlist('groupname')

    query = 'INSERT INTO Photo VALUES(%s, %s, %s, %s, %s, %s)'
    query_shared = 'INSERT INTO SharedWith VALUES(%s, %s, %s)'
    cursor.execute(query, (photo_ID, timestamp, fp, public_bool, caption, username))

    if len(group_name) > 0: 
        for group in group_name:
            cursor.execute(query_shared, (username, group, photo_ID))
    
    group_insert = request.form['groupinsert']
    group_desc = request.form['groupdesc']
    insert_fg_query = 'INSERT INTO Friendgroup VALUES(%s, %s, %s)'
    cursor.execute(insert_fg_query, (username, group_insert, group_desc))

    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

# search by poster method - Dipto
@app.route('/select_blogger', methods = ['GET', 'POST'])
def select_blogger():
    username = session['username'];
    poster = request.form['poster'];
    cursor = conn.cursor();
    query = 'SELECT photoID, photoPoster, postingdate FROM Photo WHERE photoPoster IN \
    (SELECT username_followed FROM Follow WHERE username_follower = %s AND \
    followstatus = true) AND allFollowers = true AND photoPoster = %s OR photoPoster IN \
        (SELECT owner_username FROM BelongTo WHERE member_username = %s) AND photoposter = %s ORDER BY \
        postingdate DESC'
    #query = 'SELECT DISTINCT username FROM blog'
    cursor.execute(query, (username, poster, username, poster));
    data = cursor.fetchall()
    cursor.close()
    return render_template('select_blogger.html', posts=data)
   
# search by tag method - Dipto
@app.route('/select_tag', methods = ['GET', 'POST'])
def select_tag():
    username = session['username']
    tag = request.form['tag']
    cursor = conn.cursor()
    query = 'SELECT photoID, photoPoster, postingdate FROM Photo WHERE photoPoster IN \
    ((SELECT username_followed FROM Follow WHERE username_follower = %s AND \
    followstatus = true) AND allFollowers = true OR photoPoster IN \
    (SELECT owner_username FROM BelongTo WHERE member_username = %s)) \
    AND photoID IN (SELECT photoID FROM tagged WHERE username = %s AND tagstatus = 1) ORDER BY \
    postingdate DESC'
    cursor.execute(query, (username, username, tag))
    data = cursor.fetchall()
    cursor.close()
    return render_template('select_tag.html', posts=data)
@app.route('/addfriendgroup', methods=["GET", "POST"])
def addfriendgroup():
    cursor = conn.cursor();
    username = session['username']
    group_insert = request.form['groupinsert']
    group_desc = request.form['groupdesc']

    check_exists = 'SELECT groupOwner, groupName FROM Friendgroup WHERE groupOwner = %s AND groupName = %s'
    cursor.execute(check_exists, (username, group_insert))
    check_exists_data = cursor.fetchone()
    if check_exists_data:
        error = "You have already created a group with this name"
        cursor.close()
        return render_template('addfriendgroup.html')
    else:
        insert_fg_query = 'INSERT INTO Friendgroup VALUES(%s, %s, %s)'
        cursor.execute(insert_fg_query, (username, group_insert, group_desc))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))

@app.route('/addfriend', methods=["GET", "POST"])
def addfriend():
    cursor = conn.cursor();
    username = session['username']
    friend_username = request.form['friend']
    group_names = request.form.getlist('groupname')


    check_exists = 'SELECT member_username, groupName FROM BelongTo WHERE member_username = %s AND groupName = %s'
    for grp in group_names:
        cursor.execute(check_exists, (friend_username, grp))
    check_exists_data = cursor.fetchone()
    if check_exists_data:
        error = "You have already have a friend in one of these groups"
        cursor.close()
        return render_template('addfriend.html')
    else:
        for grp in group_names:
            insert_fg_query = 'INSERT INTO BelongTo VALUES(%s, %s, %s)'
            cursor.execute(insert_fg_query, (friend_username, username, grp))
            conn.commit()
        cursor.close()
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
  
@app.route('/requestFollow', methods=['GET', 'POST'])
def requestFollow():
    username = session['username']
    follow = request.form['follow']
    cursor = conn.cursor()
    query = 'INSERT INTO follow(username_followed, username_follower, \
            followstatus) VALUES(%s, %s, %s)'
    cursor.execute(query, (follow, username, "0"))
    cursor.close()
    return redirect(url_for('home'))
    
            

@app.route('/editFollow', methods=['GET', 'POST'])
def editFollow():
    username = session['username']
    follower = request.form['follower']
    choice = request.form['choice']
    if choice == 'accept':
        cursor = conn.cursor()
        query = 'UPDATE follow SET followstatus = %s \
                where username_followed = %s AND \
                username_follower = %s'
        cursor.execute(query, ("1", username, follower))
        query = 'SELECT username_follower FROM follow WHERE \
                username_followed = %s AND followstatus = %s\
                GROUP BY username_follower'
        cursor.execute(query, (username, '0'))
        data = cursor.fetchall()
        cursor.close()
        return render_template('show_follows.html', lst = data)
    elif choice == 'reject':
        cursor = conn.cursor()
        query = "DELETE FROM follow WHERE username_followed = %s AND \
                username_follower = %s AND followstatus = %s"
        cursor.execute(query, (username, follower, "0"))
        query = 'SELECT username_follower FROM follow WHERE \
                username_followed = %s AND followstatus = %s\
                GROUP BY username_follower'
        cursor.execute(query, (username, '0'))
        data = cursor.fetchall()
        cursor.close()
        return render_template('show_follows.html', lst = data)

@app.route('/listFollow', methods=['GET', 'POST'])
def listFollow():
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT username_follower FROM follow WHERE \
                username_followed = %s AND followstatus = %s\
                GROUP BY username_follower'
    cursor.execute(query, (username, '0'))
    data = cursor.fetchall()
    cursor.close()
    return render_template('show_follows.html', lst = data)
        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = False)


