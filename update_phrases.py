from app.services.phrase_updater import update_phrases


if __name__ == '__main__':
    result = update_phrases(force=True)
    print(result)
