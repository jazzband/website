"""
Tests for mixin classes.

These tests cover database mixins and their functionality.
"""

from datetime import datetime

from jazzband.mixins import Syncable, timestamp_before_update


def test_timestamp_before_update(mock_target):
    """Test timestamp_before_update event listener."""
    # Create a datetime before calling the function
    before_time = datetime.utcnow()

    # Call the event listener
    timestamp_before_update(None, None, mock_target)

    # Verify synced_at was updated to a recent time
    assert hasattr(mock_target, "synced_at")
    assert isinstance(mock_target.synced_at, datetime)

    # Should be updated to a time after our before_time
    assert mock_target.synced_at >= before_time


def test_timestamp_before_update_with_monkeypatch(mock_target, monkeypatch):
    """Test timestamp_before_update with predictable time using monkeypatch."""
    # Use monkeypatch to replace the entire datetime module in the mixins module
    fixed_time = datetime(2023, 1, 1, 12, 0, 0)

    class MockDatetime:
        @staticmethod
        def utcnow():
            return fixed_time

    # Patch the datetime import in the mixins module
    monkeypatch.setattr("jazzband.mixins.datetime", MockDatetime)

    # Call the event listener
    timestamp_before_update(None, None, mock_target)

    # Verify synced_at was set to our fixed time
    assert mock_target.synced_at == fixed_time


def test_syncable_has_synced_at_column():
    """Test that Syncable mixin has synced_at column defined."""
    # Verify the column exists
    assert hasattr(Syncable, "synced_at")

    # The synced_at should be a SQLAlchemy Column
    synced_at = Syncable.synced_at
    assert str(synced_at.type) == "DATETIME"  # Check it's a DateTime column
    assert synced_at.nullable is False  # Should be not nullable
    assert synced_at.default is not None  # Should have a default


def test_syncable_sync_method_exists():
    """Test that Syncable has sync class method."""
    assert hasattr(Syncable, "sync")
    assert callable(Syncable.sync)


def test_sub_dict_usage_in_sync():
    """Test that sub_dict is imported and available."""
    from jazzband.utils import sub_dict

    # Test the sub_dict function used by Syncable.sync
    test_data = {"id": 1, "name": "test", "extra": "ignored"}
    fields = ["id", "name"]

    result = sub_dict(test_data, fields)

    assert result == {"id": 1, "name": "test"}
    assert "extra" not in result
