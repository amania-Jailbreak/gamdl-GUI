
class test():
    def sprint(self,message):
        print(f'[CLASS]{message}')
    def run(self):
        gamdl(urls=['https://music.apple.com/jp/album/spica-single/326430834'],codec_song=SongCodec.ASK,mp4decrypt_path='./binary/mp4decrypt.exe',ffmpeg_path='./binary/ffmpeg.exe',nm3u8dlre_path='./binary/N_m3u8DL-RE.exe',window=self)
a = test()
a.run()