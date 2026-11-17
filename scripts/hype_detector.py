#!/usr/bin/env python3
"""
弹幕高潮与热度分析检测器 (Hype Detector)
基于实时聊天流的速度突增 (Chat Velocity Spike)、表情/情绪浓度、大写率计算综合 Hype 评分
输出自动触发剪辑的高光时间段 (Hype Moments)
"""

import time
import math
import re
from collections import deque
from typing import List, Dict, Optional

# 热门高光词库与表情库
HYPE_KEYWORDS = {
    # 爆笑 / 搞砸
    "kekw": 2.5, "lmao": 2.0, "lol": 1.5, "omegalul": 2.5, "haha": 1.5, "xd": 1.5,
    "💀": 2.5, "🤣": 2.5, "😂": 2.0, "233": 2.0, "笑死": 2.5, "草": 1.5,
    # 胜利 / 精彩操作
    "w": 2.0, "pog": 2.5, "poggers": 2.5, "pogu": 2.5, "lets go": 2.0, "ez": 1.5,
    "holy": 2.0, "insane": 2.5, "clutch": 2.5, "goat": 2.0, "🔥": 2.0, "sheesh": 2.0,
    "牛逼": 2.5, "666": 2.0, "nb": 2.0,
    # 震惊 / 惨败 / 反转
    "l": 2.0, "wtf": 2.5, "what": 1.5, "omg": 1.5, "omfg": 2.5, "no way": 2.5,
    "rip": 1.5, "unlucky": 2.0, "nah": 1.5, "bro": 1.5, "😱": 2.5, "😭": 2.0, "麻了": 2.0,
    # 剪辑触发词
    "clip": 3.0, "clip it": 3.5, "clip that": 3.5, "clipper": 3.0, "shorts": 2.0, "tiktok": 2.0
}


class HypeDetector:
    def __init__(
        self,
        window_seconds: float = 8.0,
        baseline_decay: float = 0.05,
        spike_multiplier: float = 2.2,
        min_velocity: float = 1.5,
        cooldown_seconds: float = 30.0,
        clip_duration: float = 30.0
    ):
        self.window_seconds = window_seconds
        self.baseline_decay = baseline_decay
        self.spike_multiplier = spike_multiplier
        self.min_velocity = min_velocity
        self.cooldown_seconds = cooldown_seconds
        self.clip_duration = clip_duration

        self.messages = deque()  # (timestamp, text, author)
        self.baseline_score = 1.0
        self.last_spike_time = -999.0
        self.detected_moments: List[Dict] = []

    def add_message(self, timestamp: float, text: str, author: str) -> Optional[Dict]:
        """
        添加一条聊天记录并评估当前热度
        若触发高光，返回高光事件字典，否则返回 None
        """
        self.messages.append((timestamp, text, author))

        # 清除窗口外旧消息
        cutoff = timestamp - self.window_seconds
        while self.messages and self.messages[0][0] < cutoff:
            self.messages.popleft()

        msg_count = len(self.messages)
        velocity = msg_count / max(1.0, self.window_seconds)  # msg/sec

        # 计算窗口内关键词热度权重
        hype_weight = 0.0
        caps_count = 0
        keyword_hits = {}

        for _, t, _ in self.messages:
            words = re.findall(r"[\w\u4e00-\u9fff]+|[💀🤣😂🔥😱😭]", t.lower())
            if t.isupper() and len(t) >= 4:
                caps_count += 1

            for w in words:
                if w in HYPE_KEYWORDS:
                    weight = HYPE_KEYWORDS[w]
                    hype_weight += weight
                    keyword_hits[w] = keyword_hits.get(w, 0) + 1

        caps_ratio = caps_count / max(1, msg_count)
        # 综合热度得分 = 弹幕速度 * (1 + 关键词权重 / 5) * (1 + 大写比例)
        current_score = velocity * (1.0 + (hype_weight / max(1.0, msg_count * 2))) * (1.0 + caps_ratio * 0.5)

        # 更新自适应基线 (EMA)
        self.baseline_score = (1 - self.baseline_decay) * self.baseline_score + self.baseline_decay * max(1.0, current_score)

        # 判断是否触发热度爆发 (Spike)
        is_spike = (
            current_score >= self.baseline_score * self.spike_multiplier
            and velocity >= self.min_velocity
            and (timestamp - self.last_spike_time) >= self.cooldown_seconds
        )

        if is_spike:
            self.last_spike_time = timestamp
            # 剪辑区间：爆发前 15 秒 ~ 爆发后 15 秒（总共 30 秒）
            start_t = max(0.0, timestamp - (self.clip_duration / 2.0))
            end_t = start_t + self.clip_duration

            # 提取频次最高的高光词
            top_keywords = sorted(keyword_hits.items(), key=lambda x: x[1], reverse=True)[:5]
            keywords_summary = [k[0] for k in top_keywords]

            moment = {
                "id": len(self.detected_moments) + 1,
                "peak_time": round(timestamp, 2),
                "start_time": round(start_t, 2),
                "end_time": round(end_t, 2),
                "duration": round(self.clip_duration, 1),
                "velocity": round(velocity, 2),
                "score": round(current_score, 2),
                "baseline": round(self.baseline_score, 2),
                "top_keywords": keywords_summary,
                "msg_count": msg_count
            }
            self.detected_moments.append(moment)
            return moment

        return None
