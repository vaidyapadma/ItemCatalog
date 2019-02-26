catalog project .
Install Vagrant and VirtualBox
Launch Vagrant VM(i.e vagrant up)
First write datastructure for Category table and Item Table as in catalog_setup.py
Write file to add data to tables as in catlog.py
Store these files in folder catalog.
Hence forth store all the files related to this project in catalog folder.
Then write application file catalog.py to develop the app.
1.To show all the categories and recent items to the user :
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
  which will show result as :

      


