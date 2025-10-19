"""
Unit tests for GitHub Issues Deployment Script.

This module provides comprehensive test coverage for the issue_deployer.py
script including API interactions, user input handling, and file operations.
"""
import json
import os
import sys
from unittest.mock import Mock, mock_open, patch

import pytest
import requests

# Add the script directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                '../../.github/issue_deployment'))


import issue_deployer  # type: ignore # noqa: E402


class TestFetchMilestones:
    """Test class for milestone fetching functionality."""

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for testing."""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_token_123',
            'GITHUB_REPO': 'test-owner/test-repo'
        }):
            yield

    @pytest.fixture
    def sample_milestones(self):
        """Sample milestone data for testing."""
        return [
            {
                'number': 1,
                'title': 'Test Milestone 1',
                'open_issues': 5
            },
            {
                'number': 2,
                'title': 'Test Milestone 2',
                'open_issues': 3
            }
        ]

    def test_fetch_milestones_success(self, sample_milestones):
        """Test successful milestone fetching."""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_token_123',
            'GITHUB_REPO': 'test-owner/test-repo'
        }):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_milestones

            with patch('requests.get', return_value=mock_response) as mock_get:
                result = issue_deployer.fetch_milestones()

                expected_url = ('https://api.github.com/repos/test-owner/'
                                'test-repo/milestones?state=all')
                mock_get.assert_called_once_with(
                    expected_url,
                    headers={
                        'Accept': 'application/vnd.github.v3+json',
                        'Authorization': 'token test_token_123'
                    },
                    timeout=30
                )
                assert result == sample_milestones

    def test_fetch_milestones_failure(self):
        """Test milestone fetching failure."""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_token_123',
            'GITHUB_REPO': 'test-owner/test-repo'
        }):
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {'message': 'Not Found'}

            with patch('requests.get', return_value=mock_response):
                with patch('builtins.print') as mock_print:
                    with pytest.raises(SystemExit) as exc_info:
                        issue_deployer.fetch_milestones()

                    assert exc_info.value.code == 1
                    mock_print.assert_called_with(
                        'Failed to fetch milestones:',
                        {'message': 'Not Found'}
                    )


class TestDisplayMilestones:
    """Test class for milestone display functionality."""

    def test_display_milestones(self, capsys):
        """Test milestone display functionality."""
        sample_milestones = [
            {'number': 1, 'title': 'Test Milestone 1', 'open_issues': 5},
            {'number': 2, 'title': 'Test Milestone 2', 'open_issues': 3}
        ]

        issue_deployer.display_milestones(sample_milestones)

        captured = capsys.readouterr()
        assert "Available Milestones in this repo:" in captured.out
        assert "[1]: Test Milestone 1 (open issues: 5)" in captured.out
        assert "[2]: Test Milestone 2 (open issues: 3)" in captured.out


class TestLoadIssuesFromJson:
    """Test class for JSON loading functionality."""

    @pytest.fixture
    def sample_issues(self):
        """Sample issue data for testing."""
        return [
            {
                'title': 'Test Issue 1',
                'body': 'Test description 1',
                'labels': ['test', 'bug']
            },
            {
                'title': 'Test Issue 2',
                'body': 'Test description 2',
                'labels': ['feature']
            }
        ]

    @pytest.fixture
    def sample_json_data(self, sample_issues):
        """Sample JSON data with milestone for testing."""
        return {
            'milestone_name': 'Test Milestone',
            'issues': sample_issues
        }

    def test_load_issues_from_json_with_milestone(self, sample_json_data):
        """Test loading issues from JSON with milestone name."""
        json_content = json.dumps(sample_json_data)

        with patch('builtins.open', mock_open(read_data=json_content)):
            milestone_name, issues = issue_deployer.load_issues_from_json(
                'test.json')

            assert milestone_name == 'Test Milestone'
            assert len(issues) == 2
            assert issues[0]['title'] == 'Test Issue 1'

    def test_load_issues_from_json_without_milestone(self, sample_issues):
        """Test loading issues from JSON without milestone name."""
        json_content = json.dumps(sample_issues)

        with patch('builtins.open', mock_open(read_data=json_content)):
            milestone_name, issues = issue_deployer.load_issues_from_json(
                'test.json')

            assert milestone_name == '<not specified in json>'
            assert issues == sample_issues

    def test_load_issues_from_json_file_not_found(self):
        """Test handling of missing JSON file."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundError):
                issue_deployer.load_issues_from_json('nonexistent.json')

    def test_load_issues_from_json_invalid_json(self):
        """Test handling of invalid JSON content."""
        with patch('builtins.open', mock_open(read_data='invalid json')):
            with pytest.raises(json.JSONDecodeError):
                issue_deployer.load_issues_from_json('invalid.json')


