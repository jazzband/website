import redis
from spinach.contrib.flask_spinach import Spinach
from spinach.brokers.redis import recommended_socket_opts, RedisBroker

from .members.tasks import tasks as member_tasks
from .projects.tasks import tasks as project_tasks


class JazzbandSpinach(Spinach):

    def init_app(self, app):
        app.config['SPINACH_BROKER'] = RedisBroker(
            redis.from_url(
                app.config['QUEUE_URL'],
                **recommended_socket_opts
            )
        )
        super().init_app(app)
        for tasks in [member_tasks, project_tasks]:
            self.register_tasks(app, tasks)


spinach = JazzbandSpinach()
