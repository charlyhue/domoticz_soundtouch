"""
<plugin key="soundtouch" name="Bose Soundtouch" author="Charly Hue" version="0.0.2">
    <params>

        <param field="Address" label="IP Address" width="200px" required="true" default="0.0.0.0"/>
        <param field="Port" label="Port" width="30px" required="true" default="8090"/>

        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
from xml.dom import minidom


class BasePlugin:

    __HEARTBEATS2MIN = 6
    __MINUTES = 1         # or use a parameter

    # Device units
    __UNIT_SOURCE = 1
    __UNIT_PRESETS = 2
    __UNIT_LIKE = 3
    __UNIT_CONTROLS = 4
    __UNIT_VOLUME = 5

    def __init__(self):
        self.__runAgain = 0
        self.__runChoice = 0
        return

    def onStart(self):
        Domoticz.Debug("onStart called")
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
        else:
            Domoticz.Debugging(0)

        self.httpConn = Domoticz.Connection(Name="HTTP Test", Transport="TCP/IP", Protocol="HTTP",
                                            Address=Parameters["Address"], Port=Parameters["Port"])
        self.httpConn.Connect()

        # Validate parameters
        # Create devices
        # if len(Devices) == 0:
        #     Domoticz.Device(Unit=self.__UNIT_TEXT, Name="Last", TypeName="Text", Used=1).Create()
        if self.__UNIT_SOURCE not in Devices:
            Options = {"LevelActions": "||||",
                       "LevelNames": "Off|AUX|Soundtouch|Bluetooth",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "0"}
            Domoticz.Device(Name="Source", Unit=self.__UNIT_SOURCE,
                            TypeName="Selector Switch", Options=Options, Switchtype=18, Image=8).Create()
        if self.__UNIT_PRESETS not in Devices:
            Options = {"LevelActions": "|||||||",
                       "LevelNames": "|1|2|3|4|5|6",
                       "LevelOffHidden": "true",
                       "SelectorStyle": "0"}
            Domoticz.Device(Name="Presets", Unit=self.__UNIT_PRESETS ,
                            TypeName="Selector Switch", Options=Options, Image=8).Create()
        if self.__UNIT_LIKE not in Devices:
            Options = {"LevelActions": "|||",
                       "LevelNames": "|+|-",
                       "LevelOffHidden": "true",
                       "SelectorStyle": "0"}
            Domoticz.Device(Name="Like", Unit=self.__UNIT_LIKE,
                            TypeName="Selector Switch", Options=Options, Image=8).Create()
        if self.__UNIT_CONTROLS not in Devices:
            Options = {"LevelActions": "|||||",
                       "LevelNames": "|PLAY_PAUSE|PREV_TRACK|NEXT_TRACK|MUTE",
                       "LevelOffHidden": "true",
                       "SelectorStyle": "0"}
            Domoticz.Device(Name="Controls", Unit=self.__UNIT_CONTROLS,
                            TypeName="Selector Switch", Options=Options, Image=8).Create()
        if self.__UNIT_VOLUME not in Devices:
            Domoticz.Device(Name="Volume", Unit=self.__UNIT_VOLUME,
                            Type=244, Subtype=73, Switchtype=7, Image=8).Create()
        # Log config
        DumpConfigToLog()
        # Connection

    def onStop(self):
        Domoticz.Debug("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")
        print(Data)
        doc = minidom.parseString(Data['Data'].decode("utf-8", "ignore"))
        node = doc.childNodes[0]
        Domoticz.Debug(node.nodeName)

        if node.nodeName == 'volume':
            vol = node.getElementsByTagName('actualvolume')[0].firstChild.nodeValue
            Domoticz.Debug(vol)
            if vol == 0:
                n = 0
            else:
                n=2
            UpdateDevice(self.__UNIT_VOLUME, n, vol)
        if node.nodeName == 'nowPlaying':
            source = node.getAttributeNode('source').nodeValue
            Domoticz.Debug(source)
            if source == 'STANDBY':
                UpdateDevice(self.__UNIT_SOURCE, 0, '0')
            elif source == 'BLUETOOTH':
                UpdateDevice(self.__UNIT_SOURCE, 1, '30')
            elif source == 'PRODUCT':
                UpdateDevice(self.__UNIT_SOURCE, 1, '10')
            else:
                UpdateDevice(self.__UNIT_SOURCE, 1, '20')


    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug(
            "onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

        if Unit == self.__UNIT_SOURCE:
            if Command == 'Set Level' or Command == 'Off':
                if Level == 0:
                    if Devices[self.__UNIT_SOURCE].nValue != 0:
                        self.post('/key', '<key state="press" sender="Gabbo">POWER</key>')
                        self.post('/key', '<key state="release" sender="Gabbo">POWER</key>')
                elif Level == 10:
                    self.post('/select', '<ContentItem source="PRODUCT" sourceAccount="TV"></ContentItem>')
                elif Level == 20:
                    self.post('/select', '<ContentItem source="TUNEIN" type="stationurl" location="/v1/playback/station/s2109" sourceAccount="" isPresetable="true"></ContentItem>')
                elif Level == 30:
                    self.post('/select', '<ContentItem source="BLUETOOTH" sourceAccount=""></ContentItem>')
        elif Unit == self.__UNIT_PRESETS:
            if Command == 'Set Level':
                self.post('/key', '<key state="release" sender="Gabbo">PRESET_{0}</key>'.format(int(Level/10)))
        elif Unit == self.__UNIT_CONTROLS:
            if Command == 'Set Level':
                if Level == 10:
                    self.post('/key', '<key state="press" sender="Gabbo">PLAY_PAUSE</key>')
                elif Level == 20:
                    self.post('/key', '<key state="press" sender="Gabbo">PREV_TRACK</key>')
                elif Level == 30:
                    self.post('/key', '<key state="press" sender="Gabbo">NEXT_TRACK</key>')
                elif Level == 40:
                    self.post('/key', '<key state="press" sender="Gabbo">MUTE</key>')
        elif Unit == self.__UNIT_LIKE:
            if Command == 'Set Level':
                if Level == 10:
                    self.post('/key', '<key state="press" sender="Gabbo">ADD_FAVORITE</key>')
                elif Level == 20:
                    self.post('/key', '<key state="press" sender="Gabbo">REMOVE_FAVORITE</key>')
        elif Unit == self.__UNIT_VOLUME:
            if Command == 'Set Level':
                self.post('/volume', '<volume>{0}</volume>'.format(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(
            Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")
        self.httpConn.Connect()

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")
        self.__runAgain -= 1
        if self.__runAgain <= 0:
            self.__runAgain = self.__HEARTBEATS2MIN * self.__MINUTES
            # Execute your command
        else:
            Domoticz.Debug("onHeartbeat called, run again in " + str(self.__runAgain) + " heartbeats.")
            if self.__runChoice == 0:
                self.get('/now_playing')
                self.__runChoice = 1
            elif self.__runChoice == 1:
                self.get('/volume')
                self.__runChoice = 0


    def send(self, verb, url, data):
        headers = {'Content-Type': 'text/xml; charset=utf-8',
                   'Connection': 'keep-alive',
                   'Accept': 'Content-Type: text/xml; charset=UTF-8',
                   'Host': Parameters["Address"] + ":" + Parameters["Port"],
                   'User-Agent': 'Domoticz/1.0',
                   'Content-Length': "%d" % (len(data))
                   }
        self.httpConn.Send({'Verb': verb, 'URL': url, "Headers": headers, 'Data': data})

    def post(self, url, data):
        self.send('POST', url, data)

    def get(self, url):
        self.send('GET', url, {})

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

################################################################################
# Generic helper functions
################################################################################
def DumpConfigToLog():
    # Show parameters
    Domoticz.Debug("Parameters count.....: " + str(len(Parameters)))
    for x in Parameters:
        if Parameters[x] != "":
           Domoticz.Debug("Parameter '" + x + "'...: '" + str(Parameters[x]) + "'")
    # Show settings
        Domoticz.Debug("Settings count...: " + str(len(Settings)))
    for x in Settings:
       Domoticz.Debug("Setting '" + x + "'...: '" + str(Settings[x]) + "'")
    # Show images
    Domoticz.Debug("Image count..........: " + str(len(Images)))
    for x in Images:
        Domoticz.Debug("Image '" + x + "...': '" + str(Images[x]) + "'")
    # Show devices
    Domoticz.Debug("Device count.........: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device...............: " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device Idx...........: " + str(Devices[x].ID))
        Domoticz.Debug("Device Type..........: " + str(Devices[x].Type) + " / " + str(Devices[x].SubType))
        Domoticz.Debug("Device Name..........: '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue........: " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue........: '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device Options.......: '" + str(Devices[x].Options) + "'")
        Domoticz.Debug("Device Used..........: " + str(Devices[x].Used))
        Domoticz.Debug("Device ID............: '" + str(Devices[x].DeviceID) + "'")
        Domoticz.Debug("Device LastLevel.....: " + str(Devices[x].LastLevel))
        Domoticz.Debug("Device Image.........: " + str(Devices[x].Image))

def UpdateDevice(Unit, nValue, sValue, TimedOut=0, AlwaysUpdate=False):
    if Unit in Devices:
        if Devices[Unit].nValue != nValue or Devices[Unit].sValue != sValue or Devices[Unit].TimedOut != TimedOut or AlwaysUpdate:
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue), TimedOut=TimedOut)
            Domoticz.Debug("Update " + Devices[Unit].Name + ": " + str(nValue) + " - '" + str(sValue) + "'")

def UpdateDeviceOptions(Unit, Options={}):
    if Unit in Devices:
        if Devices[Unit].Options != Options:
            Devices[Unit].Update(nValue=Devices[Unit].nValue, sValue=Devices[Unit].sValue, Options=Options)
            Domoticz.Debug("Device Options update: " + Devices[Unit].Name + " = " + str(Options))

def UpdateDeviceImage(Unit, Image):
    if Unit in Devices and Image in Images:
        if Devices[Unit].Image != Images[Image].ID:
            Devices[Unit].Update(nValue=Devices[Unit].nValue, sValue=Devices[Unit].sValue, Image=Images[Image].ID)
            Domoticz.Debug("Device Image update: " + Devices[Unit].Name + " = " + str(Images[Image].ID))

def DumpHTTPResponseToLog(httpDict):
    if isinstance(httpDict, dict):
        Domoticz.Debug("HTTP Details (" + str(len(httpDict)) + "):")
        for x in httpDict:
            if isinstance(httpDict[x], dict):
                Domoticz.Debug("....'" + x + " (" + str(len(httpDict[x])) + "):")
                for y in httpDict[x]:
                    Domoticz.Debug("........'" + y + "':'" + str(httpDict[x][y]) + "'")
            else:
                Domoticz.Debug("....'" + x + "':'" + str(httpDict[x]) + "'")