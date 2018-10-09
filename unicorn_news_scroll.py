#!/usr/bin/env python
# -*- coding: utf-8 -*-

import colorsys
import signal
import time
import urlparse
import httplib
import xml.etree.ElementTree as ET
import json
import argparse
from datetime import datetime

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    exit("This script requires the pillow module\nInstall with: sudo pip install pillow")

try:
    from bs4 import BeautifulSoup
except ImportError:
    exit("This script requires the BeautifulSoup module\nInstall with: sudo pip install beautifulsoup4")
    
import unicornhathd

# Use `fc-list` to show a list of installed fonts on your system,
# or `ls /usr/share/fonts/` and explore.
# Examples:
# sudo apt install fonts-droid
# "font" : { "name" : "/usr/share/fonts/truetype/droid/DroidSans.ttf", "size" : 12 }
# sudo apt install fonts-roboto
# "font" : { "name" : "/usr/share/fonts/truetype/roboto/Roboto-Bold.ttf", "size" : 10 }

col_max = 32
col_index = 0
colours = [tuple([int(n * 255) for n in colorsys.hsv_to_rgb(x/float(col_max), 1.0, 1.0)]) for x in range(col_max)]

def scroll_text(text):
    print(text)
    
    width, height = unicornhathd.get_shape()
    text_x = width
    text_y = 2

    font = ImageFont.truetype(*FONT)
    text_width, text_height = width, 0

    for line in text.splitlines():
        w, h = font.getsize(line)
        text_width += w + width
        text_height = max(text_height,h)

    text_width += width + text_x + 1

    image = Image.new("RGB", (text_width,max(16, text_height)), (0,0,0))
    draw = ImageDraw.Draw(image)

    offset_left = 0

    global col_index

    for index, line in enumerate(text.splitlines()):
        draw.text((text_x + offset_left, text_y), line, colours[col_index], font=font)
        offset_left += font.getsize(line)[0] + width
        col_index += 1
        if col_index >= col_max:
            col_index = 0

    for scroll in range(text_width - width):
        for x in range(width):
            for y in range(height):
                pixel = image.getpixel((x+scroll, y))
                r, g, b = [int(n) for n in pixel]
                unicornhathd.set_pixel(width-1-x, y, r, g, b)

        unicornhathd.show()
        time.sleep(0.01)
    
def get_xml_request(address):

    xml_data = None

    url = urlparse.urlparse(address, allow_fragments=True)
    conn = httplib.HTTPSConnection(url.netloc)
    conn.request("GET", url.path)
    response = conn.getresponse()

    if response.status == 200:
        xml_data = response.read()
    else:
        print("ERROR: got response {} from {}".format(response.status, url))
        print(u"Reason: {}".format(response.reason))
        print(u"Message: {}".format(response.msg))

    conn.close()

    return xml_data

def get_data_list(xml):

    data_list = []

    # xml = xml.replace("&nbsp;", " ")

    root = ET.fromstring(xml)

    for channel in root.iter('channel'):
        for item in channel.iter('item'):
            title = item.find('title').text
            desc = BeautifulSoup(item.find('description').text, "html.parser").text
            link = item.find('link').text

            data_list.append((title, desc, link))

    return data_list


def mainloop(config):
    unicornhathd.rotation(config["unicornhathd"]["rotation"])
    unicornhathd.brightness(config["unicornhathd"]["brightness"])

    rss_feeds = []
    rss_feeds.append("https://feeds.bbci.co.uk/news/rss.xml")
    rss_feeds.append("https://feeds.bbci.co.uk/news/world/rss.xml")
    rss_feeds.append("https://feeds.bbci.co.uk/news/uk/rss.xml")
    rss_feeds.append("https://feeds.bbci.co.uk/news/business/rss.xml")
    rss_feeds.append("https://feeds.bbci.co.uk/news/politics/rss.xml")
    rss_feeds.append("https://feeds.bbci.co.uk/news/health/rss.xml")
    rss_feeds.append("https://feeds.bbci.co.uk/news/education/rss.xml")
    rss_feeds.append("https://feeds.bbci.co.uk/news/science_and_environment/rss.xml")
    rss_feeds.append("https://feeds.bbci.co.uk/news/technology/rss.xml")
    rss_feeds.append("https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml")
    # rss_feeds.append("http://www.eurogamer.net/?format=rss&platform=PS4")

    rss = []

    while True:
        for rss_feed in rss_feeds:
            xml_data = get_xml_request(rss_feed)
            if xml_data:
                rss.extend(get_data_list(xml_data))

        for text in rss:
            output_text = u"{}: {} ==> {}".format(time.strftime("%d/%m/%Y %H:%M:%S"), text[0], text[1])
            scroll_text(output_text)
            time.sleep(0.25)

if __name__ == "__main__":

    try:
        parser = argparse.ArgumentParser(description='Scan for keywords on Twitter and scroll on Unicorn Hat HD.')
        parser.add_argument('--config', help="Config file to load", nargs='?', type=str, default="default.json")
        parser.add_argument('--verbose', help="Enables verbose output on command line (including any dropped tweets)", action='store_true')
        args = parser.parse_args()
                        
        with open(args.config, 'r') as myfile:
            config = json.load(myfile)

        FONT = (config["font"]["name"], config["font"]["size"])
        mainloop(config)
        
    except KeyboardInterrupt:
        unicornhathd.off()
        print("Exiting!")

