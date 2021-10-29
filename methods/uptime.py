# This is a built-in function.
# Please do not modify this unless you really know what you're doing.

from commands import BaseMethod
import requests, datetime, time

class Method(BaseMethod):
    def main(self, bot):
        r = requests.get(f"https://api.twitch.tv/helix/streams?user_id={bot.channel_id}", headers=bot.auth.get_headers()).json()
        try:
            a=r['data'][0]['started_at']
        except IndexError:
            return f'{bot.channel} is not currently live.'

        a=datetime.datetime.strptime(f'{a[:-1]}', "%Y-%m-%dT%H:%M:%S")
        a=a.replace(tzinfo=datetime.timezone.utc).timestamp()

        b=str(time.gmtime())
        b=b[b.find("("):]
        r=[]
        for i in range(6):
            b=b[b.find("=")+1:]
            r.append(b[:b.find(",")])
        b=datetime.datetime.strptime(f'{"-".join(r[:3])}T{":".join(r[3:])}', "%Y-%m-%dT%H:%M:%S")
        b=b.replace(tzinfo=datetime.timezone.utc).timestamp()

        s=b-a
        m=round((s-s%60)/60)
        h=round((m-m%60)/60)
        
        return f'Uptime: {h} hours {m%60} minutes {round(s%60)} seconds.'

    def help(self):
        return 'Returns the current stream uptime. Usage: uptime'
