from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import re
import lyricsgenius
import requests
import random
import secret
client_access_token = secret.client_access_token
LyricsGenius = lyricsgenius.Genius(client_access_token)
app = Flask(__name__)
# Function to sort Keys in a Dictionary
def sortKeysByValue(d):
    ks = d.keys()
    return sorted(ks, key= lambda k: d[k])
#
#
#
# function to clean up the list of songs (adapted from Melanie Walsh in her Book,
# Introduction to Cultural Analytics and Python)
def clean_up(song_title):
    if "Ft" in song_title:
        before_ft_pattern = re.compile(".*(?=\(Ft)")
        song_title_before_ft = before_ft_pattern.search(song_title).group(0)
        clean_song_title = song_title_before_ft.strip()
        clean_song_title = clean_song_title.replace("/", "-")

    else:
        song_title_no_lyrics = song_title.replace("Lyrics", "")
        clean_song_title = song_title_no_lyrics.strip()
        clean_song_title = clean_song_title.replace("/", "-")

    return clean_song_title
#
#
#
# returns list of song objects from a given album. No API called, instead
# Uses a web scraper since geniusAPI does not have an album call feature
def get_all_songs_from_album(artist, album_name):
    artist = artist.replace(" ", "-")
    album_name = album_name.replace(" ", "-")

    response = requests.get(f"https://genius.com/albums/{artist}/{album_name}")
    html_string = response.text
    document = BeautifulSoup(html_string, "html.parser")
    song_title_tags = document.find_all("h3", attrs={"class": "chart_row-content-title"})
    song_titles = [song_title.text for song_title in song_title_tags]

    clean_songs = []
    for song_title in song_titles:
        clean_song = clean_up(song_title)
        clean_songs.append(clean_song)

    LyricsGenius.remove_section_headers = True
    song_objects = []

    for song in clean_songs:
        song_objects.append(LyricsGenius.search_song(song, artist))

    return song_objects

# returns lyricsgenius artist class. Sets number of songs to zero
# for much quicker load times
def get_artist(artist):
    return LyricsGenius.search_artist(artist_name=artist, max_songs=0)
#
#
#
# List of stopwords to remove for the word cloud
stopwords = ["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
             "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her",
             "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs",
             "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is",
             "are", "was", "were", "be", "been", "being", "have", "has", "had", "having",
             "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because",
             "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between",
             "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down",
             "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here",
             "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more",
            "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than",
             "too", "very", "s", "t", "can", "will", "just", "don", "should", "now", "urlcopyembedcopy",
             "35embedshare", "i'm", "i've", "can't", "couldn't", "didn't", "don't", "doesn't", "hadn't",
             "hasn't", "he's", "she's", "i'll", "i'd", "isn't", "it's", "let's", "she'll", "he'll", "that's"]
#
#
#
# Function to get the top n words in an album
def get_top_words_in_album(songlist, top_n = 20):
    dict = {}
    for song in songlist:
        if song != None:
            for word in song.lyrics.split():
                word = word.lower()
                word = word.strip(".-_?/!,() ")
                dict[word] = dict.get(word, 0) + 1
    filtered_words = [word for word in dict.keys() if word not in stopwords]

    sorted_dict = {}
    for word in filtered_words:
        sorted_dict[word] = dict[word]
    sorted_dict = sorted(sorted_dict.items(), key=lambda x: x[1], reverse=True)
    return sorted_dict[:top_n]


@app.route("/")
def get_lyrics():

    customized = False
    artist = request.args.get('artistlabel')
    album = request.args.get('album')
    if artist is None and album is None:
        artist = "Talking Heads"
        album = "Speaking In Tongues"

    artistclass = get_artist(artist)
    lyricslist = get_all_songs_from_album(artist=artist, album_name=album)
    topwords = get_top_words_in_album(songlist=lyricslist)
    if topwords is None:
        topwords = []
        artist = "could not find artist or album"
        album = ""
    random.shuffle(topwords)
    return render_template("index.html", topwords=topwords, artist=artist,
                           album=album, artistclass=artistclass)
if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)