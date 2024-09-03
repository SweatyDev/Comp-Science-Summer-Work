import json
from pygame import mixer
import string
import os
import curses
from curses.textpad import Textbox

with open("songs.json", "r") as f:
    songs = json.load(f)

with open("users.json", "r") as f:
    users_info = json.load(f)

# Load pygame's audio mixer.
mixer.init()

##### CREDENTIAL HELPER FUNCTIONS #####

blank_user_info = {
    "password": "",
    "dob": "",
    "fav_artist": "",
    "fav_genre": "",
    "playlists": {},
}


def save_user_info():
    with open("users.json", "w") as f:
        towrite = json.dumps(users_info)
        f.write(towrite)


def valid_password(password: str) -> (tuple, str):  # type: ignore
    """Returns True if string has 8+ characters, one uppercase, one lowercase, no illegal symbols and one special character."""
    # Check if password is longer than 8 characters.
    if password in [None, ""]:
        return False, "Please input a password."

    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    # Check if password has an uppercase character.
    elif not any(char.isupper() for char in password):
        return False, "Password must include an uppercase letter."

    # Check if password has a special character.
    elif not any(char in string.punctuation for char in password):
        return False, "Password must include a special character."

    # Passes all checks - password is acceptable.
    return True, None


def valid_username(username: str) -> (tuple, str):  # type: ignore
    """Returns True if username is unique and is between 3-15 characters."""
    # Check if username is present.
    if username in [None, ""]:
        return False, "Please input a username."

    # Check if username is unique.
    if username in users_info.keys():
        return False, "Username is already in use. Please choose another."

    # Check if username is between 3 and 15 characters.
    if not len(username) in range(3, 15):
        return False, "Username length must be between 3 and 15 characters."

    # Passes all checks - username is acceptable.
    return True, None


##### SONG HELPER FUNCTIONS #####


def generate_playlist(genre=None, artist=None, length=99999) -> list:
    """Generates a playlist from certain parameters."""
    total_length = 0
    playlist = []

    for song in songs:
        if (song["genre"] != genre) and genre:
            continue
        elif (song["artist"] != artist) and artist:
            continue
        elif song["length"] + total_length > length:
            continue

        total_length += song["length"]
        playlist.append(song)

    return playlist


def get_song(name: str):
    for song in songs:
        if song["name"] == name:
            return song

    return None


def get_song_names():
    names = []

    for song in songs:
        names.append(song["name"])

    return names


def load_music_file(name: str, artist: str):
    formatted_name = f"songs/{artist} - {name}.wav"

    if not os.path.exists(formatted_name):
        return

    mixer.music.load(formatted_name)

    # Personal note: it's "mixer.music.play()", NOT "mixer.play()"!


def output_artist_info(artist: str):
    """Outputs all of the songs written by an artist to an external .txt file."""
    artist_songs = [song for song in songs if song["artist"] == artist]
    content = "\n".join(song["name"] for song in artist_songs)

    with open(f"{artist}.txt", "w") as f:
        f.write(content)


##### CURSES HELPER FUNCTIONS #####


def get_centre(stdscr: curses.window):
    _, w = stdscr.getmaxyx()
    return w // 2


def print_centred_text(stdscr: curses.window, y: int, text: str):
    _, w = stdscr.getmaxyx()
    # Clear the area so that text doesn't overlap.
    stdscr.addstr(y, 0, f"{' ' * (w-1)}")
    stdscr.addstr(y, get_centre(stdscr) - (len(text) // 2), text)
    stdscr.refresh()


def std_choice(stdscr: curses.window, options: list, clear=True):
    """Displays a dropdown menu in the middle of the screen."""
    pointer = 0

    h, w = stdscr.getmaxyx()

    while True:
        # Display each option in the middle of the screen. Make it glow if it is chosen.
        for i, option in enumerate(options):
            mode = curses.A_REVERSE if pointer == i else curses.A_NORMAL
            x = w // 2 - len(option) // 2
            y = h // 2 - len(options) // 2 + i
            stdscr.addstr(y, x, option, mode)

        # Handling key presses.
        key = stdscr.getch() or None

        # Return the value if the user press ENTER.
        if key in (curses.KEY_ENTER, 10, 13):
            if clear:
                stdscr.clear()
                stdscr.refresh()
            return options[pointer]

        # Move the pointer up if they press the up key.
        elif key == curses.KEY_UP:
            pointer = (pointer - 1) % len(options)

        # Move the pointer down if they press the down key.
        elif key == curses.KEY_DOWN:
            pointer = (pointer + 1) % len(options)

        # Refresh the screen, looping back.
        stdscr.refresh()


def std_input(stdscr: curses.window, text: str, lines: int, columns: int, y: int):
    """An utility function that makes a curses input. Tried to design it like Python's build-in input() function."""
    # Get the width of the screen so we can centre the input.
    _, w = stdscr.getmaxyx()
    x = get_centre(stdscr) - (len(text) + columns) // 2

    # Make the input message appear.
    space = " " * (w - 1)

    stdscr.addstr(y, 0, space)  # Clear the area so that text doesn't overlap.
    stdscr.addstr(y, x, text)
    stdscr.refresh()
    # Make an input object for the user to type in a seperate window.
    editwin = curses.newwin(lines, columns, y, x + len(text))
    box = Textbox(editwin)
    box.edit()

    # Return the formatted input or a NoneType.
    return box.gather().strip() or None


def std_clear(stdscr: curses.window):
    """Clears the window. Made this procedure to stop repeating the same two lines for all eternity."""
    stdscr.clear()
    stdscr.refresh()


logo = """
  __  __   _    _    _____   _____    _____     _______   _    _   _____   _   _    _____ 
 |  \/  | | |  | |  / ____| |_   _|  / ____|   |__   __| | |  | | |_   _| | \ | |  / ____|
 | \  / | | |  | | | (___     | |   | |           | |    | |__| |   | |   |  \| | | |  __ 
 | |\/| | | |  | |  \___ \    | |   | |           | |    |  __  |   | |   | . ` | | | |_ |
 | |  | | | |__| |  ____) |  _| |_  | |____       | |    | |  | |  _| |_  | |\  | | |__| |
 |_|  |_|  \____/  |_____/  |_____|  \_____|      |_|    |_|  |_| |_____| |_| \_|  \_____|

            Using curses, pygame and json to bring you my summer coursework!                                                                                     
"""


def print_logo(stdscr: curses.window):
    lines = logo.split("\n")
    _, w = stdscr.getmaxyx()

    for i in range(0, len(lines)):
        line = lines[i]
        x = w // 2 - 45
        stdscr.addstr(i, x, line)
