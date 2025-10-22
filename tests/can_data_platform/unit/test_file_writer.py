"""Unit tests for file writer implementations."""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from projects.can_data_platform.src.file_operations.file_writer import (
    FileWriter,
    FileWriterFactory,
    JSONLFileWriter,
)


class TestFileWriter(unittest.TestCase):
    """Test FileWriter abstract base class."""

    def test_abstract_write_method(self):
        """Test that FileWriter is abstract and cannot be instantiated."""
        with self.assertRaises(TypeError):
            FileWriter()  # pylint: disable=abstract-class-instantiated

    def test_write_method_is_abstract(self):
        """Test that write method is abstract."""
        # Create a concrete class without implementing write
        class IncompleteWriter(FileWriter):
            pass

        with self.assertRaises(TypeError):
            IncompleteWriter()  # pylint: disable=abstract-class-instantiated


class TestJSONLFileWriter(unittest.TestCase):
    """Test JSONLFileWriter implementation."""

    def setUp(self):
        """Set up test environment."""
        self.writer = JSONLFileWriter()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment."""
        # Clean up any remaining temp files
        if os.path.exists(self.temp_dir):
            for file in os.listdir(self.temp_dir):
                try:
                    os.remove(os.path.join(self.temp_dir, file))
                except OSError:
                    pass
            try:
                os.rmdir(self.temp_dir)
            except OSError:
                pass

    def test_write_events_success(self):
        """Test successful writing of events to JSONL file."""
        events = [
            {"id": 1, "name": "event1", "value": 100},
            {"id": 2, "name": "event2", "value": 200},
        ]
        output_path = os.path.join(self.temp_dir, "test_events.jsonl")

        # Write events
        self.writer.write(events, output_path)

        # Verify file exists and contains correct data
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 2)

        # Verify each line is valid JSON
        event1 = json.loads(lines[0].strip())
        event2 = json.loads(lines[1].strip())

        self.assertEqual(event1, {"id": 1, "name": "event1", "value": 100})
        self.assertEqual(event2, {"id": 2, "name": "event2", "value": 200})

    def test_write_empty_events_list(self):
        """Test writing empty events list."""
        events = []
        output_path = os.path.join(self.temp_dir, "empty_events.jsonl")

        # Write empty events
        self.writer.write(events, output_path)

        # Verify file exists but is empty
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "")

    def test_write_creates_directory(self):
        """Test that write creates directory if it doesn't exist."""
        nested_dir = os.path.join(self.temp_dir, "nested", "directory")
        output_path = os.path.join(nested_dir, "test_events.jsonl")

        events = [{"test": "data"}]

        # Directory shouldn't exist yet
        self.assertFalse(os.path.exists(nested_dir))

        # Write events
        self.writer.write(events, output_path)

        # Directory should now exist
        self.assertTrue(os.path.exists(nested_dir))
        self.assertTrue(os.path.exists(output_path))

    def test_write_overwrites_existing_file(self):
        """Test that write overwrites existing file."""
        output_path = os.path.join(self.temp_dir, "overwrite_test.jsonl")

        # Write initial data
        initial_events = [{"initial": "data"}]
        self.writer.write(initial_events, output_path)

        # Write new data
        new_events = [{"new": "data1"}, {"new": "data2"}]
        self.writer.write(new_events, output_path)

        # Verify file contains only new data
        with open(output_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0].strip()), {"new": "data1"})
        self.assertEqual(json.loads(lines[1].strip()), {"new": "data2"})

    def test_write_complex_nested_data(self):
        """Test writing complex nested data structures."""
        events = [
            {
                "id": 1,
                "metadata": {"created": "2024-01-01", "tags": ["tag1", "tag2"]},
                "values": [1, 2, 3],
                "nested": {"deep": {"data": "value"}},
            }
        ]
        output_path = os.path.join(self.temp_dir, "complex_events.jsonl")

        # Write events
        self.writer.write(events, output_path)

        # Verify data integrity
        with open(output_path, "r", encoding="utf-8") as f:
            restored_event = json.loads(f.readline().strip())

        self.assertEqual(restored_event, events[0])

    @patch('builtins.open', side_effect=OSError("Permission denied"))
    def test_write_temp_file_oserror(self, mock_open_func):
        """Test handling of OSError during temp file writing."""
        events = [{"test": "data"}]
        output_path = os.path.join(self.temp_dir, "test_events.jsonl")

        with self.assertRaises(OSError) as context:
            self.writer.write(events, output_path)

        self.assertIn("Permission denied", str(context.exception))

    @patch('builtins.open', side_effect=IOError("Disk full"))
    def test_write_temp_file_ioerror(self, mock_open_func):
        """Test handling of IOError during temp file writing."""
        events = [{"test": "data"}]
        output_path = os.path.join(self.temp_dir, "test_events.jsonl")

        with self.assertRaises(IOError) as context:
            self.writer.write(events, output_path)

        self.assertIn("Disk full", str(context.exception))

    def test_write_to_temp_file(self):
        """Test writing to temporary file."""
        events = [{"temp": "data1"}, {"temp": "data2"}]
        temp_path = os.path.join(self.temp_dir, "test.tmp")

        # Call internal method
        self.writer._write_to_temp_file(events, temp_path)

        # Verify temp file exists and contains correct data
        self.assertTrue(os.path.exists(temp_path))

        with open(temp_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0].strip()), {"temp": "data1"})
        self.assertEqual(json.loads(lines[1].strip()), {"temp": "data2"})

    def test_atomic_move_new_file(self):
        """Test atomic move when target file doesn't exist."""
        temp_path = os.path.join(self.temp_dir, "temp.tmp")
        output_path = os.path.join(self.temp_dir, "final.jsonl")

        # Create temp file
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write("test data")

        # Perform atomic move
        self.writer._atomic_move(temp_path, output_path)

        # Verify temp file is gone and output file exists
        self.assertFalse(os.path.exists(temp_path))
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "test data")

    def test_atomic_move_existing_file(self):
        """Test atomic move when target file already exists."""
        temp_path = os.path.join(self.temp_dir, "temp.tmp")
        output_path = os.path.join(self.temp_dir, "final.jsonl")

        # Create existing output file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("old data")

        # Create temp file with new data
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write("new data")

        # Perform atomic move
        self.writer._atomic_move(temp_path, output_path)

        # Verify temp file is gone and output file has new data
        self.assertFalse(os.path.exists(temp_path))
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "new data")

    def test_cleanup_temp_file_exists(self):
        """Test cleanup of existing temporary file."""
        temp_path = os.path.join(self.temp_dir, "cleanup_test.tmp")

        # Create temp file
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write("temp data")

        self.assertTrue(os.path.exists(temp_path))

        # Cleanup temp file
        self.writer._cleanup_temp_file(temp_path)

        # Verify temp file is gone
        self.assertFalse(os.path.exists(temp_path))

    def test_cleanup_temp_file_not_exists(self):
        """Test cleanup when temporary file doesn't exist."""
        temp_path = os.path.join(self.temp_dir, "nonexistent.tmp")

        # Should not raise exception
        self.writer._cleanup_temp_file(temp_path)

    @patch('os.remove', side_effect=OSError("Permission denied"))
    def test_cleanup_temp_file_oserror(self, mock_remove):
        """Test cleanup handles OSError gracefully."""
        temp_path = os.path.join(self.temp_dir, "test.tmp")

        # Create temp file
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write("temp data")

        # Should not raise exception even if removal fails
        self.writer._cleanup_temp_file(temp_path)

    def test_jsonl_format_compliance(self):
        """Test that output follows JSONL format specifications."""
        events = [
            {"field1": "value1", "field2": 123},
            {"field1": "value2", "field2": 456},
        ]
        output_path = os.path.join(self.temp_dir, "jsonl_test.jsonl")

        # Write events
        self.writer.write(events, output_path)

        # Verify JSONL format (each line is valid JSON, no trailing comma)
        with open(output_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Each line should be valid JSON
        for line in lines:
            line = line.strip()
            if line:  # Skip empty lines
                parsed = json.loads(line)
                self.assertIsInstance(parsed, dict)

        # Verify compact JSON format (no spaces after separators)
        self.assertIn('{"field1":"value1","field2":123}', lines[0])
        self.assertIn('{"field1":"value2","field2":456}', lines[1])

    def test_write_failure_cleanup(self):
        """Test that temp file is cleaned up on write failure."""
        events = [{"test": "data"}]
        output_path = os.path.join(self.temp_dir, "test_events.jsonl")
        temp_path = f"{output_path}.tmp"

        # Mock os.rename to fail after temp file is created
        with patch('os.rename', side_effect=OSError("Rename failed")):
            with patch.object(self.writer, '_cleanup_temp_file') as mock_cleanup:
                with self.assertRaises(OSError):
                    self.writer.write(events, output_path)

                # Verify cleanup was called
                mock_cleanup.assert_called_once_with(temp_path)


class TestFileWriterFactory(unittest.TestCase):
    """Test FileWriterFactory implementation."""

    def test_create_jsonl_writer(self):
        """Test creating JSONL writer via factory."""
        writer = FileWriterFactory.create_jsonl_writer()

        self.assertIsInstance(writer, JSONLFileWriter)

    def test_factory_creates_different_instances(self):
        """Test that factory creates separate instances."""
        writer1 = FileWriterFactory.create_jsonl_writer()
        writer2 = FileWriterFactory.create_jsonl_writer()

        self.assertIsInstance(writer1, JSONLFileWriter)
        self.assertIsInstance(writer2, JSONLFileWriter)
        self.assertIsNot(writer1, writer2)  # Different instances


if __name__ == "__main__":
    unittest.main()