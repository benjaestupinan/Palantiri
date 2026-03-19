from transformers import pipeline

job_classifier = pipeline(
    "zero-shot-classification",
    model="MoritzLaurer/deberta-v3-large-zeroshot-v2.0",
    device=0,
)

intent_classifier = pipeline(
    "zero-shot-classification", model="MoritzLaurer/bge-m3-zeroshot-v2.0", device=0
)

LABELS = {
    "end the conversation or say goodbye": "END_SESSION",
    "answer a question or save a conversation": "COGNITIVE_REQUEST",
    "execute a command or perform an action using a tool": "EXTEND_CONTEXT_WITH_SYSTEM_ACTION",
}


def select_intent(text):
    result = intent_classifier(text, [x for x in LABELS.keys()], multi_label=False)
    return {"intent": LABELS[result["labels"][0]], "confidence": result["scores"][0]}


def select_job(text, display_labels, label_map):
    result = job_classifier(text, display_labels, multi_label=False)
    if result["scores"][0] < 0.2:
        return {"job": "None", "confidence": 1}
    return {"job": label_map[result["labels"][0]], "confidence": result["scores"][0]}


if __name__ == "__main__":
    prompts = [
        "Pon master of puppets",
        "Can you set an alarm for 7am tomorrow?",
        "Chao, hasta luego",
        "Cual es la capital de Francia?",
        "Perfecto, eso es todo gracias",
        "Hoydia va a hacer calor?",
    ]

    MCP_CATALOG = {
        "fetch_fetch": "Fetches a URL from the internet and optionally extracts its contents as markdown.",
        "spotify_addToQueue": "Adds a track, album, artist or playlist to the playback queue",
        "spotify_addTracksToPlaylist": "Add tracks to a Spotify playlist",
        "spotify_adjustVolume": "Adjust the playback volume up or down by a relative amount",
        "spotify_checkUsersSavedAlbums": "Check if albums are saved in the user's Your Music library",
        "spotify_createPlaylist": "Create a new playlist on Spotify",
        "spotify_getAlbumTracks": "Get tracks from a specific album with pagination support",
        "spotify_getAlbums": "Get detailed information about one or more albums by their Spotify IDs",
        "spotify_getAvailableDevices": "Get information about the user's available Spotify Connect devices",
        "spotify_getMyPlaylists": "Get a list of the current user's playlists on Spotify",
        "spotify_getNowPlaying": "Get information about the currently playing track on Spotify",
        "spotify_getPlaylist": "Get details of a specific Spotify playlist including tracks count, description and owner",
        "spotify_getPlaylistTracks": "Get a list of tracks in a Spotify playlist",
        "spotify_getQueue": "Get a list of the currently playing track and the next items in your Spotify queue",
        "spotify_getRecentlyPlayed": "Get a list of recently played tracks on Spotify",
        "spotify_getUsersSavedTracks": "Get a list of tracks saved in the user's Liked Songs library",
        "spotify_pausePlayback": "Pause Spotify playback on the active device",
        "spotify_playMusic": "Start playing a Spotify track, album, artist, or playlist",
        "spotify_removeTracksFromPlaylist": "Remove one or more tracks from a Spotify playlist",
        "spotify_removeUsersSavedTracks": "Remove one or more tracks from the user's Liked Songs library",
        "spotify_reorderPlaylistItems": "Reorder a range of tracks within a Spotify playlist by moving them to a new position",
        "spotify_resumePlayback": "Resume Spotify playback on the active device",
        "spotify_saveOrRemoveAlbumForUser": "Save or remove albums from the user's Your Music library",
        "spotify_searchSpotify": "Search for tracks, albums, artists, or playlists on Spotify",
        "spotify_setVolume": "Set the playback volume to a specific percentage",
        "spotify_skipToNext": "Skip to the next track in the current Spotify playback queue",
        "spotify_skipToPrevious": "Skip to the previous track in the current Spotify playback queue",
        "spotify_updatePlaylist": "Update the details of a Spotify playlist",
    }

    def build_job_labels(catalog: dict) -> tuple[list, dict]:
        display_labels = []
        label_map = {}
        for job_id, description in catalog.items():
            short = description.split(".")[0].split("\n")[0].strip()
            display_labels.append(short)
            label_map[short] = job_id
        return display_labels, label_map

    display_labels, label_map = build_job_labels(MCP_CATALOG)

    for prompt in prompts:
        intent_result = select_intent(prompt)
        print(f"\n{prompt!r}")
        print(
            f"  intent => {intent_result['intent']} ({intent_result['confidence']:.2f})"
        )
        if intent_result["intent"] == "EXTEND_CONTEXT_WITH_SYSTEM_ACTION":
            job_result = select_job(prompt, display_labels, label_map)
            print(f"  job    => {job_result['job']} ({job_result['confidence']:.2f})")
