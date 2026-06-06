#!/usr/bin/env python3
"""
测试章节识别功能
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.novel_service import split_chapters, normalize_text


def test_chapter_detection():
    """测试章节识别"""
    # 读取示例小说
    sample_path = os.path.join(os.path.dirname(__file__), '../documents/sample_novel.txt')
    
    if not os.path.exists(sample_path):
        print(f"示例小说文件不存在: {sample_path}")
        return False
    
    with open(sample_path, 'r', encoding='utf-8') as f:
        novel_text = f.read()
    
    print(f"读取到小说文本，长度: {len(novel_text)}")
    
    # 规范化文本
    normalized = normalize_text(novel_text)
    
    # 测试章节识别
    chapters = split_chapters(normalized)
    
    print(f"\n识别结果:")
    print(f"识别到 {len(chapters)} 章")
    
    if len(chapters) >= 3:
        print("\n✅ 章节识别成功！")
        return True
    else:
        print(f"\n❌ 章节识别失败！期望 >= 3 章，实际识别到 {len(chapters)} 章")
        return False


if __name__ == "__main__":
    print("="*50)
    print("测试章节识别功能")
    print("="*50)
    success = test_chapter_detection()
    sys.exit(0 if success else 1)
