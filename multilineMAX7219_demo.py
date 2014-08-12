#!/usr/bin/env python
# ---------------------------------------------------------
# Filename: multilineMAX7219_demo.py
# ---------------------------------------------------------
# Demonstration of the features in the multilineMAX7219 library
#
# v1.0
# F.Stern 2014
# ---------------------------------------------------------
# improved and extended version of JonA1961's MAX7219array
# ( https://github.com/JonA1961/MAX7219array )
# ---------------------------------------------------------
# See multilineMAX7219.py library file for more details
# ---------------------------------------------------------
# This demo script is intended to run on an array of 9 (3x3)
#   MAX7219 boards, connected as described in the library
#   script. 
# The variables MATRIX_WIDTH and MATRIX_HEIGHT, defined in the 
#	multilineMAX7219.py library script, should always be set to be 
#	consistent with the actual hardware setup in use.  If it is 
#	not set correctly, then the functions will not work as
#   intended
# ---------------------------------------------------------

import time
import math
from random import randrange

# Import library
import multilineMAX7219 as LEDMatrix
# Import fonts
from multilineMAX7219_fonts import CP437_FONT, SINCLAIRS_FONT, LCD_FONT, TINY_FONT

# The following imported variables make it easier to feed parameters to the library functions
from multilineMAX7219 import DIR_L, DIR_R, DIR_U, DIR_D
from multilineMAX7219 import DIR_LU, DIR_RU, DIR_LD, DIR_RD
from multilineMAX7219 import DISSOLVE, GFX_ON, GFX_OFF, GFX_INVERT

# Initialise the library and the MAX7219/8x8LED arrays
LEDMatrix.init()

