This app renders https://jazzband.co.

[![Jazzband](https://jazzband.co/static/img/badge.svg)](https://jazzband.co/)
[![Test & Deploy](https://github.com/jazzband/website/actions/workflows/test-and-deploy.yml/badge.svg)](https://github.com/jazzband/website/actions/workflows/test-and-deploy.yml)
[![Calver](https://img.shields.io/badge/calver-YY.MM.PATCH-22bfda.svg)](https://calver.org/)

## Installation

Copy `.end-dist` to `.env`.

Install Docker, docker-compose and NPM.

Run `make build`. This will create a set of Docker containers with all backends
and dependencies.

The Jazzband site uses a self-signed TLS certificate for development to be able
to reproduce the production environment as close as possible. To that effect
it's required to install [`mkcert`](https://github.com/FiloSottile/mkcert)
in your system's certificate trust store (once). To do that install `mkcert`
by following the installation instructions and then run `make trust`.

In case the embedded self-signed certificates are outdated you can recreate
them by running `make cert`.

## Running

Run `make run` to run the development server and worker. The website will be available
at https://localhost:5000.

## License

The content of this project is licensed under the
[Attribution-NonCommercial-ShareAlike 4.0 International] license, and
the underlying source code used to format and display that content is licensed
under the MIT license.

[add-to-org]: https://github.com/benbalter/add-to-org
[Attribution-NonCommercial-ShareAlike 4.0 International]: https://creativecommons.org/licenses/by-nc-sa/4.0/
