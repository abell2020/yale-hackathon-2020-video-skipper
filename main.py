from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, \
    QSlider, QStyle, QSizePolicy, QFileDialog, QShortcut, QLineEdit
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QIcon, QPalette, QKeySequence
from PyQt5.QtCore import Qt, QUrl
import subprocess
from pylab import*
from scipy.io import wavfile
from PyQt5 import QtCore
import numpy as np
import os, sys, time,  threading
#from PySide2 import QtCore, QtGui
#setMuted(bool) useful method, also setPlaybackRate(float)
audioThreshold=75;
jumpSize=.5;
speed = 1.25;

class QJumpSlider(QSlider):
    def __init__(self, parent = None, mediaP=""):
        self.mediaP=mediaP
        super(QJumpSlider, self).__init__(parent)

    def mousePressEvent(self, event):
        #Jump to click position
        pos = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.x(), self.width())
        self.setValue(pos)
        self.mediaP.setPosition(pos)

    def mouseMoveEvent(self, event):
        #Jump to pointer position while moving
        pos = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.x(), self.width())
        self.setValue(pos)
        self.mediaP.setPosition(pos)

class MyQLineEdit(QLineEdit):

    def focusInEvent(self, e):
        # Do something with the event here
        print(e)
        self.selectAll()
        super(MyQLineEdit, self).focusInEvent(e) # Do the default action on the parent class QLineEdit
    def mousePressEvent(self, e):
        self.selectAll()

def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    if hour >0:
        return "%d:%02d:%02d" % (hour, minutes, seconds)
    else:
        return "%02d:%02d" % (minutes, seconds)

