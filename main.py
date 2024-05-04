import customtkinter,pyperclip
from customtkinter import filedialog
import webbrowser,ctypes,os,sys,json,threading

# N_m3u8dl-RE及びmp4decryptコマンドが使えるかの確認
import subprocess

try:
    subprocess.run([".\\binary\\N_m3u8dl-RE"], check=True)
    print("N_m3u8dl-REコマンドが使えます")
except:
    MessageBox = ctypes.windll.user32.MessageBoxW
    MessageBox(None, 'Please Install N_m3u8dl-RE', 'Error', 0)
    sys.exit()

try:
    subprocess.run([".\\binary\\mp4decrypt"])
    print("mp4decryptコマンドが使えます")
except FileNotFoundError:
    MessageBox = ctypes.windll.user32.MessageBoxW
    MessageBox(None, 'Please Install mp4decrypt', 'Error', 0)
    sys.exit()


if not os.path.exists("./device.wvd"):
    MessageBox = ctypes.windll.user32.MessageBoxW
    MessageBox(None, 'Please check for the existence of device.wvd', 'Error', 0)
    sys.exit()
    
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
        
        self.paste_button = customtkinter.CTkButton(self, text="Paste", command=self.paste)
        self.paste_button.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        
        self.output_text = customtkinter.CTkLabel(self,text='output directory')
        self.output_text.grid(row=4,column=0,padx=10, pady=10,sticky='ew') 
        
        self.output_url_box = customtkinter.CTkTextbox(self,height=10)
        self.output_url_box.grid(row=5,column=0,padx=10, pady=10,sticky='ew')
        self.output_url_box.insert('0.0',text=config['output_url'])
        
        self.open_dir_button = customtkinter.CTkButton(self, text="Open Directory", command=self.open_directory)
        self.open_dir_button.grid(row=6, column=0, padx=10, pady=10, sticky="ew")
        
    def paste(self):
        self.download_url_box.delete('0.0','end-1c')
        self.download_url_box.insert('0.0',text=pyperclip.paste())
        
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
        
        self.codic = customtkinter.CTkSegmentedButton(self, values=["aac", "aac-legacy","aac-he-legacy",'aac-he','aac-binaural','aac-he-downmix','atmos','ac3','alac','ask'],width=100)
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
        
        self.cancel = customtkinter.CTkButton(self, text="Cancel", command=self.cancel)
        self.cancel.grid(row=0, column=1, padx=10, pady=10,sticky='n')
        self.cancel.configure(state='disabled')
        self.buttons = customtkinter.CTkButton(self, text="How to Setup", command=self.setup)
        self.buttons.grid(row=0, column=0, padx=10, pady=10,sticky='n')
        
        self.checkbox = customtkinter.CTkCheckBox(self, text="overwrite")
        self.checkbox.grid(row=0, column=3, padx=10, pady=10,sticky='n')
        
        self.lyrics = customtkinter.CTkCheckBox(self, text="no Lyrics")
        self.lyrics.grid(row=0, column=4, padx=10, pady=10,sticky='n')
        
    def download(self):
        option = f'-l "{self.master.setting.option.lang.get()}" -o "{self.master.setting.textbox.output_url_box.get("0.0","end-1c")}" --codec-song "{self.master.setting.option.codic.get()}" --download-mode "{self.master.setting.option.download_mode.get()}" --remux-mode ffmpeg --wvd-path device.wvd --nm3u8dlre-path ./binary/N_m3u8dl-RE.exe --mp4decrypt-path ./binary/mp4decrypt.exe --ffmpeg-path ./binary/ffmpeg.exe'
        if self.checkbox.get() == 1:
            option = f'{option} --overwrite'
        if self.lyrics.get() == 1:
            option = f'{option} --no-synced-lyrics'
        self.command = f'gamdl {option} "{self.master.setting.textbox.download_url_box.get("0.0","end-1c")}"'
        def process():
            self.button.configure(state="disabled")
            self.cancel.configure(state="normal")
            self.p = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
            for line in self.p.stdout:
                self.master.log.log.configure(state="normal")
                self.master.log.log.insert('end', line)
                self.master.log.log.see("end")
                self.master.log.log.configure(state="disabled")
            try:
                outs, errs = self.p.communicate()
            except subprocess.TimeoutExpired:
                pass
            else:
                self.p.terminate()
            self.button.configure(state="normal")
            self.cancel.configure(state="disabled")

        th1 = threading.Thread(target=process)
        th1.start()
    def cancel(self):
        self.p.kill()
        self.button.configure(state="normal")
        self.cancel.configure(state="disabled")
    def setup(self):
        webbrowser.open('https://github.com/amania-Jailbreak/gamdl-GUI/blob/main/how%20to%20setup.md')

class log(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.log = customtkinter.CTkTextbox(self,height=100,width=1270)
        self.log.grid(row=0, column=0, padx=10, pady=10,sticky='ew')
        self.log.configure(state="disabled")
class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("gamdl GUI")
        self.geometry("1310x550")
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