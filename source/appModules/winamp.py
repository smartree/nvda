#appModules/winamp.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2007 NVDA Contributors <http://www.nvda-project.org/>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

from ctypes import *
from ctypes.wintypes import *
import winKernel
import winUser
from keyUtils import key, sendKey
from NVDAObjects.IAccessible import IAccessible 
import appModuleHandler
import speech
import locale

# message used to sent many messages to winamp's main window. 
# most all of the IPC_* messages involve sending the message in the form of:
#   result = SendMessage(hwnd_winamp,WM_WA_IPC,(parameter),IPC_*);

WM_WA_IPC=winUser.WM_USER

# playlist editor
IPC_PLAYLIST_GET_NEXT_SELECTED=3029
IPC_PE_GETCURINDEX=100
IPC_PE_GETINDEXTOTAL=101
# in_process ONLY
IPC_PE_GETINDEXTITLE=200 #  lParam = pointer to fileinfo2 structure

class fileinfo2(Structure):
	_fields_=[
		('fileindex',c_int),
		('filetitle',c_char*256),
		('filelength',c_char*16),
	]

hwndWinamp=0

class appModule(appModuleHandler.appModule):

	def event_NVDAObject_init(self,obj):
		global hwndWinamp
		hwndWinamp=windll.user32.FindWindowA("Winamp v1.x",None)
		if obj.windowClassName=="Winamp PE":
			obj.__class__=winampPlaylistEditor

class winampPlaylistEditor(IAccessible):

	def _get_value(self):
		curIndex=winUser.sendMessage(hwndWinamp,WM_WA_IPC,-1,IPC_PLAYLIST_GET_NEXT_SELECTED)
		if curIndex <0:
			return None
		info=fileinfo2()
		info.fileindex=curIndex
		processHandle=winKernel.openProcess(winKernel.PROCESS_VM_OPERATION|winKernel.PROCESS_VM_READ|winKernel.PROCESS_VM_WRITE,False,self.windowProcessID)
		internalInfo=winKernel.virtualAllocEx(processHandle,None,sizeof(info),winKernel.MEM_COMMIT,winKernel.PAGE_READWRITE)
		winKernel.writeProcessMemory(processHandle,internalInfo,byref(info),sizeof(info),None)
		winUser.sendMessage(self.windowHandle,WM_WA_IPC,IPC_PE_GETINDEXTITLE,internalInfo)
		winKernel.readProcessMemory(processHandle,internalInfo,byref(info),sizeof(info),None)
		winKernel.virtualFreeEx(processHandle,internalInfo,0,winKernel.MEM_RELEASE)
		return unicode("%d.\t%s\t%s"%(curIndex+1,info.filetitle,info.filelength), errors="replace", encoding=locale.getlocale()[1])

	def _get_basicText(self):
		return self._get_value()

[winampPlaylistEditor.bindKey(keyName,scriptName) for keyName,scriptName in [
	("ExtendedUp","moveByLine"),
	("ExtendedDown","moveByLine"),
]]
