import yt_dlp, json, os
from threading import Thread
from metatube import sockets, logger
    
class YouTube:
    def is_supported(url):
        extractors = yt_dlp.extractor.gen_extractors()
        for e in extractors:
            if e.suitable(url) and e.IE_NAME == 'youtube':
                return True
        return False

    def fetch_url(url):
        if YouTube.is_supported(url):
            ytdl_options = {'logger': logger}
            with yt_dlp.YoutubeDL(ytdl_options) as ytdl:
                try:
                    info = ytdl.extract_info(url, download=False)
                    return info
                except Exception as e:
                    return str(e)
        else:
            raise ValueError("Invalid URL!")
        
    def verifytemplate(template):
        try:
            yt_dlp.YoutubeDL.validate_outtmpl(template)
            return True
        except ValueError as e:
            logger.error('Error in metatube/youtube.py: ' + str(e))
            return False
        
    def __download(self, url: list, ytdl_options: dict):
        with yt_dlp.YoutubeDL(ytdl_options) as ytdl:
            try:
                ytdl.download(url)
            except Exception as e:
                return e
    
    def download_hook(d):
        if d['status'] == 'finished':
            sockets.downloadprogress({'status': 'finished_ytdl'})
        elif d['status'] == 'downloading':
            if "total_bytes_estimate" in d:
                sockets.downloadprogress({
                    'status': 'downloading', 
                    'downloaded_bytes': d['downloaded_bytes'], 
                    'total_bytes': d['total_bytes_estimate']
                })
            elif 'total_bytes' in d:
                sockets.downloadprogress({
                    'status': 'downloading', 
                    'downloaded_bytes': d['downloaded_bytes'], 
                    'total_bytes': d['total_bytes']
                })
            else:
                sockets.downloadprogress({
                    'status': 'downloading',
                    'total_bytes': 'Unknown'
                })
                
    def postprocessor_hook(d):
        if d['status'] == 'processing' or d['status'] == 'started':
            sockets.downloadprogress({'status': 'processing'})
        elif d['status'] == 'finished':
            sockets.downloadprogress({'status': 'finished_ffmpeg', 'filepath': d['info_dict']['filepath'], 'info_dict': json.dumps(d["info_dict"])})
            
    def get_options(url, ext, output_folder, type, output_format, bitrate, skipfragments, proxy_data, ffmpeg, hw_transcoding, vaapi_device, width, height, verbose):
        proxy = json.loads(proxy_data)
        filepath = os.path.join(output_folder, output_format)
        segments = json.loads(skipfragments)
        postprocessors = []
        postprocessor_args = {}
        proxy_string = ""
        ext = "m4a" if "m4a" in ext else ext
        '''
        Audio:
        If an audio type has been selected, first try to look for a format with the selected extension
        If no audio format with the selected extension has been found, just look for the best audio format
        and automatically convert it to the selected extension anyway
        Video:
        Exactly the same for videos
        '''
        format = f'ba[ext={ext}]/ba' if type == 'Audio' else f'b[ext={ext}]/ba+bv[ext={ext}]/b/ba+bv'
        
        # choose whether to use the FFmpegExtractAudio post processor or the FFmpegVideoConverter one
        if type == 'Audio':
            postprocessors.append({
                "key": "FFmpegExtractAudio",
                "preferredcodec": ext,
                "preferredquality": bitrate
            })
        elif type == 'Video':
            postprocessors.append({
                "key": "FFmpegVideoConvertor",
                "preferedformat": ext
            })
            if bitrate != 'best':
                postprocessor_args["videoconvertor"] = ['-b:a', str(bitrate) + "k"]
                
            if height != 'best' and width != 'best':
                postprocessor_args["videoconvertor"][:0] = ['-vf', 'scale=' + str(width) + ':' + str(height)]
            
            # If hardware transcoding isn't None, add a hardware transcoding thingy to the FFmpeg arguments
            if hw_transcoding != 'None':
                if "videoconvertor" not in postprocessor_args:
                    postprocessor_args["videoconvertor"] = []
                if hw_transcoding == 'nvenc':
                    postprocessor_args["videoconvertor"].extend(['-c:v', 'h264_nvenc'])
                elif hw_transcoding == 'qsv':
                    postprocessor_args["videoconvertor"].extend(['-c:v', 'h264_qsv'])
                elif hw_transcoding == 'videotoolbox':
                    postprocessor_args["videoconvertor"].extend(['-c:v', 'h264_videotoolbox'])
                elif 'vaapi' in hw_transcoding:
                    postprocessor_args["videoconvertor"].extend(['-vaapi_device', vaapi_device, '-c:v', 'h264_vaapi'])
                elif hw_transcoding == 'amd':
                    postprocessor_args["videoconvertor"].extend(['-c:v', 'h264_amf'])
                elif hw_transcoding == 'omx':
                    postprocessor_args["videoconvertor"].extend(['-c:v', 'h264_omx'])
                    
        # If segments have been submitted by the user to exclude, add a ModifyChapters key and add ranges
        if len(segments) > 0:
            ranges = []
            for segment in segments:
                if len(segment["start"]) < 1 or len(segment["end"]) < 1:
                    sockets.searchvideo('Enter all fragment fields!')
                    return False
                else:
                    ranges.append((int(segment["start"]), int(segment["end"])))
            postprocessors.append({
                'key': 'ModifyChapters',
                'remove_ranges': ranges
            })

        ytdl_options = {
            'format': format,
            'postprocessors': postprocessors,
            'postprocessor_args': postprocessor_args,
            'ffmpeg_location': ffmpeg,
            'progress_hooks': [YouTube.download_hook],
            'postprocessor_hooks': [YouTube.postprocessor_hook],
            'logger': logger,
            'outtmpl': filepath,
            'noplaylist': True,
            'verbose': verbose
        }
        
        # Add proxy if proxy is enabled
        if proxy['proxy_type'] != 'None':
            proxy_string = proxy["proxy_type"].lower().strip() + "://"
            if len(proxy["proxy_username"]) > 0 and len(proxy["proxy_username"]) > 0:
                proxy_string += proxy["proxy_username"] + ":" + proxy["proxy_password"] + "@" + proxy["proxy_address"].strip() + ":" + proxy["proxy_port"].strip()
            else:
                proxy_string += proxy["proxy_address"].strip() + ":" + proxy["proxy_port"].strip()
            ytdl_options["proxy"] = proxy_string
        return ytdl_options

    def get_video(self, url, ytdl_options):
        Thread(target=self.__download, args=(url, ytdl_options), name="YouTube-DLP download").start()