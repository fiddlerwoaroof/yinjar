#!/usr/bin/python
#USAGE:
#python TCODfont.py /path/to/font/font.ttf 12

import Image, ImageFont, ImageDraw, sys

fontpath = sys.argv[1]
fontpoint = int(sys.argv[2])

image = Image.new('RGB', [fontpoint*16, fontpoint*16])
draw = ImageDraw.Draw(image)
font = ImageFont.truetype(fontpath, fontpoint)

i = 0
for row in range(0, 16):
    for col in range(0, 16):

        xpos = fontpoint*col+1
        ypos = fontpoint*row

        draw.text((xpos, ypos), chr(i), font=font)
        i += 1

image.save('tcod.png')
