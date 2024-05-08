import customtkinter,pyperclip
from customtkinter import filedialog
import webbrowser,ctypes,os,sys,json,threading,re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
import subprocess
from gamdl.cli import main as gamdl
from gamdl.enums import *
from pathlib import Path
def isCheckURL(url):
    try:
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            return True
        elif response.status_code == 405:  # Method Not Allowed
            allowed_methods = response.headers.get('Allow', '')
            if 'GET' in allowed_methods:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    return True
                else:
                    print(f"URL is not valid. HTTP status code: {response.status_code}")
                    return False
            else:
                print(f"URL is not valid. Neither HEAD nor GET requests are allowed.")
                return False
        else:
            print(f"URL is not valid. HTTP status code: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"URL is not valid. Error: {e}")
        return False

        
        


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
if not os.path.exists(os.path.join(os.path.abspath("."),'config.json')):
    with open(os.path.join(os.path.abspath("."),'config.json'), 'w') as f:
        f.write('''
{
    "lang": "ja-JP",
    "download_mode": "nm3u8dlre",
    "codic": "aac-legacy",
    "output_url": "./AppleMusic"
}
''')
    
if not os.path.exists("./cookies.txt"):
    MessageBox = ctypes.windll.user32.MessageBoxW
    MessageBox(None, 'Please check for the existence of cookies.txt', 'Error', 0)
    sys.exit()

class config():
    def __init__(self):
        with open('config.json') as f:
            self.config = json.load(f)
config = config().config
class TextBox(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.download_text = customtkinter.CTkLabel(self,text='AppleMusic Share URL',width=600)
        self.download_text.grid(row=1,column=0,padx=10, pady=10,sticky='ew') 
        
        self.download_url_box = customtkinter.CTkTextbox(self,height=10)
        self.download_url_box.grid(row=2,column=0,padx=10, pady=10,sticky='ew')
        
        class dl_buttons(customtkinter.CTkFrame):
            def __init__(self, master, **kwargs):
                super().__init__(master, **kwargs)
        
                self.paste_button = customtkinter.CTkButton(self, text="Paste", command=self.paste,width=280)
                self.paste_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
                self.get_all_music_links_button = customtkinter.CTkButton(self, text="Get all music by artist", command=self.get_all_music_links,width=280)
                self.get_all_music_links_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

            def get_all_music_links(self):
                url = self.master.download_url_box.get("0.0","end-1c")
                self.master.download_url_box.delete('0.0','end-1c')
                if "," in url:
                    url = url.split(',')
                elif ' ' in url:
                    url = url.split(' ')
                elif '\r\n' in url:
                    url = url.split('\r\n')
                elif '\n' in url:
                    url = url.split('\n')
                elif '.txt' in url:
                    with open(url, encoding='utf-8') as f:
                        url = f.readlines()
                        url = [i.replace('\n','') for i in url]
                else:
                    url = [url]
                self.url = url
                links = ""
                self.tmp_progress = 0
                self.all_tmp_progress = len(self.url)
                self.master.master.master.log.music_progressbar.set(0)
                self.get_all_music_links_button.configure(state='disabled')
                self.get_all_music_links_button.configure(text='Getting...')
                self.master.download_url_box.configure(state='disabled')
                def get_all_music_links():
                    url = self.url
                    for url in self.url:
                        if not isCheckURL(url):
                            continue
                        if not 'artist' in url:
                            continue
                        options = webdriver.ChromeOptions()
                        options.add_argument('--headless')
                        driver = webdriver.Chrome(options=options)
                        driver.get(url.replace('/see-all?section=top-songs','') + "/see-all?section=top-songs")
                        while True:
                            last_height = driver.execute_script("return document.getElementById('scrollable-page').scrollHeight")
                            driver.execute_script("document.getElementById('scrollable-page').scrollTo(0, document.getElementById('scrollable-page').scrollHeight)")
                            time.sleep(2)
                            new_height = driver.execute_script("return document.getElementById('scrollable-page').scrollHeight")
                            if new_height == last_height:
                                break
                        elements = driver.find_elements(by=By.XPATH, value="//a[contains(@data-testid, 'track-seo-link')]")
                        links = ""
                        for element in elements:
                            url = element.get_attribute("href")
                            if 'song' not in url:
                                continue
                            links += url + "\n"
                        driver.quit()
                        self.master.download_url_box.configure(state='normal')
                        self.master.download_url_box.insert('end',text=links)
                        self.master.download_url_box.configure(state='disabled')
                        self.tmp_progress += 1
                        self.master.master.master.log.music_progressbar.set(self.tmp_progress/self.all_tmp_progress)
                    self.get_all_music_links_button.configure(state='normal')
                    self.get_all_music_links_button.configure(text='Get all music by artist')
                    self.master.download_url_box.configure(state='normal')
                th1 = threading.Thread(target=get_all_music_links)
                th1.start()
            def paste(self):
                self.master.download_url_box.delete('0.0','end-1c')
                self.master.download_url_box.insert('0.0',text=pyperclip.paste())
        
        self.dl_buttons = dl_buttons(self)
        self.dl_buttons.grid(row=3, column=0, padx=10, pady=10, sticky='ew')
        
        self.output_text = customtkinter.CTkLabel(self,text='output directory')
        self.output_text.grid(row=4,column=0,padx=10, pady=10,sticky='ew') 
        
        self.output_url_box = customtkinter.CTkTextbox(self,height=10)
        self.output_url_box.grid(row=5,column=0,padx=10, pady=10,sticky='ew')
        self.output_url_box.insert('0.0',text=config['output_url'])
        
        self.open_dir_button = customtkinter.CTkButton(self, text="Open Directory", command=self.open_directory)
        self.open_dir_button.grid(row=6, column=0, padx=10, pady=10, sticky="ew")
        
    def open_directory(self):
        self.output_url_box.delete('0.0','end-1c')
        self.output_url_box.insert('0.0',text=filedialog.askdirectory())

class Option(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.lang_text = customtkinter.CTkLabel(self,text='Language')
        self.lang_text.grid(row=1,column=0,padx=10,pady=10,sticky='ew')
        
        self.lang = customtkinter.CTkSegmentedButton(self, values=["en-US", "ja-JP"],width=100)
        self.lang.set(config['lang'])
        self.lang.grid(row=2,column=0,padx=10,pady=10,sticky='ew')
        
        self.download_mode_text = customtkinter.CTkLabel(self,text='Download Mode')
        self.download_mode_text.grid(row=3,column=0,padx=10,pady=10,sticky='ew')
        
        self.download_mode = customtkinter.CTkSegmentedButton(self, values=["ytdlp", "nm3u8dlre"],width=100)
        self.download_mode.set(config['download_mode'])
        self.download_mode.grid(row=4,column=0,padx=10,pady=10,sticky='ew')
        
        self.codic_text = customtkinter.CTkLabel(self,text='Codec')
        self.codic_text.grid(row=5,column=0,padx=10,pady=10,sticky='ew')
        
        self.codic = customtkinter.CTkSegmentedButton(self, values=['Dolby Atmos','ALAC','AAC','AAC-LEGACY'],width=100)
        self.codic.set(config['codic'])
        self.codic.grid(row=6,column=0,padx=10,pady=10,sticky='ew')


class Setting(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.option = Option(master=self,width=100)
        self.option.grid(row=1, column=1, padx=10, pady=5,sticky='ew')
        
        self.textbox = TextBox(master=self,width=100)
        self.textbox.grid(row=1, column=0, padx=10, pady=5,sticky='ew')

class button(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.button = customtkinter.CTkButton(self, text="Download", command=self.download)
        self.button.grid(row=0, column=2, padx=10, pady=10,sticky='n')
        self.buttons = customtkinter.CTkButton(self, text="How to Setup", command=self.setup)
        self.buttons.grid(row=0, column=0, padx=10, pady=10,sticky='n')
        
        self.checkbox = customtkinter.CTkCheckBox(self, text="overwrite")
        self.checkbox.grid(row=0, column=3, padx=10, pady=10,sticky='n')
        
        self.lyrics = customtkinter.CTkCheckBox(self, text="no Lyrics")
        self.lyrics.grid(row=0, column=4, padx=10, pady=10,sticky='n')
    def logger(self,mode='normal',message=None):
        self.master.log.log.configure(state="normal")
        if mode == 'normal':
            mode = '[INFO]'
        if mode == 'warning':
            mode = '[WARNING]'
            return
        if mode == 'error':
            mode = '[CRITICAL]'
        if mode == 'debug':
            mode = '[DEBUG]'
            return
        self.master.log.log.insert('end', f'{mode} {message}\n')
        self.master.log.log.see("end")
        self.master.log.log.configure(state="disabled")
    def progless(self,type,value):
        if type == 'playlist':
            self.master.log.playlist_progressbar.set(value)
        elif type == 'music':
            self.master.log.music_progressbar.set(value)
        elif type == 'all':
            self.master.log.music_progressbar.set(value)
            self.master.log.playlist_progressbar.set(value)
            
        
    def download(self):
        url = self.master.setting.textbox.download_url_box.get("0.0","end-1c")
        if url == "":
            MessageBox = ctypes.windll.user32.MessageBoxW
            MessageBox(None, 'Please input URL', 'Error', 0)
            return
        if "," in url:
            url = url.split(',')
        elif ' ' in url:
            url = url.split(' ')
        elif '\r\n' in url:
            url = url.split('\r\n')
        elif '\n' in url:
            url = url.split('\n')
        elif '.txt' in url:
            with open(url, encoding='utf-8') as f:
                url = f.readlines()
                url = [i.replace('\n','') for i in url]
        else:
            url = [url]
        self.url = url
        self.args = {}
        self.args["lang"] = self.master.setting.option.lang.get()
        self.args["output"] = Path(self.master.setting.textbox.output_url_box.get("0.0","end-1c"))
        codec = self.master.setting.option.codic.get()
        if codec == 'AAC':
            self.args["codec"] = SongCodec.AAC
        elif codec == 'AAC-LEGACY':
            self.args['codec'] = SongCodec.AAC_LEGACY
        elif codec == 'Dolby Atmos':
            self.args['codec'] = SongCodec.ATMOS
        elif codec == 'ALAC':
            self.args['codec'] = SongCodec.ALAC
        else:
            self.logger(mode='warning',message='Use aac-legacy due to unavailability of codecs')
            self.args['codec'] = SongCodec.AAC_LEGACY
            
        if self.master.setting.option.download_mode.get() == 'nm3u8dlre':
            self.args['download-mode'] = DownloadMode.NM3U8DLRE
        else:
            self.args['download-mode'] = DownloadMode.YTDLP

        if self.checkbox.get() == 1:
            self.args['overwrite'] = True
        if self.lyrics.get() == 1:
            self.args['lytics'] = True
        def process():
            self.button.configure(state="disabled")
            gamdl(urls=self.url,language=self.args['lang'], output_path=self.args['output'], codec_song=self.args['codec'], download_mode=self.args['download-mode'], overwrite=self.args.get('overwrite', False), no_synced_lyrics=self.args.get('lytics', False),nm3u8dlre_path=resource_path("binary\\N_m3u8dl-RE.exe"),mp4decrypt_path=resource_path("binary\\mp4decrypt.exe"),ffmpeg_path=resource_path("binary\\ffmpeg.exe"),window=self)
            self.button.configure(state="normal")
        th1 = threading.Thread(target=process)
        th1.start()
        
    def setup(self):
        webbrowser.open('https://github.com/amania-Jailbreak/gamdl-GUI/blob/main/how%20to%20setup.md')

class log(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.log = customtkinter.CTkTextbox(self,height=100,width=920)
        self.log.grid(row=0, column=0, padx=10, pady=10,sticky='ew')
        self.log.configure(state="disabled")
        self.playlist_progressbar = customtkinter.CTkProgressBar(self, orientation="horizontal")
        self.playlist_progressbar.grid(row=1, column=0, padx=10, pady=10,sticky='ew')
        self.playlist_progressbar.set(0)
        self.music_progressbar = customtkinter.CTkProgressBar(self, orientation="horizontal")
        self.music_progressbar.grid(row=2, column=0, padx=10, pady=10,sticky='ew')
        self.music_progressbar.set(0)
        
class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("gamdl GUI")
        self.geometry("960x630")
        self.resizable(0, 0)
        meiryo = customtkinter.CTkFont(family="Meiryo UI", size=20)
        
        self.text = customtkinter.CTkLabel(self,text="gamdl GUI",font=meiryo)
        self.text.grid(row=0, column=0, padx=20, pady=10)
        
        self.setting = Setting(master=self)
        self.setting.grid(row=1, column=0, padx=10, pady=5)
        
        self.log = log(master=self)
        self.log.grid(row=3, column=0, padx=10, pady=5)
        
        self.button = button(master=self)
        self.button.grid(row=4, column=0, padx=10, pady=5)

if __name__ == "__main__":
    customtkinter.set_appearance_mode("dark")
    app = App()
    app.mainloop()