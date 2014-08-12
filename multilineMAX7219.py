#!/usr/bin/env python
# ---------------------------------------------------------
# Filename: multilineMAX7219.py
# ---------------------------------------------------------
# multilineMAX7219 library - functions for driving n * m
# daisy-chained MAX7219 8x8 LED matrices boards
#
# v1.0
# F.Stern 2014
# ---------------------------------------------------------
# improved and extended version of JonA1961's MAX7219array
# ( https://github.com/JonA1961/MAX7219array )
# ---------------------------------------------------------
# Controls a linear array of MAX7219 LED Display Drivers,
#   each of which is driving an 8x8 LED matrix.
#
# Terminology used in this script:
# - matrix: one of the MAX7219 boards incl 8x8 LED display
# - array: a 'daisy-chained' multiline display of such matrices
#
# Wiring up the array of MAX7219 controller boards:
# - Each board's Vcc & GND pins connected to power (not from
#   the Raspberry Pi as the current requirement would be too
#   high). Note that the common GND also needs to be connected
#   to the Pi's GND pin
# - Each board's CS & CLK pins to be connected to the corresponding
#   SPI GPIO pins (CE0=Pin24 & SCLK=Pin23) on the RPi
# - The right-most board's DIN pins to be connected to the
#   MOSI (=Pin19) SPI GPIO pin on the RPi
# - Each subsequent board's DIN pin to be connected to the DOUT
#   pin on the board to its right as shown below:
#
#   ...-+    +----+    +----+    +----+
#       |    |    |    |    |    |    |
#     DOUT-  |  DOUT-  |  DOUT-  |  DOUT-
#     |   |  |  |   |  |  |   |  |  |   |
#     -DIN-  |  -DIN-  |  -DIN-  |  -DIN-
#       |    |    |    |    |    |    |
#       +----+    +----+    +----+    +---> RPi SPI.MOSI
#
# Numbering used by this library:
# - The number of horizontal matrices (amount of matrix modules in one row)
# - The number of vertical matrices (amount of matrix modules in one column)
#   in the MATRIX_WIDTH and MATRIX_HEIGHT variables below
# - Matrices are numbered from 0 (left bottom) to MATRIX_HEIGHT*MATRIX_WIDTH-1 (right top)
#	while the following matrix is the one above. If it is the uppermost matrix, the
#	following matrix is the one in the column right next to it (bottom):
#	e.g. 4x3 matrices:
#	2  5  8  11
#	1  4  7  10
#	0  3  6  9	
# - gfx_ (graphics-based) functions use an x,y coordinate system
#   to address individual LEDs:
#     x=0 (left-hand column) to x=8*MATRIX_WIDTH-1 (right-hand column)
#     y=0 (bottom row) to y=8*MATRIX_HEIGHT-1 (top row)
# ---------------------------------------------------------
# The main use for this script is as an imported library:
#   1. In the main script, import the library using eg:
#        import multilineMAX7219.py as LEDMatrix
#   2. Also import the fonts with:
#        from multilineMAX7219_fonts import CP437_FONT, SINCLAIRS_FONT, LCD_FONT, TINY_FONT
#   3. To facilitate calling the library functions,
#      import the following pre-defined parameters:
#        from multilineMAX7219 import DIR_L, DIR_R, DIR_U, DIR_D
#        from multilineMAX7219 import DIR_LU, DIR_RU, DIR_LD, DIR_RD
#        from multilineMAX7219 import DISSOLVE, GFX_ON, GFX_OFF, GFX_INVERT
#   4. The main script can then use the library functions using eg:
#        LEDMatrix.scroll_message_horiz(["This is line 1", "Sample Text"])
#
# This script can also be executed directly as a shorthand way of running
#   a 'marquee' display.  Enter the following at the command line to use
#   this functionality:
#       python multilineMAX7219.py message [repeats [speed [direction [font]]]]"
# Or for more information on this usage, see the help text at the end of this
#   script, or alternatively, enter the following at the command line:
#       python multilineMAX7219.py
# ---------------------------------------------------------
# Based on and extended from the MAX7219array module by JonA1961
#   (see https://github.com/JonA1961/MAX7219array )
# ---------------------------------------------------------
# Requires:
# - python-dev & py-spidev modules, see install instructions
#   at www.100randomtasks.com/simple-spi-on-raspberry-pi
# - MAX7219fonts.py file containing font bitmaps
# - User should also set MATRIX_HEIGHT and MATRIX_WIDTH variables below 
# 	to the appropriate value for the setup in use.  Failure to do
#   this will prevent the library functions working properly
# ---------------------------------------------------------
# The functions from spidev used in this library are:
#   xfer()  : send bytes deasserting CS/CE after every byte
#   xfer2() : send bytes only de-asserting CS/CE at end
# ---------------------------------------------------------
# The variables MATRIX_HEIGHT and MATRIX_WIDTH, defined in the 
#	multilineMAX7219.py library script, should always be set to be 
#	consistent with the actual hardware setup in use.
#
# ---------------------------------------------------------
# See further documentation of each library function below
# Also see multilineMAX7219_demo.py script for examples of use
# MAX7219 datasheet gives full details of operation of the
# LED driver chip
# ---------------------------------------------------------

import spidev
import time
from random import randrange

# Note: If any additional fonts are added in multilineMAX7219_fonts.py, add them to the import list here:
#       Also add them to the section at the end of this script that parses command line arguments
from multilineMAX7219_fonts import CP437_FONT, SINCLAIRS_FONT, LCD_FONT, TINY_FONT

# IMPORTANT: User must specify the number of MAX7219 matrices here:
MATRIX_WIDTH  = 3
MATRIX_HEIGHT = 3

# Optional: It is also possible to change the default font for all the library functions:
DEFAULT_FONT = CP437_FONT          # Note: some fonts only contain characters in chr(32)-chr(126) range

# ---------------------------------------------------------
# Should not need to change anything below here
# ---------------------------------------------------------

