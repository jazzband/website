from flask import Blueprint

from .decorators import http_cache, templated
from .models import Project

projects = Blueprint('projects', __name__, url_prefix='/projects')


@projects.route('')
@http_cache()
@templated()
def index():
    projects = Project.query.filter_by(is_active=True).order_by(Project.name)
    return {'projects': projects}


@projects.route('/<name>')
@http_cache()
@templated()
def detail(name):
    return {
        'project': Project.query.filter_by(name=name).first_or_404()
    }
