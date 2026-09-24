"""Multimodal protocol tests."""

from ai_platform_protocol.multimodal import (
    ImageContent,
    ImageReference,
    MultimodalMessage,
    MultimodalRequest,
    TextContent,
)


def test_text_and_image_content_ordering():
    ref = ImageReference(
        id="img1",
        mime_type="image/png",
        width=100,
        height=50,
        byte_size=1024,
        storage_reference="temp://img1",
        sha256="abc",
    )
    message = MultimodalMessage(
        role="user",
        content=[
            TextContent(text="Describe this"),
            ImageContent(image=ref),
            TextContent(text="and compare"),
        ],
    )
    assert message.text_parts() == ["Describe this", "and compare"]
    assert len(message.image_parts()) == 1


def test_multimodal_request_from_prompt_and_images():
    ref = ImageReference(
        id="img1",
        mime_type="image/png",
        width=10,
        height=10,
        byte_size=100,
        storage_reference="temp://img1",
        sha256="def",
    )
    request = MultimodalRequest(prompt="Hello", images=[ref])
    messages = request.resolved_messages()
    assert len(messages) == 1
    assert request.image_count() == 1


def test_multimodal_request_serialization():
    request = MultimodalRequest(prompt="test")
    data = request.model_dump()
    assert data["prompt"] == "test"
