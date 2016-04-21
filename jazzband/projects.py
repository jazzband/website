from flask import Blueprint

from .decorators import templated
from .models import Project

projects = Blueprint('projects', __name__, url_prefix='/projects')


@projects.route('')
@templated()
def index():
    projects = Project.query.filter_by(is_active=True).order_by(Project.name)
    return {'projects': projects}


@projects.route('/<name>')
@templated()
def detail(name):
    return {
        'project': Project.query.filter_by(name=name).first_or_404()
    }
