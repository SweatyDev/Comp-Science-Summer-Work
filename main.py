import utils
import curses
from time import sleep
import threading

current_username = current_user = None


def artist_out_screen(stdscr: curses.window):
    name = utils.std_input(stdscr, "Artist: ", 1, 20, 16)
    utils.output_artist_info(name)
    menu(stdscr)


def song_list(stdscr: curses.window):
    names = sorted(utils.get_song_names())
    song = utils.std_choice(stdscr, names)

    song_info = utils.get_song(song)
    utils.load_music_file(song, song_info["artist"])
    mixer = utils.mixer

    isPaused = False
    isLooping = False

    while True:
        choices = [
            "PLAY",
            f"{'UNPAUSE' if isPaused else 'PAUSE'}",
            f"{'UNLOOP' if isLooping else 'LOOP'}",
            "EXIT",
        ]
        choice = utils.std_choice(stdscr, choices)

        if choice == "PLAY":
            mixer.music.play(loops=-1 if isLooping else 0)
            isPaused = False
        elif choice == "PAUSE":
            mixer.music.pause()
            isPaused = True
        elif choice == "UNPAUSE":
            mixer.music.unpause()
            isPaused = False
        elif choice == "LOOP":
            isLooping = True
            if not isPaused:
                mixer.music.play(loops=-1)
        elif choice == "UNLOOP":
            isLooping = False
            if not isPaused:
                mixer.music.play(loops=0)
        elif choice == "EXIT":
            mixer.music.stop()
            menu(stdscr)
            return


def edit_info(stdscr: curses.window):
    while True:
        utils.std_clear(stdscr)
        choices = ["EDIT FAVOURITE ARTIST", "EDIT FAVOURITE GENRE", "EXIT"]
        choice = utils.std_choice(stdscr, choices)

        if choice == "EDIT FAVOURITE ARTIST":
            favourite_artist = utils.std_input(stdscr, "Favourite Artist: ", 1, 20, 16)
            current_user["fav_artist"] = favourite_artist

        elif choice == "EDIT FAVOURITE GENRE":
            favourite_genre = utils.std_input(stdscr, "Favourite Genre: ", 1, 20, 16)
            current_user["fav_genre"] = favourite_genre

        elif choice == "EXIT":
            menu(stdscr)
            return

        utils.users_info[current_username] = current_user


def play_playlist(stdscr, playlist):
    mixer = utils.mixer
    looped = False
    nextSong = threading.Event()
    isPaused = False
    stopThread = threading.Event()

    def play_music_loop(playlist):
        for songname in playlist:
            if stopThread.is_set():
                break

            song_info = utils.get_song(songname)
            if not song_info:
                continue

            utils.load_music_file(song_info["name"], song_info["artist"])
            mixer.music.play()

            time_left = song_info["length"]
            while time_left > 0:
                if stopThread.is_set():
                    mixer.music.stop()
                    return

                if nextSong.is_set():
                    nextSong.clear()
                    break

                if not isPaused:
                    sleep(1)
                    time_left -= 1

        if looped and not stopThread.is_set():
            play_music_loop(playlist)

    music_loop_thread = threading.Thread(
        target=play_music_loop, args=(playlist,), daemon=True
    )
    music_loop_thread.start()

    while True:
        choices = [
            f"{'UNPAUSE' if isPaused else 'PAUSE'}",
            "NEXT",
            f"{'LOOP' if not looped else 'UNLOOP'}",
            "EXIT",
        ]
        choice = utils.std_choice(stdscr, choices)

        if choice == "PAUSE":
            mixer.music.pause()
            isPaused = True
        elif choice == "UNPAUSE":
            mixer.music.unpause()
            isPaused = False
        elif choice == "NEXT":
            nextSong.set()
        elif choice in ["LOOP", "UNLOOP"]:
            looped = not looped
        else:
            stopThread.set()
            mixer.music.stop()
            menu(stdscr)
            return


def make_playlist(stdscr: curses.window):
    utils.std_clear(stdscr)

    genre = utils.std_input(stdscr, "Genre: ", 1, 15, 16) or None
    artist = utils.std_input(stdscr, "Artist: ", 1, 20, 16) or None
    length = utils.std_input(stdscr, "Playlist Length (Seconds)_: ", 1, 5, 16) or 99999

    new_playlist = utils.generate_playlist(genre, artist, length)

    utils.std_clear(stdscr)

    for i, song in enumerate(new_playlist):
        utils.print_centred_text(stdscr, 10 + i, song)

    utils.print_centred_text(stdscr, 5, "Does this look good?")
    choice = utils.std_choice(stdscr, ["YES", "NO"])

    if choice == "YES":
        noPlaylists = len(current_user["playlists"])
        playlist_name = f"playlist{noPlaylists}"
        current_user["playlists"][playlist_name] = new_playlist
        utils.users_info[current_username] = current_user

    playlist_menu(stdscr)
    return


