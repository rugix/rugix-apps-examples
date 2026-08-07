# Python Web Server

This starter Rugix App serves a static page over HTTP from a small Python
container. It uses Python's standard-library HTTP server, so the workload has
no application dependencies or external services.

The app contains one `web` service. Docker Compose publishes it on port `8080`
by default and checks that the page remains reachable. Set `PYTHON_WEB_PORT` to
use a different host port.

> [!CAUTION]
> Python's standard-library HTTP server is suitable for this example, not for a
> production deployment. Replace it with a production server and review the
> network exposure before adapting the app for a deployed product.

## Run with Compose

Build the local container image and start the app:

```sh
../../tools/podman-build.sh --example python-web-server
podman compose up
```

Open <http://localhost:8080> to view the page.

## Bundle

```sh
../../tools/build-bundles.sh --example python-web-server
```
