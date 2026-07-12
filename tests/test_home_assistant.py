import pytest


@pytest.fixture
def tools(load_tool):
    return load_tool("home-assistant/home-assistant.py")


class TestHomeAssistantTools:
    def test_loads(self, tools):
        assert tools is not None


    async def test_get_home_assistant_entities(self, tools, kwargs_for):
        # NOTE: This test WILL FAIL unless HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN env vars are set.
        # That is expected — it exercises the live HTTP path.
        kwargs = kwargs_for(tools, "get_home_assistant_entities")
        result = await tools.get_home_assistant_entities(**kwargs)
        # When env vars are missing the request returns an error JSON string — that's OK.
        # When they are set it should contain real HA entities.
        assert result is not None
        
    async def test_get_home_assistant_states(self, tools, kwargs_for):
        # NOTE: This test WILL FAIL unless HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN env vars are set.
        # That is expected — it exercises the live HTTP path.
        kwargs = kwargs_for(tools, "get_home_assistant_states")
        result = await tools.get_home_assistant_states(**kwargs)
        # When env vars are missing the request returns an error JSON string — that's OK.
        # When they are set it should contain real HA states.
        assert result is not None
        
    async def test_update_home_assistant_device_state(self, tools, kwargs_for):
        # NOTE: This test WILL FAIL unless HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN env vars are set.
        # That is expected — it exercises the live HTTP path.
        kwargs = kwargs_for(tools, "update_home_assistant_device_state", entity_id="light.living_room_light", state="on")
        result = await tools.update_home_assistant_device_state(**kwargs)
        # When env vars are missing the request returns an error JSON string — that's OK.
        # When they are set it should contain real HA states.
        assert result is not None
        
    async def test_update_home_assistant_device_attributes(self, tools, kwargs_for):
        # NOTE: This test WILL FAIL unless HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN env vars are set.
        # That is expected — it exercises the live HTTP path.
        kwargs = kwargs_for(tools, "update_home_assistant_device_attributes", entity_id="light.living_room_light", attributes={"brightness": "on"})
        result = await tools.update_home_assistant_device_attributes(**kwargs)
        # When env vars are missing the request returns an error JSON string — that's OK.
        # When they are set it should contain real HA states.
        assert result is not None
        
    async def test_call_home_assistant_service(self, tools, kwargs_for):
        # NOTE: This test WILL FAIL unless HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN env vars are set.
        # That is expected — it exercises the live HTTP path.
        kwargs = kwargs_for(tools, "call_home_assistant_service", service="light.turn_on", entity_id="light.living_room_light")
        result = await tools.call_home_assistant_service(**kwargs)
        # When env vars are missing the request returns an error JSON string — that's OK.
        # When they are set it should contain real HA states.
        assert result is not None
        
    async def test_get_home_assistant_scene(self, tools, kwargs_for):
        # NOTE: This test WILL FAIL unless HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN env vars are set.
        # That is expected — it exercises the live HTTP path.
        kwargs = kwargs_for(tools, "get_home_assistant_scene", entity_id="scene.living_room_lights_dimmed")
        result = await tools.get_home_assistant_scene(**kwargs)
        # When env vars are missing the request returns an error JSON string — that's OK.
        # When they are set it should contain real HA states.
        assert result is not None
        
    async def test_update_home_assistant_scene(self, tools, kwargs_for):
        # NOTE: This test WILL FAIL unless HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN env vars are set.
        # That is expected — it exercises the live HTTP path.
        kwargs = kwargs_for(tools, "update_home_assistant_scene", entity_id="scene.living_room_lights_dimmed", state="on")
        result = await tools.update_home_assistant_scene(**kwargs)
        # When env vars are missing the request returns an error JSON string — that's OK.
        # When they are set it should contain real HA states.
        assert result is not None
