from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from catalog_setup import Category, Base, Item, User

engine = create_engine('sqlite:///category_id.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

# Menu for Soccer
category1 = Category(user_id=1, name="Soccer")

session.add(category1)
session.commit()

Item2 = Item(user_id=1, name="Shinguards", description="A shin guard or shin pad is a piece of equipment worn on the front of a players shin to protect them from injury",
                    category=category1)

session.add(Item2)
session.commit()


Item1 = Item(user_id=1, name="Shorts", description="Goalkeepers are allowed to wear tracksuit bottoms instead of shorts.",
                    category=category1)

session.add(Item1)
session.commit()

Item3 = Item(user_id=1, name="soccer shoes", description="Get laced up for training and competition with the latest styles and color combinations of men's soccer cleats and shoes.",
                    category=category1)

session.add(Item3)
session.commit()


# Menu for Basketball
category2 = Category(user_id=1, name="Basketball")

session.add(category2)
session.commit()


Item1 = Item(user_id=1, name="Basketball Shoes", description="With your choice of brand",
                    category=category2)

session.add(Item1)
session.commit()

Item2 = Item(user_id=1, name="Backboards",
                    description="It is a raised vertical board with an attached basket consisting of a net suspended from a hoop. ", category=category2)

session.add(Item2)
session.commit()

Item3 = Item(user_id=1, name="sleeve", description="A basketball sleeve, like the wristband, is an accessory that some basketball players wear.",
                    category=category2)

session.add(Item3)
session.commit()



# Menu for Hockey
category3 = Category(user_id=1, name="Hockey")

session.add(category3)
session.commit()


Item1 = Item(user_id=1, name="Shin Pads", description="Block that point shot with confidence with Hockey Shin Guards",
                    category=category3)

session.add(Item1)
session.commit()

Item2 = Item(user_id=1, name="Hockey Stick", description=" In field hockey, each player carries a stick and cannot take part in the game without it. ",
                    category=category3)

session.add(Item2)
session.commit()

Item3 =Item(user_id=1, name="Hockey Pants", description="Warrior Covert QRL Junior Ice Hockey Pants",
                    category=category3)

session.add(Item3)
session.commit()



# Menu for Frisbe
category1 = Category(user_id=1, name="Frisbee ")

session.add(category1)
session.commit()


Item1 = Item(user_id=1, name="Frisbee", description="is a gliding toy or sporting item that is generally plastic and roughly 8 to 10 inches (20 to 25 cm) in diameter with a pronounced lip. It is used recreationally and competitively for throwing and catching, as in flying disc games.",
                    category=category1)

session.add(Item1)
session.commit()



# Menu for Skating
category1 = Category(user_id=1, name="Skating ")

session.add(category1)
session.commit()


Item1 = Item(user_id=1, name="Skating board", description="Skaters who regularly ride in the street, skateparks and half-pipes.",
                    category=category1)

session.add(Item1)
session.commit()




print "added menu items!"