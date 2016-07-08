from pymongo_odm import MongoModel, fields, connect

from common import salted_hash


# Establish a connection to the database.
connect('mongodb://localhost:27017/msb')


class User(MongoModel):
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

    def as_dict(self):
        """Get this User as a dict that can be sent client-side."""
        export_fields = ('email', 'handle')
        return {field: getattr(self, field) for field in export_fields}


class Comment(MongoModel):
    date = fields.DateTimeField()
    body = fields.CharField()


class Post(MongoModel):
    title = fields.CharField()
    body = fields.CharField()
    date = fields.DateTimeField()
    author = fields.ReferenceField(User)
