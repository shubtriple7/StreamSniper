#!/usr/bin/env python3
"""
跨平台实时直播聊天流抓取器
支持: Twitch, Kick, YouTube
输出标准化聊天流供 Hype Detector 实时分析
"""

import sys
import os
import re
import json
import time
import socket
import asyncio
from typing import Callable, Optional, Dict
from dataclasses import dataclass

@dataclass
class ChatMessage:
    platform: str
    author: str
    text: str
    timestamp: float  # 秒数（自启动以来的相对时间或绝对时间）


class TwitchChatListener:
    """Twitch 实时 IRC 聊天监听器 (无需 API Key，匿名连接)"""
    def __init__(self, channel: str, callback: Callable[[ChatMessage], None]):
        self.channel = channel.lower().lstrip('#')
        self.callback = callback
        self.running = False
        self._sock = None

    def start(self, start_time: float):
        self.running = True
        self.start_time = start_time
        try:
            self._sock = socket.socket()
            self._sock.settimeout(2.0)
            self._sock.connect(('irc.chat.twitch.tv', 6667))
            self._sock.send(f"PASS oauth:dummy\r\nNICK justinfan{int(time.time())%100000}\r\nJOIN #{self.channel}\r\n".encode())

            buffer = ""
            while self.running:
                try:
                    data = self._sock.recv(4096).decode('utf-8', errors='ignore')
                    if not data:
                        break
                    buffer += data
                    lines = buffer.split('\r\n')
                    buffer = lines.pop()

                    for line in lines:
                        if line.startswith("PING"):
                            self._sock.send(b"PONG :tmi.twitch.tv\r\n")
                        elif "PRIVMSG" in line:
                            match = re.match(r":([^!]+)![^ ]+ PRIVMSG #[^ ]+ :(.*)", line)
                            if match:
                                author = match.group(1)
                                text = match.group(2)
                                rel_time = time.time() - self.start_time
                                self.callback(ChatMessage(platform="twitch", author=author, text=text, timestamp=rel_time))
                except socket.timeout:
                    continue
                except Exception:
                    break
        finally:
            if self._sock:
                self._sock.close()

    def stop(self):
        self.running = False


class KickChatListener:
    """Kick 实时 Pusher WebSocket 聊天监听器"""
    def __init__(self, channel: str, callback: Callable[[ChatMessage], None]):
        self.channel = channel.lower()
        self.callback = callback
        self.running = False
        self.chatroom_id = None

    def _get_chatroom_id(self) -> Optional[int]:
        try:
            from curl_cffi import requests
            r = requests.get(f"https://kick.com/api/v2/channels/{self.channel}", impersonate="chrome124", timeout=10)
            if r.status_code == 200:
                data = r.json()
                return data.get("chatroom", {}).get("id")
        except Exception as e:
            print(f"⚠️ 获取 Kick chatroom id 异常: {e}")
        return None

    async def _listen_ws(self, start_time: float):
        import websockets
        pusher_key = "34bf7a0ff419a2a775b9"
        cluster = "us2"
        uri = f"wss://ws-{cluster}.pusher.com/app/{pusher_key}?protocol=7&client=js&version=8.4.0-rc2&flash=false"

        while self.running:
            try:
                async with websockets.connect(uri, ping_interval=20, ping_timeout=10) as ws:
                    sub_payload = {
                        "event": "pusher:subscribe",
                        "data": {"auth": "", "channel": f"chatrooms.{self.chatroom_id}.v2"}
                    }
                    await ws.send(json.dumps(sub_payload))

                    while self.running:
                        msg_str = await ws.recv()
                        data = json.loads(msg_str)
                        event = data.get("event")
                        if event == "App\\Events\\ChatMessageEvent":
                            cdata = json.loads(data.get("data", "{}"))
                            author = cdata.get("sender", {}).get("username", "user")
                            content = cdata.get("content", "")
                            rel_time = time.time() - start_time
                            self.callback(ChatMessage(platform="kick", author=author, text=content, timestamp=rel_time))
            except Exception as e:
                if self.running:
                    await asyncio.sleep(2)

    def start(self, start_time: float):
        self.running = True
        self.chatroom_id = self._get_chatroom_id()
        if not self.chatroom_id:
            print(f"❌ 无法获取 Kick 频道 [{self.channel}] 的聊天室信息")
            return
        asyncio.run(self._listen_ws(start_time))

    def stop(self):
        self.running = False


class YouTubeChatListener:
    """YouTube 实时 Live Chat 监听器 (基于 pytchat)"""
    def __init__(self, video_id: str, callback: Callable[[ChatMessage], None]):
        self.video_id = video_id
        self.callback = callback
        self.running = False

    def start(self, start_time: float):
        self.running = True
        try:
            import pytchat
            chat = pytchat.create(video_id=self.video_id)
            while self.running and chat.is_alive():
                for c in chat.get().sync_items():
                    rel_time = time.time() - start_time
                    self.callback(ChatMessage(platform="youtube", author=c.author.name, text=c.message, timestamp=rel_time))
                time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ YouTube live chat error: {e}")

    def stop(self):
        self.running = False
