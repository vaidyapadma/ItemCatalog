from flask import Flask, render_template , request , redirect , jsonify , url_for , flash
app = Flask(__name__)

from sqlalchemy import create_engine , asc , desc , func
from sqlalchemy.orm import sessionmaker , joinedload
from catalog_setup import Base, Category , Item , User
from pprint import pprint
 
 
# New imports for login session
from flask import session as login_session
import random, string
# IMPORTS FOR THIS STEP
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"




# Connect to Database and create database session
engine = create_engine('sqlite:///category_id.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# create login session


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase  + string.digits) for x in xrange(32) )
    login_session['state'] = state
    return render_template('login.html', STATE=state)
    #return "The current login session is %s" %login_session['state']

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code, now compatible with Python3
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


#JSON APIs to view Catalog Information

def getCatalog():
    categories = session.query(Category).options(joinedload(Category.items)).all()
    return dict(Catalog=[dict(c.serialize, items=[i.serialize
                                                     for i in c.items])
                         for c in categories])


@app.route('/catalog/JSON')
def catalogtMenuJSON():
    return jsonify(getCatalog())


@app.route('/catalog/<int:catagory_id>/menu/JSON')
def catalogcatid(catagory_id):
    catagory = session.query(Category).filter_by(id=catagory_id).one()
    items = session.query(Item).filter_by(category_name = catagory.name).all()
    return jsonify(Item=[i.serialize for i in items])   


@app.route('/catalog/<int:catagory_id>/menu/<int:item_id>/JSON')
def catalogitemid(catagory_id,item_id):
    catagory = session.query(Category).filter_by(id = catagory_id).one()
    items = session.query(Item).filter_by(id = item_id).one()
    return jsonify(Item = items.serialize) 


#Show all Catagories
@app.route('/')
@app.route('/catalog/')
def showCatalog():
  catagory = session.query(Category).order_by(asc(Category.name))
  items =session.query(Item).order_by(desc(Item.id)).limit(5)
  if 'username' not in login_session:
      return render_template('publiccatalog.html', catagory = catagory , items=items)

  else:
      return render_template('catalog.html', catagory = catagory , items=items)


#Show  Catagories
@app.route('/catalog/<string:catagory_name>/',methods=['GET','POST'])
@app.route('/catalog/<string:catagory_name>/items/',methods=['GET','POST'])
def showMenu(catagory_name):
    
    catagory = session.query(Category).order_by(asc(Category.name))
    cat = session.query(Category).filter_by(name = catagory_name).one()
    items = session.query(Item).filter_by(category_id = cat.id)
    rows = session.query(func.count(Item.id)).filter_by(category_id = cat.id).scalar()
    print rows
    
    if request.method == 'POST':

        return render_template('menu.html',items = items, catagory = catagory)
    else:

        return render_template('menu.html', items = items,catagory = catagory,rows = rows,catagory_name=catagory_name)


#Show Item Description
@app.route('/catalog/<string:catagory_name>/<string:item_name>',methods=['GET','POST'])
def showItem(catagory_name,item_name):
    items = session.query(Item).filter_by(name = item_name)
    if 'username' not in login_session:

       if request.method == 'POST':
           return render_template('showItem.html',items = items)


        
       else:
           return render_template('showItem.html', items = items)
    
    else:
        return render_template('editdelete.html', items = items)

#Create a new  item
@app.route('/catalog/new/',methods=['GET','POST'])
def newItem():
  catagory = session.query(Category).order_by(asc(Category.name))
  items =session.query(Item).order_by(desc(Item.id)).limit(5)
  user = session.query(User).filter_by(email=login_session['email']).one()
             
  if 'username' not in login_session:
      return  render_template('publiccatalog.html', catagory = catagory,items=items)
  else:
        if request.method == 'POST':
            catg = session.query(Category).filter_by(name = request.form['cat']).one()
            newItem = Item(name = request.form['name'] , description = request.form['des'] , category_id = catg.id , user_id = user.id)
            # newItem = Item(name = request.form['name'] , description = request.form['des'] , category_name = request.form['cat'])
            session.add(newItem)
            session.commit()
            flash('New Menu %s Item Successfully Created' % (newItem.name))
            return redirect(url_for('showMenu', catagory_name = request.form['cat']))

      
        else:

            return render_template('additem.html',catagory=catagory)

#Edit a menu item
@app.route('/catalog/<string:item_name>/edit', methods=['GET','POST'])
def editItem(item_name):
    catagory = session.query(Category).order_by(asc(Category.name))
    items =session.query(Item).order_by(desc(Item.id)).limit(5)
    itemcat= session.query(Item).filter_by(name=item_name).one()
    cat = session.query(Category).filter_by(id=itemcat.category_id).one()
    user = session.query(User).filter_by(email=login_session['email']).one()
    if 'username' not in login_session:

        return  render_template('publiccatalog.html', catagory = catagory,items=items)
    else:

        editedItem = session.query(Item).filter_by(name = item_name).one()
        if editedItem.user_id != user.id:
            flash("You don't have permission to edit this item")
            return render_template('catalog.html', catagory = catagory,items=items)
        else:
            if request.method == 'POST':


                if request.form['name']:
                    editedItem.name = request.form['name']
                     
                if request.form['description']:
                    editedItem.description = request.form['description']
                    session.add(editedItem)
                    session.commit() 
                    flash(' Item Successfully Edited')
                    return redirect(url_for('showMenu', catagory_name = cat.name))
   
            else:

                return render_template('edititem.html',  item = editedItem)

          



#Delete a menu item
@app.route('/catalog/<string:item_name>/delete', methods = ['GET','POST'])
def deleteItem(item_name):
    catagory = session.query(Category).order_by(asc(Category.name))
    items =session.query(Item).order_by(desc(Item.id)).limit(5)
    user = session.query(User).filter_by(email=login_session['email']).one()

    if 'username' not in login_session:

        return  render_template('publiccatalog.html', catagory = catagory,items=items)
    else:
    
        itemToDelete = session.query(Item).filter_by(name = item_name).one() 
        cat = session.query(Category).filter_by(id = itemToDelete.category_id).one()
        if request.method == 'POST':
        
            session.delete(itemToDelete)
            session.commit()
            flash('Menu Item Successfully Deleted')
            return redirect(url_for('showMenu', catagory_name = cat.name))
       
        else:
            return render_template('deleteitem.html', item = itemToDelete)
       

# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        
            del login_session['username']
            del login_session['email']
            del login_session['picture']
        
            del login_session['provider']
            flash("You have successfully been logged out.")
            return redirect(url_for('showCatalog'))
    else:
        flash("You were not logged in")
        del login_session['username']
        
        del login_session['gplus_id']
        del login_session['access_token']
        del login_session['email']
        del login_session['picture']
        return redirect(url_for('showCatalog'))





if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000)