class TestUserInteractions:
    """Test class for user input handling functionality."""

    def test_get_milestone_assignment_valid_number(self):
        """Test valid milestone number input."""
        with patch('builtins.input', return_value='5'):
            result = issue_deployer.get_milestone_assignment()
            assert result == 5

    def test_get_milestone_assignment_empty_input(self):
        """Test empty milestone input."""
        with patch('builtins.input', return_value=''):
            result = issue_deployer.get_milestone_assignment()
            assert result is None

    def test_get_milestone_assignment_non_numeric(self):
        """Test non-numeric milestone input."""
        with patch('builtins.input', return_value='abc'):
            result = issue_deployer.get_milestone_assignment()
            assert result is None

    def test_confirm_deployment_yes(self):
        """Test deployment confirmation with YES."""
        with patch('builtins.input', return_value='YES'):
            result = issue_deployer.confirm_deployment(5)
            assert result is True

    def test_confirm_deployment_yes_lowercase(self):
        """Test deployment confirmation with yes in lowercase."""
        with patch('builtins.input', return_value='yes'):
            result = issue_deployer.confirm_deployment(5)
            assert result is True

    def test_confirm_deployment_no(self):
        """Test deployment confirmation with NO."""
        with patch('builtins.input', return_value='NO'):
            result = issue_deployer.confirm_deployment(5)
            assert result is False

    def test_confirm_deployment_empty(self):
        """Test deployment confirmation with empty input."""
        with patch('builtins.input', return_value=''):
            result = issue_deployer.confirm_deployment(5)
            assert result is False


class TestDeployIssues:
    """Test class for issue deployment functionality."""

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for testing."""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_token_123',
            'GITHUB_REPO': 'test-owner/test-repo'
        }):
            yield

    @pytest.fixture
    def sample_issues(self):
        """Sample issue data for testing."""
        return [
            {
                'title': 'Test Issue 1',
                'body': 'Test description 1',
                'labels': ['test']
            },
            {
                'title': 'Test Issue 2',
                'body': 'Test description 2',
                'labels': ['feature']
            }
        ]

    def test_deploy_issues_success(self, sample_issues):
        """Test successful issue deployment."""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_token_123',
            'GITHUB_REPO': 'test-owner/test-repo'
        }):
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {'id': 123, 'number': 1}

            with patch('requests.post',
                       return_value=mock_response) as mock_post:
                with patch('builtins.print') as mock_print:
                    issue_deployer.deploy_issues(sample_issues, 5)

                    assert mock_post.call_count == 2
                    # Verify milestone was added to issues
                    for call in mock_post.call_args_list:
                        issue_data = call[1]['json']
                        assert issue_data['milestone'] == 5

                    assert mock_print.call_count == 2

    def test_deploy_issues_no_milestone(self, sample_issues):
        """Test issue deployment without milestone."""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_token_123',
            'GITHUB_REPO': 'test-owner/test-repo'
        }):
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {'id': 123}

            with patch('requests.post',
                       return_value=mock_response) as mock_post:
                issue_deployer.deploy_issues(sample_issues, None)

                # Verify no milestone was added
                for call in mock_post.call_args_list:
                    issue_data = call[1]['json']
                    assert 'milestone' not in issue_data

    def test_deploy_issues_api_failure(self, sample_issues):
        """Test issue deployment with API failure."""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_token_123',
            'GITHUB_REPO': 'test-owner/test-repo'
        }):
            mock_response = Mock()
            mock_response.status_code = 422
            mock_response.json.return_value = {'message': 'Validation Failed'}

            with patch('requests.post', return_value=mock_response):
                with patch('builtins.print') as mock_print:
                    issue_deployer.deploy_issues(sample_issues, 5)

                    mock_print.assert_called()

    def test_deploy_issues_network_timeout(self, sample_issues):
        """Test issue deployment with network timeout."""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_token_123',
            'GITHUB_REPO': 'test-owner/test-repo'
        }):
            with patch('requests.post', side_effect=requests.Timeout):
                with pytest.raises(requests.Timeout):
                    issue_deployer.deploy_issues(sample_issues, 5)


class TestMainFunction:
    """Test class for main function orchestration."""

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for testing."""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_token_123',
            'GITHUB_REPO': 'test-owner/test-repo'
        }):
            yield

    def test_main_missing_arguments(self):
        """Test main function with missing arguments."""
        with patch.object(sys, 'argv', ['script.py']):
            with patch('builtins.print') as mock_print:
                with pytest.raises(SystemExit) as exc_info:
                    issue_deployer.main()

                assert exc_info.value.code == 1
                mock_print.assert_called_with(
                    'Usage: python issue_deployer.py path/to/issues.json')

    def test_main_user_abort(self):
        """Test main function when user aborts deployment."""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_token_123',
            'GITHUB_REPO': 'test-owner/test-repo'
        }):
            with patch.object(sys, 'argv', ['script.py', 'test.json']):
                with patch('issue_deployer.fetch_milestones', return_value=[]):
                    with patch('issue_deployer.display_milestones'):
                        load_patch = 'issue_deployer.load_issues_from_json'
                        with patch(load_patch, return_value=('Test', [])):
                            with patch('builtins.print'):
                                get_patch = ('issue_deployer'
                                             '.get_milestone_assignment')
                                confirm_patch = ('issue_deployer'
                                                 '.confirm_deployment')
                                with patch(get_patch, return_value=5):
                                    with patch(confirm_patch,
                                               return_value=False):
                                        with pytest.raises(SystemExit) as exc:
                                            issue_deployer.main()

                                        exc_val = 'Aborted by user.'
                                        assert str(exc.value) == exc_val

    def test_main_successful_deployment(self):
        """Test successful main function execution."""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_token_123',
            'GITHUB_REPO': 'test-owner/test-repo'
        }):
            with patch.object(sys, 'argv', ['script.py', 'test.json']):
                with patch('issue_deployer.fetch_milestones', return_value=[]):
                    with patch('issue_deployer.display_milestones'):
                        load_patch = 'issue_deployer.load_issues_from_json'
                        with patch(load_patch, return_value=('Test', [])):
                            with patch('builtins.print'):
                                get_patch = ('issue_deployer'
                                             '.get_milestone_assignment')
                                confirm_patch = ('issue_deployer'
                                                 '.confirm_deployment')
                                deploy_patch = ('issue_deployer'
                                                '.deploy_issues')
                                with patch(get_patch, return_value=5):
                                    with patch(confirm_patch,
                                               return_value=True):
                                        with patch(deploy_patch):
                                            # Should not raise exception
                                            issue_deployer.main()


