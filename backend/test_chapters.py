#!/usr/bin/env python3
"""
测试章节识别功能
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.novel_service import split_chapters, normalize_text


def test_chapter_detection_with_titles():
    """测试有标题的小说"""
    print("\n" + "="*50)
    print("测试1: 有章节标题的小说")
    print("="*50)
    
    sample_path = os.path.join(os.path.dirname(__file__), '../documents/sample_novel.txt')
    
    if not os.path.exists(sample_path):
        print(f"示例小说文件不存在: {sample_path}")
        return False
    
    with open(sample_path, 'r', encoding='utf-8') as f:
        novel_text = f.read()
    
    print(f"文本长度: {len(novel_text)}")
    
    # 规范化文本
    normalized = normalize_text(novel_text)
    
    # 测试章节识别
    chapters = split_chapters(normalized)
    
    print(f"\n识别结果:")
    print(f"识别到 {len(chapters)} 章")
    for i, ch in enumerate(chapters):
        print(f"  第 {i+1} 章: {ch['title']} ({len(ch['content'])} 字)")
    
    return len(chapters) >= 3


def test_chapter_detection_without_titles():
    """测试没有标题的小说"""
    print("\n" + "="*50)
    print("测试2: 没有章节标题的小说")
    print("="*50)
    
    # 创建一个没有标题的测试文本
    novel_text = """窗外的大雨已经下了整整三天。南城旧街的青石板路被雨水冲刷得发亮，两旁的老式路灯在雾气中摇曳，像是随时会熄灭的幽灵。

林澈推开旧书店的门，雨水顺着他的黑色外套滴落在地上。门上的铜铃发出清脆的响声，在寂静的店堂里回荡。

店里弥漫着陈旧纸张特有的气息，混合着淡淡的檀香。四周的书架高耸入云，塞满了发黄的旧书。柜台后面，一盏台灯散发着昏黄的光。

"你终于来了。"

林澈没有立刻回答。他的目光穿过层层书架，落在柜台后面的那个身影上。多年的岁月在那张脸上留下了痕迹，但她依然是记忆中的模样——沈眠，他儿时的玩伴，也是他寻找了十年的人。

"我找了你十年。"林澈的声音低沉，像是从喉咙深处挤出来的。

沈眠轻轻叹了口气，将手中的书放下。"我知道你会来。只是没想到会是在今晚。"

门外站着一个年轻女人。她穿着一件米色的风衣，长发被雨水打湿，贴在脸上。她的眼睛很大，却有一种说不出的疲惫感。

"沈眠姐，我——"女人的声音在看到林澈时戛然而止。

沈眠快步走过去，轻轻拉住女人的手。"小雨，你怎么来了？不是说好今晚不要出门吗？"

小雨没有回答，她的目光一直停留在林澈身上。那眼神里有惊讶，有恐惧，还有一丝难以捉摸的复杂情绪。

第二天清晨，南城旧街笼罩在一层薄雾中。

林澈一夜未眠。他反复翻看父亲留下的那张地图，上面标注的位置在城郊的一座废弃工厂里。

沈眠和苏雨都建议他报警，但林澈知道这事情没那么简单。如果陈志远真的有能力杀死自己的父亲还能逍遥法外这么多年，那么普通的法律途径根本不可能解决问题。"""
    
    print(f"文本长度: {len(novel_text)}")
    
    # 规范化文本
    normalized = normalize_text(novel_text)
    
    # 测试章节识别
    chapters = split_chapters(normalized)
    
    print(f"\n识别结果:")
    print(f"识别到 {len(chapters)} 章")
    for i, ch in enumerate(chapters):
        print(f"  第 {i+1} 章: {ch['title']} ({len(ch['content'])} 字)")
    
    return len(chapters) >= 3


if __name__ == "__main__":
    print("="*60)
    print("测试章节识别功能")
    print("="*60)
    
    success1 = test_chapter_detection_with_titles()
    success2 = test_chapter_detection_without_titles()
    
    print("\n" + "="*60)
    if success1 and success2:
        print("✅ 所有测试通过！")
        sys.exit(0)
    else:
        print("❌ 部分测试失败！")
        sys.exit(1)
