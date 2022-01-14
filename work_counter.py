# Import widgets
from PyQt5.QtWidgets import QDateEdit, QMainWindow, QApplication, QSpinBox, QLabel, QTextEdit, QPushButton, QMessageBox, QTabWidget, QListWidget, QListWidgetItem, QDateTimeEdit, QComboBox, QCalendarWidget, QTimeEdit, QPlainTextEdit
from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5.QtCore import QDate, QTime
import PyQt5.QtCore
import sys
from threading import *
import time
from datetime import datetime, timedelta, date
import sqlite3
import json
from pygame import mixer
import webbrowser

# Establish connection
conn = sqlite3.connect('productivity.db')
c = conn.cursor()
c.execute("""CREATE TABLE if not exists productivity(
    start_date text,
    end_date text,
    description text,
    duration integer
)""")
c.execute("""CREATE TABLE if not exists productivity_bak(
    start_date text,
    end_date text,
    description text,
    duration integer
)""")
# Pygame sound
mixer.init()
mixer.music.load("alarm-loop.wav")

timerTime = 0
stop = False
totalTime = 0
exitThread = False
startTime = ""
endTime = ""
description = ""
timeBuffer = 0
timerCancel = False
taskDict = {}

class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        self.setFixedSize(247, 393)
        # UI to be loaded
        uic.loadUi("productivity-game.ui", self)
        # Tasks Today, Work
        self.workButton = self.findChild(QPushButton, "pushButton_2")
        self.timeToday = self.findChild(QLabel, "label_4")
        self.weekLeft = self.findChild(QLabel, "label_5")
        self.taskInput = self.findChild(QTextEdit, "textEdit")
        self.mainTab = self.findChild(QTabWidget, "tabWidget")
        self.hourDisplay = self.findChild(QLabel, "label_9")
        self.minuteDisplay = self.findChild(QLabel, "label_10")
        self.secondDisplay = self.findChild(QLabel, "label_11")
        self.startButton = self.findChild(QPushButton, "pushButton_5")
        self.breakButton = self.findChild(QPushButton, "pushButton_6")
        self.timerButton = self.findChild(QPushButton, "pushButton_3")
        self.timerTime = self.findChild(QSpinBox, "spinBox_2")
        self.cancelButton = self.findChild(QPushButton, "pushButton_4")
        self.timerDisplay = self.findChild(QLabel, "label_2")
        # Stats
        self.listArea = self.findChild(QListWidget, "listWidget")
        self.listWeekly = self.findChild(QPushButton, "pushButton")
        self.listDaily = self.findChild(QPushButton, "pushButton_7")
        self.listMonthly = self.findChild(QPushButton, "pushButton_9")
        self.listAllTime = self.findChild(QPushButton, "pushButton_8")
        self.totalProductivity = self.findChild(QLabel, "label_15")
        # Admin Tools
        self.dateNow = self.findChild(QDateEdit, "dateEdit")
        self.startingTime = self.findChild(QTimeEdit, "timeEdit")
        self.endingTime = self.findChild(QTimeEdit, "timeEdit_2")
        self.duration = self.findChild(QSpinBox, "spinBox")
        self.desc = self.findChild(QTextEdit, "textEdit_2")
        self.addEntryButton = self.findChild(QPushButton,"pushButton_11")
        self.removeEntryButton = self.findChild(QPushButton,"pushButton_10")
        self.refreshEntryButton = self.findChild(QPushButton,"pushButton_12")
        self.removeList = self.findChild(QListWidget, "listWidget_2")
        self.sortItemsButton = self.findChild(QPushButton, "pushButton_13")
        # Checklist
        self.taskName = self.findChild(QTextEdit, "textEdit_3")
        self.addCheckList = self.findChild(QPushButton, "pushButton_14")
        self.checkList = self.findChild(QListWidget, "listWidget_3")
        self.moveToDone = self.findChild(QPushButton, "pushButton_15")
        self.doneList = self.findChild(QListWidget, "listWidget_4")
        self.removeFromDone = self.findChild(QPushButton, "pushButton_16")
        self.undoFromDone = self.findChild(QPushButton, "pushButton_17")
        # Notes
        self.noteInput = self.findChild(QPlainTextEdit, "plainTextEdit")
        self.saveNoteButton = self.findChild(QPushButton, "pushButton_18")
        self.openNoteFileButton = self.findChild(QPushButton, "pushButton_19")
        self.savedLabel = self.findChild(QLabel, "label_26")
        # Button links
        self.timerButton.clicked.connect(self.setTimer)
        self.workButton.clicked.connect(self.workButtonClicked)
        self.startButton.clicked.connect(self.startButtonClicked)
        self.breakButton.clicked.connect(self.breakTime)
        self.cancelButton.clicked.connect(self.resetApp)
        self.listDaily.clicked.connect(self.listDailyStats)
        self.listWeekly.clicked.connect(self.listWeeklyStats)
        self.listMonthly.clicked.connect(self.listMonthlyStats)
        self.listAllTime.clicked.connect(self.listAllTimeStats)
        self.removeEntryButton.clicked.connect(self.removeEntry)
        self.addEntryButton.clicked.connect(self.addEntry)
        self.refreshEntryButton.clicked.connect(self.loadRemoveEntry)
        self.sortItemsButton.clicked.connect(self.sortEntry)
        self.addCheckList.clicked.connect(self.addCheckListItem)
        self.moveToDone.clicked.connect(self.moveToDoneList)
        self.removeFromDone.clicked.connect(self.removeFromDoneList)
        self.undoFromDone.clicked.connect(self.undoFromDoneList)
        self.saveNoteButton.clicked.connect(self.saveNote)
        self.openNoteFileButton.clicked.connect(self.openNoteFile)
        # Some parameters
        self.mainTab.setTabEnabled(1,False)
        self.dateNow.setDate(QDate.currentDate())
        self.startingTime.setTime(QTime.currentTime())
        self.endingTime.setTime(QTime.currentTime())
        self.loadCheckList()
        # Show the app
        self.updateStats()
        self.show()

    # Notes
    def saveNote(self):
        if self.noteInput.toPlainText() == "":
            self.infoDialog("Notes cannot be empty.")
        else:
            today = datetime.now().strftime("%b %d %Y %H:%M:%S")
            text = f"\n(DATE: {today})\n\n{self.noteInput.toPlainText()}  \n--END OF NOTE--"
            with open("notes.txt","a+") as f:
                f.write(text)
            self.noteInput.clear()
            T = Thread(target=self.savePrompt)
            T.setDaemon(True)
            T.start()
    
    def savePrompt(self):
        self.savedLabel.setText("Saved!")
        time.sleep(2)
        self.savedLabel.setText("")
    
    def openNoteFile(self):
        webbrowser.open("notes.txt")

    # Checklist
    def loadCheckList(self): # Load json file here ; turn to dict. False = not done, True = done
        global taskDict
        self.doneList.clear()
        self.checkList.clear()
        try:
            jsonFile = open("tasks.json", "r")
            taskDict = json.load(jsonFile)
            for key, value in taskDict.items():
                if value:
                    self.doneList.addItem(key)
                else:
                    self.checkList.addItem(key)
            pass
        except:
            print("Json file empty. Ignoring load.")

    def addCheckListItem(self): # Not yet saved to the dictionary. should save
        global taskDict
        if self.taskName.toPlainText() == "":
            self.infoDialog("Input task name")
        else:
            #self.checkList.addItem(self.taskName.toPlainText())
            taskDict[self.taskName.toPlainText()] = False
            self.taskName.clear()
            self.saveCheckList()
            self.loadCheckList()

    def moveToDoneList(self):
        global taskDict
        if self.checkList.currentRow() != -1:
            taskDict[self.checkList.currentItem().text()] = True
            #taskDict.pop(y)
            self.saveCheckList()
            self.loadCheckList()
        else:
            self.infoDialog("Select task from Current Tasks to move to Tasks Done.")

    def removeFromDoneList(self):
        global taskDict
        if self.doneList.currentRow() != -1:
            taskDict.pop(self.doneList.currentItem().text())
            self.saveCheckList()
            self.loadCheckList()
            print(taskDict)
        else:
            self.infoDialog("Select task from Tasks Done to delete. \nNote: You can only remove tasks from Tasks Done. If you want to remove from Current Tasks, move them to Tasks Done first.")

    def undoFromDoneList(self):
        global taskDict
        if self.doneList.currentRow() != -1:
            taskDict[self.doneList.currentItem().text()] = False
            self.saveCheckList()
            self.loadCheckList()
        else:
            self.infoDialog("Select task from Tasks Done to move to Current Tasks.")

    def saveCheckList(self):
        global taskDict
        jsonFile = open("tasks.json","w")
        jsonFile = json.dump(taskDict, jsonFile)

    # Timer
    def setTimer(self):
        global timerCancel
        if self.timerButton.text() == "Timer":
            if self.timerTime.value() == 0:
                self.infoDialog("Input time (in minutes)")
            else:
                self.timerButton.setText("Cancel")
                global timerTime
                timerTime = self.timerTime.value() * 60
                T = Thread(target=self.timerAlert)
                T.setDaemon(True)
                T.start()
        else:
            self.timerButton.setText("Timer")
            timerCancel = True
            self.infoDialog("Canceled.")
            self.timerDisplay.setText("Canceled.")
    
    def timerAlert(self):
        global timerCancel
        global timerTime
        i = 0
        while i != timerTime:
            if timerCancel:
                timerCancel = False
                break
            if timerTime == 0:
                break
            time.sleep(1)
            i += 1
            display = f"{(timerTime-i) // 60}M {(timerTime-i) % 60}S Left!"
            self.timerDisplay.setText(display)
        if i == timerTime:
            mixer.music.play()
            timerTime = 0
            self.timerDisplay.setText("Done!")
            self.timerButton.setText("Timer")
        print("Timer thread ends.")

    # Admin Tools

    def loadRemoveEntry(self):
        c.execute("SELECT * from productivity")
        allWork = c.fetchall() # Returns a list
        self.removeList.clear()
        self.removeList.addItem("Date&Time \t\t |Duration \t |Description")
        for data in allWork:
            date = datetime.strptime(data[0], "%d/%m/%Y %H:%M:%S").strftime('%b %d %Y %H:%M:%S')
            dur = "{:0>8}".format(str(timedelta(seconds=data[3])))
            entry = f"{date} \t  {dur} \t  {data[2]}"
            self.removeList.addItem(entry)
    
    def sortEntry(self):
        self.removeList.clear()
        sortedList = []
        c.execute("SELECT * from productivity")
        allWork = c.fetchall()
        c.execute("DELETE FROM productivity_bak")
        c.execute("INSERT INTO productivity_bak SELECT * FROM productivity")
        for data in allWork:
            start_dateObject = datetime.strptime(data[0],'%d/%m/%Y %H:%M:%S')
            sortedList.append([start_dateObject, data[1], data[2] ,data[3]])
        sortedList.sort(key = lambda x:x[0])
        c.execute(f"DELETE FROM productivity")
        i = 0
        for data in sortedList:
            i += 1
            data[0] = datetime.strftime(data[0], '%d/%m/%Y %H:%M:%S')
            c.execute(f"INSERT INTO productivity VALUES ('{data[0]}','{data[1]}','{data[2]}','{data[3]}')")
            conn.commit()
        self.infoDialog(f"Sorted {i} entries.")

    def removeEntry(self):
        removeIdx = self.removeList.currentRow()
        if removeIdx != -1:
            conf = self.confirmAction("Remove the highlighted entry?")
            if conf:
                print(self.removeList.currentItem().text())
                c.execute(f"DELETE FROM productivity WHERE start_date in (SELECT start_date FROM productivity LIMIT 1 OFFSET {removeIdx-1})")
                #date = datetime.strptime(data[0], "%d/%m/%Y %H:%M:%S").strftime('%b %d %Y %H:%M:%S')
                self.loadRemoveEntry()
        else:
            self.infoDialog("Select an entry from the list to remove.")
            pass

    def addEntry(self):
        d0 = self.dateNow.date().toString("dd/MM/yyyy")
        d1 = self.startingTime.time().toString("hh:mm:ss")
        d2 = self.endingTime.time().toString("hh:mm:ss")
        d3 = self.duration.value() * 60
        d4 = self.desc.toPlainText()
        if d1 == d2:
            self.infoDialog("Start and end time must be different.")
        elif d3 == 0:
            self.infoDialog("Enter duration.")
        elif d4 == "":
            self.infoDialog("Enter description.")
        else:
            conf = self.confirmAction(f"Add this to the entry?\nStart: {d1} \nEnd: {d2} \nDesc: {d4} \nDuration: {d3/60} Minutes")
            if conf:
                starting = f"{d0} {d1}"
                ending = f"{d0} {d2}"
                c.execute(f"INSERT INTO productivity VALUES ('{starting}','{ending}','{d4}','{d3}')") #Description and duration inverted
                self.infoDialog("Added.")
                self.duration.setValue(0)
                self.desc.clear()
                self.dateNow.setDate(QDate.currentDate())
                self.startingTime.setTime(QTime.currentTime())
                self.endingTime.setTime(QTime.currentTime())
                self.updateStats()

    # Global Functions
    def infoDialog(self, text):
        msg = QMessageBox()
        msg.setWindowTitle("Prompt")
        msg.setIcon(QMessageBox.Information)
        msg.setText(text)
        msg.exec_()

    def resetApp(self):
        global stop
        global totalTime
        global exitThread
        global timeBuffer
        global timerTime
        global timerCancel
        self.mainTab.setTabEnabled(1,False)
        self.mainTab.setCurrentIndex(0)
        self.mainTab.setTabEnabled(0,True)
        stop = True
        self.hourDisplay.setText(f"0 H")
        self.minuteDisplay.setText(f"0 M")
        self.secondDisplay.setText(f"0 S")
        self.startButton.setText("Start!")
        self.taskInput.clear()
        self.breakButton.setText("Break")
        self.timerDisplay.setText("Set time for breaks!")
        self.timerButton.setText("Timer")
        totalTime = 0
        timeBuffer = 0
        timerTime = 0
        exitThread = True
        self.updateStats()
        timerCancel = False

    # Stats
    def listDailyStats(self):
        totalInt = 0
        c.execute("SELECT * from productivity")
        allWork = c.fetchall() # Returns a list'
        self.listArea.clear()
        self.listArea.addItem("Date \t |Duration \t |Description")
        endTime = datetime.now().strftime("%d/%m/%Y")
        for data in allWork:
            if endTime in data[0]:
                dur = "{:0>8}".format(str(timedelta(seconds=data[3])))
                date = datetime.strptime(data[0][0:10], "%d/%m/%Y").strftime('%b %d %Y')
                entry = f"{date} \t  {dur} \t  {data[2]}"
                self.listArea.addItem(entry)
                totalInt += data[3]
        totalInt = "{:0>8}".format(str(timedelta(seconds=totalInt)))
        self.totalProductivity.setText(totalInt)

    def listWeeklyStats(self):
        c.execute("SELECT * from productivity")
        allWork = c.fetchall() # Returns a list
        self.listArea.clear()
        self.listArea.addItem("Date \t |Duration \t |Description")
        my_date = datetime.now()
        year, week_num, day_of_week = my_date.isocalendar()
        weekTotalInt = 0
        #print("Week #" + str(week_num) + " of year " + str(year))
        for data in allWork:
            dateForWeek = datetime.strptime(data[0], '%d/%m/%Y %H:%M:%S')
            _, week, _ = dateForWeek.isocalendar()
            if week_num == week:
                dur = "{:0>8}".format(str(timedelta(seconds=data[3])))
                date = datetime.strptime(data[0][0:10], "%d/%m/%Y").strftime('%b %d %Y')
                entry = f"{date} \t  {dur} \t  {data[2]}"
                self.listArea.addItem(entry)
                weekTotalInt += data[3]
        weekTotalInt = "{:0>8}".format(str(timedelta(seconds=weekTotalInt)))
        self.totalProductivity.setText(weekTotalInt)

    def listMonthlyStats(self):
        totalInt = 0
        c.execute("SELECT * from productivity")
        allWork = c.fetchall() # Returns a list'
        self.listArea.clear()
        self.listArea.addItem("Date \t |Duration \t |Description")
        endTime = datetime.now().strftime("%m/%Y")
        for data in allWork:
            if endTime in data[0]:
                dur = "{:0>8}".format(str(timedelta(seconds=data[3])))
                date = datetime.strptime(data[0][0:10], "%d/%m/%Y").strftime('%b %d %Y')
                entry = f"{date} \t  {dur} \t  {data[2]}"
                self.listArea.addItem(entry)
                totalInt += data[3]
        totalInt = "{:0>8}".format(str(timedelta(seconds=totalInt)))
        self.totalProductivity.setText(totalInt)

    def listAllTimeStats(self):
        totalInt = 0
        c.execute("SELECT * from productivity")
        allWork = c.fetchall() # Returns a list'
        self.listArea.clear()
        self.listArea.addItem("Date \t |Duration \t |Description")
        for data in allWork:
            dur = "{:0>8}".format(str(timedelta(seconds=data[3])))
            date = datetime.strptime(data[0][0:10], "%d/%m/%Y").strftime('%b %d %Y')
            entry = f"{date} \t  {dur} \t  {data[2]}"
            self.listArea.addItem(entry)
            totalInt += data[3]
        totalInt = "{:0>8}".format(str(timedelta(seconds=totalInt)))
        self.totalProductivity.setText(totalInt)

    # Work, Tasks Today
    def updateStats(self):
        # For today
        allTime = 0
        c.execute("SELECT * from productivity")
        allWork = c.fetchall() # Returns a list
        for data in allWork:
            allTime += data[3]
        print(allTime)
        hours = (allTime // 60) // 60
        minutes = (allTime // 60) % 60
        self.timeToday.setText(f"{hours} Hours and {minutes} Minutes")
        # Left for the Week
        my_date = datetime.now()
        year, week_num, day_of_week = my_date.isocalendar()
        weekTotalInt = 0
        print("Week #" + str(week_num) + " of year " + str(year))
        for data in allWork:
            dateForWeek = datetime.strptime(data[0], '%d/%m/%Y %H:%M:%S')
            _, week, _ = dateForWeek.isocalendar()
            if week_num == week:
                weekTotalInt += data[3]
        # PLACEHOLDER - 40 HOURS A WEEK GOAL. WILL MAKE IT CHANGEABLE
        goal = 40 * 3600
        weekTotalInt = goal - weekTotalInt
        print(weekTotalInt)
        hours = (weekTotalInt // 60) // 60
        minutes = (weekTotalInt // 60) % 60
        self.weekLeft.setText(f"{hours} Hours and {minutes} Minutes")
    
    def workButtonClicked(self):
        global description
        if self.taskInput.toPlainText() == (""):
            self.infoDialog("Input empty. What type of productivity will you be doing?")
        else:
            self.mainTab.setTabEnabled(1,True)
            self.mainTab.setCurrentIndex(1)
            self.mainTab.setTabEnabled(0,False)
            description = self.taskInput.toPlainText()
            self.breakButton.setEnabled(False)
            self.timerDisplay.setText("Set time for breaks!")

    def startButtonClicked(self):
        global stop
        global totalTime
        global startTime
        global endTime
        if self.startButton.text() == "Start!":
            totalTime = 0
            startTime = datetime.now().strftime("%d/%m/%Y %H:%M:%S") 
            #startTime = "01/01/2022 23:59:57" # For testing epochTime
            stop = False
            self.startButton.setText("Finish!")
            self.breakButton.setEnabled(True)
            T = Thread(target=self.startTime)
            T.setDaemon(True)
            T.start()
        else:
            endTime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            self.updateStats()
            self.saveData()
            self.resetApp()

    def saveData(self): # Save data here, happens when you click finish
        global startTime
        global endTime
        global totalTime
        global description
        c.execute(f"INSERT INTO productivity VALUES ('{startTime}','{endTime}','{description}','{totalTime-timeBuffer}')")
        print(f"INSERT INTO productivity VALUES ('{startTime}','{endTime}','{description}','{totalTime-timeBuffer}')")
        conn.commit()
    
    def epochHandler(self):
        global startTime
        global totalTime
        global timeBuffer
        timeBuffer += totalTime
        endOfDay = startTime[0:10]+" 23:59:59"
        with sqlite3.connect("productivity.db") as con:
            cur = con.cursor()
            cur.execute(f"INSERT INTO productivity VALUES ('{startTime}','{endOfDay}','{description}','{totalTime}')")
            print(f"INSERT INTO productivity VALUES ('{startTime}','{endOfDay}','{description}','{totalTime}')")
            startTime = datetime.now().strftime("%d/%m/%Y %H:%M:%S") # Turn back startTime to now
            con.commit()
    
    def startTime(self):
        global stop
        global totalTime
        global exitThread
        global startTime
        global timeBuffer
        startEpoch = (int(startTime[11:13]) * 3600) + (int(startTime[14:16]) * 60) + int(startTime[17:19])
        endEpoch = 86400 - startEpoch # Seconds left for the day
        while not exitThread:
            if totalTime == endEpoch: # If its already 12mn, add this shit
                self.epochHandler()
            if not stop:
                hours = totalTime // 3600
                minutes = (totalTime % 3600) // 60
                seconds = (totalTime % 3600) % 60
                self.hourDisplay.setText(f"{hours} H")
                self.minuteDisplay.setText(f"{minutes} M")
                self.secondDisplay.setText(f"{seconds} S")
                time.sleep(1)
                totalTime += 1
                print(f'total time {totalTime}')
        exitThread = False
        print("Thread ends.")

    def breakTime(self):
        global stop
        if self.breakButton.text() == "Break":
            self.breakButton.setText("Continue")
            stop = True
        else:
            self.breakButton.setText("Break")
            stop = False

    def confirmAction(self, text):
        reply = QMessageBox.question(self, 'Confirmation Prompt', text,QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            return True
        else:
            return False

# Initialisation
if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
app = QApplication(sys.argv)
UIWindow = UI()
app.exec_()
