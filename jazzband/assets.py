# coding: utf-8
from flask_assets import Bundle, Environment

assets = Environment()

styles = Bundle(
    "scss/styles.scss",
    "../../node_modules/@fortawesome/fontawesome-free/css/all.css",
    filters="libsass,datauri",
    output="css/styles.%(version)s.css",
    depends=("**/*.scss"),
)

assets.register("styles", styles)
