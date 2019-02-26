from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
app = Flask(__name__)

from sqlalchemy import create_engine, asc,desc,func
from sqlalchemy.orm import sessionmaker,joinedload
from catalog_setup import Base, Category,Item ,User
from pprint import pprint

#New imports for login session
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




#Connect to Database and create database session
engine = create_engine('sqlite:///category.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()



#create login session

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase  + string.digits) for x in xrange(32) )
    login_session['state'] = state
    return render_template('login.html',STATE=state)
    #return "The current login session is %s" %login_session['state']

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token


    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]


    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server token exchange we have to
        split the token first on commas and select the first index which gives us the key : value
        for the server access token then we split it on colons to pull out the actual token value
        and replace the remaining quotes with nothing so that it can be used directly in the graph
        api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
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

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

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
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
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
        print "Token's client ID does not match app's."
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
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'


    # see if user already exists in DB

    user_id = getUserId(login_session['email'])
    if not user_id :
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
    print "done!"
    return output

def createUser(login_session):
    newUser = User(name = login_session['username'],email = login_session['email'],picture = login_session['picture'] )
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUserId(email):
    try:
        user = session.query(User).filter_by(email = email).one()
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
"""  def catalogtMenuJSON():
    catalog = session.query(Item).order_by(Item.category_name)

    return jsonify(catalog= [r.serialize for r in catalog])
    # return dict(Catalog=[dict(c.serialize,items=[i.serialize for i in c.items]) for c in catalog])


@app.route('/catalog/<string:catalog_name>/menu/<string:item_name>/JSON')
def menuItemJSON(catalog_id, item_id):
    Menu_Item = session.query(Item).filter_by(id = item_id).one()
    return jsonify(Item = Item.serialize)

@app.route('/restaurant/JSON')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(restaurants= [r.serialize for r in restaurants])
"""

#Show all Catagories
@app.route('/')
@app.route('/catalog/')
def showCatalog():

  catagory = session.query(Category).order_by(asc(Category.name))
  items =session.query(Item).order_by(desc(Item.id)).limit(5)
  if 'username' not in login_session:
      return render_template('publiccatalog.html', catagory = catagory,items=items)

  else:
      return render_template('catalog.html', catagory = catagory,items=items)

""" 
  
#Create a new Catagory
@app.route('/catalog/new/', methods=['GET','POST'])
def newCatagory():
    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
      newCatagory = Category(name = request.form['name'],user_id = login_session['user_id'])
      

      session.add(newCatagory )
      flash('New Catagory %s Successfully Created' % newCatagory.name)
      session.commit()
      return redirect(url_for('showCatalog'))
    else:
      return render_template('newCatalog.html')
 
#Edit a Catagory
@app.route('/catalog/<string:catagory_name>/edit/', methods = ['GET', 'POST'])
def editCatagory(catagory_name):
  editedCatagory = session.query(Catagory).filter_by(name = catagory_name).one()
  if request.method == 'POST':
      if request.form['name']:
        editedCatagory.name = request.form['name']
        flash('Catagory Successfully Edited %s' % editedCatagory.name)
        return redirect(url_for('showCatalog'))
  else:
    return render_template('editCatalog.html', restaurant = editedCatagory)


#Delete a Catagory
@app.route('/catalog/<string:catagory_name>/delete/', methods = ['GET','POST'])
def deleteRestaurant(catagory_name):
  catagoryToDelete = session.query(Catagory).filter_by(name = catagory_name).one()
  if request.method == 'POST':
    session.delete(catagoryToDelete)
    flash('%s Successfully Deleted' % catagoryToDelete.name)
    session.commit()
    return redirect(url_for('showCatalog', catagory_name = catagory_name))
  else:
    return render_template('deleteCatagory.html',catagory = catagoryToDelete)
"""
#Show  Catagories
@app.route('/catalog/<string:catagory_name>/',methods=['GET','POST'])
@app.route('/catalog/<string:catagory_name>/items/',methods=['GET','POST'])
def showMenu(catagory_name):
    print catagory_name
    catagory = session.query(Category).order_by(asc(Category.name))
    items = session.query(Item).filter_by(category_name = catagory_name)
    rows = session.query(func.count(Item.id)).filter_by(category_name = catagory_name).scalar()
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
  if request.method == 'POST':
      newItem = Item(name = request.form['name'], description = request.form['des'], category_name = request.form['cat'])
      session.add(newItem)
      session.commit()
      flash('New Menu %s Item Successfully Created' % (newItem.name))
      return redirect(url_for('showMenu', catagory_name = request.form['cat']))
  else:
      return render_template('additem.html',catagory=catagory)

#Edit a menu item
@app.route('/catalog/<string:item_name>/edit', methods=['GET','POST'])
def editItem(item_name):

    
    
    editedItem = session.query(Item).filter_by(name = item_name).one()
    print editedItem.name
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
            

        
        session.add(editedItem)
        session.commit() 
        flash(' Item Successfully Edited')
        return redirect(url_for('showMenu', catagory_name = request.form['cat']))
    else:
        return render_template('edititem.html',  item = editedItem)


#Delete a menu item
@app.route('/catalog/<string:item_name>/delete', methods = ['GET','POST'])
def deleteItem(item_name):
    
    itemToDelete = session.query(Item).filter_by(name = item_name).one() 
    catagory = session.query(Category).filter_by(name = itemToDelete.category_name).one()
    

    if request.method == 'POST':
        
        session.delete(itemToDelete)
        session.commit()
        flash('Menu Item Successfully Deleted')
        return redirect(url_for('showMenu', catagory_name = catagory.name))

        
        
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
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCatalog'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCatalog'))




if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000)
