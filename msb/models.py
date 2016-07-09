from pymongo_odm import MongoModel, fields, connect

from common import salted_hash


# Establish a connection to the database.
connect('mongodb://localhost:27017/msb')


class JSONAble(object):
    export_fields = []

    def as_json(self):
        if not self.export_fields:
            return self.__dict__
        return {field: getattr(self, field) for field in self.export_fields}


class User(MongoModel, JSONAble):
    export_fields = ('email', 'handle')

    email = fields.EmailField(primary_key=True)
    handle = fields.CharField()  # TODO: some way of specifying 'unique'?
    password = fields.CharField()

    @classmethod
    def valid_user(cls, email, password):
        """Return the user with the given email/password or None."""
        password = salted_hash(password)
        try:
            return cls.objects.get({'_id': email, 'password': password})
        except User.DoesNotExist:
            return None


class Comment(MongoModel, JSONAble):
    export_fields = ('date', 'body')

    date = fields.DateTimeField()
    body = fields.CharField()


class Post(MongoModel, JSONAble):
    export_fields = ('date', 'title', 'body', 'author_handle')

    title = fields.CharField()
    body = fields.CharField()
    date = fields.DateTimeField()
    author = fields.ReferenceField(User)

    @property
    def author_handle(self):
        return self.author.handle
