import requests


def account_exists(handle):
    handle_url_encoded = handle.replace("@", "")

    url = f"https://api.x.com/graphql/96tVxbPqMZDoYB5pmzezKA/UserByScreenName?variables=%7B%22screen_name%22%3A%22{handle_url_encoded}%22%2C%22withGrokTranslatedBio%22%3Afalse%7D&features=%7B%22hidden_profile_subscriptions_enabled%22%3Atrue%2C%22payments_enabled%22%3Afalse%2C%22profile_label_improvements_pcf_label_in_post_enabled%22%3Atrue%2C%22rweb_tipjar_consumption_enabled%22%3Atrue%2C%22verified_phone_label_enabled%22%3Afalse%2C%22subscriptions_verification_info_is_identity_verified_enabled%22%3Atrue%2C%22subscriptions_verification_info_verified_since_enabled%22%3Atrue%2C%22highlights_tweets_tab_ui_enabled%22%3Atrue%2C%22responsive_web_twitter_article_notes_tab_enabled%22%3Atrue%2C%22subscriptions_feature_can_gift_premium%22%3Atrue%2C%22creator_subscriptions_tweet_preview_api_enabled%22%3Atrue%2C%22responsive_web_graphql_skip_user_profile_image_extensions_enabled%22%3Afalse%2C%22responsive_web_graphql_timeline_navigation_enabled%22%3Atrue%7D&fieldToggles=%7B%22withAuxiliaryUserLabels%22%3Atrue%7D"

    headers = {
        "accept": "*/*",
        "accept-language": "en-GB,en;q=0.9",
        "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "origin": "https://x.com",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://x.com/",
        "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Brave";v="140"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        "x-client-transaction-id": "zcVrDRSIRWct0CXT5dceAT2N5xwliK+Nxkijb3TPCA16/oa44aGUkRBDP/wJm87H9A+kSckr/RdWjvO/n/ktx/La3vPEzg",
        "x-guest-token": "1970803204867682327",
        "x-twitter-active-user": "yes",
        "x-twitter-client-language": "en-GB",
        "x-xp-forwarded-for": "38cb822faf802d12f9a727d427f9b1014fbd26331085ff5627a9b0c468630c7eff0cd0d43e6195e3c79c43661bb7fa5314711c287e2035c395de5f855be30bd6c0d91b6b891f2c765f883796cc5c76b1dea0bbc49193e4a139ec4168499daefc00426b798829b6163aecf027ed47418510a1b6f2b8add52e87efa04524909db5e1debc9e3f8c0d66891eab7d3e80824a73a706d7bec9a0bd1428c1a8c56c8f02c0e972668556ae9c9fa4fd5d93b76b61980a3551c2c5de4dc05858e1c855af1889944cbd44da5650237bd6c5c45888c36d080a5cea283729af8d71ff3be1dbf723e97b0511225ab55cfb735d9553fc4f911c674079dba0b791c359c05fd1adc66e",
    }

    response = requests.get(url, headers=headers)
    if response.json().get("data") == {}:
        return False

    else:
        return True


handle = "femke_plantinga"
exists = account_exists(handle)
if exists:
    print(f"Account {handle} exists")
else:
    print(f"Account {handle} does not exist")
