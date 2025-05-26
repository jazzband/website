[![Jazzband](https://jazzband.co/static/img/badge.svg)](https://jazzband.co/)
[![Test & Deploy](https://github.com/jazzband/website/actions/workflows/test-and-deploy.yml/badge.svg)](https://github.com/jazzband/website/actions/workflows/test-and-deploy.yml)
[![Calver](https://img.shields.io/badge/calver-YY.MM.PATCH-22bfda.svg)](https://calver.org/)

The code that renders https://jazzband.co.

## Installation

Copy `.env-dist` to `.env`.

Install Docker and NPM.

Run `make build`. This will create a set of Docker containers with all backends
and dependencies.

## Running

Get [Orbstack](https://orbstack.dev/).

Run `make run` to run the development server and worker. The website will be available
at https://jazzband.local.

## License

The content of this project is licensed under the
[Attribution-NonCommercial-ShareAlike 4.0 International] license, and
the underlying source code used to format and display that content is licensed
under the MIT license.

[add-to-org]: https://github.com/benbalter/add-to-org
[Attribution-NonCommercial-ShareAlike 4.0 International]: https://creativecommons.org/licenses/by-nc-sa/4.0/
