# Copyright 2025 Google LLC All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test cases for the utils module."""

import json
import os
import tempfile
import unittest
import unittest.mock
from unittest.mock import patch

from analytics_mcp.tools import utils


class TestUtils(unittest.TestCase):
    """Test cases for the utils module."""

    def test_construct_property_rn(self):
        """Tests construct_property_rn using valid input."""
        self.assertEqual(
            utils.construct_property_rn(12345),
            "properties/12345",
            "Numeric property ID should b considered valid",
        )
        self.assertEqual(
            utils.construct_property_rn("12345"),
            "properties/12345",
            "Numeric property ID as string should be considered valid",
        )
        self.assertEqual(
            utils.construct_property_rn(" 12345  "),
            "properties/12345",
            "Whitespace around property ID should be considered valid",
        )
        self.assertEqual(
            utils.construct_property_rn("properties/12345"),
            "properties/12345",
            "Full resource name should be considered valid",
        )

    def test_construct_property_rn_invalid_input(self):
        """Tests that construct_property_rn raises a ValueError for invalid input."""
        with self.assertRaises(ValueError, msg="None should fail"):
            utils.construct_property_rn(None)
        with self.assertRaises(ValueError, msg="Empty string should fail"):
            utils.construct_property_rn("")
        with self.assertRaises(
            ValueError, msg="Non-numeric string should fail"
        ):
            utils.construct_property_rn("abc")
        with self.assertRaises(
            ValueError, msg="Resource name without ID should fail"
        ):
            utils.construct_property_rn("properties/")
        with self.assertRaises(
            ValueError, msg="Resource name with non-numeric ID should fail"
        ):
            utils.construct_property_rn("properties/abc")
        with self.assertRaises(
            ValueError,
            msg="Resource name with more than 2 components should fail",
        ):
            utils.construct_property_rn("properties/123/abc")

    def test_create_credentials_with_custom_adc_path(self):
        """Tests _create_credentials with CUSTOM_ADC_PATH set."""
        # Create a temporary credentials file
        test_credentials = {
            "type": "authorized_user",
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "refresh_token": "test-refresh-token"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_credentials, f)
            temp_path = f.name
        
        try:
            # Test with CUSTOM_ADC_PATH set
            with patch.dict(os.environ, {'CUSTOM_ADC_PATH': temp_path}):
                with patch('google.oauth2.credentials.Credentials.from_authorized_user_file') as mock_from_file:
                    mock_credentials = unittest.mock.Mock()
                    mock_from_file.return_value = mock_credentials
                    
                    credentials = utils._create_credentials()
                    self.assertIsNotNone(credentials)
                    # Verify that from_authorized_user_file was called with correct parameters
                    mock_from_file.assert_called_once_with(
                        temp_path,
                        scopes=[utils._READ_ONLY_ANALYTICS_SCOPE]
                    )
                    
        finally:
            # Clean up
            os.unlink(temp_path)

    def test_create_credentials_with_custom_scopes(self):
        """Tests _create_credentials with custom scopes in the credentials file."""
        # Create a temporary credentials file with custom scopes
        test_credentials = {
            "type": "authorized_user",
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "refresh_token": "test-refresh-token",
            "scopes": ["https://www.googleapis.com/auth/analytics"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_credentials, f)
            temp_path = f.name
        
        try:
            # Test with CUSTOM_ADC_PATH set
            with patch.dict(os.environ, {'CUSTOM_ADC_PATH': temp_path}):
                with patch('google.oauth2.credentials.Credentials.from_authorized_user_file') as mock_from_file:
                    mock_credentials = unittest.mock.Mock()
                    mock_from_file.return_value = mock_credentials
                    
                    credentials = utils._create_credentials()
                    self.assertIsNotNone(credentials)
                    # Verify that from_authorized_user_file was called with custom scopes
                    mock_from_file.assert_called_once_with(
                        temp_path,
                        scopes=["https://www.googleapis.com/auth/analytics"]
                    )
                    
        finally:
            # Clean up
            os.unlink(temp_path)

    def test_create_credentials_with_missing_custom_adc_path(self):
        """Tests _create_credentials with non-existent CUSTOM_ADC_PATH file."""
        with patch.dict(os.environ, {'CUSTOM_ADC_PATH': '/nonexistent/path.json'}):
            with self.assertRaises(ValueError, msg="Should raise ValueError for missing file"):
                utils._create_credentials()

    def test_create_credentials_fallback_to_default(self):
        """Tests _create_credentials falls back to default ADC when CUSTOM_ADC_PATH is not set."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('google.auth.default') as mock_default:
                mock_credentials = unittest.mock.Mock()
                mock_default.return_value = (mock_credentials, "project")
                
                result = utils._create_credentials()
                self.assertEqual(result, mock_credentials)
                mock_default.assert_called_once_with(scopes=[utils._READ_ONLY_ANALYTICS_SCOPE])
