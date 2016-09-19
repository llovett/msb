from pymodm import MongoModel, fields, connect

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
    # TODO: some way of specifying 'unique'?
    handle = fields.CharField(required=True)
    password = fields.CharField(required=True)

    @classmethod
    def valid_user(cls, email, password):
        """Return the user with the given email/password or None."""
        password = salted_hash(password)
        try:
            return cls.objects.get({'_id': email, 'password': password})
        except User.DoesNotExist:
            return None


class Comment(MongoModel, JSONAble):
    export_fields = ('date', 'body', 'author')

    author = fields.EmailField(required=True)
    date = fields.DateTimeField(required=True)
    body = fields.CharField(required=True)


class Post(MongoModel, JSONAble):
    export_fields = (
        'id', 'date', 'title', 'body', 'summary', 'active', 'author_handle')

    title = fields.CharField(required=True)
    body = fields.CharField(required=True)
    summary = fields.CharField(required=True)
    date = fields.DateTimeField(required=True)
    author = fields.ReferenceField(User, required=True)
    # Is this Post published?
    active = fields.BooleanField(default=False)

    @property
    def author_handle(self):
        return self.author.handle

    @property
    def id(self):
        return str(self.pk)
