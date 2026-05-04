#!/usr/bin/env python3
"""Generate outfit photo for 坛哥"""

import sys
import os

# Add scripts dir to path
sys.path.insert(0, os.path.dirname(__file__))

from generator import main

if __name__ == "__main__":
    prompt = """年轻少女，白色修身短款露腰针织短袖，紧身贴合身形，凸显腰线锁骨；黑色高腰显瘦皮质短裙，简约利落版型，百搭辣妹风；银色细链条项链、小巧耳钉；慵懒棕黑长卷发，蓬松氛围感，清冷辣妹妆容，眉眼精致，冷白通透皮肤。场景平潭海边网红堤坝，蓝绿色大海、灰色礁石、海边栈道，晴朗白天明媚自然光，海边清透空气感，侧光勾勒身材线条，干净冷白色调，海边街拍感，高清真人质感，性感又清纯的海边辣妹纯欲穿搭。"""
    main(prompt)