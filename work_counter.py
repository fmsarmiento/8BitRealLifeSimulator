# Import widgets
from PyQt5.QtWidgets import QDateEdit, QMainWindow, QApplication, QSpinBox, QLabel, QTextEdit, QPushButton, QMessageBox, QTabWidget, QListWidget, QListWidgetItem, QDateTimeEdit, QComboBox, QCalendarWidget, QTimeEdit, QPlainTextEdit, QAction
from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QDate, QTime
import sys, time, sqlite3, json
from threading import *
from datetime import datetime, timedelta
from pygame import mixer
import webbrowser
import random, os

### NOTES
### - Background not yet processed.
### - Treasure interaction in adventure not yet implemented.
### - Menu bar: Add links to adventure, stats and treasure.
# Establish connection
conn = sqlite3.connect('data/productivity.db')
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
# Pygame sound object
mixer.init()
mixer.music.load("media/alarm-loop.wav")

# gvars
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
playerStatsDict = {}
statPointsAvailable = 0
playerStatus = {}
playerIdx = 0
realtimePlayerStatus = {}
canProceed = True
actionTime = 5 # 60 default, or maybe 5, so game will be fast paced?
runeTime = 60 # 300 default, or maybe 60 if fast-paced
config = {}

class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        self.setFixedSize(247, 393)
        uic.loadUi("data/productivity-game.ui", self) # UI to be loaded
# --- GUI CONNECTS, BUTTON LINKS ---
        # Tab: Tasks Today, Work
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
        # Tab: Stats
        self.listArea = self.findChild(QListWidget, "listWidget")
        self.listWeekly = self.findChild(QPushButton, "pushButton")
        self.listDaily = self.findChild(QPushButton, "pushButton_7")
        self.listMonthly = self.findChild(QPushButton, "pushButton_9")
        self.listAllTime = self.findChild(QPushButton, "pushButton_8")
        self.totalProductivity = self.findChild(QLabel, "label_15")
        # Tab: Admin Tools
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
        self.weeklyGoalBox = self.findChild(QSpinBox, "spinBox_3")
        self.setWeekly = self.findChild(QPushButton, "pushButton_24")
        # Tab: Checklist
        self.taskName = self.findChild(QTextEdit, "textEdit_3")
        self.addCheckList = self.findChild(QPushButton, "pushButton_14")
        self.checkList = self.findChild(QListWidget, "listWidget_3")
        self.moveToDone = self.findChild(QPushButton, "pushButton_15")
        self.doneList = self.findChild(QListWidget, "listWidget_4")
        self.removeFromDone = self.findChild(QPushButton, "pushButton_16")
        self.undoFromDone = self.findChild(QPushButton, "pushButton_17")
        # Tab: Notes
        self.noteInput = self.findChild(QPlainTextEdit, "plainTextEdit")
        self.saveNoteButton = self.findChild(QPushButton, "pushButton_18")
        self.openNoteFileButton = self.findChild(QPushButton, "pushButton_19")
        self.savedLabel = self.findChild(QLabel, "label_26")
        # Tab: Player Stats
        self.statsAvailable = self.findChild(QLabel,"label_27")
        self.luk = self.findChild(QLabel,"label_36")
        self.agi = self.findChild(QLabel,"label_37")
        self.str = self.findChild(QLabel,"label_38")
        self.vit = self.findChild(QLabel,"label_39")
        self.lukButton = self.findChild(QPushButton, "pushButton_20")
        self.agiButton = self.findChild(QPushButton, "pushButton_21")
        self.strButton = self.findChild(QPushButton, "pushButton_22")
        self.vitButton = self.findChild(QPushButton, "pushButton_23")
        # Tab: Adventure
        self.gridTable = []
        for x in range (40,70):
            self.gridTable.append(self.findChild(QLabel, f"label_{x}"))
        self.consoleText = self.findChild(QLabel, "label_70")
        self.statusText = self.findChild(QLabel, "label_71")
        self.enemyStatusText = self.findChild(QLabel, "label_72")
        self.floorLevelText = self.findChild(QLabel, "label_73")
        self.backgroundImg = self.findChild(QLabel, "label_75")
        # Tab: Treasures
        self.underConstruction = self.findChild(QLabel, "label_78")
        # Tab: Actions
        self.tasksToday = self.findChild(QAction, "actionTasks_Today")
        self.work = self.findChild(QAction, "actionWork")
        self.stats = self.findChild(QAction, "actionWork_Statistics")
        self.admin = self.findChild(QAction, "actionAdmin_Tools")
        self.todo = self.findChild(QAction, "actionTodo")
        self.notes = self.findChild(QAction, "actionNotes")
        self.adventure = self.findChild(QAction, "actionAdventure")
        self.statPoints = self.findChild(QAction, "actionStats_2")
        self.treasures = self.findChild(QAction, "actionTreasures")
        # Tab Connects (For menu bar)
        self.tasksToday.triggered.connect(lambda: self.switchTab(0))
        self.work.triggered.connect(lambda: self.switchTab(1))
        self.stats.triggered.connect(lambda: self.switchTab(2))
        self.admin.triggered.connect(lambda: self.switchTab(3))
        self.todo.triggered.connect(lambda: self.switchTab(4))
        self.notes.triggered.connect(lambda: self.switchTab(5))
        self.statPoints.triggered.connect(lambda: self.switchTab(6))
        self.adventure.triggered.connect(lambda: self.switchTab(7))
        self.treasures.triggered.connect(lambda: self.switchTab(8))
        # Button links to functions
        self.lukButton.clicked.connect(lambda: self.addStatPoint("luk"))
        self.agiButton.clicked.connect(lambda: self.addStatPoint("agi"))
        self.strButton.clicked.connect(lambda: self.addStatPoint("str"))
        self.vitButton.clicked.connect(lambda: self.addStatPoint("vit"))
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
        self.setWeekly.clicked.connect(self.setGoal)
        # Setting Params
        self.mainTab.setTabEnabled(1,False)
        self.dateNow.setDate(QDate.currentDate())
        self.startingTime.setTime(QTime.currentTime())
        self.endingTime.setTime(QTime.currentTime())
        T = Thread(target=self.playerMove)
        T.setDaemon(True)
        T.start()
        # Show app, load assets
        self.updateConfig()
        self.loadCheckList()
        self.updateStats()
        self.updatePlayerStats()
        self.updateAdventureAssets()
        self.underConstructionTabs()
        self.show()

    def underConstructionTabs(self):
        self.ucPic = QPixmap('media/underconstruction.png')
        self.underConstruction.setPixmap(self.ucPic)

