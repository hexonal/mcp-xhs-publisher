import argparse
import json
import sys
from typing import List, Optional

from mcp_xhs_publisher.publisher import init_publisher
from mcp_xhs_publisher.utils import check_files_exist, log_error


def parse_topics(topics_str: Optional[str]) -> Optional[List[str]]:
    """
    解析话题字符串为列表。
    Args:
        topics_str: 逗号分隔的话题字符串
    Returns:
        话题列表或 None
    """
    if topics_str:
        return [t.strip() for t in topics_str.split(",") if t.strip()]
    return None


def main():
    parser = argparse.ArgumentParser(description="小红书笔记自动发布 MCP 工具")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # 通用参数
    parser.add_argument("--cookie", required=True, help="小红书 Cookie")
    parser.add_argument("--sign_url", required=True, help="签名服务 URL")

    # 纯文本笔记
    text_parser = subparsers.add_parser("text", help="发布纯文本笔记")
    text_parser.add_argument("--content", required=True, help="笔记内容")
    text_parser.add_argument("--topics", help="话题，逗号分隔")

    # 图文笔记
    image_parser = subparsers.add_parser("image", help="发布图文笔记")
    image_parser.add_argument("--content", required=True, help="笔记内容")
    image_parser.add_argument("--images", required=True, help="图片路径，逗号分隔")
    image_parser.add_argument("--topics", help="话题，逗号分隔")

    # 视频笔记
    video_parser = subparsers.add_parser("video", help="发布视频笔记")
    video_parser.add_argument("--content", required=True, help="笔记内容")
    video_parser.add_argument("--video", required=True, help="视频文件路径")
    video_parser.add_argument("--cover", help="封面图片路径")
    video_parser.add_argument("--topics", help="话题，逗号分隔")

    args = parser.parse_args()

    publisher = init_publisher(args.cookie, args.sign_url)

    try:
        if args.mode == "text":
            result = publisher.publish_text(
                content=args.content, topics=parse_topics(args.topics)
            )
        elif args.mode == "image":
            image_paths = [p.strip() for p in args.images.split(",") if p.strip()]
            if not check_files_exist(image_paths):
                log_error("部分图片文件不存在！")
                sys.exit(1)
            result = publisher.publish_image(
                content=args.content,
                image_paths=image_paths,
                topics=parse_topics(args.topics),
            )
        elif args.mode == "video":
            if not check_files_exist(
                [args.video] + ([args.cover] if args.cover else [])
            ):
                log_error("视频或封面文件不存在！")
                sys.exit(1)
            result = publisher.publish_video(
                content=args.content,
                video_path=args.video,
                cover_path=args.cover,
                topics=parse_topics(args.topics),
            )
        else:
            log_error("未知发布模式")
            sys.exit(1)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        log_error(f"发布失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
