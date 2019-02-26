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
  which will show result as in folder output_files/localhost.htm


2.To show all items in the perticular category:
Click on the perticular category and you will get all the items of that category as in output_files/localhost2.htm


3.To get details of item click on the perticular item and reult wil be as in:
output_files/Basketball Shoes.htm

4.Login to App using google api using gmail sign in.I am using Restuarant Menu App from my gmail account to have access to app.Agetr clickin "click here to sign in" will land to page as in output_files/login.htm

5.After login you will land into a page which shows all categories and Latest item with add item button as in output_files/localhostlogin.htm

6.After clicking on add item button you will land into page which dispalys form to add item with name, description ,category as in output_files/localhostadd.htm

7.After clicking submit button you will land into pagee which displays Categories and Items of perticular categories along with newly added item as shown in output_files/localhostaddeditem.htm(http://localhost:5000/catalog/Hockey/items/)

8.If you click on any item you will land into page which shows description of the item along with edit|delete link as shown in output_files/Shin Pads.htm(http://localhost:5000/catalog/Hockey/Shin%20Pads)

9.If you press edit hyperlink you will land into page which shows details of item in which you can edit the description, name of item as shown in output_files/edit.htm(http://localhost:5000/catalog/Shin%20Pads/edit)

10.After pressing Save button You will land to page which shows list of categories and items of category which was edited as shown in output_files/localhostedited.htm(http://localhost:5000/catalog/Hockey/items/)

11.After pressing delete hyperlink for item description will take to page which confirms whether user want to delete item or not as shown in output_files/delete.htm(http://localhost:5000/catalog/Shin%20Pads/delete)

12.After pressing delete it will land to page with Categories and items of perticular which shows item being deletd as shown in output_files/localhostdeleted.htm(http://localhost:5000/catalog/Hockey/items/)

13.After pressing logout button attop right you will land in to page shows catalogof itemsas ashown in output_files/localhostloggedout.htm(http://localhost:5000/catalog/Hockey/items/)




  


      


