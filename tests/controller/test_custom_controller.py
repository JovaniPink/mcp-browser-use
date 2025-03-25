import pytest
from browser_use.agent.views import ActionResult
from mcp_browser_use.controller.custom_controller import CustomController


@pytest.mark.asyncio
async def test_copy_to_clipboard():
    controller = CustomController()
    copy_action = controller.registry.actions["Copy text to clipboard"]
    result = copy_action("Test Clip")
    assert isinstance(result, ActionResult)
    assert result.extracted_content == "Test Clip"
    assert result.error is None


@pytest.mark.asyncio
async def test_paste_from_clipboard(mocker):
    controller = CustomController()
    paste_action = controller.registry.actions["Paste text from clipboard"]
    # Mock a browser context
    fake_browser_context = mocker.MagicMock()
    fake_page = mocker.MagicMock()
    fake_browser_context.get_current_page.return_value = fake_page
    # Simulate reading from clipboard
    mocker.patch("pyperclip.paste", return_value="ClipboardData")

    result = await paste_action(fake_browser_context)
    assert result.extracted_content == "ClipboardData"
    fake_page.keyboard.type.assert_called_with("ClipboardData")
