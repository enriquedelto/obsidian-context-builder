import unittest
import json
import os
from pathlib import Path
from unittest.mock import patch, mock_open
import io
import sys

# Assuming config_handler.py is in the parent directory (root of the repo)
# Adjust the path if your structure is different
sys.path.insert(0, str(Path(__file__).parent.parent))
from config_handler import load_config, save_config, CONFIG_FILENAME # get_config_path is not directly used in tests but by load_config

# Helper to create a temporary config file path
TEMP_CONFIG_DIR = Path(__file__).parent / "temp_test_configs"
TEMP_CONFIG_FILE = TEMP_CONFIG_DIR / CONFIG_FILENAME

class TestConfigHandler(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for config files if it doesn't exist
        TEMP_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        # Ensure the temp config file is cleaned up before each test if it exists from a failed run
        if TEMP_CONFIG_FILE.exists():
            TEMP_CONFIG_FILE.unlink()

    def tearDown(self):
        # Clean up the temporary config file after each test
        if TEMP_CONFIG_FILE.exists():
            TEMP_CONFIG_FILE.unlink()
        # Clean up the temporary directory if it's empty
        if TEMP_CONFIG_DIR.exists() and not any(TEMP_CONFIG_DIR.iterdir()):
            TEMP_CONFIG_DIR.rmdir()

    @patch('config_handler.CONFIG_FILENAME', new_callable=lambda: TEMP_CONFIG_FILE.name)
    @patch('config_handler.get_config_path', return_value=TEMP_CONFIG_FILE)
    def test_load_valid_config(self, mock_get_path, mock_filename):
        # Create a temporary valid JSON config file
        valid_config_data = {
            "vaults": {"test_vault": "/path/to/test_vault"},
            "last_vault_name": "test_vault"
        }
        with open(TEMP_CONFIG_FILE, 'w') as f:
            json.dump(valid_config_data, f)

        loaded_config = load_config()
        self.assertEqual(loaded_config, valid_config_data)

    @patch('config_handler.CONFIG_FILENAME', new_callable=lambda: "non_existent_config.json")
    @patch('config_handler.get_config_path', return_value=TEMP_CONFIG_DIR / "non_existent_config.json")
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_load_missing_config(self, mock_stderr, mock_get_path, mock_filename):
        # Ensure the file does not exist before calling load_config
        non_existent_path = TEMP_CONFIG_DIR / "non_existent_config.json"
        if non_existent_path.exists():
            non_existent_path.unlink()

        loaded_config = load_config()
        self.assertEqual(loaded_config, {"vaults": {}, "last_vault_name": None})
        expected_error_msg = f"Error: Configuration file not found at {non_existent_path}. Please run the application with `--add-vault` to create one or ensure the file exists.\n"
        self.assertEqual(mock_stderr.getvalue(), expected_error_msg)

    @patch('config_handler.CONFIG_FILENAME', new_callable=lambda: TEMP_CONFIG_FILE.name)
    @patch('config_handler.get_config_path', return_value=TEMP_CONFIG_FILE)
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_load_malformed_config(self, mock_stderr, mock_get_path, mock_filename):
        # Create a temporary file with invalid JSON content
        malformed_json_content = "this is not valid json"
        with open(TEMP_CONFIG_FILE, 'w') as f:
            f.write(malformed_json_content)

        loaded_config = load_config()
        self.assertEqual(loaded_config, {"vaults": {}, "last_vault_name": None})
        expected_error_msg = f"Error: Configuration file is malformed and cannot be parsed. Please check its content at {TEMP_CONFIG_FILE}.\n"
        self.assertEqual(mock_stderr.getvalue(), expected_error_msg)

    @patch('config_handler.CONFIG_FILENAME', new_callable=lambda: TEMP_CONFIG_FILE.name)
    @patch('config_handler.get_config_path', return_value=TEMP_CONFIG_FILE)
    def test_save_and_load_config(self, mock_get_path, mock_filename):
        sample_config_data = {
            "vaults": {"main_vault": "/path/to/main", "archive": "/path/to/archive"},
            "last_vault_name": "main_vault"
        }

        # Save the sample config
        save_config(sample_config_data)

        # Load the config
        loaded_config = load_config()

        self.assertEqual(loaded_config, sample_config_data)

if __name__ == '__main__':
    unittest.main()