# --- ADVENTURE FUNCTIONS ---
    def updateAdventureAssets(self):
        """Loads up all assets needed for the adventure tab - pngs of each object in the game."""
        global playerStatus
        global realtimePlayerStatus
        self.player = QPixmap('media/player.png')
        self.background = QPixmap('media/background.png')
        self.backgroundImg.setPixmap(self.background)
        self.enemyList = [] #enemyList[0:9]
        self.treasure = QPixmap('media/treasure.png')
        self.bossList = [] #bossList[0:2]
        self.mysteryBlock = QPixmap('media/mystery.png')
        self.goal = QPixmap('media/goal.png')
        self.tavern = QPixmap('media/tavern.png')
        self.tile = QPixmap('media/tile.png')
        for x in range(0,10):
            self.enemyList.append(QPixmap(f"media/enemy{x}.png"))
        for x in range(0,3):
            self.bossList.append(QPixmap(f"media/boss{x}.png"))
        # Dictionary Loading
        try:
            jsonFile = open("data/floor.json", "r")
            playerStatus = json.load(jsonFile)
        except:
            print("Json file empty. Creating.")
            jsonFile = open("data/floor.json","w")
            playerStatus = {"floorHash":"","currentFloor":1,"playerItems": "","currentHealth":realtimePlayerStatus["maxHealth"]} 
            jsonFile = json.dump(playerStatus, jsonFile)
        realtimePlayerStatus["currentHealth"] = playerStatus["currentHealth"]
        self.loadFloor()
        
    def generateFloorHash(self):
        """Generates a random floorhash with specific parameters. Floorhash is a 60char string, with [i:i+2] representing each hashcode."""
        global playerStatus
        bossType = random.randint(0,2)
        treasureChance = random.randint(1,5)
        enemychance = random.randint(1,100)
        mysteryChance = random.randint(1,3)
        treasure = False
        if treasureChance == 1:
            treasure = True
        mystery = 3
        if mysteryChance == 1:
            mystery += 1
        enemy = 5
        if enemychance <= 5:
            enemy = 0
        elif (enemychance > 5) and (enemychance <= 15):
            enemy = 6
        floorDict = {}
        floorDict[0] = "pp"
        floorDict[14] = "rr"
        floorDict[28] = f"b{bossType}"
        floorDict[29] = "gg"
        dictNums = []
        for x in range(1,28):
            dictNums.append(x)
        dictNums.remove(14)
        if treasure:
            x = random.choice(dictNums)
            dictNums.remove(x)
            floorDict[x] = "tt"
        for elt in range(0,mystery):
            x = random.choice(dictNums)
            dictNums.remove(x)
            floorDict[x] = "mm"
        for elt in range(0, enemy):
            x = random.choice(dictNums)
            dictNums.remove(x)
            floorDict[x] = f"e{random.randint(0,9)}"
        for x in dictNums:
            floorDict[x] = "xx"
        dictItems = floorDict.items()
        sorted_items = sorted(dictItems)
        ans = ""
        for item in sorted_items:
            ans += item[1]
        playerStatus["floorHash"] = ans
    
    def saveFloor(self):
        """Saves current statusDict to json."""
        global playerStatus
        jsonFile = open("data/floor.json","w")
        jsonFile = json.dump(playerStatus, jsonFile)
    
    def loadFloor(self):
        "Loads data/floor.json to statusDict, or generates a floorhash if empty."
        global playerStatus
        self.floorLevelText.setText(f"Floor level: {playerStatus['currentFloor']}")
        global playerIdx
        floorHash = playerStatus["floorHash"]
        if floorHash == "":
            self.generateFloorHash()
            self.saveFloor()
        floorHash = playerStatus["floorHash"]
        for i in range(0,30):
            block = floorHash[i*2:(i*2)+2]
            if block == "pp":
                self.gridTable[i].setPixmap(self.player)
                playerIdx = i
            elif block == "tt":
                self.gridTable[i].setPixmap(self.treasure)
            elif block == "mm":
                self.gridTable[i].setPixmap(self.mysteryBlock)
            elif block == "gg":
                self.gridTable[i].setPixmap(self.goal)
            elif block == "rr":
                self.gridTable[i].setPixmap(self.tavern)
            elif block == "xx":
                self.gridTable[i].setPixmap(self.tile)
            elif block[0] == "e":
                self.gridTable[i].setPixmap(self.enemyList[int(block[1])])
            elif block[0] == "b":
                self.gridTable[i].setPixmap(self.bossList[int(block[1])])
            else:
                print(f"Error. Please check floorhash. block is {block}")
                exit()
    
    def playerMove(self):
        """Defines player movement. """
        global realtimePlayerStatus
        global playerIdx
        global canProceed
        global playerStatus
        global actionTime
        actionCount = 0
        while True: 
            time.sleep(actionTime)
            actionCount += 1
            proceed = self.nextAction(actionCount)
            if proceed:
                actionCount = 0
                pass
                if canProceed: #Yes means move next tile, no means go back to start, with full health.
                    tempHash = playerStatus["floorHash"]
                    tempHash = tempHash.replace("pp","xx")
                    tempHash = tempHash[0:((playerIdx+1)*2)] + "pp" + tempHash[((playerIdx+1)*2)+2:]
                else:
                    playerStatus["currentHealth"] = realtimePlayerStatus["maxHealth"]
                    realtimePlayerStatus["currentHealth"] = realtimePlayerStatus["maxHealth"]
                    tempHash = playerStatus["floorHash"]
                    tempHash = tempHash.replace("pp","xx")
                    tempHash = "pp" + tempHash[2:((playerIdx+1)*2)] + "xx" + tempHash[((playerIdx+1)*2)+2:]
                self.statusText.setText( f"Player Health: {'|'*int(realtimePlayerStatus['currentHealth'])} Damage: {str(realtimePlayerStatus['damage'])}")
                playerStatus["floorHash"] = tempHash
                self.saveFloor() # Save Json
                self.loadFloor() # Display json
    
    def nextAction(self, actionCount):
        """Console printing, and checks decision to make based on next hashcode from floorHash. nextTile represents the tile next to playerIdx."""
        global canProceed
        global playerIdx
        nextTile = playerStatus["floorHash"][((playerIdx+1)*2):((playerIdx+1)*2)+2] # get floorHash of next tile
        if nextTile == "tt": # Treasure
            if actionCount == 3:
                self.getTreasure()
                return True
            elif actionCount == 2:
                self.consoleText.setText("Searching...")
            elif actionCount == 1:
                self.consoleText.setText("You sense a treasure up ahead!")
        elif nextTile == "mm": # Mystery
            self.consoleText.setText("A mysterious crate.. What could it be?")
            self.getMystery()
            return True
        elif nextTile == "gg": # Goal
            self.consoleText.setText("Floor cleared! Moving to the next floor.")
            self.nextFloor()
            return True
        elif nextTile == "rr": # Tavern
            if actionCount == 1:
                self.consoleText.setText("You arrive at the tavern. You sit at the bar.")
            elif actionCount == 2:
                self.consoleText.setText("The tavern master arrives with food and mead for you. Health restored!")
                canProceed = True
                playerStatus["currentHealth"] = realtimePlayerStatus["maxHealth"]
                return True
        elif nextTile == "xx": # Floor tile
            if actionCount == 1:
                self.consoleText.setText("Hmm. Seems like a barren land.")
                x = random.randint(1,100)
                if realtimePlayerStatus["runSpeed"] >= x:
                    self.consoleText.setText("Your agility makes you run faster. Tile skipped!")
                    canProceed = True
                    return True
            if actionCount == 2:
                self.consoleText.setText("You venture forward.")
                canProceed = True
                return True
        elif nextTile[0] == "e": #enemy X
            if actionCount == 1:
                self.consoleText.setText("You encounter a wild monster. Battling.") # Change wild monster to {something}, depending on enemy number
            else:
                if self.battleAction(nextTile[1], actionCount, False):
                    return True
        elif nextTile[0] == "b": #boss X
            if actionCount == 1:
                self.consoleText.setText("You encounter a tough monster. This is gonna be hard.")
            else:
                if self.battleAction(nextTile[1], actionCount, True):
                    return True
        else:
            print(f"Invalid floorHash. Error. Floorhash is {nextTile}")
            exit()
    
    def battleAction(self, enemyNumber, actionCount, isBoss):
        """If nextTile is enemy or boss, battle commences. The winner is already decided even before the battle starts."""
        global canProceed
        global playerStatus
        global realtimePlayerStatus
        enemyNumber = int(enemyNumber)
        if not isBoss:
            if (enemyNumber < 7): # 0 to 6
                enemyHealth = 4
                enemyDamage = 1
            elif (enemyNumber == 7):
                enemyHealth = 4
                enemyDamage = 4
            elif (enemyNumber == 8): 
                enemyHealth = 10
                enemyDamage = 1
            elif (enemyNumber == 9): # 9
                enemyHealth = 10
                enemyDamage = 3
        else:
            if enemyNumber == 0:
                enemyHealth = 10
                enemyDamage = 3
            if enemyNumber == 1:
                enemyHealth = 5
                enemyDamage = 5
            if enemyNumber == 2:
                enemyHealth = 1
                enemyDamage = 10
        playerDamage = realtimePlayerStatus["damage"]
        playerHealth = realtimePlayerStatus["currentHealth"]
        enemyDeadTurns = (enemyHealth // playerDamage) + ((enemyHealth % playerDamage) > 0)
        playerDeadTurns = (playerHealth // enemyDamage) + ((playerHealth % enemyDamage) > 0)
        if enemyDeadTurns < playerDeadTurns: # Player Wins
            if actionCount == enemyDeadTurns + 1:
                realtimePlayerStatus["currentHealth"] -= (enemyDamage * enemyDeadTurns)
                playerStatus["currentHealth"] = realtimePlayerStatus["currentHealth"]
                self.enemyStatusText.setText("")
                self.consoleText.setText("You won the battle. Continuing to the floor.")
                canProceed = True
                return True
            else:
                pHealthGUI = "|"*(int(realtimePlayerStatus["currentHealth"])-(actionCount*enemyDamage))
                eHealthGUI = "|"*(enemyHealth-(actionCount*int(playerDamage)))
                self.statusText.setText(f"Player Health: {pHealthGUI} Damage: {playerDamage}")
                self.enemyStatusText.setText(f"Enemy Health: {eHealthGUI} Damage: {enemyDamage}")
                self.consoleText.setText(f"Battling!")
        elif enemyDeadTurns > playerDeadTurns: # Enemy Wins
            if actionCount == playerDeadTurns + 1:
                self.enemyStatusText.setText("")
                self.consoleText.setText("You were defeated. You return to the start of the floor. The monster fled.")
                canProceed = False
                return True
            else:
                x = realtimePlayerStatus["currentHealth"]
                pHealthGUI = "|"*(int(realtimePlayerStatus["currentHealth"])-(actionCount*int(enemyDamage)))
                eHealthGUI = "|"*(enemyHealth-(actionCount*int(playerDamage)))
                self.statusText.setText(f"Player Health: {pHealthGUI} Damage: {playerDamage}")
                self.enemyStatusText.setText(f"Enemy Health: {eHealthGUI} Damage: {enemyDamage}")
                self.consoleText.setText(f"Battling!")
        else: # Tie
            if actionCount == enemyDeadTurns + 1:
                canProceed = False
                self.enemyStatusText.setText("")
                self.consoleText.setText("Both of you landed the final strike. You return to the start of the floor to rest.")
                return True
            else:
                x = realtimePlayerStatus["currentHealth"]
                pHealthGUI = "|"*(int(realtimePlayerStatus["currentHealth"])-(actionCount*int(enemyDamage)))
                eHealthGUI = "|"*(enemyHealth-(actionCount*int(playerDamage)))
                self.statusText.setText(f"Player Health: {pHealthGUI} Damage: {playerDamage}")
                self.enemyStatusText.setText(f"Enemy Health: {eHealthGUI} Damage: {enemyDamage}")
                self.consoleText.setText(f"Battling!")
    
    def getTreasure(self):
        """Handles treasure interaction for nextTile. Incomplete, will develop in the future."""
        x = random.randint(1,5)
        if x == 1:
            self.consoleText.setText("A dud. The chest contained rotten bones. Yuck!")
        elif x == 2:
            self.consoleText.setText("A group of thieves spotted you and stole the chest. Good thing they spared your life!")
        else: # Treasure time!
            self.consoleText.setText("You are about to get something, but the developer was too lazy to give you one. Dang!") # Work on this.. lol
            pass

    def getMystery(self):
        """Handles mystery interaction. Currently a 75% chance of a buff and 25% chance of a debuff."""
        global realtimePlayerStatus
        global playerStatus
        x = random.randint(1,4)
        if x == 1:
            self.consoleText.setText("Boon of haste found. Your feet seem to get lighter. Action time halved for a short duration.")
            T = Thread(target=self.haste)
            T.setDaemon(True)
            T.start()
        if x == 2:
            self.consoleText.setText("You stepped on a thorny bush! Action time takes a bit longer for a short duration.")
            T = Thread(target=self.slow)
            T.setDaemon(True)
            T.start()
        if x == 3:
            self.consoleText.setText("A mystic light heals you. Health restored!")
            realtimePlayerStatus["currentHealth"] = realtimePlayerStatus["maxHealth"]
            playerStatus["currentHealth"] = realtimePlayerStatus["maxHealth"]
        if x == 4:
            self.consoleText.setText("Your sword is imbued with the power of the spirits. Double damage for a short duration.")
            T = Thread(target=self.doubleDamage)
            T.setDaemon(True)
            T.start()
            
    def doubleDamage(self):
        """Runs thread that sets damage to be doubled for runeTime seconds, then resets it after the thread."""
        global runeTime
        global realtimePlayerStatus
        realtimePlayerStatus["damage"] = realtimePlayerStatus["damage"] * 2
        print(f"damage is {realtimePlayerStatus['damage']}")
        time.sleep(runeTime)
        realtimePlayerStatus["damage"] = realtimePlayerStatus["damage"] / 2
        print(f"damage reverted is {realtimePlayerStatus['damage']}")
    
    def haste(self):
        """Runs thread that sets actionTime to be half of original value for runeTime seconds, then resets it after the thread."""
        global runeTime
        global actionTime
        actionTime = actionTime / 2
        print(f"actionTime is {actionTime}")
        time.sleep(runeTime)
        actionTime = actionTime * 2
        print(f"actionTime is reverted to {actionTime}")
    
    def slow(self):
        """Runs thread that sets actionTime to be 1.5x the original value for runeTime seconds, then resets it after the thread."""
        global runeTime
        global actionTime
        actionTime = actionTime * 1.5
        print(f"actionTime is {actionTime}")
        time.sleep(runeTime)
        actionTime = actionTime / 1.5
        print(f"actionTime is reverted to {actionTime}")

    def nextFloor(self):
        """Load next floor, happens when player's nextTile is the goal."""
        global playerStatus
        self.generateFloorHash()
        playerStatus["currentFloor"] += 1
        self.saveFloor()
        self.loadFloor()

    # --- PLAYER STATS ---
    def updatePlayerStats(self):
        """Loads player current stat points. 
        Also runs verifier to make sure that stat points allocated are not higher than the current allowable stats given for the user's productivity time."""
        global realtimePlayerStatus
        global playerStatsDict
        global statPointsAvailable
        playerStatsDict = {}
        c.execute("SELECT * from productivity")
        allWork = c.fetchall()
        totalDuration = 0
        for data in allWork:
            totalDuration += data[3]
        totalStats = totalDuration // 2700 # every 45 minutes = 1 stat point
        # Load stats file
        try:
            jsonFile = open("data/player_stats.json", "r")
            playerStatsDict = json.load(jsonFile)
        except:
            print("Json file empty. Creating")
            jsonFile = open("data/player_stats.json","w")
            playerStatsDict = {"luk":0,"agi":0,"str":0,"vit":0}
            jsonFile = json.dump(playerStatsDict, jsonFile)
        # Compute for allocated & available stats
        statsAllocated = 0
        for key, value in playerStatsDict.items():
            statsAllocated += value
        if totalStats < statsAllocated: # If total allocated is more than total stats allowable for the current productivity time,
            print("Error. Allocated stats higher than current available stats. Resetting.")
            playerStatsDict = {"luk":0,"agi":0,"str":0,"vit":0}
            statPointsAvailable = totalStats
        else:
            statPointsAvailable = totalStats - statsAllocated
        # Realtime stat computation
        realtimePlayerStatus["itemFind"] = 1.0 + (playerStatsDict["luk"] * 0.01) # treasure multiplier
        realtimePlayerStatus["runSpeed"] = 1 + (playerStatsDict["agi"] * 2) # chance to skip tiles
        realtimePlayerStatus["damage"] = 1.0 + (playerStatsDict["str"] * 0.0225) # baseDamage + damage
        realtimePlayerStatus["maxHealth"] = 10 + (playerStatsDict["vit"] * 0.05) # baseHealth + vit
        # Display
        self.statsAvailable.setText(f"Stats Available: {statPointsAvailable}")
        self.luk.setText(str(playerStatsDict["luk"]))
        self.agi.setText(str(playerStatsDict["agi"]))
        self.str.setText(str(playerStatsDict["str"]))
        self.vit.setText(str(playerStatsDict["vit"]))
        # Disable button if 0
        if statPointsAvailable == 0:
            self.lukButton.setEnabled(False)
            self.agiButton.setEnabled(False)
            self.strButton.setEnabled(False)
            self.vitButton.setEnabled(False)
    
    def addStatPoint(self, stat):
        """Adds specified stat points."""
        global playerStatsDict
        global statPointsAvailable
        if statPointsAvailable == 0: # Just another debugging tool, technically won't happen but just another bug barrier, if ever
            self.infoDialog("You have no stat points. Continue grinding to get more!")
        else:
            playerStatsDict[stat] += 1
            statPointsAvailable -= 1
            jsonFile = open("data/player_stats.json","w")
            jsonFile = json.dump(playerStatsDict, jsonFile)
            self.updatePlayerStats()

    # --- NOTES ---
    def saveNote(self):
        """Saves the specified note."""
        if self.noteInput.toPlainText() == "":
            self.infoDialog("Notes cannot be empty.")
        else:
            today = datetime.now().strftime("%b %d %Y %H:%M:%S")
            text = f"\n(DATE: {today})\n\n{self.noteInput.toPlainText()}  \n--END OF NOTE--"
            with open("data/notes.txt","a+") as f:
                f.write(text)
            self.noteInput.clear()
            T = Thread(target=self.savePrompt)
            T.setDaemon(True)
            T.start()
    
    def savePrompt(self):
        """Prompt if note is saved."""
        # Didn't use an info dialog because it might be too much of a hassle for the user to click "Ok" every after saving.
        # But I also wanted the user to be notified that their note has been saved, you feel me?
        self.savedLabel.setText("Saved!")
        time.sleep(2)
        self.savedLabel.setText("")
    
    def openNoteFile(self):
        """Button connect to open notes in notepad."""
        webbrowser.open("data/notes.txt")

    # --- TO-DO LIST ---
    def loadCheckList(self):
        """Loads to-do list. If no json file, ignore loading."""
        global taskDict
        self.doneList.clear()
        self.checkList.clear()
        try:
            jsonFile = open("data/tasks.json", "r")
            taskDict = json.load(jsonFile)
            for key, value in taskDict.items():
                if value:
                    self.doneList.addItem(key)
                else:
                    self.checkList.addItem(key)
            pass
        except:
            print("Json file empty. Ignoring load.")

    def addCheckListItem(self):
        """Adds the task input to name."""
        global taskDict
        if self.taskName.toPlainText() == "":
            self.infoDialog("Input task name")
        else:
            taskDict[self.taskName.toPlainText()] = False
            self.taskName.clear()
            self.saveCheckList()
            self.loadCheckList()

    def moveToDoneList(self):
        """Moves highlighted to-do task to the done list."""
        global taskDict
        if self.checkList.currentRow() != -1:
            taskDict[self.checkList.currentItem().text()] = True
            self.saveCheckList()
            self.loadCheckList()
        else:
            self.infoDialog("Select task from Current Tasks to move to Tasks Done.")

    def removeFromDoneList(self):
        """Removes highlighted done list."""
        global taskDict
        if self.doneList.currentRow() != -1:
            taskDict.pop(self.doneList.currentItem().text())
            self.saveCheckList()
            self.loadCheckList()
        else:
            self.infoDialog("Select task from Tasks Done to delete. \nNote: You can only remove tasks from Tasks Done. If you want to remove from Current Tasks, move them to Tasks Done first.")

    def undoFromDoneList(self):
        """Moves highlighted done task back to to-do list."""
        global taskDict
        if self.doneList.currentRow() != -1:
            taskDict[self.doneList.currentItem().text()] = False
            self.saveCheckList()
            self.loadCheckList()
        else:
            self.infoDialog("Select task from Tasks Done to move to Current Tasks.")

    def saveCheckList(self):
        """Saves todoList as json file."""
        global taskDict
        jsonFile = open("data/tasks.json","w")
        jsonFile = json.dump(taskDict, jsonFile)

    # --- PRODUCTIVITY TIMER ---
    def setTimer(self):
        """Starts the timer thread."""
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
        """Updates the label for time left, also plays alert sound when timer finishes."""
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

    # --- ADMIN'S TOOLS ---
    def loadRemoveEntry(self):
        """Refreshes the list of entries at the list."""
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
        """Sorts entries by date & time. Also creates a backup in the process."""
        self.removeList.clear()
        sortedList = []
        c.execute("SELECT * from productivity")
        allWork = c.fetchall()
        c.execute("DELETE FROM productivity_bak")
        c.execute("INSERT INTO productivity_bak SELECT * FROM productivity") # Create backup
        for data in allWork:
            start_dateObject = datetime.strptime(data[0],'%d/%m/%Y %H:%M:%S')
            sortedList.append([start_dateObject, data[1], data[2] ,data[3]])
        sortedList.sort(key = lambda x:x[0])
        c.execute(f"DELETE FROM productivity") # Delete main table
        i = 0
        for data in sortedList:
            i += 1
            data[0] = datetime.strftime(data[0], '%d/%m/%Y %H:%M:%S')
            c.execute(f"INSERT INTO productivity VALUES ('{data[0]}','{data[1]}','{data[2]}','{data[3]}')") # Insert new table
            conn.commit()
        self.infoDialog(f"Sorted {i} entries.")

    def removeEntry(self):
        """Removes highlighted entry from the database."""
        removeIdx = self.removeList.currentRow()
        if removeIdx != -1:
            conf = self.confirmAction("Remove the highlighted entry?")
            if conf:
                c.execute(f"DELETE FROM productivity WHERE start_date in (SELECT start_date FROM productivity LIMIT 1 OFFSET {removeIdx-1})")
                conn.commit()
                self.loadRemoveEntry()
                self.updateStats()
        else:
            self.infoDialog("Select an entry from the list to remove.")

    def addEntry(self):
        """Adds specified entry to the database."""
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
                conn.commit()
                self.infoDialog("Added.")
                self.duration.setValue(0)
                self.desc.clear()
                self.dateNow.setDate(QDate.currentDate())
                self.startingTime.setTime(QTime.currentTime())
                self.endingTime.setTime(QTime.currentTime())
                self.updateStats()

    def updateConfig(self):
        global config
        try:
            jsonFile = open("media/config.json", "r")
            config = json.load(jsonFile)
        except:
            config = {"weeklyGoal":40}
            print("config does not exist. Setting to default.")
            jsonFile = open("media/config.json","w")
            jsonFile = json.dump(config, jsonFile)
    
    def setGoal(self):
        global config
        if self.weeklyGoalBox.value() == 0:
            self.infoDialog("Input your weekly goal. Default is 40 hours.")
        else: 
            config["weeklyGoal"] = self.weeklyGoalBox.value()
            jsonFile = open("config.json", "w") # Saving to json
            jsonFile = json.dump(config, jsonFile)
            self.updateStats()
            self.infoDialog("Weekly goal set.")

    # --- STATISTICS ---
    def listDailyStats(self):
        """Shows a list of your productivity for the day."""
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
        """Shows a list of your productivity for the week."""
        c.execute("SELECT * from productivity")
        allWork = c.fetchall() # Returns a list
        self.listArea.clear()
        self.listArea.addItem("Date \t |Duration \t |Description")
        my_date = datetime.now()
        year, week_num, day_of_week = my_date.isocalendar()
        weekTotalInt = 0
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
        """Shows a list of your productivity for the month."""
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
        """Displays all-time productivity."""
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

    # --- WORK AND TASKS TABS ---
    def updateStats(self):
        global config
        """Shows a list of your productivity for the day."""
        # For today
        allTime = 0
        c.execute("SELECT * from productivity")
        endTime = datetime.now().strftime("%d/%m/%Y")
        allWork = c.fetchall() # Returns a list
        for data in allWork:
            if endTime in data[0]:
                allTime += data[3]
        hours = (allTime // 60) // 60
        minutes = (allTime // 60) % 60
        self.timeToday.setText(f"{hours} Hours and {minutes} Minutes")
        # Left for the Week
        my_date = datetime.now()
        year, week_num, day_of_week = my_date.isocalendar()
        weekTotalInt = 0
        for data in allWork:
            dateForWeek = datetime.strptime(data[0], '%d/%m/%Y %H:%M:%S')
            _, week, _ = dateForWeek.isocalendar()
            if week_num == week:
                weekTotalInt += data[3]
        goal = int(config["weeklyGoal"]) * 3600 # PLACEHOLDER - 40 hours a week goal. Will make it user interactive 
        weekTotalInt = goal - weekTotalInt
        hours = (weekTotalInt // 60) // 60
        minutes = (weekTotalInt // 60) % 60
        self.weekLeft.setText(f"{hours} Hours and {minutes} Minutes")
        self.updatePlayerStats() # Update player stats
    
    def workButtonClicked(self):
        """Connects to button for work. Enables work tab."""
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
        """Starts the thread for the countdown timer of your productivity."""
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

    def saveData(self):
        """Saves data of productivity into the database."""
        global startTime
        global endTime
        global totalTime
        global description
        c.execute(f"INSERT INTO productivity VALUES ('{startTime}','{endTime}','{description}','{totalTime-timeBuffer}')")
        conn.commit()
    
    def epochHandler(self):
        """Automatically saves the productivity log if it's 12AM."""
        global startTime
        global totalTime
        global timeBuffer
        timeBuffer += totalTime
        endOfDay = startTime[0:10]+" 23:59:59"
        with sqlite3.connect("data/productivity.db") as con:
            cur = con.cursor()
            cur.execute(f"INSERT INTO productivity VALUES ('{startTime}','{endOfDay}','{description}','{totalTime}')")
            startTime = datetime.now().strftime("%d/%m/%Y %H:%M:%S") # Turn back startTime to now
            con.commit()
    
    def startTime(self):
        """Thread for the productivity timer. Thread also checks for 12AM event (refer to epochHandler(self))"""
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
        """Pauses the thread for productivity, used for breaks. Same function to unpause as well."""
        global stop
        if self.breakButton.text() == "Break":
            self.breakButton.setText("Continue")
            stop = True
        else:
            self.breakButton.setText("Break")
            stop = False

# --- GLOBAL FNX ---
    def confirmAction(self, text):
        """Confirmation message box."""
        reply = QMessageBox.question(self, 'Confirmation Prompt', text,QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            return True
        else:
            return False

    def switchTab(self, idx):
        """Switches tab, connects to main menu."""
        self.mainTab.setCurrentIndex(idx)
    
    def infoDialog(self, text):
        """Information dialog."""
        msg = QMessageBox()
        msg.setWindowTitle("Prompt")
        msg.setIcon(QMessageBox.Information)
        msg.setText(text)
        msg.exec_()

    def resetApp(self):
        """Resets the application."""
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

# Initialisation
if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
app = QApplication(sys.argv)
UIWindow = UI()
app.exec_()