class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.audio = "";
        self.sampFreq=0;

        self.setWindowTitle("Silence Skipper Video Player")
        self.setGeometry(350, 100, 700, 500)
        self.setWindowIcon(QIcon('helicopter.jpg'))

        p = self.palette()
        p.setColor(QPalette.Window, Qt.black)
        self.setPalette(p)

        self.init_ui()

        self.show()

    def init_ui(self):

        # create media player object
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        # create videowidget object

        videowidget = QVideoWidget()

        # create open button
        openBtn = QPushButton('Open Video')
        openBtn.clicked.connect(self.open_file)

        # create button for playing
        self.playBtn = QPushButton()
        self.playBtn.setEnabled(False)
        self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playBtn.clicked.connect(self.play_video)
        self.playBtnShortcut = QShortcut(QKeySequence('Space'), self)
        self.playBtnShortcut.activated.connect(self.play_video)

        # create skip forward button
        self.skipForward = QPushButton()
        self.skipForward.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.skipForward.setEnabled(False)
        self.skipForward.clicked.connect(self.skip_forward)
        self.forwardShortcut = QShortcut(QKeySequence('Right'), self)
        self.forwardShortcut.activated.connect(self.skip_forward)
        self.forwardShortcut = QShortcut(QKeySequence('Shift+Right'), self)
        self.forwardShortcut.activated.connect(self.skip_forward_tiny)
        #make mutton invis
        self.skipForward.setVisible(False)

        # create skip backward button
        self.skipBackwards = QPushButton()
        self.skipBackwards.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.skipBackwards.setEnabled(False)
        self.skipBackwards.clicked.connect(self.skip_backwards)
        self.backwardsShortcut = QShortcut(QKeySequence('Left'), self)
        self.backwardsShortcut.activated.connect(self.skip_backwards)
        self.backwardsShortcutTiny = QShortcut(QKeySequence('Shift+Left'), self)
        self.backwardsShortcutTiny.activated.connect(self.skip_backwards_tiny)
        #make mutton invis
        self.skipBackwards.setVisible(False)

        # create speed setter button
        self.speedButton = MyQLineEdit()
        self.speedButton.textChanged[str].connect(self.speed_popup)
        speed = "1"
        self.speedButton.setText(speed)
        self.speedButton.setMaxLength(4)
        self.speedButton.setFixedWidth(30)


        self.label = QLabel('Yellow', self)
        self.label.setStyleSheet("color:white;")
        self.label.setText("sound threshold factor: ")
        self.label.setAlignment(Qt.AlignRight)
        self.label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        #self.label.setFixedWidth(160)

        self.soundThreshold = MyQLineEdit()
        self.soundThreshold.textChanged[str].connect(self.sound_thresh)
        self.soundThreshold.setText(str(audioThreshold))
        self.soundThreshold.setMaxLength(5)
        self.soundThreshold.setFixedWidth(35)
        self.soundThreshold.setAlignment(Qt.AlignLeft)
        #self.speedButton.editingFinished.connect(self.speed_popup)

        # create slider
        self.slider = QJumpSlider(Qt.Horizontal,mediaP=self.mediaPlayer)
        #self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.set_position)

        # create label

        self.label2 = QLabel('Yellow', self)
        self.label2.setStyleSheet("background-color: yellow; border: 1px solid black;")
        self.label2.setText("duration")
        self.label2.setAlignment(Qt.AlignRight)
        self.label2.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)


        hboxLayout2 = QHBoxLayout()
        hboxLayout2.setContentsMargins(0, 0, 0, 0)
        hboxLayout2.addWidget(self.label)
        hboxLayout2.addWidget(self.soundThreshold)

        # create hbox layout
        hboxLayout = QHBoxLayout()
        hboxLayout.setContentsMargins(0, 0, 0, 0)

        # set widgets to the hbox layout
        hboxLayout.addWidget(openBtn)
        hboxLayout.addWidget(self.playBtn)
        hboxLayout.addWidget(self.skipBackwards)
        hboxLayout.addWidget(self.skipForward)
        hboxLayout.addWidget(self.slider)
        hboxLayout.addWidget(self.speedButton)
        hboxLayout.addWidget(self.label2)

        # create vbox layout

        vboxLayout = QVBoxLayout()
        vboxLayout.addLayout(hboxLayout2)
        vboxLayout.addWidget(videowidget)
        vboxLayout.addLayout(hboxLayout)
        vboxLayout.setContentsMargins(10,10,10,10)

        self.setLayout(vboxLayout)

        self.mediaPlayer.setVideoOutput(videowidget)

        # media player signals

        self.mediaPlayer.stateChanged.connect(self.mediastate_changed)
        self.mediaPlayer.positionChanged.connect(self.position_changed)
        self.mediaPlayer.durationChanged.connect(self.duration_changed)

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Video")
        print(filename)
        if filename != '':

            if os.path.exists("audio.wav"):
              os.remove("audio.wav")
            command = "ffmpeg_dir\\bin\\ffmpeg -i "+filename+" -ac 1 -ar 11025 -vn audio.wav"
            subprocess.call(command, shell=True)
            self.sampFreq, self.audio = wavfile.read('audio.wav')
            print(self.audio.shape)
            print(self.sampFreq)
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))
            self.playBtn.setEnabled(True)
            self.skipForward.setEnabled(True)
            self.skipBackwards.setEnabled(True)
            self.mediaPlayer.setPosition(1)

    def play_video(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()

        else:
            self.mediaPlayer.play()

    def skip_forward(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.setPosition(self.mediaPlayer.position() + 5000)
        else:
            self.mediaPlayer.setPosition(self.mediaPlayer.position() + 33)

    def skip_forward_tiny(self):
        self.mediaPlayer.setPosition(self.mediaPlayer.position() + 1000)

    def skip_backwards(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.setPosition(self.mediaPlayer.position() - 5000)
        else:
            self.mediaPlayer.setPosition(self.mediaPlayer.position() - 33)

    def skip_backwards_tiny(self):
        self.mediaPlayer.setPosition(self.mediaPlayer.position() - 1000)

    def mediastate_changed(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playBtn.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause)

            )

        else:
            self.playBtn.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay)

            )

    def position_changed(self, position):
        self.slider.setValue(position)
        print(self.mediaPlayer.duration())
        self.label2.setText( str(convert(int(position/1000))) +"/"+ str(convert(int(self.mediaPlayer.duration()/1000)))  )

    def duration_changed(self, duration):
        self.slider.setRange(0, duration)

    def set_position(self, position):
        self.mediaPlayer.setPosition(position)

    def speed_popup(self,text):
        print(text)
        self.mediaPlayer.setPlaybackRate(float(text))

    def sound_thresh(self,text):
        global audioThreshold
        audioThreshold=float(text)
        print(audioThreshold)


    def handle_errors(self):
        self.playBtn.setEnabled(False)
        self.label.setText("Error: " + self.mediaPlayer.errorString())

def skip(window,position):
    pos = int( position * window.sampFreq / 1000)
    endpos = pos+int(window.sampFreq*jumpSize)
    a = np.array(window.audio[pos:endpos])

    avg = np.mean(np.absolute(a))
    print("pos",position,"| avg",avg,"      ",audioThreshold)
    if avg < audioThreshold:
        print("skipippppppppppppppppppppppp" +str(audioThreshold))
        position = position + 1000*jumpSize;
        window.mediaPlayer.setPosition(position)
        skip(window,position)

def thread_function(name,window):
    print("yo")
    while(True):
        time.sleep(.1)
        if window.mediaPlayer.state() == QMediaPlayer.PlayingState:
            position = window.mediaPlayer.position()
            skip(window,position)



app = QApplication(sys.argv)
window = Window()
x = threading.Thread(target=thread_function, args=(1,window))
x.start()



sys.exit(app.exec_())
