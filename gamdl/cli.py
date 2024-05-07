from __future__ import annotations

import inspect
import json
import logging
from enum import Enum
from pathlib import Path

import click

from . import __version__
from .apple_music_api import AppleMusicApi
from .constants import *
from .downloader import Downloader
from .downloader_music_video import DownloaderMusicVideo
from .downloader_post import DownloaderPost
from .downloader_song import DownloaderSong
from .downloader_song_legacy import DownloaderSongLegacy
from .enums import CoverFormat, DownloadMode, MusicVideoCodec, PostQuality, RemuxMode
from .itunes_api import ItunesApi

apple_music_api_sig = inspect.signature(AppleMusicApi.__init__)
downloader_sig = inspect.signature(Downloader.__init__)
downloader_song_sig = inspect.signature(DownloaderSong.__init__)
downloader_music_video_sig = inspect.signature(DownloaderMusicVideo.__init__)
downloader_post_sig = inspect.signature(DownloaderPost.__init__)


def get_param_string(param: click.Parameter) -> str:
    if isinstance(param.default, Enum):
        return param.default.value
    elif isinstance(param.default, Path):
        return str(param.default)
    else:
        return param.default


def write_default_config_file(ctx: click.Context):
    ctx.params["config_path"].parent.mkdir(parents=True, exist_ok=True)
    config_file = {
        param.name: get_param_string(param)
        for param in ctx.command.params
        if param.name not in EXCLUDED_CONFIG_FILE_PARAMS
    }
    ctx.params["config_path"].write_text(json.dumps(config_file, indent=4))


def load_config_file(
    ctx: click.Context,
    param: click.Parameter,
    no_config_file: bool,
) -> click.Context:
    if no_config_file:
        return ctx
    if not ctx.params["config_path"].exists():
        write_default_config_file(ctx)
    config_file = dict(json.loads(ctx.params["config_path"].read_text()))
    for param in ctx.command.params:
        if (
            config_file.get(param.name) is not None
            and not ctx.get_parameter_source(param.name)
            == click.core.ParameterSource.COMMANDLINE
        ):
            ctx.params[param.name] = param.type_cast_value(ctx, config_file[param.name])
    return ctx

