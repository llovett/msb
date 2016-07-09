"""MSB API."""

import functools
import os

from flask import Flask, jsonify, request, session
from pymongo_odm.errors import ValidationError

from common import pluralize
from models import User, Post


# Secret key used to encrypt session cookies.
SECRET_KEY = os.getenv('MSB_SECRET_KEY')


app = Flask(__name__)
app.secret_key = SECRET_KEY


def login_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'errors': ['Must be logged in.']}), 401
        return func(*args, **kwargs)
    return wrapper


def create(model):
    @login_required
    def create_instance():
        try:
            data = request.get_json(force=True)
            # Add the current user.
            if hasattr(model, 'author'):
                data['author'] = session['user']['email']
            return jsonify(model.objects.create(**data).as_json())
        except ValidationError as exc:
            return jsonify({'errors': exc.message}), 400
    return create_instance


def update(model):
    @login_required
    def update_instance(instance_id):
        try:
            data = request.get_json(force=True)
            model.objects.update({'_id': instance_id}, **data)
        except Exception as exc:
            return jsonify({'errors': [str(exc)]}), 400
        return jsonify({'ok': True})
    return update_instance


def read(model):
    def read_instance(instance_id):
        try:
            return model.objects.get(pk=instance_id).as_json()
        except model.DoesNotExist:
            return jsonify({'errors': ['No {} object with id {}'.format(
                model.__name__.lower(), instance_id)]}), 404
    return read_instance


def read_many(model):
    def read_all():
        all_objects = [inst.as_json() for inst in model.objects.all()]
        return jsonify({pluralize(model.__name__.lower()): all_objects})
    return read_all


def destroy(model):
    @login_required
    def destroy_instance(instance_id):
        deleted = model.objects.raw({'_id': instance_id}).delete()
        return jsonify({'deleted': deleted}), 200 if deleted else 404
    return destroy_instance


# Model-related routes.
for model in (User, Post):
    model_name = pluralize(model.__name__.lower())
    app.add_url_rule('/v1/' + model_name,
                     endpoint='read-many-{}'.format(model_name),
                     view_func=read_many(model),
                     methods=['GET']),
    app.add_url_rule('/v1/' + model_name + '/<instance_id>',
                     endpoint='read={}'.format(model_name),
                     view_func=read(model),
                     methods=['GET']),
    app.add_url_rule('/v1/' + model_name + '/<instance_id>',
                     endpoint='delete={}'.format(model_name),
                     view_func=destroy(model),
                     methods=['DELETE']),
    app.add_url_rule('/v1/' + model_name + '/<instance_id>',
                     endpoint='update-{}'.format(model_name),
                     view_func=update(model),
                     methods=['POST']),
    app.add_url_rule('/v1/' + model_name,
                     endpoint='create-{}'.format(model_name),
                     view_func=create(model),
                     methods=['POST'])


# Other routes.
@app.route('/v1/users/login', methods=['POST'])
def login_api():
    user_data = request.get_json(force=True)
    logged_in = User.valid_user(user_data['email'], user_data['password'])
    if logged_in:
        user_json = logged_in.as_json()
        session['user'] = user_json
        return jsonify(user_json)
    return jsonify({'errors': ['Bad email/password.']}), 400


def main():
    app.run(debug=True)


if __name__ == '__main__':
    main()
