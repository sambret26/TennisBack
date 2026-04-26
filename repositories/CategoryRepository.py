from models.Category import Category
from database import db

class CategoryRepository:

    #GETTERS
    @staticmethod
    def getAllCategories():
        return Category.query.all()

    @staticmethod
    def getCategoriesMap():
        return {c.fftId: c for c in Category.query.all()}

    #ADDERS
    @staticmethod
    def addCategories(categories):
        db.session.add_all(categories)
        db.session.commit()

    #DELETERS
    @staticmethod
    def deleteAllCategories():
        Category.query.delete()
        db.session.commit()