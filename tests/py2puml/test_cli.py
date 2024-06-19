from io import StringIO
from subprocess import PIPE, run
from typing import List

from pytest import mark

from pyaas2puml.asserts import assert_multilines
from pyaas2puml.py2puml import py2puml

from tests import TESTS_PATH, __description__, __version__


@mark.parametrize('entrypoint', [['pyaas2puml'], ['python', '-m', 'pyaas2puml']])
def test_cli_consistency_with_the_default_configuration(entrypoint: List[str]):
    command = entrypoint + ['pyaas2puml/domain', 'pyaas2puml.domain']
    cli_stdout = run(command, stdout=PIPE, stderr=PIPE, text=True, check=True).stdout

    puml_content = py2puml('pyaas2puml/domain', 'pyaas2puml.domain')

    assert ''.join(puml_content).strip() == cli_stdout.strip()


@mark.parametrize(
    ['command', 'current_working_directory', 'expected_puml_contents_file'],
    [
        (['python', '-m', 'pyaas2puml', 'withrootnotincwd', 'withrootnotincwd'], 'tests/modules', 'withrootnotincwd.puml'),
        (['pyaas2puml', 'withrootnotincwd', 'withrootnotincwd'], 'tests/modules', 'withrootnotincwd.puml'),
        (['python', '-m', 'pyaas2puml', 'test', 'test'], 'tests/modules/withconfusingrootpackage', 'test.puml'),
        (['pyaas2puml', 'test', 'test'], 'tests/modules/withconfusingrootpackage', 'test.puml'),
    ],
)
def test_cli_on_specific_working_directory(
    command: List[str], current_working_directory: str, expected_puml_contents_file: str
):
    cli_process = run(command, stdout=PIPE, stderr=PIPE, text=True, check=True, cwd=current_working_directory)

    with open(TESTS_PATH / 'puml_files' / expected_puml_contents_file, 'r', encoding='utf8') as expected_puml_file:
        assert_multilines(
            # removes the last return carriage added by the stdout
            list(StringIO(cli_process.stdout))[:-1],
            expected_puml_file,
        )


@mark.parametrize('version_command', [['-v'], ['--version']])
def test_cli_version(version_command: List[str]):
    """
    Ensures the consistency between the CLI version and the project version set in pyproject.toml
    which is not included when the CLI is installed system-wise
    """
    command = ['pyaas2puml'] + version_command
    cli_version = run(command, stdout=PIPE, stderr=PIPE, text=True, check=True).stdout

    assert cli_version == f'pyaas2puml {__version__}\n'


@mark.parametrize('help_command', [['-h'], ['--help']])
def test_cli_help(help_command: List[str]):
    """
    Ensures the consistency between the CLI help and the project description set in pyproject.toml
    which is not included when the CLI is installed system-wise
    """
    command = ['pyaas2puml'] + help_command
    help_text = run(command, stdout=PIPE, stderr=PIPE, text=True, check=True).stdout.replace('\n', ' ')

    assert __description__ in help_text
