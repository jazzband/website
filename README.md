This app renders https://jazzband.co.

[![Jazzband](https://jazzband.co/static/img/badge.svg)](https://jazzband.co/)
[![GitHub CI status](https://github.com/jazzband-roadies/website/workflows/Deploy/badge.svg)](https://github.com/jazzband-roadies/website)
[![Dependabot Status](https://api.dependabot.com/badges/status?host=github&repo=jazzband-roadies/website)](https://dependabot.com)
[![Calver](https://img.shields.io/badge/calver-YY.MM.PATCH-22bfda.svg)](https://calver.org/)

## Installation

Copy `.end-dist` to `.env`.

Install Docker, docker-compose and NPM.

Run `make build`. This will create a set of Docker containers with all backends
and dependencies.

## Running

Run `make run` to run the development server and worker. The website will be available
at localhost:5000.

## License

The content of this project is licensed under the
[Attribution-NonCommercial-ShareAlike 4.0 International] license, and
the underlying source code used to format and display that content is licensed
under the MIT license.

[add-to-org]: https://github.com/benbalter/add-to-org
[Attribution-NonCommercial-ShareAlike 4.0 International]: https://creativecommons.org/licenses/by-nc-sa/4.0/
