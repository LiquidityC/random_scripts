#!/usr/bin/python

"""
This script takes a file as an argument. Everytime it is un it will
fetch post titles from the top posts from /r/showerthoughts on reddit and merge them into
the provided file. Running it often enough should provide a rather extensive database of funny
quotes. This could for example be used to update your 'fortune' db.

@author Linus Probert <linus.probert@gmail.com>
@example https://liquidityc.github.io/python/fortune/cowsay/fun/2018/07/06/fun-with-fortunes.html
"""

import feedparser
import re
import urllib.request
import os.path
import sys

def read_list_from_file(infile):
    list = []

    if not os.path.isfile(infile):
        return list

    with open(infile, "r") as file:
        for line in iter(file.readline, ""):
            line = line.strip()
            if line == "%" or line == "":
                continue
            list.append(line)

    return list

def save_list_to_file(list, outfile):
    with open(outfile, "w") as file:
        file.write("\n%\n".join(list))

if len(sys.argv) < 2:
    print("You need to provide a storage file")
    sys.exit(0)

fname = sys.argv[1]

quotes = read_list_from_file(fname)

rss = feedparser.parse("https://www.reddit.com/r/Showerthoughts/top/.rss")
for post in rss.entries:
    quotes.append(post.title)

quotes = [quote.strip() for quote in sorted(set(quotes))]

save_list_to_file(quotes, fname)
