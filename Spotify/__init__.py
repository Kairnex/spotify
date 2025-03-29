from Spotify.core.bot import Chiku
from Spotify.core.dir import dirr
from Spotify.core.git import git
from Spotify.core.userbot import Userbot
from Spotify.misc import dbb, heroku

from .logging import LOGGER

dirr()
git()
dbb()
heroku()

app = Chiku()
userbot = Userbot()


from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()
