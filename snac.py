import asyncio
import os
import pickle
from threading import Thread
from functools import partial
from time import time

from wizwalker import utils
from wizwalker.constants import Keycode
from wizwalker.errors import MemoryReadError
from wizwalker.extensions.wizsprinter import (CombatConfigProvider, SprintyCombat, WizSprinter)
from wizwalker.utils import XYZ, wait_for_non_error
					 
def clearConsole():
	command = 'clear'
	if os.name in ('nt', 'dos'):	# If Machine is running on Windows, use cls
		command = 'cls'
	os.system(command)

async def get_window_from_path(root_window, name_path):
	async def _recurse_follow_path(window, path):
		if len(path) == 0:
			return window

		for child in await window.children():
			if await child.name() == path[0]:
				found_window = await _recurse_follow_path(child, path[1:])
				if not found_window is False:
					return found_window

		return False

	return await _recurse_follow_path(root_window, name_path)

class SnacBot(WizSprinter):
	run = True
	# Data pickling
	try:
		data = pickle.load(open( "snac.p", "rb"))
	except (OSError, IOError) as e:
		data = {"crumbs_eaten" : 0}
		pickle.dump(data, open( "snac.p", "wb"))

	async def run(self):
		clearConsole()
		
		# Register client
		self.get_new_clients()
		client = self.get_ordered_clients()[0]
		self.client = client
		client.title = "snac time"
		await client.activate_hooks()
		await client.mouse_handler.activate_mouseless()

		await self.chomp(70)
		while self.run:
			# shop away
			await self.shop(70)
			
			# chomp away
			await self.chomp(70)
			print(f"Snacs eaten so far: {self.data['crumbs_eaten']}")
		
	#await self.clients[0].root_window.children()[0].debug_print_ui_tree()
	async def chomp(self, crumbs = 70):
	
		# Open housing inventory and decorations page
		await self.client.send_key(Keycode.U)
		await self.click_window_from_path(["WorldView", "DeckConfiguration", "FurnitureSpellbookPage", "Tab_Decoration"])
		
		# Snac loop
		i, j = 0, 0
		while i < crumbs and j < 8*crumbs/7 and self.run:
			try:
				await self.click_window_from_path(["WorldView", "DeckConfiguration", "FurnitureSpellbookPage", "Item_1"])
				await self.click_window_from_path(["WorldView", "DeckConfiguration", "FurnitureSpellbookPage", "windowForBtns", "Layout", "btnFeedPet"])
				await self.click_window_from_path(["WorldView", "DeckConfiguration", "MessageBoxModalWindow", "messageBoxBG", "messageBoxLayout", "AdjustmentWindow", "Layout", "centerButton"])
			except:
				i -= 1
			try:
				await self.click_window_from_path(["WorldView", "DeckConfiguration", "FurnitureSpellbookPage", "PetGameRewards", "btnBack"])
			except:
				pass
			i += 1; j += 1
		self.data["crumbs_eaten"] += crumbs
		pickle.dump(self.data, open( "snac.p", "wb"))
		await self.client.send_key(Keycode.ESC)
	
	async def shop(self, crumbs = 70):
		amt = crumbs // 7
		await self.click_window_named("CrownShopButtonsWindow")
		await asyncio.sleep(1)
		await self.client.mouse_handler.click(320, 69)
		for i in range(40):
			await self.client.mouse_handler.click(530, 515)
		await self.client.mouse_handler.click(165, 490)
		await asyncio.sleep(.2)
		await self.client.mouse_handler.click(675, 425)
		await asyncio.sleep(.2)
		await self.client.mouse_handler.click(730, 460)
		for i in range(amt):
			await self.client.mouse_handler.click(366, 277)
		await asyncio.sleep(.2)
		await self.client.mouse_handler.click(260, 365)
		await asyncio.sleep(.2)
		for i in range(amt+2): # sometimes doesn't close all pages
			await self.client.mouse_handler.click(402, 484)
		await asyncio.sleep(.2)
		await self.client.mouse_handler.click(777, 20)
		await asyncio.sleep(.2)
		await self.client.mouse_handler.click(685, 120)
		await asyncio.sleep(.2)
		await self.click_window_named("rightButton")
		

	async def click_window_from_path(self, path_array):
		for client in self.clients:
			coro = partial(get_window_from_path, client.root_window, path_array)
			window = await utils.wait_for_non_error(coro)
			await client.mouse_handler.click_window(window)

	async def click_window_named(self, button_name):
		for client in self.clients:
			coro = partial(client.mouse_handler.click_window_with_name, button_name)
			await utils.wait_for_non_error(coro)
		

class UserInput(Thread):
	def __init__(self, lm : SnacBot):
		Thread.__init__(self)
		self.lm = lm
		
	def run(self):
		while True:
			inp = input()
			if inp == "q":
				print("Finishing snacs")
				self.lm.run = False
				break
		self.lm.running = False # in the event of a keyboard interupt

async def startBot(snacbot : SnacBot):
	try:
		await snacbot.run()
	except:
		import traceback
		traceback.print_exc()
	
		
# Error Handling
async def main():
	snacbot = SnacBot() 
	userInput = UserInput(snacbot)
	userInput.start()
	await startBot(snacbot)
	userInput.join()
	await snacbot.close()


# Start
if __name__ == "__main__":
	asyncio.run(main())