NUM_MATRICES  = MATRIX_WIDTH * MATRIX_HEIGHT 
PAD_STRING   = " " * NUM_MATRICES  # String for trimming text to fit
NO_OP        = [0,0]               # 'No operation' tuple: 0x00 sent to register MAX_7219_NOOP
MATRICES     = range(NUM_MATRICES) # List of available matrices for validation

# Graphics setup
gfx_rows    = range(MATRIX_HEIGHT * 8)
gfx_columns = range(MATRIX_WIDTH * 8)
gfx_buffer  = [[0 for x1 in xrange(MATRIX_HEIGHT*8)] for x2 in xrange(MATRIX_WIDTH*8)]

# Registers in the MAX7219 matrix controller (see datasheet)
MAX7219_REG_NOOP        = 0x0
MAX7219_REG_DIGIT0      = 0x1
MAX7219_REG_DIGIT1      = 0x2
MAX7219_REG_DIGIT2      = 0x3
MAX7219_REG_DIGIT3      = 0x4
MAX7219_REG_DIGIT4      = 0x5
MAX7219_REG_DIGIT5      = 0x6
MAX7219_REG_DIGIT6      = 0x7
MAX7219_REG_DIGIT7      = 0x8
MAX7219_REG_DECODEMODE  = 0x9
MAX7219_REG_INTENSITY   = 0xA
MAX7219_REG_SCANLIMIT   = 0xB
MAX7219_REG_SHUTDOWN    = 0xC
MAX7219_REG_DISPLAYTEST = 0xF

# Scroll & wipe directions, for use as arguments to various library functions
# For ease of use, import the following constants into the main script
DIR_U      = 1   # Up
DIR_R      = 2   # Right
DIR_D      = 4   # Down
DIR_L      = 8   # Left
DIR_RU     = 3   # Right & up diagonal scrolling for gfx_scroll() function only
DIR_RD     = 6   # Right & down diagonal scrolling for gfx_scroll() function only
DIR_LU     = 9   # Left & up diagonal scrolling for gfx_scroll() function only
DIR_LD     = 12  # Left & down diagonal scrolling for gfx_scroll() function only
DISSOLVE   = 16  # Pseudo-random fade transition for wipe_message() function only
GFX_OFF    = 0   # Turn the relevant LEDs off, or omit (don't draw) the endpoint of a line
GFX_ON     = 1   # Turn the relevant LEDs on, or include (draw) the endpoint of a line
GFX_INVERT = 2   # Invert the state of the relevant LEDs

# Open SPI bus#0 using CS0 (CE0)
spi = spidev.SpiDev()
spi.open(0,0)

# ---------------------------------------
# Library function definitions begin here
# ---------------------------------------

def send_reg_byte(register, data):
    # Send one byte of data to one register via SPI port, then raise CS to latch
    # Note that subsequent sends will cycle this tuple through to successive MAX7219 chips
    spi.xfer([register, data])

def send_bytes(datalist):
    # Send sequence of bytes (should be [register,data] tuples) via SPI port, then raise CS
    # Included for ease of remembering the syntax rather than the native spidev command, but also to avoid reassigning to 'datalist' argument
    spi.xfer2(datalist[:])

def send_matrix_reg_byte(matrix, register, data):
    # Send one byte of data to one register in just one MAX7219 without affecting others
    if matrix in MATRICES:
        padded_data = NO_OP * (NUM_MATRICES - 1 - matrix) + [register, data] + NO_OP * matrix
        send_bytes(padded_data)

def send_all_reg_byte(register, data):
    # Send the same byte of data to the same register in all of the MAX7219 chips
    send_bytes([register, data] * NUM_MATRICES)

def clear(matrix_list):
    # Clear one or more specified MAX7219 matrices (argument(s) to be specified as a list even if just one)
    for matrix in matrix_list:
        if matrix in MATRICES:
            for col in range(8):
                send_matrix_reg_byte(matrix, col+1, 0)

def clear_all():
    # Clear all of the connected MAX7219 matrices
    for col in range(8):
        send_all_reg_byte(col+1, 0)

def brightness(intensity):
    # Set a specified brightness level on all of the connected MAX7219 matrices
    # Intensity: 0-15 with 0=dimmest, 15=brightest; in practice the full range does not represent a large difference
    intensity = int(max(0, min(15, intensity)))
    send_bytes([MAX7219_REG_INTENSITY, intensity] * NUM_MATRICES)

	
def send_matrix_letter(matrix, char_code, font=DEFAULT_FONT):
    # Send one character from the specified font to a specified MAX7219 matrix
    if matrix in MATRICES:
        for col in range(8):
            send_matrix_reg_byte(matrix, col+1, font[char_code % 0x100][col])

def send_matrix_shifted_letter(matrix, curr_code, next_code, progress, direction=DIR_L, font=DEFAULT_FONT):
    # Send to one MAX7219 matrix a combination of two specified characters, representing a partially-scrolled position
    # progress: 0-7: how many pixels the characters are shifted: 0=curr_code fully displayed; 7=one pixel less than fully shifted to next_code
    # With multiple matrices, this function sends many NO_OP tuples, limiting the scrolling speed achievable for a whole line
    # scroll_message_horiz() and scroll_message_vert() are more efficient and can scroll a whole line of text faster
    curr_char = font[curr_code % 0x100]
    next_char = font[next_code % 0x100]
    show_char = [0,0,0,0,0,0,0,0]
    progress  = progress % 8
    if matrix in MATRICES:
        if direction == DIR_L:
            for col in range(8):
                if col+progress < 8:
                    show_char[col] = curr_char[col+progress]
                else:
                    show_char[col] = next_char[col+progress-8]
                send_matrix_reg_byte(matrix, col+1, show_char[col])
        elif direction == DIR_R:
            for col in range(8):
                if col >= progress:
                    show_char[col] = curr_char[col-progress]
                else:
                    show_char[col] = next_char[col-progress+8]
                send_matrix_reg_byte(matrix, col+1, show_char[col])
        elif direction == DIR_U:
            for col in range(8):
                show_char[col] = (curr_char[col] >> progress) + (next_char[col] << (8-progress))
                send_matrix_reg_byte(matrix, col+1, show_char[col])
        elif direction == DIR_D:
            for col in range(8):
                show_char[col] = (curr_char[col] << progress) + (next_char[col] >> (8-progress))
                send_matrix_reg_byte(matrix, col+1, show_char[col])