def main(
    urls: list[str],
    disable_music_video_skip: bool = False,
    save_cover: bool = False,
    overwrite: bool = False,
    read_urls_as_txt: bool = False,
    synced_lyrics_only: bool = False,
    no_synced_lyrics: bool =False,
    config_path: Path = Path.home() / ".gamdl" / "config.json",
    log_level: str = "INFO",
    print_exceptions: bool = False,
    cookies_path: Path = apple_music_api_sig.parameters["cookies_path"].default,
    language: str = apple_music_api_sig.parameters["language"].default,
    output_path: Path = downloader_sig.parameters["output_path"].default,
    temp_path: Path = downloader_sig.parameters["temp_path"].default,
    wvd_path: Path = downloader_sig.parameters["wvd_path"].default,
    nm3u8dlre_path: str = downloader_sig.parameters["nm3u8dlre_path"].default,
    mp4decrypt_path: str = downloader_sig.parameters["mp4decrypt_path"].default,
    ffmpeg_path: str = downloader_sig.parameters["ffmpeg_path"].default,
    mp4box_path: str = downloader_sig.parameters["mp4box_path"].default,
    download_mode: DownloadMode = downloader_sig.parameters["download_mode"].default,
    remux_mode: RemuxMode = downloader_sig.parameters["remux_mode"].default,
    cover_format: CoverFormat = downloader_sig.parameters["cover_format"].default,
    template_folder_album: str = downloader_sig.parameters["template_folder_album"].default,
    template_folder_compilation: str = downloader_sig.parameters["template_folder_compilation"].default,
    template_file_single_disc: str = downloader_sig.parameters["template_file_single_disc"].default,
    template_file_multi_disc: str = downloader_sig.parameters["template_file_multi_disc"].default,
    template_folder_no_album: str = downloader_sig.parameters["template_folder_no_album"].default,
    template_file_no_album: str = downloader_sig.parameters["template_file_no_album"].default,
    template_date: str = downloader_sig.parameters["template_date"].default,
    exclude_tags: str = downloader_sig.parameters["exclude_tags"].default,
    cover_size: int = downloader_sig.parameters["cover_size"].default,
    truncate: int = downloader_sig.parameters["truncate"].default,
    codec_song: SongCodec = downloader_song_sig.parameters["codec"].default,
    synced_lyrics_format: SyncedLyricsFormat = downloader_song_sig.parameters["synced_lyrics_format"].default,
    codec_music_video: MusicVideoCodec = downloader_music_video_sig.parameters["codec"].default,
    quality_post: PostQuality = downloader_post_sig.parameters["quality"].default,
    no_config_file: bool = False,
    window = None,
):
    window.logger("debug","Starting downloader")
    if not cookies_path.exists():
        window.logger("error",X_NOT_FOUND_STRING.format("Cookies file", cookies_path))
        return
    apple_music_api = AppleMusicApi(
        cookies_path,
        language=language,
    )
    itunes_api = ItunesApi(
        apple_music_api.storefront,
        apple_music_api.language,
    )
    downloader = Downloader(
        apple_music_api,
        itunes_api,
        output_path,
        temp_path,
        wvd_path,
        nm3u8dlre_path,
        mp4decrypt_path,
        ffmpeg_path,
        mp4box_path,
        download_mode,
        remux_mode,
        cover_format,
        template_folder_album,
        template_folder_compilation,
        template_file_single_disc,
        template_file_multi_disc,
        template_folder_no_album,
        template_file_no_album,
        template_date,
        exclude_tags,
        cover_size,
        truncate,
    )
    downloader_song = DownloaderSong(
        downloader,
        codec_song,
        synced_lyrics_format,
    )
    downloader_song_legacy = DownloaderSongLegacy(
        downloader,
        codec_song,
    )
    downloader_music_video = DownloaderMusicVideo(
        downloader,
        codec_music_video,
    )
    downloader_post = DownloaderPost(
        downloader,
        quality_post,
    )
    if not synced_lyrics_only:
        if wvd_path and not wvd_path.exists():
            window.logger("error",X_NOT_FOUND_STRING.format(".wvd file", wvd_path))
            return
        window.logger("debug","Setting up CDM")
        downloader.set_cdm()
        if not downloader.ffmpeg_path_full and (
            remux_mode == RemuxMode.FFMPEG or download_mode == DownloadMode.NM3U8DLRE
        ):
            window.logger("error",X_NOT_FOUND_STRING.format("ffmpeg", ffmpeg_path))
            return
        if not downloader.mp4box_path_full and remux_mode == RemuxMode.MP4BOX:
            window.logger("error",X_NOT_FOUND_STRING.format("MP4Box", mp4box_path))
            return
        if (
            not downloader.mp4decrypt_path_full
            and codec_song
            not in (
                SongCodec.AAC_LEGACY,
                SongCodec.AAC_HE_LEGACY,
            )
            or (remux_mode == RemuxMode.MP4BOX and not downloader.mp4decrypt_path_full)
        ):
            window.logger("error",X_NOT_FOUND_STRING.format("mp4decrypt", mp4decrypt_path))
            return
        if (
            download_mode == DownloadMode.NM3U8DLRE
            and not downloader.nm3u8dlre_path_full
        ):
            window.logger("error",X_NOT_FOUND_STRING.format("N_m3u8DL-RE", nm3u8dlre_path))
            return
        if not downloader.mp4decrypt_path_full:
            window.logger('warning',
                X_NOT_FOUND_STRING.format("mp4decrypt", mp4decrypt_path)
                + ", music videos will not be downloaded"
            )
            skip_mv = True
        else:
            skip_mv = False
        if codec_song not in LEGACY_CODECS:
            window.logger('warning',
                "You have chosen a non-legacy codec. Support for non-legacy codecs are not guaranteed, "
                "as most of the songs cannot be downloaded when using non-legacy codecs."
            )
    error_count = 0
    if read_urls_as_txt:
        _urls = []
        for url in urls:
            if Path(url).exists():
                _urls.extend(Path(url).read_text().splitlines())
        urls = _urls
    for url_index, url in enumerate(urls, start=1):
        url_progress = f"URL {url_index}/{len(urls)}"
        try:
            window.logger('normal',f'({url_progress}) Checking "{url}"')
            url_info = downloader.get_url_info(url)
            download_queue = downloader.get_download_queue(url_info)
        except Exception as e:
            error_count += 1
            window.logger("error",
                f'({url_progress}) Failed to check "{url}"',
                exc_info=print_exceptions,
            )
            continue
        for queue_index, queue_item in enumerate(download_queue, start=1):
            queue_progress = f"Track {queue_index}/{len(download_queue)} from URL {url_index}/{len(urls)}"
            track = queue_item.metadata
            try:
                window.logger('normal',
                    f'({queue_progress}) Downloading "{track["attributes"]["name"]}"'
                )
                if not track["attributes"].get("playParams"):
                    window.logger('warning',
                        f"({queue_progress}) Track is not streamable, skipping"
                    )
                    continue
                if (
                    (synced_lyrics_only and track["type"] != "songs")
                    or (track["type"] == "music-videos" and skip_mv)
                    or (
                        track["type"] == "music-videos"
                        and url_info.type == "album"
                        and not disable_music_video_skip
                    )
                ):
                    window.logger('warning',
                        f"({queue_progress}) Track is not downloadable with current configuration, skipping"
                    )
                elif track["type"] == "songs":
                    window.logger("debug","Getting lyrics")
                    lyrics = downloader_song.get_lyrics(track)
                    window.logger("debug","Getting webplayback")
                    webplayback = apple_music_api.get_webplayback(track["id"])
                    tags = downloader_song.get_tags(webplayback, lyrics.unsynced)
                    final_path = downloader.get_final_path(tags, ".m4a")
                    lyrics_synced_path = downloader_song.get_lyrics_synced_path(
                        final_path
                    )
                    cover_path = downloader_song.get_cover_path(final_path)
                    cover_url = downloader.get_cover_url(track)
                    if synced_lyrics_only:
                        pass
                    elif final_path.exists() and not overwrite:
                        window.logger('normal',
                            f'({queue_progress}) Song already exists at "{final_path}", skipping'
                        )
                    else:
                        window.logger("debug","Getting stream info")
                        if codec_song in LEGACY_CODECS:
                            stream_info = downloader_song_legacy.get_stream_info(
                                webplayback
                            )
                            window.logger("debug","Getting decryption key")
                            decryption_key = downloader_song_legacy.get_decryption_key(
                                stream_info.pssh, track["id"]
                            )
                        else:
                            stream_info = downloader_song.get_stream_info(track)
                            if not stream_info.stream_url or not stream_info.pssh:
                                window.logger('warning',
                                    f"({queue_progress}) Song is not downloadable or is not"
                                    " available in the chosen codec, skipping"
                                )
                                continue
                            window.logger('warning',"Getting decryption key")
                            decryption_key = downloader.get_decryption_key(
                                stream_info.pssh, track["id"]
                            )
                        encrypted_path = downloader_song.get_encrypted_path(track["id"])
                        decrypted_path = downloader_song.get_decrypted_path(track["id"])
                        remuxed_path = downloader_song.get_remuxed_path(track["id"])
                        window.logger("debug",f"Downloading to {encrypted_path}")
                        downloader.download(encrypted_path, stream_info.stream_url)
                        if codec_song in LEGACY_CODECS:
                            window.logger("debug",f"Remuxing/Decrypting to {remuxed_path}")
                            downloader_song_legacy.remux(
                                encrypted_path,
                                decrypted_path,
                                remuxed_path,
                                decryption_key,
                            )
                        else:
                            window.logger("debug",f"Decrypting to {decrypted_path}")
                            downloader_song.decrypt(
                                encrypted_path, decrypted_path, decryption_key
                            )
                            window.logger("debug",f"Remuxing to {final_path}")
                            downloader_song.remux(
                                decrypted_path,
                                remuxed_path,
                                stream_info.codec,
                            )
                        window.logger("debug","Applying tags")
                        downloader.apply_tags(remuxed_path, tags, cover_url)
                        window.logger("debug",f"Moving to {final_path}")
                        downloader.move_to_output_path(remuxed_path, final_path)
                    if no_synced_lyrics or not lyrics.synced:
                        pass
                    elif lyrics_synced_path.exists() and not overwrite:
                        window.logger("debug",
                            f'Synced lyrics already exists at "{lyrics_synced_path}", skipping'
                        )
                    else:
                        window.logger("debug",f'Saving synced lyrics to "{lyrics_synced_path}"')
                        downloader_song.save_lyrics_synced(
                            lyrics_synced_path, lyrics.synced
                        )
                    if synced_lyrics_only or not save_cover:
                        pass
                    elif cover_path.exists() and not overwrite:
                        window.logger("debug",
                            f'Cover already exists at "{cover_path}", skipping'
                        )
                    else:
                        window.logger("debug",f'Saving cover to "{cover_path}"')
                        downloader.save_cover(cover_path, cover_url)
                elif track["type"] == "music-videos":
                    music_video_id_alt = downloader_music_video.get_music_video_id_alt(
                        track
                    )
                    window.logger("debug","Getting iTunes page")
                    itunes_page = itunes_api.get_itunes_page(
                        "music-video", music_video_id_alt
                    )
                    stream_url_master = downloader_music_video.get_stream_url_master(
                        itunes_page
                    )
                    window.logger("debug","Getting M3U8 data")
                    m3u8_master_data = downloader_music_video.get_m3u8_master_data(
                        stream_url_master
                    )
                    tags = downloader_music_video.get_tags(
                        music_video_id_alt,
                        itunes_page,
                        track,
                    )
                    final_path = downloader.get_final_path(tags, ".m4v")
                    cover_path = downloader_music_video.get_cover_path(final_path)
                    cover_url = downloader.get_cover_url(track)
                    if final_path.exists() and not overwrite:
                        window.logger('warning',
                            f'({queue_progress}) Music video already exists at "{final_path}", skipping'
                        )
                    else:
                        window.logger("debug","Getting stream info")
                        stream_info_video, stream_info_audio = (
                            downloader_music_video.get_stream_info_video(
                                m3u8_master_data
                            ),
                            downloader_music_video.get_stream_info_audio(
                                m3u8_master_data
                            ),
                        )
                        decryption_key_video = downloader.get_decryption_key(
                            stream_info_video.pssh, track["id"]
                        )
                        decryption_key_audio = downloader.get_decryption_key(
                            stream_info_audio.pssh, track["id"]
                        )
                        encrypted_path_video = (
                            downloader_music_video.get_encrypted_path_video(track["id"])
                        )
                        encrypted_path_audio = (
                            downloader_music_video.get_encrypted_path_audio(track["id"])
                        )
                        decrypted_path_video = (
                            downloader_music_video.get_decrypted_path_video(track["id"])
                        )
                        decrypted_path_audio = (
                            downloader_music_video.get_decrypted_path_audio(track["id"])
                        )
                        remuxed_path = downloader_music_video.get_remuxed_path(
                            track["id"]
                        )
                        window.logger("debug",f"Downloading video to {encrypted_path_video}")
                        downloader.download(
                            encrypted_path_video, stream_info_video.stream_url
                        )
                        window.logger("debug",f"Downloading audio to {encrypted_path_audio}")
                        downloader.download(
                            encrypted_path_audio, stream_info_audio.stream_url
                        )
                        window.logger("debug",f"Decrypting video to {decrypted_path_video}")
                        downloader_music_video.decrypt(
                            encrypted_path_video,
                            decryption_key_video,
                            decrypted_path_video,
                        )
                        window.logger("debug",f"Decrypting audio to {decrypted_path_audio}")
                        downloader_music_video.decrypt(
                            encrypted_path_audio,
                            decryption_key_audio,
                            decrypted_path_audio,
                        )
                        window.logger("debug",f"Remuxing to {remuxed_path}")
                        downloader_music_video.remux(
                            decrypted_path_video,
                            decrypted_path_audio,
                            remuxed_path,
                            stream_info_video.codec,
                            stream_info_audio.codec,
                        )
                        window.logger("debug","Applying tags")
                        downloader.apply_tags(remuxed_path, tags, cover_url)
                        window.logger("debug",f"Moving to {final_path}")
                        downloader.move_to_output_path(remuxed_path, final_path)
                    if not save_cover:
                        pass
                    elif cover_path.exists() and not overwrite:
                        window.logger('warning',
                            f'Cover already exists at "{cover_path}", skipping'
                        )
                    else:
                        window.logger("debug",f'Saving cover to "{cover_path}"')
                        downloader.save_cover(cover_path, cover_url)
                elif track["type"] == "uploaded-videos":
                    stream_url = downloader_post.get_stream_url(track)
                    tags = downloader_post.get_tags(track)
                    temp_path = downloader_post.get_temp_path(track["id"])
                    final_path = downloader.get_final_path(tags, ".m4v")
                    cover_path = downloader_music_video.get_cover_path(final_path)
                    cover_url = downloader.get_cover_url(track)
                    if final_path.exists() and not overwrite:
                        window.logger('warning',
                            f'({queue_progress}) Post video already exists at "{final_path}", skipping'
                        )
                    else:
                        window.logger('normal',f"Downloading to {final_path}")
                        downloader.download_ytdlp(temp_path, stream_url)
                        window.logger("debug","Applying tags")
                        downloader.apply_tags(temp_path, tags, cover_url)
                        window.logger("debug",f"Moving to {final_path}")
                        downloader.move_to_output_path(temp_path, final_path)
                    if not save_cover:
                        pass
                    elif cover_path.exists() and not overwrite:
                        window.logger('warning',
                            f'Cover already exists at "{cover_path}", skipping'
                        )
                    else:
                        window.logger("debug",f'Saving cover to "{cover_path}"')
                        downloader.save_cover(cover_path, cover_url)
            except Exception as e:
                error_count += 1
                window.logger('warning',
                    f'({queue_progress}) Failed to download "{track["attributes"]["name"]}"',
                    exc_info=print_exceptions,
                )
            finally:
                if temp_path.exists():
                    window.logger('normal',f'Cleaning up "{temp_path}"')
                    downloader.cleanup_temp_path()
    window.logger('normal',f"Done ({error_count} error(s))")
