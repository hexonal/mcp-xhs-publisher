import pytest

from mcp_xhs_publisher.publisher import Publisher


@pytest.fixture(scope="module")
def publisher():
    # 可根据需要传递 cookie_dir、cookie_name、sign_url 等参数
    return Publisher.build()


def test_publish_text(publisher):
    result = publisher.publish_text("测试内容", topics=["测试"])
    assert isinstance(result, dict)
    assert result["status"] in ("success", "error")


def test_publish_image(publisher, tmp_path):
    # 创建一个临时图片文件
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"\xff\xd8\xff\xd9")  # 简单 JPEG 头尾
    result = publisher.publish_image(
        "图文内容", image_paths=[str(img_path)], topics=["图文"]
    )
    assert isinstance(result, dict)
    assert result["status"] in ("success", "error")


def test_publish_video(publisher, tmp_path):
    # 创建一个临时视频文件
    video_path = tmp_path / "test.mp4"
    video_path.write_bytes(b"\x00\x00\x00\x18ftypmp42")  # 简单 MP4 头
    result = publisher.publish_video(
        "视频内容", video_path=str(video_path), cover_path=None, topics=["视频"]
    )
    assert isinstance(result, dict)
    assert result["status"] in ("success", "error")


def test_get_user_info(publisher):
    info = publisher.client.get_self_info()
    assert isinstance(info, dict)
    assert "nickname" in info or "user_id" in info
