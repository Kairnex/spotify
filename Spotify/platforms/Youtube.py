import asyncio
import os
import re
from typing import Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch

from Spotify.utils.database import is_on_off
from Spotify.utils.formatters import time_to_seconds

cookies_file = "Spotify/cookies.txt"

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset is None:
            return None
        return text[offset : offset + length]

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["duration"]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["thumbnails"][0]["url"].split("?")[0]

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--cookies", cookies_file,
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            return 0, stderr.decode()

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        playlist = await shell_cmd(
            f"yt-dlp --cookies {cookies_file} -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
        )
        result = [key for key in playlist.split("\n") if key]
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            track_details = {
                "title": result["title"],
                "link": result["link"],
                "vidid": result["id"],
                "duration_min": result["duration"],
                "thumb": result["thumbnails"][0]["url"].split("?")[0],
            }
            return track_details, result["id"]

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {"quiet": True, "cookiefile": cookies_file}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for f in r["formats"]:
                if "dash" not in str(f["format"]).lower():
                    formats_available.append({
                        "format": f.get("format"),
                        "filesize": f.get("filesize"),
                        "format_id": f.get("format_id"),
                        "ext": f.get("ext"),
                        "format_note": f.get("format_note"),
                        "yturl": link,
                    })
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        r = result[query_type]
        return r["title"], r["duration"], r["thumbnails"][0]["url"].split("?")[0], r["id"]

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        loop = asyncio.get_running_loop()

        def safe_dl(ydl_opts, link):
            try:
                ydl = yt_dlp.YoutubeDL(ydl_opts)
                info = ydl.extract_info(link, download=True)
                return os.path.join("downloads", f"{info['id']}.{info.get('ext','mp4')}")
            except Exception as e:
                print(f"[yt-dlp ERROR] {e}")
                # fallback to bestaudio
                fallback_opts = ydl_opts.copy()
                fallback_opts["format"] = "bestaudio/best"
                ydl = yt_dlp.YoutubeDL(fallback_opts)
                info = ydl.extract_info(link, download=True)
                return os.path.join("downloads", f"{info['id']}.{info.get('ext','mp3')}")

        if songvideo:
            ydl_opts = {
                "format": f"{format_id}+140",
                "outtmpl": f"downloads/{title}.%(ext)s",
                "quiet": True,
                "no_warnings": True,
                "cookiefile": cookies_file,
                "merge_output_format": "mp4",
            }
            fpath = await loop.run_in_executor(None, safe_dl, ydl_opts, link)
            return fpath

        elif songaudio:
            ydl_opts = {
                "format": format_id,
                "outtmpl": f"downloads/{title}.%(ext)s",
                "quiet": True,
                "no_warnings": True,
                "cookiefile": cookies_file,
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
                ],
            }
            fpath = await loop.run_in_executor(None, safe_dl, ydl_opts, link)
            return fpath

        elif video:
            ydl_opts = {
                "format": "best[height<=?720][width<=?1280]",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
                "no_warnings": True,
                "cookiefile": cookies_file,
            }
            fpath = await loop.run_in_executor(None, safe_dl, ydl_opts, link)
            return fpath, True

        else:  # audio-only
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
                "no_warnings": True,
                "cookiefile": cookies_file,
            }
            fpath = await loop.run_in_executor(None, safe_dl, ydl_opts, link)
            return fpath, True
