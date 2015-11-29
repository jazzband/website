from flask.ext.assets import Environment, Bundle

assets = Environment()

assets.register(
    'styles',
    Bundle(
        'scss/styles.scss',
        'octicons/octicons.css',
        filters='libsass,datauri',
        output='css/styles.%(version)s.css',
        depends=('**/*.scss'),
    )
)
