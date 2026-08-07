APP_NAME = "python-web-server"


def test_python_web_server_serves_static_page(activate_app):
    """Verify that the activated app serves its static landing page over HTTP."""
    app = activate_app(APP_NAME)

    result = app.exec(
        "web",
        "python",
        "-c",
        "from urllib.request import urlopen; "
        "print(urlopen('http://127.0.0.1:8080/', timeout=2).read().decode())",
    )

    assert "Your Python web server is running." in result.stdout