def playlist_menu(stdscr: curses.window):
    """user_playlists = current_user["playlists"]
    user_playlists.append("CREATE NEW PLAYLIST")
    user_playlists.append("EXIT")

    choice = utils.std_choice(stdscr, user_playlists)

    if choice == "EXIT":
        menu(stdscr)
        return
    elif choice == "CREATE NEW PLAYLIST":
        length = utils.std_input(stdscr, "Playlist Length (Seconds): ", 1, 10, 16)
        artist = utils.std_input(stdscr, "Playlist Artist: ", 1, 20, 16)
        genre = utils.std_input(stdscr, "Playlist Genre: ", 1, 20, 16)

        new_playlist = utils.generate_playlist(genre, artist, length)
        current_user["playlists"].append(new_playlist)

        playlist_menu(stdscr)
        return
    # It's a playlist.
    else:
        # TODO
        playlist_menu(stdscr)
        return"""

    user_playlists = list(current_user["playlists"].items())
    options = [play[0] for play in user_playlists]
    options.append("CREATE NEW PLAYLIST")
    options.append("BACK")

    choice = utils.std_choice(stdscr, options)

    # User wants to return to menu.
    if choice == "BACK":
        menu(stdscr)
        return
    elif choice == "CREATE NEW PLAYLIST":
        make_playlist(stdscr)
        return
    # A playlist was selected.
    else:
        playlist = user_playlists[options.index(choice)][1]
        play_playlist(stdscr, playlist)
        return


def menu(stdscr: curses.window):
    while True:
        # Clear screen and display logo.
        utils.std_clear(stdscr)
        utils.print_logo(stdscr)

        utils.print_centred_text(stdscr, 10, f"Welcome, {current_username}!")

        options = ["SONGS", "EDIT INFO", "PLAYLISTS", "OUTPUT ARTIST SONGS"]
        choice = utils.std_choice(stdscr, options)

        if choice == "SONGS":
            song_list(stdscr)
            return
        elif choice == "EDIT INFO":
            edit_info(stdscr)
            return
        elif choice == "PLAYLISTS":
            playlist_menu(stdscr)
            return
        elif choice == "OUTPUT ARTIST SONGS":
            artist_out_screen(stdscr)
            return  # It just works.


def signup(stdscr: curses.window):
    utils.print_logo(stdscr)

    # Prompt user to input a new, unique username.
    valid = False

    while not valid:
        name = utils.std_input(stdscr, "New Username: ", 1, 15, 16)

        valid, reason = utils.valid_username(name)

        if name == "back":
            utils.print_centred_text(stdscr, 14, "Nice try ;)")

        # A check, just in case.
        if not valid:
            utils.print_centred_text(stdscr, 14, reason)

    # Prompt user to input a new password.
    valid = False

    while not valid:
        password = utils.std_input(stdscr, "New Password: ", 1, 15, 16)

        valid, reason = utils.valid_password(password)

        # A check, just in case.
        if not valid:
            utils.print_centred_text(stdscr, 14, reason)

    dob = utils.std_input(stdscr, "Date of Birth (DD/MM/YYYY):_", 1, 11, 16)
    favourite_artist = utils.std_input(stdscr, "Favourite Artist: ", 1, 20, 16)
    favourite_genre = utils.std_input(stdscr, "Favourite Genre: ", 1, 20, 16)

    # Add user to users_info. Prompt and redirect after 3 seconds.
    utils.users_info[name] = utils.blank_user_info
    utils.users_info[name]["password"] = password
    utils.users_info[name]["dob"] = dob
    utils.users_info[name]["fav_artist"] = favourite_artist
    utils.users_info[name]["fav_genre"] = favourite_genre
    utils.print_centred_text(
        stdscr, 14, "Account registered! Redirecting in 3 seconds."
    )

    sleep(3)

    utils.std_clear(stdscr)
    on_start(stdscr)
    return  # For some reason, curses breaks when you don't put this here. Fixed the errors, so I'll keep on using it :)


def login(stdscr: curses.window):
    while True:
        utils.print_logo(stdscr)

        # Get username.
        name = utils.std_input(
            stdscr, "Username ('back' to return to menu): ", 1, 20, 16
        )

        # User wants to go back to the menu.
        if name == "back":
            on_start(stdscr)
            return

        # If the username is not found, loop back.
        if not name in utils.users_info.keys():
            utils.std_clear(stdscr)
            utils.print_centred_text(stdscr, 14, "Username not found!")
            continue

        correct_password = utils.users_info[name]["password"]
        password = utils.std_input(stdscr, "Password: ", 1, 20, 17)

        # If the password is incorrect, loop back. Offer a hint.
        if password != correct_password:
            utils.std_clear(stdscr)
            utils.print_centred_text(
                stdscr,
                14,
                f"Incorrect password! Hint: {correct_password[0]}{'.' * (len(correct_password) - 1)}",
            )
            continue

        break

    # Correct password - user has logged in.
    global current_username, current_user
    current_username = name
    current_user = utils.users_info[name]

    # Goto main menu (TODO)
    menu(stdscr)


def on_start(stdscr: curses.window):
    # Clean the screen (to avoid issues).
    utils.std_clear(stdscr)

    # Resize the screen.
    curses.resize_term(30, 128)

    # Login or signup?
    utils.print_logo(stdscr)  # Of course, need that branding :)

    choice = utils.std_choice(stdscr, ["MAKE A NEW ACCOUNT", "LOGIN"])

    if choice == "LOGIN":
        # Goto login function.
        login(stdscr)
        pass

    elif choice == "MAKE A NEW ACCOUNT":
        # Go to signup function.
        signup(stdscr)
        pass


if __name__ == "__main__":
    try:
        curses.wrapper(on_start)
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        utils.save_user_info()
