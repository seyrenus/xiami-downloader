#-*- encoding:UTF-8 -*-
import re
import os
import urllib
import urllib2
import wx
import threading
from HTMLParser import HTMLParser

class XiaMi(threading.Thread):
    def __init__(self, window, url, save_path, cookiezi):
        threading.Thread.__init__(self)
        self.timeToQuit = threading.Event()
        self.timeToQuit.clear()
        self.window = window
        self.opener = urllib2.build_opener()
        self.s = '\x1b[1;%dm%s\x1b[0m'

        self.re_songs = re.compile(r'href="/song/(\d+)" title')
        self.re_ids = re.compile(r'song_id>(\d+)<')
        self.re_sname = re.compile(r'title><!\[CDATA\[(.+?)\]\]')
        self.re_artist = re.compile(r'artist><!\[CDATA\[(.+?)\]\]')
        self.re_song = re.compile(r'"location":"(.+?)"')

        self.parser = HTMLParser()
        self.template_info = 'http://www.xiami.com/song/playlist/id/%s'
        self.template_parse = 'http://www.xiami.com/song/gethqsong/sid/%s'
        self.url =  url
        self.save_path = save_path
        self.cookiezi = "member_auth=" + str(cookiezi)
        self.opener.addheaders = [('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'), ('User-Agent', 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.95 Safari/537.36'), ('Cookie', self.cookiezi)]
    def decry(self, row, encryed_url):
        url = encryed_url
        urllen = len(url)
        rows = int(row)

        cols_base = urllen / rows  # basic column count
        rows_ex = urllen % rows    # count of rows that have 1 more column

        matrix = []
        for r in xrange(rows):
            length = cols_base + 1 if r < rows_ex else cols_base
            matrix.append(url[:length])
            url = url[length:]

        url = ''
        for i in xrange(urllen):
            url += matrix[i % rows][i / rows]

        return urllib.unquote(url).replace('^', '0')

    def song_infos(self, song_id_list):
        api_xml = self.opener.open(self.template_info % ','.join(song_id_list)).read()
        id_list = self.re_ids.findall(api_xml)
        sname_list = self.re_sname.findall(api_xml)
        artist_list = self.re_artist.findall(api_xml)

        infos = zip(id_list, sname_list, artist_list)
        return infos

    def modified_sname(self, sname):
        sname = self.parser.unescape(sname)
        sname = sname.replace('/', ' - ')
        sname = sname.replace('\\', '')
        sname = sname.replace('"', '\\"')
        try:
            sname = sname.encode('utf8')
        except UnicodeDecodeError:
            pass
        if len(sname) >= 250:
            return sname[:243] + '...mp3'
        else:
            return sname

   # def run(self, url, savePath):
    def run(self):
        msg = 'Seyren出品\n'
        wx.CallAfter(self.window.LogMessage, msg)
        f = self.opener.open(self.url).read()
        song_id_list = self.re_songs.findall(f)
        infos = self.song_infos(song_id_list)
        size = len(infos)
        z = 0
        if size <= 9:
            z = 1
        elif size >= 10 and size <= 99:
            z = 2
        elif size >= 100 and size <= 999:
            z = 3
        else:
            z = 1

        ii = 1
        for i in infos:
            self.timeToQuit.wait(10)
            wx.CallAfter(self.window.LogMessage, "开始下载请等待\n")
            sname = str(ii).zfill(z) + '.' + i[1] + ' -- ' + i[2] + '.mp3'
            sname = self.modified_sname(sname)
            ii += 1
            j = self.opener.open(self.template_parse % i[0]).read()
            t = self.re_song.search(j)
            t = t.group(1)
            row = t[0]
            encryed_url = t[1:]
            durl = self.decry(row, encryed_url)
            wx.CallAfter(self.window.LogMessage, "开始下载" + sname + "\n")
            wx.CallAfter(self.window.LogMessage, self.save_path)

            try:
                musicData = urllib2.urlopen(durl).read()
                musicName = str(self.save_path) + '//' + sname
                if os.path.exists(musicName):
                    wx.CallAfter(self.window.LogMessage, "该歌曲已下载\n")
                    continue
                output = open(musicName, 'wb')
                output.write(musicData)
                output.close
                wx.CallAfter(self.window.LogMessage, sname + "下载成功\n")
            except:
                wx.CallAfter(self.window.LogMessage, sname + "下载失败\n")
        wx.CallAfter(self.window.LogMessage, "所有歌曲下载完毕")

class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="虾米下载", size = (500, 335))
        self.threads = []
        self.count = 0

        self.panel = wx.Panel(self)
        chooseButton = wx.Button(self.panel, -1, "浏览")
        loadButton = wx.Button(self.panel, -1, "下载")

        label1 = wx.StaticText(self.panel, 1, "设置保存目录")
        label2 = wx.StaticText(self.panel, 1, "虾米精选集网址")
        label3 = wx.StaticText(self.panel, 1, "cookie设置")

        self.xiamilink = wx.TextCtrl(self.panel, -1,"http://www.xiami.com/song/showcollect/id/22851218" )
        self.musicdir = wx.TextCtrl(self.panel, -1, "/home/arch/Desktop")
        self.log = wx.TextCtrl(self.panel, -1, "", style = wx.TE_RICH | wx.TE_MULTILINE)
        self.memid = wx.TextCtrl(self.panel, -1,"设置你的cookie")

        hbox = wx.BoxSizer()
        hbox.Add(label1, proportion = 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        hbox.Add(self.musicdir, 1, wx.EXPAND, 5)
        hbox.Add(chooseButton, 0, wx.LEFT, 5)

        ibox = wx.BoxSizer()
        ibox.Add(label2, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        ibox.Add(self.xiamilink, 1, wx.EXPAND, 5)
        ibox.Add(loadButton, 0, wx.LEFT, 5)

        sbox = wx.BoxSizer()
        sbox.Add(label3, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        sbox.Add(self.memid, 1, wx.EXPAND, 5)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(hbox, 0, wx.EXPAND | wx.ALL, 5)
        vbox.Add(sbox, 0, wx.EXPAND | wx.ALL, 5)
        vbox.Add(ibox, 0, wx.EXPAND | wx.ALL, 5)
        vbox.Add(self.log, proportion=1,
                 flag=wx.EXPAND | wx.LEFT | wx.BOTTOM | wx.RIGHT, border=5)

        self.panel.SetSizer(vbox)

        self.Bind(wx.EVT_BUTTON, self.OnChooseDir, chooseButton)
        self.Bind(wx.EVT_BUTTON, self.OnLoad, loadButton)
        self.Bind(wx.EVT_CLOSE,  self.OnCloseWindow)

    def OnChooseDir(self, evt):
        dir = wx.DirDialog(self.panel, '选择保存文件夹', style = wx.DD_DEFAULT_STYLE)

        if dir.ShowModal() == wx.ID_OK:
            path = dir.GetPath()
            self.musicdir.SetValue(path)
        dir.Destroy()

    def OnLoad(self, evt):
        Thread = XiaMi(self, self.xiamilink.GetValue(), self.musicdir.GetValue(), self.memid.GetValue())
        Thread.start()

    def OnCloseWindow(self, evt):
        self.StopThreads()
        self.Destroy()
    def LogMessage(self, msg):
        self.log.AppendText(msg)

    def StopThreads(self):
        while self.threads:
            thread = self.threads[0]
            thread.stop()
            self.threads.remove(thread)

app = wx.PySimpleApp()
frm = MyFrame()
frm.Show()
app.MainLoop()
