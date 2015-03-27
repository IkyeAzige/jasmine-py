from mockfs import replace_builtins, restore_builtins
import pkg_resources
import pytest

from jasmine.standalone import JasmineApp


class FakeConfig(object):
    def __init__(
            self,
            src_dir=None,
            spec_dir=None,
            stylesheet_urls=None,
            script_urls=None
    ):
        self._src_dir = src_dir
        self._spec_dir = spec_dir
        self._stylesheet_urls = stylesheet_urls
        self._script_urls = script_urls

        self.reload_call_count = 0

    def src_dir(self):
        return self._src_dir

    def spec_dir(self):
        return self._spec_dir

    def stylesheet_urls(self):
        return self._stylesheet_urls

    def script_urls(self):
        return self._script_urls

    def reload(self):
        self.reload_call_count += 1


@pytest.fixture
def jasmine_config():
    script_urls = ['__src__/main.js', '__spec__/main_spec.js']
    stylesheet_urls = ['__src__/main.css']

    return FakeConfig(
        src_dir='src',
        spec_dir='spec',
        script_urls=script_urls,
        stylesheet_urls=stylesheet_urls
    )

@pytest.fixture
def app(jasmine_config):
    jasmine_app = JasmineApp(jasmine_config=jasmine_config)

    jasmine_app.app.testing = True
    return jasmine_app.app


@pytest.fixture
def template():
    return pkg_resources.resource_string('jasmine.django.templates', 'runner.html')


@pytest.fixture
def mockfs(request):
    mfs = replace_builtins()
    request.addfinalizer(lambda: restore_builtins())
    return mfs


@pytest.mark.usefixtures('mockfs')
def test__favicon(monkeypatch, app):
    monkeypatch.setattr(pkg_resources, 'resource_stream', lambda package, filename: [])

    with app.test_client() as client:
        response = client.get("/jasmine_favicon.png")

        assert response.status_code == 200


def test__serve(mockfs, app):
    mockfs.add_entries({
        "/src/main.css": "CSS",
        "/src/main.js": "JS",
        "/src/main.png": "PNG"
    })

    with app.test_client() as client:
        rv = client.get("/__src__/main.css")

        assert rv.status_code == 200
        assert rv.headers['Content-Type'] == 'text/css; charset=utf-8'

        rv = client.get("/__src__/main.js")

        assert rv.status_code == 200
        assert rv.headers['Content-Type'] == 'application/javascript'

        rv = client.get("/__src__/main.png")

        assert rv.status_code == 200
        assert rv.headers['Content-Type'] == 'image/png'


def test__serve_jasmine_files():
    pass #cover 'if filetype' at top of serve


def test__run(template, mockfs, monkeypatch, app, jasmine_config):
    monkeypatch.setattr(
        pkg_resources,
        'resource_listdir',
        lambda package, dir: [
            'jasmine.js',
            'boot.js',
            'node_boot.js'
        ]
    )
    monkeypatch.setattr(
        pkg_resources,
        'resource_string',
        lambda package, filename: template
    )

    with app.test_client() as client:
        response = client.get("/")

        assert jasmine_config.reload_call_count == 1
        assert response.status_code == 200

        html = response.get_data(as_text=True)

        assert """<script src="__src__/main.js" type="text/javascript"></script>""" in html
        assert """<script src="__spec__/main_spec.js" type="text/javascript"></script>""" in html
        assert """<link rel="stylesheet" href="__src__/main.css" type="text/css" media="screen"/>""" in html