def static_message(message, direction=DIR_RD, delay=0, font=DEFAULT_FONT):
    # Send a stationary text message to the array of MAX7219 matrices
    # Message will be truncated from the right to fit the array
	# Message can be send in this directions:	DIR_RD	DIR_RU	DIR_D	DIR_U
	# (e.g. message='012345678')				0 1 2 	6 7 8	0 3 6	2 5 8
	#											3 4 5	3 4 5	1 4 7	1 4 7
	#											6 7 8	0 1 2	2 5 8	0 3 6
	# delay = x seconds can delay the appearance of the following character
	message = trim(message)
	delay = delay
	idx = 0
	if direction == DIR_RD or direction == DIR_R:
		for l_row in reversed(range(MATRIX_HEIGHT)):
			for l_col in range(MATRIX_WIDTH):
				matrix = l_row + l_col*MATRIX_HEIGHT
				send_matrix_letter( matrix, ord(message[idx] ), font)
				idx += 1
				time.sleep(delay)
	elif direction == DIR_RU:
		for l_row in range(MATRIX_HEIGHT):
			for l_col in range(MATRIX_WIDTH):
				matrix = l_row + l_col*MATRIX_HEIGHT
				send_matrix_letter( matrix, ord(message[idx] ), font)
				idx += 1
				time.sleep(delay)
	elif direction == DIR_D:
		for l_col in range(MATRIX_WIDTH):
			for l_row in reversed(range(MATRIX_HEIGHT)):
				matrix = l_row + l_col*MATRIX_HEIGHT
				send_matrix_letter( matrix, ord(message[idx] ), font)
				idx += 1
				time.sleep(delay)
	elif direction == DIR_U:
		for l_col in range(MATRIX_WIDTH):
			for l_row in range(MATRIX_HEIGHT):
				matrix = l_row + l_col*MATRIX_HEIGHT
				send_matrix_letter( matrix, ord(message[idx] ), font)
				idx += 1
				time.sleep(delay)
	
def scroll_message_horiz(messages, repeats=0, speed=3, direction=DIR_L, font=DEFAULT_FONT, finish=True):
    # Scroll some text messages across the lines, for a specified number of times (repeats)
    # repeats=0 gives indefinite scrolling until script is interrupted
    # speed: 0-9 for practical purposes; speed does not have to integral
    # direction: DIR_L or DIR_R only; DIR_U & DIR_D will do nothing
    # finish: True/False - True ensures array is clear at end, False ends with the last columns of the messages
    #   still displayed on the array - this is included for completeness but rarely likely to be required in practice
    # Scrolling starts with messages off the RHS(DIR_L)/LHS(DIR_R) of array, and ends with messages off the LHS/RHS
    # If repeats>1, add space(s) at the ends 'message' in each row to separate the end of messages & start of its repeat
	delay = 0.5 ** speed
	if repeats <= 0:
		indef = True
	else:
		indef = False
		repeats = int(repeats)
	longest_msg = max( [len(m) for m in messages] )
	for row in range(len(messages)):
		if len(messages[row]) < longest_msg:
			messages[row] = trim(messages[row], longest_msg)
	messages = messages * MATRIX_HEIGHT
	messages = messages[:MATRIX_HEIGHT]
	# Repeatedly scroll the whole message (initially 'front-padded' with blanks) until the last char appears
	if direction == DIR_L:
		scroll_texts = [PAD_STRING[:MATRIX_WIDTH] + m for m in messages ]
	elif direction == DIR_R:
		scroll_texts = [m + PAD_STRING[:MATRIX_WIDTH] for m in messages ]
	counter = repeats
	while (counter > 0) or indef:
		scroll_text_once(scroll_texts, delay, direction, font)
		# After the first scroll, replace the blank 'front-padding' with the start of the same messages
		if counter == repeats:
			if direction == DIR_L:
				scroll_texts = [ m[-MATRIX_WIDTH:] + m for m in messages]
			elif direction == DIR_R:
				scroll_texts = [ m + m[:MATRIX_WIDTH] for m in messages]
		counter -= 1
	# To finish, 'end-pad' the messages with blanks and scroll the end of the messages off the array
	if direction == DIR_L:
		scroll_texts = [ m[-MATRIX_WIDTH:] + PAD_STRING[:MATRIX_WIDTH] for m in messages]
	elif direction == DIR_R:
		scroll_texts = [ PAD_STRING[:MATRIX_WIDTH] + m[:MATRIX_WIDTH] for m in messages]
	scroll_text_once(scroll_texts, delay, direction, font)
	# Above algorithm leaves the last column of the last character displayed on the array, so optionally erase it
	if finish:
		clear_all()
		