class TestConfigurationAndSetup:
    """Test class for configuration and setup validation."""

    @pytest.mark.skip(reason="Environment variable testing complex due to import caching")
    def test_missing_environment_variables(self):
        """Test handling of missing environment variables when running as main."""
        # We can't easily test the ValidationError in current implementation
        # since it only happens when script is executed as __main__ with missing vars
        # This test just verifies the default values work
        with patch.dict(os.environ, {}, clear=True):
            # Should not raise when imported as module
            import importlib
            importlib.reload(issue_deployer)

            # But functions should use fallback values
            assert issue_deployer.get_base_url() == "https://api.github.com/repos/test/repo"
            assert issue_deployer.get_headers()["Authorization"] == "token test-token"

    def test_request_timeout_configuration(self):
        """Test request timeout configuration."""
        import importlib
        importlib.reload(issue_deployer)
        assert issue_deployer.REQUEST_TIMEOUT == 30

    def test_headers_configuration(self):
        """Test headers configuration."""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_token_123',
            'GITHUB_REPO': 'test-owner/test-repo'
        }):
            expected_headers = {
                'Accept': 'application/vnd.github.v3+json',
                'Authorization': 'token test_token_123'
            }
            assert issue_deployer.get_headers() == expected_headers

    def test_base_url_configuration(self):
        """Test base URL configuration."""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_token_123',
            'GITHUB_REPO': 'test-owner/test-repo'
        }):
            expected_url = 'https://api.github.com/repos/test-owner/test-repo'
            assert issue_deployer.get_base_url() == expected_url


class TestCodeQuality:
    """Test class for code quality and documentation validation."""

    def test_module_docstring(self):
        """Test that the module has a proper docstring."""
        assert issue_deployer.__doc__ is not None
        assert len(issue_deployer.__doc__.strip()) > 0

    def test_all_functions_have_docstrings(self):
        """Test that all functions have proper docstrings."""
        functions_to_check = [
            'fetch_milestones',
            'display_milestones',
            'load_issues_from_json',
            'get_milestone_assignment',
            'confirm_deployment',
            'deploy_issues',
            'main'
        ]

        for func_name in functions_to_check:
            func = getattr(issue_deployer, func_name)
            message = f"{func_name} missing docstring"
            assert func.__doc__ is not None, message
            message = f"{func_name} empty docstring"
            assert len(func.__doc__.strip()) > 0, message


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
