from gliclass import GLiClassModel, ZeroShotClassificationPipeline
from transformers import AutoTokenizer, pipeline

model = GLiClassModel.from_pretrained("knowledgator/gliclass-instruct-large-v1.0")
tokenizer = AutoTokenizer.from_pretrained("knowledgator/gliclass-instruct-large-v1.0")
job_classification_pipeline = ZeroShotClassificationPipeline(model, tokenizer, classification_type='single-label', device='cuda:0')


classifier = pipeline(
    "zero-shot-classification", model="MoritzLaurer/bge-m3-zeroshot-v2.0", device=0
)

LABELS = {
    "end the conversation or say goodbye": "END_SESSION",
    "answer a question or save a conversation": "COGNITIVE_REQUEST",
    "execute a command or perform an action using a tool": "EXTEND_CONTEXT_WITH_SYSTEM_ACTION",
}


def select_intent(text):
    result = classifier(text, [x for x in LABELS.keys()], multi_label=False)
    return {"intent": LABELS[result["labels"][0]], "confidence": result["scores"][0]}

def select_job(text, catalog):
    result = job_classification_pipeline(text, catalog, threshold=0.5)[0]
    return { "job": result[0]["label"], "confidence": result[0]["score"] }

if __name__ == "__main__":
    prompts = [
        "Pon master of puppets",
        "Can you set an alarm for 7am tomorrow?",
        "Chao, hasta luego",
        "Cual es la capital de Francia?",
        "Perfecto, eso es todo gracias",
        "Hoydia va a hacer calor?",
    ]

    for prompt in prompts:
        print(f"----- {prompt} -----")
        result = select_intent(prompt)
        print(result["intent"], "=>", result["confidence"])



    prompts = [
        "Pon master of puppets",
        "Can you set an alarm for 7am tomorrow?",
        "Hoydia va a hacer calor?",
    ]

    catalog = [
        "fetch_fetch",
        "spotify_addToQueue",
        "spotify_addTracksToPlaylist",
        "spotify_adjustVolume",
        "spotify_checkUsersSavedAlbums",
        "spotify_createPlaylist",
        "spotify_getAlbumTracks",
        "spotify_getAlbums",
        "spotify_getAvailableDevices",
        "spotify_getMyPlaylists",
        "spotify_getNowPlaying",
        "spotify_getPlaylist",
        "spotify_getPlaylistTracks",
        "spotify_getQueue",
        "spotify_getRecentlyPlayed",
        "spotify_getUsersSavedTracks",
        "spotify_pausePlayback",
        "spotify_playMusic",
        "spotify_removeTracksFromPlaylist",
        "spotify_removeUsersSavedTracks",
        "spotify_reorderPlaylistItems",
        "spotify_resumePlayback",
        "spotify_saveOrRemoveAlbumForUser",
        "spotify_searchSpotify",
        "spotify_setVolume",
        "spotify_skipToNext",
        "spotify_skipToPrevious",
        "spotify_updatePlaylist",
    ]

    for prompt in prompts:
        print(f"----- {prompt} -----")
        result = select_job(prompt, catalog)
        print(result["job"], "=>", result["confidence"])
