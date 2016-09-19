"""MSB API."""

import functools
import os

from bson.objectid import ObjectId
from flask import Flask, jsonify, request, session, make_response
from pymodm.errors import ValidationError

from common import pluralize
from models import User, Post, Comment


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


def add_response_headers(headers={}):
    """This decorator adds the headers passed in to the response"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            resp = make_response(f(*args, **kwargs))
            h = resp.headers
            for header, value in headers.items():
                h[header] = value
            return resp
        return decorated_function
    return decorator


def links_for_model(model):
    """Get a list of all valid endpoints relating to the given Model."""
    model_name = model.__name__
    model_example = {
        field.attname: '<{}>'.format(field.attname.upper())
        for field in model._mongometa.get_fields()
    }
    first_example_key = next(iter(model_example))
    update_example = {"$set": {first_example_key: '<{}>'.format(
        first_example_key.upper())}}
    id_path = '/<{}_id>'.format(model_name.lower())
    plural_name = pluralize(model_name.lower())
    endpoint_specs = (
        # endpoint or None, method, description, example payload or None
        (
            None,
            'GET',
            'Get a listing of all {} objects.'.format(model_name),
            None
        ),
        (
            None,
            'POST',
            'Create a new {} object.'.format(model_name),
            model_example
        ),
        (
            id_path,
            'GET',
            'Retrieve the specified {} object.'.format(model_name),
            None
        ),
        (
            id_path,
            'POST',
            ('Update the specified {} object '
             'with a MongoDB query document.').format(model_name),
            update_example
        ),
        (
            id_path,
            'DELETE',
            'Delete the specified {} object.'.format(model_name),
            None
        )
    )
    endpoints = []
    for path, method, desc, example in endpoint_specs:
        link = {
            'endpoint': '/v1/{}{}'.format(plural_name, path or ''),
            'method': method,
            'description': desc
        }
        if example is not None:
            link['example'] = example
        endpoints.append(link)
    return endpoints


def create(model):
    @add_response_headers({'Access-Control-Allow-Origin': '*'})
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
    @add_response_headers({'Access-Control-Allow-Origin': '*'})
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
    @add_response_headers({'Access-Control-Allow-Origin': '*'})
    def read_instance(instance_id):
        try:
            return jsonify(
                model.objects.get({'_id': ObjectId(instance_id)}).as_json())
        except model.DoesNotExist:
            return jsonify({'errors': ['No {} object with id {}'.format(
                model.__name__.lower(), instance_id)]}), 404
    return read_instance


def read_many(model):
    @add_response_headers({'Access-Control-Allow-Origin': '*'})
    def read_all():
        all_objects = [inst.as_json() for inst in model.objects.all()]
        return jsonify({pluralize(model.__name__.lower()): all_objects})
    return read_all


def destroy(model):
    @add_response_headers({'Access-Control-Allow-Origin': '*'})
    @login_required
    def destroy_instance(instance_id):
        deleted = model.objects.raw({'_id': instance_id}).delete()
        return jsonify({'deleted': deleted}), 200 if deleted else 404
    return destroy_instance


@add_response_headers({'Access-Control-Allow-Origin': '*'})
def stupid():
    return ''


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
    app.add_url_rule('/v1/' + model_name, endpoint='stupid-' + model_name,
                     view_func=stupid,
                     methods=['HEAD', 'OPTIONS'])


# Other routes.
@app.route('/v1/users/login', methods=['POST'])
@add_response_headers({'Access-Control-Allow-Origin': '*'})
def login_api():
    user_data = request.get_json(force=True)
    logged_in = User.valid_user(user_data['email'], user_data['password'])
    if logged_in:
        user_json = logged_in.as_json()
        session['user'] = user_json
        return jsonify(user_json)
    return jsonify({'errors': ['Bad email/password.']}), 400


@app.route('/v1')
@add_response_headers({'Access-Control-Allow-Origin': '*'})
def index_api():
    all_links = (
        links_for_model(Post) +
        links_for_model(Comment) +
        links_for_model(User)
    )
    # Add miscellaneous links.
    all_links.extend([
        {
            'endpoint': '/v1/users/login',
            'method': 'POST',
            'description': (
                'Request a session cookie to use for future requests that '
                'require authorization.'
            )
        },
        {
            'endpoint': '/v1',
            'method': '<any>',
            'description': 'Retrieve a listing of available API endpoints.'
        }
    ])

    return jsonify({
        'service': 'MSB is My Sweet Blog.',
        'version': 'v1',
        'links': all_links
    })


def main():
    app.run(host='0.0.0.0', debug=True)


if __name__ == '__main__':
    main()
