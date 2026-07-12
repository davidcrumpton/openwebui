import pytest


@pytest.fixture
def tools(load_tool):
    return load_tool("home-assistant/home-assistant.py")


class TestHomeAssistantTools:
    def test_loads(self, tools):
        assert tools is not None

    def test_ping(self, tools):
        # This should at least return a JSON structure indicating success/failure
        result = tools.ping()
        assert result is not None
        # Should be valid JSON string
        assert '"success"' in result

    def test_get_config(self, tools):
        # This should at least return a JSON structure indicating success/failure
        result = tools.get_config()
        assert result is not None
        # Should be valid JSON string
        assert '"success"' in result

    def test_get_states(self, tools):
        # This should at least return a JSON structure indicating success/failure
        result = tools.get_states()
        assert result is not None
        # Should be valid JSON string
        assert '"success"' in result

    def test_get_services(self, tools):
        # This should at least return a JSON structure indicating success/failure
        result = tools.get_services()
        assert result is not None
        # Should be valid JSON string
        assert '"success"' in result

    def test_get_events(self, tools):
        # This should at least return a JSON structure indicating success/failure
        result = tools.get_events()
        assert result is not None
        # Should be valid JSON string
        assert '"success"' in result

    def test_get_error_log(self, tools):
        # This should at least return a JSON structure indicating success/failure
        result = tools.get_error_log()
        assert result is not None
        # Should be valid JSON string
        assert '"success"' in result

    def test_check_config(self, tools):
        # This should at least return a JSON structure indicating success/failure
        result = tools.check_config()
        assert result is not None
        # Should be valid JSON string
        assert '"success"' in result
        
    def test_get_calendars(self, tools):
        # This should at least return a JSON structure indicating success/failure
        result = tools.get_calendars()
        assert result is not None
        # Should be valid JSON string
        assert '"success"' in result

    def test_render_template(self, tools):
        # Test basic template rendering with simple template
        result = tools.render_template("hello world")
        assert result is not None
        # Should be valid JSON string
        assert '"success"' in result

    def test_get_state(self, tools):
        # Test get_state with a dummy entity_id
        result = tools.get_state("sensor.test")
        assert result is not None
        # Should be valid JSON string
        assert '"success"' in result

    def test_set_state(self, tools):
        # Test set_state with basic values
        result = tools.set_state("sensor.test", "on")
        assert result is not None
        # Should be valid JSON string
        assert '"success"' in result

    def test_call_service(self, tools):
        # Test calling a basic service
        result = tools.call_service("light", "turn_on", {"entity_id": "light.bed_light"})
        assert result is not None
        # Should be valid JSON string
        assert '"success"' in result

    def test_fire_event(self, tools):
        # Test firing an event
        result = tools.fire_event("test_event")
        assert result is not None
        # Should be valid JSON string
        assert '"success"' in result

    @pytest.mark.parametrize(
        "entity_id",
        [
            "sensor.test",
            "light.living_room_light",
            "switch.bedroom_switch"
        ]
    )
    def test_get_history(self, tools, entity_id):
        # Test getting history for various entity types
        result = tools.get_history(entity_id)
        assert result is not None
        # Should be valid JSON string
        assert '"success"' in result

    @pytest.mark.parametrize(
        "start_time, end_time",
        [
            ("", ""),
            ("2023-01-01T00:00:00Z", "2023-01-02T00:00:00Z"),
        ]
    )
    def test_get_logbook(self, tools, start_time, end_time):
        # Test getting logbook entries
        result = tools.get_logbook(start_time=start_time, end_time=end_time)
        assert result is not None
        # Should be valid JSON string
        assert '"success"' in result

    def test_calendar_events(self, tools):
        # Test calendar events with dummy parameters
        result = tools.get_calendar_events("calendar.test", "2023-01-01T00:00:00Z", "2023-01-02T00:00:00Z")
        assert result is not None
        # Should be valid JSON string
        assert '"success"' in result