try:
	# Display a stationary message
	LEDMatrix.static_message("Welcome!")
	time.sleep(2)
	LEDMatrix.clear_all()

	# Cycle through the range of brightness levels - up then down
	LEDMatrix.brightness(0)
	LEDMatrix.static_message("Bright ?")
	for loop in range(2):
		for brightness in range(15*(loop%2), 16-17*(loop%2), 1-2*(loop%2)):
			LEDMatrix.brightness(brightness)
			time.sleep(0.1)
		time.sleep(1)

	# Clear the whole display and reset brightness
	LEDMatrix.clear_all()
	LEDMatrix.brightness(3)

	# Display all characters from the font individually
	for char in range(0x100):
		LEDMatrix.send_matrix_letter((char%9), char)
		time.sleep(0.22)
	time.sleep(0.5)
	LEDMatrix.clear_all()
	time.sleep(1)

	# Scroll characters in each of 4 directions
	for matrix in range(9):
		LEDMatrix.send_matrix_letter(matrix, 65 + matrix)
	time.sleep(0.5)
	letter_offset=0
	for dir in (DIR_L, DIR_R):
		for stage in range(8):
			for matrix in range(9):
				LEDMatrix.send_matrix_shifted_letter(matrix, 65 + matrix + 3*letter_offset, 68 + matrix - 3*letter_offset, stage, dir)
			time.sleep(0.1)
		letter_offset = 1 - letter_offset
	for dir in (DIR_D, DIR_U):
		for stage in range(8):
			for matrix in range(9):
				LEDMatrix.send_matrix_shifted_letter(matrix, 65 + matrix + letter_offset, 66 + matrix - letter_offset, stage, dir)
			time.sleep(0.1)
		letter_offset = 1 - letter_offset
	for matrix in range(9):
		LEDMatrix.send_matrix_letter(matrix, 65 + matrix)
	time.sleep(1)
	LEDMatrix.clear_all()
	
	# Send a message from some directions
	for index, dir in enumerate([DIR_RD, DIR_RU, DIR_D, DIR_U]):
		LEDMatrix.static_message("Example " + str(index+1), dir, 0.15 )
		time.sleep(0.3)
		LEDMatrix.clear_all()
	time.sleep(0.5)
	
	# Scroll only part of a display
	Floors = ["B", "G", "1", "2"]
	LEDMatrix.static_message("Floor: " + Floors[0])
	time.sleep(1)
	for floor, display in enumerate(Floors[:-1]):
		for stage in range(8):
			LEDMatrix.send_matrix_shifted_letter(3, ord(display), ord(Floors[floor+1]), stage, DIR_D)
			time.sleep(0.1)
	LEDMatrix.static_message("Floor: " + Floors[-1])
	time.sleep(1)
	LEDMatrix.clear_all()

	# Horizontally scroll and repeat a long message
	for dir in [DIR_L, DIR_R]:
		for speed in [3,6,9]:
			texts = [""] * (speed//3-1) +["Speed:"+chr(48+speed)+" ", "", ""]
			LEDMatrix.scroll_message_horiz(texts, speed//3 , speed, dir)
	time.sleep(1)

	# Vertically transition (scroll) between different messages
	for speed in [3,6,9]:
		LEDMatrix.static_message("Speed: "+chr(48+speed))
		time.sleep(1)
		LEDMatrix.scroll_message_vert("Speed: "+chr(48+speed), "Message 2",speed, DIR_U)
		time.sleep(0.25)
		LEDMatrix.scroll_message_vert("Message 2", "Message 3", speed, DIR_U)
		time.sleep(0.25)
		LEDMatrix.scroll_message_vert("Message 3", "Speed: "+chr(48+speed), speed, DIR_U)
		time.sleep(1)
		LEDMatrix.scroll_message_vert("Speed: "+chr(48+speed), "Message 5", speed, DIR_D)
		time.sleep(0.25)
		LEDMatrix.scroll_message_vert("Message 5", "Message 6", speed, DIR_D)
		time.sleep(0.25)
		LEDMatrix.scroll_message_vert("Message 6", "Speed: "+chr(48+speed), speed, DIR_D)
		time.sleep(1)
	LEDMatrix.clear_all()
	time.sleep(1)

	# Different fonts available in fonts.py
	LEDMatrix.scroll_message_horiz(["CP437_FONT : ABCDEFGH abcdefgh 1234567890 +++ ","",""], 2, 6, DIR_L, CP437_FONT)
	LEDMatrix.scroll_message_horiz(["","LCD_FONT : ABCDEFGH abcdefgh 1234567890 +++ ",""], 2, 6, DIR_L, LCD_FONT)
	LEDMatrix.scroll_message_horiz(["","","SINCLAIRS_FONT : ABCDEFGH abcdefgh 1234567890 +++ "], 2, 6, DIR_L, SINCLAIRS_FONT)
	LEDMatrix.scroll_message_horiz(["TINY_FONT : ABCDEFGH abcdefgh 1234567890 +++ ","",""], 2, 6, DIR_L, TINY_FONT)

	# Clear each matrix in turn
	for matrix in range(7, -1, -1):
		LEDMatrix.clear([matrix])
		time.sleep(0.2)
	time.sleep(1)
	
	# Print text characters using gfx_ method
	text="MAX 7219"
	for letter in range(len(text)):
		LEDMatrix.gfx_letter(ord(text[letter]), (letter%LEDMatrix.MATRIX_WIDTH)*8, ((LEDMatrix.MATRIX_HEIGHT-1) - letter//LEDMatrix.MATRIX_WIDTH)*8 -1)
		LEDMatrix.gfx_render()
		time.sleep(0.2)

	# Using gfx_ methods allows easy subsequent manipulation eg inverting text
	for col in range(0,LEDMatrix.MATRIX_WIDTH*8):
		LEDMatrix.gfx_set_col(col, GFX_INVERT)
		time.sleep(0.08)
		LEDMatrix.gfx_render()
	time.sleep(1.5)

	# Define & draw a sprite array, and then move it around on the array
	Pi = [[0,0,0,0,0,0,1,1],[0,0,0,0,0,1,0,1],[0,0,1,1,1,0,0,1],[0,1,0,0,0,1,1,0],[1,0,1,0,1,0,1,0],[1,0,0,1,0,1,0,0],[1,0,1,0,1,0,1,0],[0,1,0,0,0,1,1,0],[0,0,1,1,1,0,0,1],[0,0,0,0,0,1,0,1],[0,0,0,0,0,0,1,1],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]]
	LEDMatrix.gfx_set_all(GFX_OFF)
	LEDMatrix.gfx_sprite_array(Pi, 7,8)
	LEDMatrix.gfx_render()
	time.sleep(1)
	for repeat in range(2):
		for scroll in (DIR_L, DIR_LU, DIR_U, DIR_RU, DIR_R, DIR_RD, DIR_D, DIR_LD):
			moves = 2*repeat+1
			if scroll in [DIR_R, DIR_RD, DIR_D, DIR_LD]:
				moves += 1
			for loop in range(moves):
				LEDMatrix.gfx_scroll(scroll)
				LEDMatrix.gfx_render()
				time.sleep(0.1)
	time.sleep(1)

	# Rain Effect
	imgx = [[0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0],[0,1,1,0,0,0,1,0,1,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0],[1,0,0,0,0,1,1,0,1,0,0,0,0,1,1,0,1,0,0,1,0,0,0,0],[1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,1,0,0,0,1,0,0,0],[0,1,1,1,1,1,1,0,0,1,0,0,1,1,0,0,1,0,0,0,0,1,0,0],[0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,1,0,0,0,0,1,0,0],[0,0,0,0,0,1,1,0,1,0,0,0,0,1,1,0,1,0,0,0,1,0,0,0],[0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0],[0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,1,1,1,0,0,0,1,0,0,1,0,0,0,0,1,0,0,0,0,0,1,0],[0,1,1,1,1,1,0,0,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,0],[0,1,0,0,0,1,0,0,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,0],[0,1,0,0,0,1,0,0,1,0,0,1,0,0,1,0,1,0,0,1,0,0,1,0],[0,1,1,0,1,1,0,0,0,0,0,0,0,1,1,0,1,0,1,1,1,0,1,0],[0,0,1,0,1,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,1,1,0],[0,0,0,0,1,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],[0,1,1,1,1,1,0,0,1,1,1,1,1,0,0,0,1,0,0,1,0,0,0,0],[1,1,1,1,1,1,1,0,1,0,1,0,1,0,0,0,1,1,1,1,1,1,0,0],[1,0,0,0,1,0,0,0,1,0,1,0,1,0,0,0,1,1,1,1,1,1,1,0],[0,1,0,0,1,0,0,0,1,0,1,1,1,0,0,0,1,0,0,1,0,0,1,0],[0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,1,1,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0]]
	LEDMatrix.gfx_effect_rain(imgx)
	time.sleep(1.5)

	# Wipe to Raspberry Pi Logo
	PiLogo = [] # for the logo and the inverted version
	PiLogo += [[[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,1,0,0,1,1,0,0,0,0,0,0,0,1,1,1,0],[0,0,0,1,1,1,1,1,0,0,0,0,1,1,1,0,0,0,0,1,0,0,1,0],[0,0,1,1,0,0,1,0,0,0,0,0,1,0,0,1,1,1,1,0,0,0,0,1],[0,0,1,0,0,0,0,1,1,1,1,1,1,1,0,0,1,1,0,0,0,1,0,1],[0,1,0,0,0,0,1,1,1,1,0,0,1,1,1,0,0,1,0,0,0,1,0,1],[0,1,1,1,1,1,1,1,1,0,0,0,0,1,1,0,0,1,0,0,1,0,0,1],[0,1,1,1,1,1,1,1,1,0,0,0,0,1,1,1,1,1,0,0,1,0,1,0],[1,1,0,1,1,0,0,1,1,0,0,0,0,1,0,0,1,1,0,1,0,0,1,0],[1,0,0,1,0,0,0,1,1,1,0,0,1,1,0,0,1,1,1,0,0,0,1,0],[1,0,0,1,0,0,0,0,1,1,1,1,1,1,0,0,0,1,1,1,1,1,0,0],[1,0,0,1,0,0,0,0,1,1,1,1,1,1,0,0,0,1,1,1,1,1,0,0],[1,0,0,1,0,0,0,1,1,1,0,0,1,1,0,0,1,1,1,0,0,0,1,0],[1,1,0,1,1,0,0,1,1,0,0,0,0,1,0,0,1,1,0,1,0,0,1,0],[0,1,1,1,1,1,1,1,1,0,0,0,0,1,1,1,1,1,0,0,1,0,1,0],[0,1,1,1,1,1,1,1,1,0,0,0,0,1,1,0,0,1,0,0,1,0,0,1],[0,1,0,0,0,0,1,1,1,1,0,0,1,1,1,0,0,1,0,0,0,1,0,1],[0,0,1,0,0,0,0,1,1,1,1,1,1,1,0,0,1,1,0,0,0,1,0,1],[0,0,1,1,0,0,1,0,0,0,0,0,1,0,0,1,1,1,1,0,0,0,0,1],[0,0,0,1,1,1,1,1,0,0,0,0,1,1,1,0,0,0,0,1,0,0,1,0],[0,0,0,0,0,0,0,0,1,0,0,1,1,0,0,0,0,0,0,0,1,1,1,0],[0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]]
	PiLogo += [[[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,0,1,1,0,0,1,1,1,1,1,1,1,0,0,0,1],[1,1,1,0,0,0,0,0,1,1,1,1,0,0,0,1,1,1,1,0,1,1,0,1],[1,1,0,0,1,1,0,1,1,1,1,1,0,1,1,0,0,0,0,1,1,1,1,0],[1,1,0,1,1,1,1,0,0,0,0,0,0,0,1,1,0,0,1,1,1,0,1,0],[1,0,1,1,1,1,0,0,0,0,1,1,0,0,0,1,1,0,1,1,1,0,1,0],[1,0,0,0,0,0,0,0,0,1,1,1,1,0,0,1,1,0,1,1,0,1,1,0],[1,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,1,1,0,1,0,1],[0,0,1,0,0,1,1,0,0,1,1,1,1,0,1,1,0,0,1,0,1,1,0,1],[0,1,1,0,1,1,1,0,0,0,1,1,0,0,1,1,0,0,0,1,1,1,0,1],[0,1,1,0,1,1,1,1,0,0,0,0,0,0,1,1,1,0,0,0,0,0,1,1],[0,1,1,0,1,1,1,1,0,0,0,0,0,0,1,1,1,0,0,0,0,0,1,1],[0,1,1,0,1,1,1,0,0,0,1,1,0,0,1,1,0,0,0,1,1,1,0,1],[0,0,1,0,0,1,1,0,0,1,1,1,1,0,1,1,0,0,1,0,1,1,0,1],[1,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,1,1,0,1,0,1],[1,0,0,0,0,0,0,0,0,1,1,1,1,0,0,1,1,0,1,1,0,1,1,0],[1,0,1,1,1,1,0,0,0,0,1,1,0,0,0,1,1,0,1,1,1,0,1,0],[1,1,0,1,1,1,1,0,0,0,0,0,0,0,1,1,0,0,1,1,1,0,1,0],[1,1,0,0,1,1,0,1,1,1,1,1,0,1,1,0,0,0,0,1,1,1,1,0],[1,1,1,0,0,0,0,0,1,1,1,1,0,0,0,1,1,1,1,0,1,1,0,1],[1,1,1,1,1,1,1,1,0,1,1,0,0,1,1,1,1,1,1,1,0,0,0,1],[1,1,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]]]
	for index, scroll in enumerate([DIR_L, DIR_LU, DIR_U, DIR_RU, DIR_R, DIR_RD, DIR_D, DIR_LD]):
		LEDMatrix.gfx_effect_wipe(PiLogo[index%2], 3, scroll)
		time.sleep(0.5)
	
	# Scroll another Graphic to screen
	LEDMatrix.gfx_scroll_towards(PiLogo[0], 1, 3, DIR_L)
	LEDMatrix.gfx_scroll_towards(PiLogo[1], 2, 4, DIR_U)
	LEDMatrix.gfx_scroll_towards(PiLogo[1], 3, 5, DIR_R)
	LEDMatrix.gfx_scroll_towards(PiLogo[0], 1, 6, DIR_D)
	time.sleep(1)
	
	# Display a clock
	LEDMatrix.gfx_set_all(GFX_OFF)
	clock = [[0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[1,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1,1,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]
	centerX = 11	# position for the clockhand
	centerY = 11
	clockHandSec = 8 # length of the clockhand
	clockHandMin = 6
	clockHandHour = 5
	for s in range(30):
		sec = int(time.strftime('%S'))*6
		min = int(time.strftime('%M'))*6
		hour = int(time.strftime('%I'))*30 + int(time.strftime('%M'))/2
		LEDMatrix.gfx_set_all(GFX_OFF)
		LEDMatrix.gfx_sprite_array(clock,0,0,GFX_ON)
		LEDMatrix.gfx_line(centerX, centerY, centerX + math.sin(sec*(math.pi/180))*clockHandSec, centerY + math.cos(sec*(math.pi/180))*clockHandSec, GFX_ON)
		LEDMatrix.gfx_line(centerX, centerY, centerX + math.sin(min*(math.pi/180))*clockHandMin, centerY + math.cos(min*(math.pi/180))*clockHandMin, GFX_ON)
		LEDMatrix.gfx_line(centerX, centerY, centerX + math.sin(hour*(math.pi/180))*clockHandHour, centerY + math.cos(hour*(math.pi/180))*clockHandHour, GFX_ON)
		LEDMatrix.gfx_render()
		time.sleep(1)


	# Continuous marquee display
	diamonds = chr(4) * 5
	LEDMatrix.scroll_message_horiz([" This is the end of the demo " + diamonds, "                             Press <Ctrl><C> to end ",""], 0, 5)

except KeyboardInterrupt:
    # reset array
    LEDMatrix.scroll_message_horiz(["","Goodbye!",""], 1, 8)
    LEDMatrix.clear_all()
