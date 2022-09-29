# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from commands import BaseModule
import requests
import datetime
import time


class Module(BaseModule):
    helpmsg = 'Returns the current stream uptime. Usage: uptime'

    def main(self, bot):
        r = requests.get(
            f"https://api.twitch.tv/helix/streams?user_id={bot.channel_id}", headers=bot.auth.get_headers()).json()
        try:
            time_start = r['data'][0]['started_at']
        except IndexError:
            return f'{bot.channel} is not currently live.'

        time_start = datetime.datetime.strptime(
            f'{time_start[:-1]}', "%Y-%m-%dT%H:%M:%S")
        time_start = time_start.replace(
            tzinfo=datetime.timezone.utc).timestamp()

        time_now = str(time.gmtime())
        time_now = time_now[time_now.find("("):]

        r = []
        for _ in range(6):
            time_now = time_now[time_now.find("=")+1:]
            r.append(time_now[:time_now.find(",")])
        time_now = datetime.datetime.strptime(
            f'{"-".join(r[:3])}T{":".join(r[3:])}', "%Y-%m-%dT%H:%M:%S")
        time_now = time_now.replace(tzinfo=datetime.timezone.utc).timestamp()

        secs = time_now-time_start
        mins = round((secs-secs % 60)/60)
        hrs = round((mins-mins % 60)/60)

        return f'Uptime: {hrs}h{mins%60}m{round(secs%60)}s.'
