"""Unit tests for event generator functionality."""

import unittest
from unittest.mock import patch

import pytest

from projects.can_data_platform.src.events.generator import (
    BatteryEventGenerator,
    EventGenerator,
    EventGeneratorFactory,
    EventGeneratorInterface,
)
from projects.can_data_platform.src.events.models import BatteryModule, TelemetryEvent


class TestEventGeneratorInterface(unittest.TestCase):
    """Test EventGeneratorInterface abstract base class."""

    def test_interface_cannot_be_instantiated(self):
        """Test that the interface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            EventGeneratorInterface()

    def test_interface_requires_implementation(self):
        """Test that concrete classes must implement required methods."""
        class IncompleteGenerator(EventGeneratorInterface):
            pass

        with pytest.raises(TypeError):
            IncompleteGenerator()


class TestBatteryEventGenerator(unittest.TestCase):
    """Test BatteryEventGenerator implementation."""

    def setUp(self):
        """Set up test instances."""
        self.generator = BatteryEventGenerator()
        self.custom_generator = BatteryEventGenerator(
            num_modules=6,
            voltage_range=(3000, 4000),
            offset_range=(-20, 20),
        )

    def test_initialization_with_defaults(self):
        """Test generator initialization with default parameters."""
        generator = BatteryEventGenerator()
        
        assert generator.num_modules == 4
        assert generator.voltage_range == (3400, 4150)
        assert generator.offset_range == (-40, 40)
        assert len(generator.module_offsets) == 4
        
        # Check that offsets are within expected range
        for offset in generator.module_offsets:
            assert -40 <= offset <= 40

    def test_initialization_with_custom_parameters(self):
        """Test generator initialization with custom parameters."""
        generator = BatteryEventGenerator(
            num_modules=8,
            voltage_range=(3500, 4200),
            offset_range=(-50, 50),
        )
        
        assert generator.num_modules == 8
        assert generator.voltage_range == (3500, 4200)
        assert generator.offset_range == (-50, 50)
        assert len(generator.module_offsets) == 8
        
        # Check that offsets are within expected range
        for offset in generator.module_offsets:
            assert -50 <= offset <= 50

    def test_module_offsets_consistency(self):
        """Test that module offsets remain consistent across calls."""
        generator = BatteryEventGenerator(num_modules=3)
        
        original_offsets = generator.module_offsets.copy()
        
        # Generate events multiple times
        generator.generate_events(5)
        generator.generate_events(3)
        
        # Offsets should remain the same
        assert generator.module_offsets == original_offsets

    def test_generate_events_single_event(self):
        """Test generating a single event."""
        events = self.generator.generate_events(1)
        
        assert len(events) == 1
        assert isinstance(events[0], TelemetryEvent)
        assert events[0].sequence_number == 0

    def test_generate_events_multiple_events(self):
        """Test generating multiple events."""
        num_events = 5
        events = self.generator.generate_events(num_events)
        
        assert len(events) == num_events
        
        # Check sequence numbers are correct
        for i, event in enumerate(events):
            assert isinstance(event, TelemetryEvent)
            assert event.sequence_number == i

    def test_generate_events_zero_events(self):
        """Test generating zero events."""
        events = self.generator.generate_events(0)
        
        assert len(events) == 0
        assert isinstance(events, list)

    def test_generate_events_custom_modules(self):
        """Test generating events with custom number of modules."""
        generator = BatteryEventGenerator(num_modules=6)
        events = generator.generate_events(2)
        
        assert len(events) == 2
        for event in events:
            assert len(event.modules) == 6

    @patch('random.randint')
    def test_generate_modules_voltage_ranges(self, mock_randint):
        """Test that voltage generation respects configured ranges."""
        # Mock random.randint to return predictable values
        # First calls for module offsets during initialization
        mock_randint.side_effect = [10, 20, 30, 40, 3500, 3600, 3700, 3800]
        
        generator = BatteryEventGenerator(
            num_modules=4,
            voltage_range=(3500, 4000),
            offset_range=(0, 50),
        )
        
        modules = generator._generate_modules()
        
        assert len(modules) == 4
        for i, module in enumerate(modules):
            assert isinstance(module, BatteryModule)
            assert module.module_id == i
            # The mock returns 3500+i*100 for base voltage
            expected_base = 3500 + i * 100
            assert module.base_voltage == expected_base
            # Offsets were set during initialization
            assert module.offset in [10, 20, 30, 40]

    def test_generate_modules_structure(self):
        """Test the structure of generated modules."""
        modules = self.generator._generate_modules()
        
        assert len(modules) == self.generator.num_modules
        
        for i, module in enumerate(modules):
            assert isinstance(module, BatteryModule)
            assert module.module_id == i
            assert isinstance(module.base_voltage, int)
            assert isinstance(module.offset, int)
            
            # Check voltage is within range
            assert self.generator.voltage_range[0] <= module.base_voltage <= self.generator.voltage_range[1]
            
            # Check offset matches pre-generated offset
            assert module.offset == self.generator.module_offsets[i]

    def test_voltage_range_boundaries(self):
        """Test voltage generation at range boundaries."""
        # Test with narrow range
        generator = BatteryEventGenerator(
            num_modules=2,
            voltage_range=(3400, 3401),  # Very narrow range
            offset_range=(0, 0),  # No offset variation
        )
        
        modules = generator._generate_modules()
        
        for module in modules:
            assert 3400 <= module.base_voltage <= 3401

    def test_offset_range_boundaries(self):
        """Test offset generation at range boundaries."""
        # Test with narrow offset range
        generator = BatteryEventGenerator(
            num_modules=2,
            voltage_range=(3500, 3500),  # Fixed voltage
            offset_range=(-1, 1),  # Very narrow offset range
        )
        
        for offset in generator.module_offsets:
            assert -1 <= offset <= 1

    def test_event_uniqueness(self):
        """Test that generated events have unique characteristics."""
        events = self.generator.generate_events(10)
        
        # Check sequence numbers are unique
        sequence_numbers = [event.sequence_number for event in events]
        assert len(set(sequence_numbers)) == len(sequence_numbers)
        
        # Check timestamps are unique (assuming they're generated close enough in time)
        timestamps = [event.epoch_timestamp for event in events]
        assert len(set(timestamps)) == len(timestamps)
        
        # Check event IDs are unique
        event_ids = [event.event_id for event in events]
        assert len(set(event_ids)) == len(event_ids)

    def test_interface_compliance(self):
        """Test that BatteryEventGenerator implements the interface correctly."""
        assert isinstance(self.generator, EventGeneratorInterface)
        
        # Should have the required method
        assert hasattr(self.generator, 'generate_events')
        assert callable(getattr(self.generator, 'generate_events'))


class TestEventGeneratorFactory(unittest.TestCase):
    """Test EventGeneratorFactory functionality."""

    def test_create_battery_generator_default(self):
        """Test creating battery generator with default parameters."""
        generator = EventGeneratorFactory.create_battery_generator()
        
        assert isinstance(generator, BatteryEventGenerator)
        assert generator.num_modules == 4
        assert generator.voltage_range == (3400, 4150)
        assert generator.offset_range == (-40, 40)

    def test_create_battery_generator_with_parameters(self):
        """Test creating battery generator with custom parameters."""
        generator = EventGeneratorFactory.create_battery_generator(
            num_modules=8,
            voltage_range=(3000, 4500),
            offset_range=(-100, 100),
        )
        
        assert isinstance(generator, BatteryEventGenerator)
        assert generator.num_modules == 8
        assert generator.voltage_range == (3000, 4500)
        assert generator.offset_range == (-100, 100)

    def test_create_battery_generator_partial_parameters(self):
        """Test creating battery generator with some custom parameters."""
        generator = EventGeneratorFactory.create_battery_generator(
            num_modules=6,
            # voltage_range and offset_range use defaults
        )
        
        assert isinstance(generator, BatteryEventGenerator)
        assert generator.num_modules == 6
        assert generator.voltage_range == (3400, 4150)  # Default
        assert generator.offset_range == (-40, 40)  # Default

    def test_factory_creates_independent_instances(self):
        """Test that factory creates independent generator instances."""
        generator1 = EventGeneratorFactory.create_battery_generator(num_modules=4)
        generator2 = EventGeneratorFactory.create_battery_generator(num_modules=4)
        
        assert generator1 is not generator2
        assert generator1.module_offsets != generator2.module_offsets  # Should be different due to randomness


class TestEventGeneratorAlias(unittest.TestCase):
    """Test backward compatibility alias."""

    def test_event_generator_alias(self):
        """Test that EventGenerator is an alias for BatteryEventGenerator."""
        assert EventGenerator is BatteryEventGenerator

    def test_alias_functionality(self):
        """Test that the alias works as expected."""
        generator = EventGenerator(num_modules=3)
        
        assert isinstance(generator, BatteryEventGenerator)
        assert generator.num_modules == 3
        
        events = generator.generate_events(2)
        assert len(events) == 2


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios and edge cases."""

    def test_large_number_of_events(self):
        """Test generating a large number of events."""
        generator = BatteryEventGenerator()
        events = generator.generate_events(1000)
        
        assert len(events) == 1000
        
        # Check that all events are valid
        for i, event in enumerate(events):
            assert event.sequence_number == i
            assert len(event.modules) == 4

    def test_single_module_generator(self):
        """Test generator with only one module."""
        generator = BatteryEventGenerator(num_modules=1)
        events = generator.generate_events(3)
        
        assert len(events) == 3
        for event in events:
            assert len(event.modules) == 1
            assert event.modules[0].module_id == 0

    def test_extreme_voltage_ranges(self):
        """Test generator with extreme voltage ranges."""
        generator = BatteryEventGenerator(
            num_modules=2,
            voltage_range=(1, 10000),
            offset_range=(-5000, 5000),
        )
        
        events = generator.generate_events(5)
        assert len(events) == 5
        
        for event in events:
            for module in event.modules:
                assert 1 <= module.base_voltage <= 10000
                assert -5000 <= module.offset <= 5000

    def test_reproducibility_with_seed(self):
        """Test that generator behavior can be made reproducible."""
        import random
        
        # Set seed and generate events
        random.seed(42)
        generator1 = BatteryEventGenerator(num_modules=3)
        events1 = generator1.generate_events(5)
        
        # Reset seed and generate again
        random.seed(42)
        generator2 = BatteryEventGenerator(num_modules=3)
        events2 = generator2.generate_events(5)
        
        # Results should be identical
        assert len(events1) == len(events2)
        for event1, event2 in zip(events1, events2):
            assert event1.sequence_number == event2.sequence_number
            assert len(event1.modules) == len(event2.modules)
            for mod1, mod2 in zip(event1.modules, event2.modules):
                assert mod1.module_id == mod2.module_id
                assert mod1.base_voltage == mod2.base_voltage
                assert mod1.offset == mod2.offset