def scroll_text_once(texts, delay, direction, font):
    # Subroutine used by scroll_message_horiz(), scrolls texts[line] once across a line , starting & ending with test on the array
    # Not intended to be used as a user routine; if used, note different syntax: compulsory arguments & requires delay rather than speed
	length = len(texts[0]) - MATRIX_WIDTH
	start_range = []
	if direction == DIR_L:
		start_range = range(length)
	elif direction == DIR_R:
		start_range = range(length-1, -1, -1)
	for start_char in start_range:
		for stage in range(8):
			for col in range(8):
				column_data = []
				for matrix in range(NUM_MATRICES):
					if direction == DIR_L:
						this_char = font[ord(texts[matrix % MATRIX_HEIGHT][start_char + MATRIX_WIDTH - matrix//MATRIX_HEIGHT - 1])]
						next_char = font[ord(texts[matrix % MATRIX_HEIGHT][start_char + MATRIX_WIDTH - matrix//MATRIX_HEIGHT])]
						if col+stage < 8:
							column_data += [col+1, this_char[col+stage]]
						else:
							column_data += [col+1, next_char[col+stage-8]]
					elif direction == DIR_R:
						this_char = font[ord(texts[matrix % MATRIX_HEIGHT][start_char + MATRIX_WIDTH - matrix//MATRIX_HEIGHT])]
						next_char = font[ord(texts[matrix % MATRIX_HEIGHT][start_char + MATRIX_WIDTH - matrix//MATRIX_HEIGHT - 1])]
						if col >= stage:
							column_data += [col+1, this_char[col-stage]]
						else:
							column_data += [col+1, next_char[col-stage+8]]
				send_bytes(column_data)
			time.sleep(delay)

def scroll_message_vert(old_message, new_message, speed=3, direction=DIR_U, font=DEFAULT_FONT, finish=True):
    # Transitions vertically between two different (truncated if necessary) text messages
    # speed: 0-9 for practical purposes; speed does not have to integral
    # direction: DIR_U or DIR_D only; DIR_L & DIR_R will do nothing
    # finish: True/False : True completely displays new_message at end, False leaves the transition one pixel short
    # False should be used to ensure smooth scrolling if another vertical scroll is to follow immediately
	delay = 0.5 ** speed
	old_message = trim(old_message)
	new_message = trim(new_message)
	for iter in range(MATRIX_HEIGHT):
		for stage in range(8):
			for col in range(8):
				column_data=[]
				for matrix in range(NUM_MATRICES-1, -1, -1):
					position = (matrix//MATRIX_HEIGHT) + (MATRIX_HEIGHT - 1 - (matrix%MATRIX_WIDTH))*MATRIX_WIDTH
					scrolled_char = [0,0,0,0,0,0,0,0]
					if direction == DIR_U:
						if position + iter*MATRIX_WIDTH < NUM_MATRICES:
							this_char = font[ord(old_message[position + iter*MATRIX_WIDTH])]
						else:
							this_char = font[ord(new_message[position + iter*MATRIX_WIDTH - MATRIX_WIDTH*MATRIX_HEIGHT])]
						if position + (iter+1)*MATRIX_WIDTH < NUM_MATRICES:
							next_char = font[ord(old_message[position + (iter+1)*MATRIX_WIDTH])]
						else:
							next_char = font[ord(new_message[position + (iter+1)*MATRIX_WIDTH - MATRIX_WIDTH*MATRIX_HEIGHT])]
						scrolled_char[col] = (this_char[col] >> stage) + (next_char[col] << (8-stage))
					elif direction == DIR_D:
						if position - iter*MATRIX_WIDTH < 0:
							this_char = font[ord(new_message[MATRIX_WIDTH*MATRIX_HEIGHT + position - iter*MATRIX_WIDTH])]
						else:
							this_char = font[ord(old_message[position - iter*MATRIX_WIDTH])]
							
						if position - (iter+1)*MATRIX_WIDTH < 0:
							next_char = font[ord(new_message[MATRIX_WIDTH*MATRIX_HEIGHT + position - (iter+1)*MATRIX_WIDTH])]
						else:
							next_char = font[ord(old_message[position - (iter+1)*MATRIX_WIDTH])]
						#scrolled_char[col] = (this_char[col] >> stage) + (next_char[col] << (8-stage))
						scrolled_char[col] = (this_char[col] << stage) + (next_char[col] >> (8-stage))
					column_data += [col+1, scrolled_char[col]]
				send_bytes(column_data)
			time.sleep(delay)
	# above algorithm finishes one shift before fully displaying new_message, so optionally complete the display
	if finish:
		static_message(new_message)

def trim(text, length=NUM_MATRICES):
    # Trim or pad specified text to specified length
    text += " " * length
    text = text[:length]
    return text


def gfx_set_px(g_x, g_y, state=GFX_INVERT):
    # Set an individual pixel in the graphics buffer to on, off, or the inverse of its previous state
    if (g_x in gfx_columns) and (g_y in gfx_rows):
        if state == GFX_ON:
            gfx_buffer[g_x][g_y] = 1
        elif state == GFX_OFF:
            gfx_buffer[g_x][g_y] = 0
        elif state == GFX_INVERT:
            gfx_buffer[g_x][g_y] = (gfx_buffer[g_x][g_y] ^ 1) & 0x01	

def gfx_set_col(g_col, state=GFX_INVERT):
    # Set an entire column in the graphics buffer to on, off, or the inverse of its previous state
    if (g_col in gfx_columns):
        if state == GFX_ON:
			for g_y in range(MATRIX_HEIGHT*8):
				gfx_buffer[g_col][g_y] = 1
        elif state == GFX_OFF:
			for g_y in range(MATRIX_HEIGHT*8):
				gfx_buffer[g_col][g_y] = 0
        elif state == GFX_INVERT:
            for g_y in range(MATRIX_HEIGHT*8):
				gfx_buffer[g_col][g_y] = gfx_buffer[g_col][g_y] ^ 1

def gfx_set_all(state=GFX_INVERT):
    # Set the entire graphics buffer to on, off, or the inverse of its previous state
    for g_col in gfx_columns:
        if state == GFX_ON:
            for g_y in range(MATRIX_HEIGHT*8):
				gfx_buffer[g_col][g_y] = 1
        elif state == GFX_OFF:
            for g_y in range(MATRIX_HEIGHT*8):
				gfx_buffer[g_col][g_y] = 0
        elif state == GFX_INVERT:
            for g_y in range(MATRIX_HEIGHT*8):
				gfx_buffer[g_col][g_y] = gfx_buffer[g_col][g_y] ^ 1
				
def gfx_line(start_x, start_y, end_x, end_y, state=GFX_INVERT, incl_endpoint=GFX_ON):
    # Draw a straight line in the graphics buffer between the specified start- & end-points
    # The line can be drawn by setting each affected pixel to either on, off, or the inverse of its previous state
    # The final point of the line (end_x, end_y) can either be included (default) or omitted
    # It can be usefully omitted if drawing another line starting from this previous endpoint using GFX_INVERT
    start_x, end_x = int(start_x), int(end_x)
    start_y, end_y = int(start_y), int(end_y)
    len_x = end_x - start_x
    len_y = end_y - start_y
    if abs(len_x) + abs(len_y) == 0:
        if incl_endpoint == GFX_ON:
            gfx_set_px(start_x, start_y, state)
    elif abs(len_x) > abs(len_y):
        step_x = abs(len_x) / len_x
        for g_x in range(start_x, end_x + incl_endpoint*step_x, step_x):
            g_y = int(start_y + float(len_y) * (float(g_x - start_x)) / float(len_x) + 0.5)
            if (g_x in gfx_columns) and (g_y in gfx_rows):
            #if (0 <= g_x < 8*NUM_MATRICES) and (0<= g_y <8):
                gfx_set_px(g_x, g_y, state)
    else:
        step_y = abs(len_y) / len_y
        for g_y in range(start_y, end_y + incl_endpoint*step_y, step_y):
            g_x = int(start_x + float(len_x) * (float(g_y - start_y)) / float(len_y) + 0.5)
            if (g_x in gfx_columns) and (g_y in gfx_rows):
            #if (0 <= g_x < 8*NUM_MATRICES) and (0<= g_y <8):
                gfx_set_px(g_x, g_y, state)

def gfx_letter(char_code, start_x=0, start_y=0, state=GFX_INVERT, font=DEFAULT_FONT):
    # Overlay one character from the specified font into the graphics buffer, at a specified x-y position
    # The character is drawn by setting each affected pixel to either on, off, or the inverse of its previous state
	start_x = int(start_x)
	start_y = int(start_y)
	for l_row in range(0, 8):
		for l_col in range(0, 8):
			if (l_col + start_x) in gfx_columns and (l_row + start_y) in gfx_rows:
				if state == GFX_ON:
					gfx_buffer[l_col + start_x][l_row + start_y] = ((font[char_code][l_col] & pow(2, 7-l_row))>>(7-l_row))
				elif state == GFX_OFF:
					gfx_buffer[l_col + start_x][l_row + start_y] = ~((font[char_code][l_col] & pow(2, 7-l_row))>>(7-l_row))
				elif state == GFX_INVERT:
					gfx_buffer[l_col + start_x][l_row + start_y] = ((font[char_code][l_col] & pow(2, 7-l_row))>>(7-l_row)) ^ gfx_buffer[l_col + start_x][l_row + start_y]

def gfx_sprite_array(sprite, start_x=0, start_y=0, state=GFX_INVERT):
    # Overlay a specified 2d array[x][y] into the graphics buffer, at a specified position
    # The sprite is drawn by setting each affected pixel to either on, off, or the inverse of its previous state
    # Sprite is an m-pixel (wide) x n-pixel hide array, eg [[0,0,1,0],[1,1,1,1],[0,0,1,0]] for a cross
	start_x = int(start_x)
	start_y = int(start_y)
	for l_col in range(len(sprite)):
		for l_row in range(len(sprite[l_col])):
			if (l_col + start_x) < len(gfx_buffer) and (l_row + start_y) < len(gfx_buffer[l_col + start_x]):
				if state == GFX_ON:
					gfx_buffer[l_col + start_x][l_row + start_y] = sprite[l_col][l_row]
				elif state == GFX_OFF:
					gfx_buffer[l_col + start_x][l_row + start_y] = ~sprite[l_col][l_row]
				elif state == GFX_INVERT:
					gfx_buffer[l_col + start_x][l_row + start_y] = sprite[l_col][l_row] ^ gfx_buffer[l_col + start_x][l_row + start_y]

def gfx_scroll_towards(new_graphic=GFX_OFF, repeats=0, speed=3, direction=DIR_L, finish=True):
	# Scrolls another graphic (2d array, same width and height like gfx_buffer: (8*MATRIX_WIDTH) x (8*MATRIX_HEIGHT) )
	# to the chosen direction.
	# repeats=0 gives indefinite scrolling until script is interrupted
    # speed: 0-9 for practical purposes; speed does not have to integral
    # direction: DIR_L, DIR_R, DIR_U, DIR_D    
	delay = 0.5 ** speed
	if repeats <= 0:
		indef = True
	else:
		indef = False
		repeats = int(repeats)
	#errorhandling
	if new_graphic == GFX_OFF:
		new_graphic = [([0] * 8*MATRIX_HEIGHT)] * MATRIX_WIDTH*8
	elif new_graphic == GFX_ON:
		new_graphic = [([1] * 8*MATRIX_HEIGHT)] * MATRIX_WIDTH*8
	else:
		if ( not ( isinstance(new_graphic, list) ) ):
			new_graphic = []			
		for (i, item) in enumerate(new_graphic):
			if (not isinstance(item, list)):
				item = []
			new_graphic[i] = (item + ([0]*8*MATRIX_HEIGHT))[:8*MATRIX_HEIGHT]
		new_graphic = (new_graphic + ([ [0] * 8*MATRIX_HEIGHT ] * MATRIX_WIDTH*8) )[:MATRIX_WIDTH*8]
	old_graphic = gfx_read_buffer()
	#loop
	while indef or repeats > 0:
		repeats -= 1
		if direction & DIR_L:
			for l_col in range(8*MATRIX_WIDTH):
				graphic = [new_graphic[l_col]]	#only column
				gfx_scroll(DIR_L, graphic, 0, 8*MATRIX_WIDTH, 0, 8*MATRIX_HEIGHT, 1)
				gfx_render()
				time.sleep(delay)
		elif direction & DIR_R:
			for l_col in reversed(range(8*MATRIX_WIDTH)):
				graphic = [ [0] * MATRIX_HEIGHT*8 ]*(len(new_graphic)-1) + [new_graphic[l_col]]
				gfx_scroll(DIR_R, graphic, 0, 8*MATRIX_WIDTH, 0, 8*MATRIX_HEIGHT, 1)
				gfx_render()
				time.sleep(delay)
		elif direction & DIR_U:
			for l_row in reversed(range(8*MATRIX_HEIGHT)):
				graphic = []
				for col in range(len(new_graphic)):
					graphic	+= [[0]*(MATRIX_HEIGHT*8 -1) + [new_graphic[col][l_row]]]
				gfx_scroll(DIR_U, graphic, 0, 8*MATRIX_WIDTH, 0, 8*MATRIX_HEIGHT, 1)
				gfx_render()
				time.sleep(delay)
		elif direction & DIR_D:
			for l_row in range(8*MATRIX_HEIGHT):
				graphic = []
				for col in range(len(new_graphic)):
					graphic	+=  [[new_graphic[col][l_row]] + [0]*(MATRIX_HEIGHT*8 -1)]
				gfx_scroll(DIR_D, graphic, 0, 8*MATRIX_WIDTH, 0, 8*MATRIX_HEIGHT, 1)
				gfx_render()
				time.sleep(delay)
		"""elif direction & DIR_LU:
		
		elif direction & DIR_RU:
		
		elif direction & DIR_LD:
		
		elif direction & DIR_RD:"""
		new_graphic, old_graphic = old_graphic, new_graphic

def gfx_scroll(direction=DIR_L, new_graphic=GFX_OFF, start_x=0, extent_x=MATRIX_WIDTH*8, start_y=0, extent_y=MATRIX_HEIGHT*8, distance=1):
    # Scroll the specified area of the graphics buffer by (distance) pixel in the given direction
    # direction: any of DIR_U, DIR_D, DIR_L, DIR_R
    # Pixels outside the rectangle are unaffected; pixels scrolled outside the rectangle are discarded
    # The 'new' pixels in the gap created are either set to on or off or in the new graphic
	distance = abs(int(distance))
	if (direction == DIR_L or direction == DIR_R) and distance > extent_x:
		distance = extent_x
	if (direction == DIR_U or direction == DIR_D) and distance > extent_y:
		distance = extent_y
	start_x  = max(0, min(8*MATRIX_WIDTH - 1 , int(start_x)))
	extent_x = max(0, min(8*MATRIX_WIDTH - start_x, int(extent_x)))
	start_y  = max(0, min(8*MATRIX_HEIGHT - 1, int(start_y)))
	extent_y = max(0, min(8*MATRIX_HEIGHT - start_y, int(extent_y)))
	if new_graphic == GFX_OFF:
		new_graphic = [([0] * extent_y)] * extent_x
	elif new_graphic == GFX_ON:
		new_graphic = [([1] * extent_y)] * extent_x
	else:
		if ( not ( isinstance(new_graphic, list) ) ):
			new_graphic = []			
		for (i, item) in enumerate(new_graphic):
			if (not isinstance(item, list)):
				item = []
			new_graphic[i] = (item + ([0]*extent_y))[:extent_y]
		new_graphic = (new_graphic + ([ [0] * extent_y ] * extent_x) )[:extent_x]
	if direction & DIR_L:
		for g_x in range(start_x, start_x + extent_x):
			for g_y in range(start_y, start_y + extent_y):
				if g_x + distance < start_x + extent_x :
					gfx_buffer[g_x][g_y] = gfx_buffer[g_x+distance][g_y]
				else:
					gfx_buffer[g_x][g_y] = new_graphic[g_x - start_x - extent_x + distance][g_y - start_y]
	elif direction & DIR_R:
		for g_x in reversed(range(start_x, start_x + extent_x)):
			for g_y in range(start_y, start_y + extent_y):
				if g_x - distance < start_x:
					gfx_buffer[g_x][g_y] = new_graphic[g_x - start_x + extent_x - distance][g_y - start_y]
				else:
					gfx_buffer[g_x][g_y] = gfx_buffer[g_x-distance][g_y]
	if direction & DIR_U:
		for g_x in range(start_x, start_x + extent_x):
			for g_y in reversed(range(start_y, start_y + extent_y)):
				if g_y - distance < start_y :
					gfx_buffer[g_x][g_y] = new_graphic[g_x - start_x][g_y - start_y + extent_y - distance]
				else:
					gfx_buffer[g_x][g_y] = gfx_buffer[g_x][g_y-distance]
	elif direction & DIR_D:
		for g_x in range(start_x, start_x + extent_x):
			for g_y in range(start_y, start_y + extent_y):
				if g_y + distance < start_y + extent_y:
					gfx_buffer[g_x][g_y] = gfx_buffer[g_x][g_y+distance]
				else:
					gfx_buffer[g_x][g_y] = new_graphic[g_x - start_x][g_y - start_y - extent_y + distance]

def gfx_effect_wipe(new_graphic, speed=3, transition=DIR_R):
	# Transition from displayed graphic to another graphic by a 'wipe'
	# speed: 0-9 for practical purposes; speed does not have to integral
	# transition: DIR_U, DIR_D, DIR_L, DIR_R, DIR_RU, DIR_RD, DIR_LU, DIR_LD
	delay = 0.5 ** speed
	#errorhandling
	if new_graphic == GFX_OFF:
		new_graphic = [([0] * 8*MATRIX_HEIGHT)] * MATRIX_WIDTH*8
	elif new_graphic == GFX_ON:
		new_graphic = [([1] * 8*MATRIX_HEIGHT)] * MATRIX_WIDTH*8
	else:
		if ( not ( isinstance(new_graphic, list) ) ):
			new_graphic = []			
		for (i, item) in enumerate(new_graphic):
			if (not isinstance(item, list)):
				item = []
			new_graphic[i] = (item + ([0]*8*MATRIX_HEIGHT))[:8*MATRIX_HEIGHT]
		new_graphic = (new_graphic + ([ [0] * 8*MATRIX_HEIGHT ] * MATRIX_WIDTH*8) )[:MATRIX_WIDTH*8]
		
	maximum = max(MATRIX_HEIGHT*8, MATRIX_WIDTH*8)
	if transition == DIR_L:
		for g_col in reversed(range(MATRIX_WIDTH*8)):
			for g_row in range(MATRIX_HEIGHT*8):
				gfx_buffer[g_col][g_row] = new_graphic[g_col][g_row]
			gfx_render()
			time.sleep(delay)
	elif transition == DIR_R:
		for g_col in range(MATRIX_WIDTH*8):
			for g_row in range(MATRIX_HEIGHT*8):
				gfx_buffer[g_col][g_row] = new_graphic[g_col][g_row]
			gfx_render()
			time.sleep(delay)
	elif transition == DIR_D:
		for g_row in reversed(range(MATRIX_HEIGHT*8)):
			for g_col in range(MATRIX_WIDTH*8):
				gfx_buffer[g_col][g_row] = new_graphic[g_col][g_row]
			gfx_render()
			time.sleep(delay)
	elif transition == DIR_U:
		for g_row in range(MATRIX_HEIGHT*8):
			for g_col in range(MATRIX_WIDTH*8):
				gfx_buffer[g_col][g_row] = new_graphic[g_col][g_row]
			gfx_render()
			time.sleep(delay)
	elif transition == DIR_RU:
		for iter in range( MATRIX_HEIGHT*8 + MATRIX_WIDTH*8 - 1):
			for stage in range(min(iter + 1,maximum)):
				if iter - stage < MATRIX_WIDTH*8 and stage < MATRIX_HEIGHT*8:
					gfx_buffer[iter - stage][stage] = new_graphic[iter - stage][stage]
			gfx_render()
			time.sleep(delay)
	elif transition == DIR_LD:
		for iter in reversed(range( MATRIX_HEIGHT*8 + MATRIX_WIDTH*8 - 1)):
			for stage in range(min(iter + 1,maximum)):
				if iter - stage < MATRIX_WIDTH*8 and stage < MATRIX_HEIGHT*8:
					gfx_buffer[iter - stage][stage] = new_graphic[iter - stage][stage]
			gfx_render()
			time.sleep(delay)
	elif transition == DIR_RD:
		for iter in range( MATRIX_HEIGHT*8 + MATRIX_WIDTH*8 - 1):
			for stage in range(min(iter + 1,maximum)):
				if MATRIX_HEIGHT*8-1 - iter + stage >= 0 and stage < MATRIX_WIDTH*8:
					gfx_buffer[stage][MATRIX_HEIGHT*8-1 - iter + stage] = new_graphic[stage][MATRIX_HEIGHT*8-1 - iter + stage]
			gfx_render()
			time.sleep(delay)
	elif transition == DIR_LU:
		for iter in reversed(range( MATRIX_HEIGHT*8 + MATRIX_WIDTH*8 - 1)):
			for stage in range(min(iter + 1,maximum)):
				if MATRIX_HEIGHT*8-1 - iter + stage >= 0 and stage < MATRIX_WIDTH*8:
					gfx_buffer[stage][MATRIX_HEIGHT*8-1 - iter + stage] = new_graphic[stage][MATRIX_HEIGHT*8-1 - iter + stage]
			gfx_render()
			time.sleep(delay)
	
def gfx_effect_rain(new_graphic, speed=3):
	# Sends pixels from top to its position (with random speed for every column)
	# new_graphic has to be a 2d array with same width and height like gfx_buffer: 8*MATRIX_WIDTH x 8*MATRIX_HEIGHT
	# speed: 0-9 for practical purposes; speed does not have to integral
	delay = 0.5**speed
	if ( not ( isinstance(new_graphic, list) ) ):
		return
	for (i, item) in enumerate(new_graphic):
		if (not isinstance(item, list)):
			item = []
		new_graphic[i] = (item + ([0]*8*MATRIX_HEIGHT))[:8*MATRIX_HEIGHT]
	new_graphic = (new_graphic + ([ [0] * 8*MATRIX_HEIGHT ] * MATRIX_WIDTH*8) )[:MATRIX_WIDTH*8]
	tmp_buffer = [[None for x1 in xrange(MATRIX_HEIGHT*8)] for x2 in xrange(MATRIX_WIDTH*8)] 
	speeds = [randrange(2,6) for c in range(MATRIX_WIDTH*8)]
	for l_col in range(MATRIX_WIDTH*8):
		tmp_buffer[l_col][MATRIX_HEIGHT*8-1] = new_graphic[l_col][0]
	gfx_set_all(GFX_OFF)
	for g_col in range(MATRIX_WIDTH*8):
		for g_row in range(MATRIX_HEIGHT*8):
			gfx_buffer[g_col][g_row] = 1 if tmp_buffer[g_col][g_row] == 1 else 0
	gfx_render()
	time.sleep(delay)
	for iter in range(1,MATRIX_HEIGHT*8):
		for l_col in range(MATRIX_WIDTH*8):
			emptyCells = [idx for idx,i in enumerate(tmp_buffer[l_col]) if i==None]
			if emptyCells != []:
				firstEmptyCell = emptyCells[0]
				for l_row in range(firstEmptyCell, MATRIX_HEIGHT*8):
					nextNotNone = [idx for idx,i in enumerate(tmp_buffer[l_col]) if (i!=None and idx > l_row)]
					if nextNotNone != []:
						nxt = min(nextNotNone[0], l_row + speeds[l_col])
						if nxt < MATRIX_HEIGHT*8:
							tmp_buffer[l_col][l_row] = tmp_buffer[l_col][nxt]
							tmp_buffer[l_col][nxt] = None
					elif l_row == MATRIX_HEIGHT*8-1:
						tmp_buffer[l_col][MATRIX_HEIGHT*8-1] = new_graphic[l_col][iter]
		gfx_set_all(GFX_OFF)
		for g_col in range(MATRIX_WIDTH*8):
			for g_row in range(MATRIX_HEIGHT*8):
				gfx_buffer[g_col][g_row] = 1 if tmp_buffer[g_col][g_row] == 1 else 0
		gfx_render()
		time.sleep(delay)
				
def gfx_read_buffer(g_x=None, g_y=None):
    # Return the current state (on=1, off=0) of an individual pixel in the graphics buffer
	# if no pixel is declared, it returns the whole gfx_buffer array
    # Note that this buffer only reflects the operations of these gfx_ functions, since the buffer was last cleared
    # The buffer does not reflect the effects of other library functions such as send_matrix_letter() or (static_message()
	if g_x == None and g_y == None:
		import copy
		return copy.deepcopy(gfx_buffer)
	elif (g_x in gfx_columns) and (g_y in gfx_rows):
		return (gfx_buffer[g_x][g_y])
		
def gfx_render():
    # All of the above gfx_ functions (except of the gfx_effect_ functions) only write to (or read from) a graphics buffer maintained in memory
    # This command sends the entire buffer to the matrix array - use it to display the effect of one or more previous gfx_ functions
	for g_col in range(8):
		column_data = []
		for matrix in reversed(range(NUM_MATRICES)):
			val = 0x00
			for px in range(8):
				val += gfx_buffer[g_col + (matrix//MATRIX_HEIGHT)*8 ][px+(matrix%MATRIX_HEIGHT)*8] * pow(2,7-px)
			column_data += [g_col+1, val]
		send_bytes(column_data)

def init():
    # Initialise all of the MAX7219 chips (see datasheet for details of registers)
    send_all_reg_byte(MAX7219_REG_SCANLIMIT, 7)   # show all 8 digits
    send_all_reg_byte(MAX7219_REG_DECODEMODE, 0)  # using a LED matrix (not digits)
    send_all_reg_byte(MAX7219_REG_DISPLAYTEST, 0) # no display test
    clear_all()                                   # ensure the whole array is blank
    brightness(3)                                 # set character intensity: range: 0..15
    send_all_reg_byte(MAX7219_REG_SHUTDOWN, 1)    # not in shutdown mode (i.e start it up)
    gfx_set_all(GFX_OFF)                          # clear the graphics buffer

# -----------------------------------------------------
# Library function definitions end here
# The following script executes if run from command line
# ------------------------------------------------------

if __name__ == "__main__":
    import sys
    # Parse arguments and attempt to correct obvious errors
    try:
        # message text
        message = sys.argv[1]
        # number of marequu repeats
        try:
            repeats = abs(int(sys.argv[2]))
        except (IndexError, ValueError):
            repeats = 0
        # speed of marquee scrolling
        try:
            speed = float(sys.argv[3])
        except (IndexError, ValueError):
            speed = 3
        if speed < 1:
            speed = 3
        elif speed > 9:
            speed = 9
        # direction of marquee scrolling
        try:
            direction = sys.argv[4].lower()
            if direction in ["dir_r", "dirr", "r", "right", ">", 2]:
                direction = 2 # Right
            else:
                direction = 8 # Left
        except (IndexError, ValueError):
            direction = 8 # Left
        # font
        try:
            font = sys.argv[5].lower()
            if font in ["cp437", "cp437_font", "cp437font", "cp_437", "cp_437font", "cp_437_font"]:
               font = CP437_FONT
            elif font in ["sinclairs_font", "sinclairs", "sinclair_s", "sinclair_s_font", "sinclairsfont"]:
               font = SINCLAIRS_FONT
            elif font in ["lcd_font", "lcd", "lcdfont"]:
               font = LCD_FONT
            elif font in ["tiny_font", "tiny", "tinyfont"]:
               font = TINY_FONT
            # Note: if further fonts are added to multilineMAX7219_fonts.py, add suitable references to parse command line arguments here
            else:
               font = CP437_FONT
        except (IndexError, ValueError):
            font = CP437_FONT
        # Call the marquee function with the parsed arguments
        try:
            scroll_message_horiz([message], repeats, speed, direction, font)
        except KeyboardInterrupt:
            clear_all()
    except IndexError:
        # If no arguments given, show help text
        print "multilineMAX7219.py"
        print "Scrolls a message across an m x n array of MAX7219 8x8 LED boards"
        print "Run syntax:"
        print "  python multilineMAX7219.py message [repeats [speed [direction [font]]]]"
        print "    or, if the file has been made executable with chmod +x multilineMAX7219.py :"
        print "      ./multilineMAX7219.py message [repeats [speed [direction [font]]]]"
        print "Parameters:"
        print "  (none)               : displays this help information"
        print "  message              : any text to be displayed on the array"
        print "                         if message is more than one word, it must be enclosed in 'quotation marks'"
        print "                         Note: include blank space(s) at the end of 'message' if it is to be displayed multiple times"
        print "  repeats (optional)   : number of times the message is scrolled"
        print "                         repeats = 0 scrolls indefinitely until <Ctrl<C> is pressed"
        print "                         if omitted, 'repeats' defaults to 0 (indefinitely)"
        print "  speed (optional)     : how fast the text is scrolled across the array"
        print "                         1 (v.slow) to 9 (v.fast) inclusive (not necessarily integral)"
        print "                         if omitted, 'speed' defaults to 3"
        print "  direction (optional) : direction the text is scrolled"
        print "                         L or R - if omitted, 'direction' defaults to L"
        print "  font (optional)      : font to use for the displayed text"
        print "                         CP437, SINCLAIRS, LCD or TINY only - default 'font' if not recognized is CP437"
        print "multilineMAX7219.py can also be imported as a module to provide a wider range of functions for driving the array"
        print "  See documentation within the script for details of these functions, and how to setup the library and the array"
                                                               

