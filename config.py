from aqt import mw


def get_user_option(key, default=None):
    user_config = mw.addonManager.getConfig(__name__)
    return user_config.get(key, default)
