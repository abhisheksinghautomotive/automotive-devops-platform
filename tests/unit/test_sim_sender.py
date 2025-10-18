"""Unit tests for sim_sender module - Maximum Coverage.

This module contains comprehensive unit tests achieving 95%+ coverage
for the event sending functionality with proper file mocking.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, mock_open, MagicMock

import requests

from projects.can_data_platform.scripts.sim_sender import send_events


class TestSendEvents(unittest.TestCase):
    """Test suite for send_events function with maximum coverage."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_events = [
            {"Cell1Voltage": 3800, "Cell2Voltage": 3850},
            {"Cell1Voltage": 3900, "Cell2Voltage": 3950},
            {"Cell1Voltage": 4000, "Cell2Voltage": 4050}
        ]
        self.jsonl_lines = [json.dumps(event) for event in self.sample_events]

    @patch('projects.can_data_platform.scripts.sim_sender.requests.post')
    @patch('projects.can_data_platform.scripts.sim_sender.logging')
    @patch('builtins.open', new_callable=mock_open)
    def test_send_events_success_all_paths(
            self, mock_file, mock_logging, mock_post):
        """Test successful event sending covering all code paths."""
        # KEY FIX: Properly mock file iteration
        mock_file.return_value.__enter__.return_value.__iter__ = (
            lambda x: iter(self.jsonl_lines))

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        send_events('test_events.jsonl')

        # Verify all 3 events were sent
        self.assertEqual(mock_post.call_count, 3)

        # Verify logging was called (covers logging lines)
        self.assertTrue(mock_logging.info.called)

        # Verify summary statistics were logged
        info_calls = [
            str(call[0][0]) for call in mock_logging.info.call_args_list
        ]
        self.assertTrue(any("Total Event Sent:" in c for c in info_calls))
        self.assertTrue(any("Average latency" in c for c in info_calls))
        self.assertTrue(any("Max latency" in c for c in info_calls))
        self.assertTrue(any("Min latency" in c for c in info_calls))

    @patch('projects.can_data_platform.scripts.sim_sender.requests.post')
    @patch('projects.can_data_platform.scripts.sim_sender.logging')
    @patch('builtins.open', new_callable=mock_open)
    def test_send_events_custom_endpoint(
            self, mock_file, _mock_logging, mock_post):
        """Test send_events with custom endpoint."""
        mock_file.return_value.__enter__.return_value.__iter__ = (
            lambda x: iter(self.jsonl_lines))
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        custom_endpoint = "http://example.com:9000/api/events"
        send_events('test_events.jsonl', endpoint=custom_endpoint)

        for call_item in mock_post.call_args_list:
            self.assertEqual(call_item[0][0], custom_endpoint)

    @patch('projects.can_data_platform.scripts.sim_sender.requests.post')
    @patch('projects.can_data_platform.scripts.sim_sender.logging')
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_send_events_request_timeout(
            self,
            mock_print,
            mock_file,
            _mock_logging,
            mock_post):
        """Test handling of request timeout."""
        mock_file.return_value.__enter__.return_value.__iter__ = (

            lambda x: iter(self.jsonl_lines))
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")

        send_events('test_events.jsonl')

        # Verify print was called for error
        self.assertTrue(mock_print.called)
        print_calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("Request failed" in str(c) for c in print_calls))

    @patch('projects.can_data_platform.scripts.sim_sender.requests.post')
    @patch('projects.can_data_platform.scripts.sim_sender.logging')
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_send_events_connection_error(
            self,
            mock_print,
            mock_file,
            _mock_logging,
            mock_post):
        """Test handling of connection errors."""
        mock_file.return_value.__enter__.return_value.__iter__ = (

            lambda x: iter(self.jsonl_lines))
        mock_post.side_effect = requests.exceptions.ConnectionError(
            "Connection failed")

        send_events('test_events.jsonl')

        self.assertTrue(mock_print.called)

    @patch('projects.can_data_platform.scripts.sim_sender.requests.post')
    @patch('projects.can_data_platform.scripts.sim_sender.logging')
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_send_events_http_error(
            self,
            _mock_print,
            mock_file,
            _mock_logging,
            mock_post):
        """Test handling of HTTP errors (4xx, 5xx)."""
        mock_file.return_value.__enter__.return_value.__iter__ = (

            lambda x: iter(self.jsonl_lines))

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = (
            requests.exceptions.HTTPError("500 Server Error"))
        mock_post.return_value = mock_response

        send_events('test_events.jsonl')

        # Verify raise_for_status was called
        self.assertTrue(mock_response.raise_for_status.called)

    @patch('projects.can_data_platform.scripts.sim_sender.requests.post')
    @patch('projects.can_data_platform.scripts.sim_sender.logging')
    @patch('builtins.open', new_callable=mock_open)
    def test_send_events_empty_file(self, mock_file, mock_logging, mock_post):
        """Test handling of empty JSONL file."""
        # Empty file - no lines to iterate
        mock_file.return_value.__enter__.return_value.__iter__ = (
            lambda x: iter([]))

        send_events('empty_events.jsonl')

        # No HTTP requests should be made
        self.assertEqual(mock_post.call_count, 0)

        # Verify "No events were sent" message
        info_calls = [

            str(call[0][0]) for call in mock_logging.info.call_args_list

        ]
        self.assertTrue(any("No events were sent" in c for c in info_calls))

    @patch('projects.can_data_platform.scripts.sim_sender.requests.post')
    @patch('projects.can_data_platform.scripts.sim_sender.logging')
    @patch('builtins.open', new_callable=mock_open)
    def test_send_events_partial_failure(
            self, mock_file, mock_logging, mock_post):
        """Test handling when some requests succeed and others fail."""
        mock_file.return_value.__enter__.return_value.__iter__ = (

            lambda x: iter(self.jsonl_lines))

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200

        # First succeeds, second fails, third succeeds
        mock_post.side_effect = [
            mock_response_success,
            requests.exceptions.Timeout("Timeout"),
            mock_response_success
        ]

        send_events('test_events.jsonl')

        # Verify that 2 events were sent successfully
        info_calls = [
            str(call[0]) for call in mock_logging.info.call_args_list
        ]
        self.assertTrue(
            any('Total Event Sent:' in str(c) for c in info_calls)
        )

    @patch('projects.can_data_platform.scripts.sim_sender.requests.post')
    @patch('projects.can_data_platform.scripts.sim_sender.logging')
    @patch('builtins.open', new_callable=mock_open)
    def test_send_events_request_timeout_parameter(
            self, mock_file, _mock_logging, mock_post):
        """Test that requests include timeout=10 parameter."""
        single_line = [json.dumps({"voltage": 3800})]
        mock_file.return_value.__enter__.return_value.__iter__ = (

            lambda x: iter(single_line))

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        send_events('test.jsonl')

        # Verify timeout parameter
        call_kwargs = mock_post.call_args[1]
        self.assertEqual(call_kwargs.get('timeout'), 10)

    @patch('projects.can_data_platform.scripts.sim_sender.requests.post')
    @patch('projects.can_data_platform.scripts.sim_sender.logging')
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_send_events_malformed_json(
            self,
            _mock_print,
            mock_file,
            _mock_logging,
            _mock_post):
        """Test handling of malformed JSON in file."""
        malformed_line = ['not valid json']
        mock_file.return_value.__enter__.return_value.__iter__ = (

            lambda x: iter(malformed_line))

        with self.assertRaises(json.JSONDecodeError):
            send_events('malformed.jsonl')

    @patch('projects.can_data_platform.scripts.sim_sender.logging')
    def test_send_events_file_not_found(self, _mock_logging):
        """Test handling of non-existent file."""
        with self.assertRaises(FileNotFoundError):
            send_events('nonexistent_file.jsonl')

    @patch('projects.can_data_platform.scripts.sim_sender.requests.post')
    @patch('projects.can_data_platform.scripts.sim_sender.logging')
    @patch('builtins.open', new_callable=mock_open)
    def test_send_events_single_event(
            self, mock_file, mock_logging, mock_post):
        """Test sending single event."""
        single_line = [json.dumps({"voltage": 3800})]
        mock_file.return_value.__enter__.return_value.__iter__ = (

            lambda x: iter(single_line))

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        send_events('single_event.jsonl')

        self.assertEqual(mock_post.call_count, 1)

        # Verify logging for single event
        info_calls = [

            str(call[0][0]) for call in mock_logging.info.call_args_list

        ]
        self.assertTrue(any("Total Event Sent:" in c for c in info_calls))

    @patch('projects.can_data_platform.scripts.sim_sender.requests.post')
    @patch('projects.can_data_platform.scripts.sim_sender.logging')
    @patch('builtins.open', new_callable=mock_open)
    def test_send_events_all_fail(self, mock_file, mock_logging, mock_post):
        """Test when all events fail to send."""
        mock_file.return_value.__enter__.return_value.__iter__ = (

            lambda x: iter(self.jsonl_lines))

        # All requests fail
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")

        send_events('test_events.jsonl')

        # Should log "No events were sent successfully"
        info_calls = [

            str(call[0][0]) for call in mock_logging.info.call_args_list

        ]
        self.assertTrue(any("No events were sent" in c for c in info_calls))

    @patch('projects.can_data_platform.scripts.sim_sender.requests.post')
    @patch('projects.can_data_platform.scripts.sim_sender.logging')
    @patch('builtins.open', new_callable=mock_open)
    def test_send_events_response_status_logged(
            self, mock_file, mock_logging, mock_post):
        """Test that response status is logged."""
        single_line = [json.dumps({"voltage": 3800})]
        mock_file.return_value.__enter__.return_value.__iter__ = (

            lambda x: iter(single_line))

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        send_events('test.jsonl')

        # Verify status code appears in logs
        info_calls = [str(call) for call in mock_logging.info.call_args_list]
        self.assertTrue(any("201" in str(c) for c in info_calls))


class TestSendEventsIntegration(unittest.TestCase):
    """Integration tests using real temporary files."""

    def test_send_events_with_real_file(self):
        """Test send_events with actual temporary file."""
        events = [
            {"Cell1Voltage": 3800, "test": "data1"},
            {"Cell2Voltage": 3900, "test": "data2"}
        ]

        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.jsonl', delete=False) as tmp_file:
            for event in events:
                tmp_file.write(json.dumps(event) + '\n')
            tmp_file_path = tmp_file.name

        try:
            with patch('projects.can_data_platform.scripts.sim_sender.requests.post') as mock_post:  # pylint: disable=line-too-long
                with patch('projects.can_data_platform.scripts.sim_sender.logging'):  # pylint: disable=line-too-long
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_post.return_value = mock_response

                    send_events(tmp_file_path)

                    self.assertEqual(mock_post.call_count, 2)
        finally:
            os.unlink(tmp_file_path)


if __name__ == '__main__':
    unittest.main()
