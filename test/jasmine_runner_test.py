from jasmine_core import Core
import pytest
from mock import Mock


@pytest.fixture
def config():
    from jasmine import Config

    mock_config = Mock(spec=Config, autospec=True)

    mock_config.lists = {
        "src_files": ["/src/file1.js", "/src/file2.js"],
        "spec_files": ["/specs/file1_spec.js", "/specs/file2_spec.js"],
        "helpers": ['/specs/helpers/spec_helper.js'],
        "stylesheets": ['/src/css/user.css']
    }

    mock_config.src_files.return_value = ["/src/file1.js", "/src/file2.js"]
    mock_config.spec_files.return_value = ["/specs/file1_spec.js", "/specs/file2_spec.js"]
    mock_config.helpers.return_value = ["/specs/helpers/spec_helper.js"]
    mock_config.stylesheets.return_value = ["/src/css/user.css"]
    mock_config.src_dir = "src"
    mock_config.spec_dir = "specs"

    return mock_config


@pytest.fixture
def response(rf, config):
    from jasmine.views import JasmineRunner

    request = rf.get("")

    return JasmineRunner.as_view(template_name="runner.html", config=config)(request)


def test_js_files(config, response):
    core_js_files = ["core/{0}".format(f) for f in Core.js_files()]
    boot_js_files = ["boot/{0}".format(f) for f in Core.boot_files()]

    user_files = config.lists['src_files'] + config.lists['helpers'] + config.lists['spec_files']

    assert response.context_data['js_files'] == core_js_files + boot_js_files + [f[1:] for f in user_files]


def test_css_files(config, response):
    core_css_files = ["core/{0}".format(css) for css in Core.css_files()]
    user_css_files = config.lists['stylesheets']

    assert response.context_data['css_files'] == core_css_files + [f[1:] for f in user_css_files]


def test_reload_on_each_request(config, response):
    config.reload.assert_called_once_with()