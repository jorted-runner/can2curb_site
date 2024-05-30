class Retrieval:
    def get_user(self, User, data, data_type):
        match data_type:
            case 'email':
                return User.query.filter_by(email=data).first()
            case 'username':
                return User.query.filter_by(username=data).first()
            case 'id':
                return User.query.filter_by(id=data).first()    

    def get_recipe(self, Recipe, data, data_type):
        match data_type:
            case 'id':
                return Recipe.query.filter_by(id=data).first()
            case 'user_recipes':
                return Recipe.query.filter_by(user_id=data).all()
