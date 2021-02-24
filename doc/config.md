# MC74.mp -- Configuration Object for reviveMC74 app

A VOIP application to revive the MC74 that was withdrawn and abandoned by Cisco/Meraki.
This package contains code and instructions on how to (more or less) automatically root
an MC74 and install the new Android apps to allow the phone to be used on any VOIP
provider.


### Prerequisites

Aside from an MC74 and a host computer (with Python), you need:

* POE (Power Over Ethernet) power injector or switch port
* Ethernet cable
* USB A to USB A (host connector on both ends)
* 'git clone' this reviveMC74 repository to host computer

The reviveMC74 git repository contains any needed scripts, disk images, applications
or other files -- or will attempt to download them from the internet.  The first thing
reviveMC74.py does is verify that all the needed files are in the repo's 'installFiles'
directory.

Get a copy of the repo. In a command prompt, 'cd' to the directory where you want the 
repo.  This is where all the revival programs and backed-up image files and stuff
will be kept.

    git clone https://github.com/reviveMC74/reviveMC74.git
    cd reviveMC74

### MC74.mp object Contents and Format
The MC74.mp file is configuration file sort of like a .XML file but with a simpler format.
It contains sections for defining or configuring various parts of the MC74 software, such as the 
list of buttons on the left side of the screen, the menu items on the menu that 'slides' our 
from the left of the screen, the background images, voicemail servers and passwords, and location 
information (ie for the weather radar page and forecast graph).


his cable is used for the ADB (Android Debug Bridge) connection between your computer,
which is a USB Host (ie has a USB-A connector) and the MC74 USB-A host connector on
the right side of the MC74, just lower than the Mute button.  Make it yourself:
[USB-A to USB-A Instructable](https://www.instructables.com/Male-to-Male-A-to-A-USB-Cable/)
Of buy one, such as: 
[this one](https://www.amazon.com/UGREEN-Transfer-Enclosures-Printers-Cameras/dp/B00P0E394U)
or 
[this one](https://www.walmart.com/ip/SF-Cable-3-feet-USB-2-0-A-Male-to-A-Male-Cable-Off-White/987955884).
    

    TITLE: 'Meraki MC74 Config'
    bg: 'whiteSlate.jpg'
    config:
      screenSaver:
	img: "row.jpg"
	lightSleep: '600'
	deepSleep: '1200'
      ringtone: '/system/media/audio/ringtones/Trad.ogg'
      ringVibrate:
    swipe:
      inRight: 'ribo.ssm.Phone doKeyEvent BACK'
      outLeft: 'ribo.ssm.Phone doKeyEvent BACK'
      inTop: 'ribo.ssm.Phone doKeyEvent HOME' 
      inBottom: 'ribo.ssm.Phone doKeyEvent MENU' 
    mainFooter: ''
      history: ''
	act: 'org.linphone.history.HistoryActivity'
	img: 'footer_log'
      -contacts: ''
	act: 'org.linphone.contacts.ContactsActivity'
	img: 'footer_contacts'
      voicemail: ''
	act: 'ribo.phone.VoicemailAct'
	img: 'footer_voicemail'
      dialer: ''
	act: 'org.linphone.dialer.DialerActivity'
	img: 'footer_dialer'
      -chat: ''
	act: 'org.linphone.chat.ChatActivity'
	img: 'footer_chat'
	bg: 'white.png'
      sms: ''
	act: 'ribo.phone.WebPanel'
	img: 'footer_sms'
	url: 'http://localhost:1808/smspanel'
    sideMenu: ''
      -assistant: 'Assistant'
	img: 'menu_assistant'
	act: 'org.linphone.assistant.GenericConnectionAssistantActivity'
	-act: 'org.linphone.assistant.MenuAssistantActivity'
      voipSettings: 'SIP address'
	img: 'menu_weather'
	act: 'ribo.phone.WebAct'
	cmd: 'http://localhost:1808/voipsettings'
      recordings: 'Recordings'
	img: 'menu_recordings'
	act: 'org.linphone.recording.RecordingsActivity'
      wRadar: 'Weather Radar'
	img: 'menu_weather'
	act: 'ribo.phone.WebAct'
	cmd: 'http://localhost:1808/weather/radar'
      wGraph: 'Weather Forecast Graph'
	img: 'menu_weather'
	act: 'ribo.phone.WebAct'
	cmd: 'http://localhost:1808/weather/graph'
      settings: 'Settings'
	img: 'menu_options'
	act: 'org.linphone.settings.SettingsActivity'
	bg: 'white.png'



## Weather Radar Page

![Weather Radar Page](doc/weatherRadar.jpg)

The weather radar menu item on the left 'slide out' menu is defined be following part of the
MC74.mp configuration object:

    sideMenu: ''
      wRadar: 'Weather Radar'
	img: 'menu_weather'
	act: 'ribo.phone.WebAct'
	cmd: 'http://localhost:1808/weather/radar'

The default location for the map for the radar image is defined in another section of the MC74 object:

    weather:
      latLong: '41.8239, -71.4128'
      location: 'Boston'
      map: 'street'
      zoom: '8'

The 'latLong' entry specifies the latitude and longitude in degrees for the center point of the 
map image.  I use a location slightly to the south west of my location of interest because 
storms usually come in from that direction.

If latLong is omitted, the text in the 'location' entry use passed to (weather.gov, the website
that provides the weather info) to find the location.
