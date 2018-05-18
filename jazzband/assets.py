# coding: utf-8
from flask_assets import Environment, Bundle
from webassets.filter import Filter, register_filter


class FixedLibSass(Filter):
    """
    This filter based on Jesús Jerez <jerezmoreno@gmail.com> code [1].

    [1] https://bitbucket.org/jhuss/webassets-libsass

    Converts `Sass <http://sass-lang.com/>`_ markup to real CSS.

    Requires the ``libsass`` package (https://pypi.org/project/libsass/)::

        pip install libsass

    `libsass <http://dahlia.kr/libsass-python>`_ is binding to C/C++
    implementation of a Sass compiler `Libsass
    <https://github.com/hcatlin/libsass>`_

    *Configuration options:*

    LIBSASS_STYLE (style)
        an optional coding style of the compiled result. choose one of:
        `nested` (default), `expanded`, `compact`, `compressed`

    LIBSASS_INCLUDES (includes)
        an optional list of paths to find @imported SASS/CSS source files

    See libsass documentation for full documentation about these configuration
    options:

        http://hongminhee.org/libsass-python/sass.html#sass.compile

    Copied until https://github.com/miracle2k/webassets/pull/435 is fixed.
    """
    name = 'fixedlibsass'
    options = {
        'style': 'LIBSASS_STYLE',
        'includes': 'LIBSASS_INCLUDES',
    }
    max_debug_level = None

    def setup(self):
        super(FixedLibSass, self).setup()

        try:
            import sass
        except ImportError:
            raise EnvironmentError('The "libsass" package is not installed.')
        else:
            self.sass = sass

        if not self.style:
            self.style = 'nested'

    def input(self, _in, out, **kwargs):
        source_path = kwargs['source_path']

        out.write(
            # http://hongminhee.org/libsass-python/sass.html#sass.compile
            self.sass.compile(
                filename=source_path,
                output_style=self.style,
                include_paths=(self.includes if self.includes else []),
            )
        )


register_filter(FixedLibSass)

assets = Environment()

styles = Bundle(
    'scss/styles.scss',
    'octicons/octicons.css',
    filters='fixedlibsass,datauri',
    output='css/styles.%(version)s.css',
    depends=('**/*.scss'),
)

assets.register('styles', styles)
