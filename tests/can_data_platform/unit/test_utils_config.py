"""Unit tests for utils config module."""

import os
import sys
from pathlib import Path
from unittest.mock import patch


def setup_project_path():
    """Add project root to Python path for module imports."""
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


# Setup path before importing project modules
setup_project_path()


class TestUtilsConfig:
    """Test cases for utils config module."""

    def test_config_imports_without_dotenv(self):
        """Test config module works without dotenv installed."""
        # Mock ImportError for dotenv by mocking the load_dotenv import directly
        with patch(
            'projects.can_data_platform.src.utils.config.load_dotenv',
            side_effect=ImportError("No module named 'dotenv'"),
        ):
            # Re-import the module to test ImportError handling
            import importlib

            if 'projects.can_data_platform.src.utils.config' in sys.modules:
                importlib.reload(
                    sys.modules['projects.can_data_platform.src.utils.config']
                )
            else:
                from projects.can_data_platform.src.utils import config

                assert hasattr(config, 'API_KEY')  # Use the import to satisfy linter

    def test_api_key_default_value(self):
        """Test API_KEY default value when not set in environment."""
        with patch.dict(os.environ, {}, clear=True):
            # Re-import to get fresh values
            import importlib
            from projects.can_data_platform.src.utils import config

            importlib.reload(config)

            assert config.API_KEY == "dev-key"

    def test_api_key_from_environment(self):
        """Test API_KEY loaded from environment variable."""
        test_api_key = "test-api-key-12345"
        with patch.dict(os.environ, {"API_KEY": test_api_key}):
            # Re-import to get fresh values
            import importlib
            from projects.can_data_platform.src.utils import config

            importlib.reload(config)

            assert config.API_KEY == test_api_key

    def test_batch_size_default_value(self):
        """Test BATCH_SIZE default value when not set in environment."""
        with patch.dict(os.environ, {}, clear=True):
            # Re-import to get fresh values
            import importlib
            from projects.can_data_platform.src.utils import config

            importlib.reload(config)

            assert config.BATCH_SIZE == 100

    def test_batch_size_from_environment(self):
        """Test BATCH_SIZE loaded from environment variable."""
        test_batch_size = "250"
        with patch.dict(os.environ, {"BATCH_SIZE": test_batch_size}):
            # Re-import to get fresh values
            import importlib
            from projects.can_data_platform.src.utils import config

            importlib.reload(config)

            assert config.BATCH_SIZE == 250

    def test_batch_size_integer_conversion(self):
        """Test BATCH_SIZE is properly converted to integer."""
        test_values = ["50", "1000", "1"]
        expected_values = [50, 1000, 1]

        for test_val, expected_val in zip(test_values, expected_values):
            with patch.dict(os.environ, {"BATCH_SIZE": test_val}):
                # Re-import to get fresh values
                import importlib
                from projects.can_data_platform.src.utils import config

                importlib.reload(config)

                assert config.BATCH_SIZE == expected_val
                assert isinstance(config.BATCH_SIZE, int)

    def test_config_with_dotenv_available(self):
        """Test config module with dotenv available."""
        # Since load_dotenv is already called during module import,
        # we just verify it exists and is callable
        from projects.can_data_platform.src.utils import config

        # Verify the module loaded successfully
        assert hasattr(config, 'API_KEY')
        assert hasattr(config, 'BATCH_SIZE')

    def test_multiple_environment_variables(self):
        """Test loading multiple environment variables together."""
        test_env = {"API_KEY": "production-key-789", "BATCH_SIZE": "500"}

        with patch.dict(os.environ, test_env):
            # Re-import to get fresh values
            import importlib
            from projects.can_data_platform.src.utils import config

            importlib.reload(config)

            assert config.API_KEY == "production-key-789"
            assert config.BATCH_SIZE == 500

    def test_config_module_attributes(self):
        """Test that config module has expected attributes."""
        from projects.can_data_platform.src.utils import config

        # Check that required attributes exist
        assert hasattr(config, 'API_KEY')
        assert hasattr(config, 'BATCH_SIZE')

        # Check types
        assert isinstance(config.API_KEY, str)
        assert isinstance(config.BATCH_SIZE, int)
