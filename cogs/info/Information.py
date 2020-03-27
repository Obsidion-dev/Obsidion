from discord.ext import commands
from random import choice
import discord
import aiohttp
import requests
from datetime import datetime
import base64
from html.parser import HTMLParser

def get(url):
    r = requests.get(url)

    if r.status_code == 200:
        data = r.json()
        return data
    else:
        return False

def get_uuid(username):
    r = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{username}")

    if r.status_code == 200:
        data = r.json()
        uuid = data["id"]
        return uuid
    else:
        return False


class Information(commands.Cog, name="Information"):

    @commands.command(aliases=['whois', 'p', "names", "namehistory", "pastnames", "namehis"])
    async def profile(self, ctx, username):
        """View a players Minecraft UUID, Username history and skin."""

        uuid = get_uuid(username)
        if uuid:
            long_uuid = f"{uuid[0:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:]}"

            names = get(f"https://api.mojang.com/user/profiles/{uuid}/names")

            name_list=""
            for name in names[::-1][:-1]:
                name1 = name["name"]
                date = datetime.utcfromtimestamp(int(str(name["changedToAt"])[:-3])).strftime("%Y-%m-%d %H:%M:%S (UTC)") # Prettify and give actual month and time passed
                name_list += f"**{names.index(name)+1}.** `{name1}` - {date} "+ "\n"
            original = names[0]["name"]
            name_list+=f"**1.** `{original}` - First Username"

            uuids = "Short UUID: `" + uuid + "\n" + "`Long UUID: `" + long_uuid + "`"

            embed = discord.Embed(title=f"Minecraft profile for {username}", color=0x00ff00)

            embed.add_field(name="UUID's", inline=False, value=uuids)
            embed.add_field(name="Textures", inline=True, value=f"Skin: [Open Skin](https://visage.surgeplay.com/bust/{uuid})")
            embed.add_field(name="Information", inline=True, value=f"Username Changes: {len(names)-1}")
            embed.add_field(name="Name History", inline=False, value=name_list)
            embed.set_thumbnail(url=(f"https://visage.surgeplay.com/bust/{uuid}"))

            await ctx.send(embed=embed)
        else:
            await ctx.send("That username is not been used.")

    @commands.command(aliases=["available", "availability", "namecheck"])
    async def checkName(self, ctx, username):
        """Check weather a username is currently in use."""

        if get_uuid(username):
            # Need to add option to view profile with reaction
            embed = discord.Embed(color=0x00ff00)
            embed.add_field(name="Name Checker", value=f"The username: `{username}` is currently unavailable.")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(color=0x00ff00)
            embed.add_field(name="Name Checker", value=f"The username: `{username}` is available! \n Claim the username here: https://account.mojang.com/me")
            await ctx.send(embed=embed)

    @commands.command()
    async def uuid(self, ctx, username):
        """Get a players UUID."""

        uuid = get_uuid(username)
        if uuid:
            long_uuid = f"{uuid[0:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16-20]}-{uuid[20:]}"
            embed = discord.Embed(title=f"Showing {username}'s Minecraft UUID", color=0x00ff00)
            embed.add_field(name=f"{username}'s UUID", value=f"Short UUID: `{uuid}` \n Long UUID:  `{long_uuid}`")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{ctx.message.author.mention}, :x: the user: `{username}` does not exist!")


    ######################
    ## WORK IN PROGRESS ##
    ######################
    
    @commands.command()
    async def server(self, ctx, server):

        
        """Request a JAVA Minecraft server for information such as online player count, MOTD and more."""

        data = get(f"https://mcapi.us/server/status?ip={server}")

        if data["online"] == True:
            embed = discord.Embed(title=f"Java Server: {server}", color=0x00ff00)

            class MyHTMLParser(HTMLParser):

            def handle_data(self, data):
                print("Encountered some data  :", data)

            parser = MyHTMLParser()
            parser.feed('<span style="color: #55FF55">Hypixel Network  </span><span style="color: #FF5555">[1.8-1.15]</span>","         <span style="color: #55FFFF"><span style="font-weight: bold;">SPRING SALE </span></span><span style="color: #AAAAAA">- </span><span style="color: #FFAA00"><span style="font-weight: bold;">UP TO </span></span><span style="color: #FF5555"><span style="font-weight: bold;">55% OFF</span></span>')

            embed.add_field(name="Description", value=data["motd"]) # need to fix encoding issues
            if data["players"]["now"] > 10:
                now = data["players"]["now"]
                max = data["players"]["max"]
                embed.add_field(name="Players", value=f"Online: `{now:,}` \n Maximum: `{max:,}`")
            else:
                #embed.add_field(name="Players: ", value=)
                pass
            #imagedata = base64.b64decode(data["favicon"][22:])
            #filename = 'favicon.png'  # I assume you have a way of picking unique filenames
            #with open(filename, 'wb') as f:
            #    f.write(imagedata)
            #embed.set_thumbnail(url=("attachment://favicon.png"))
            embed.add_field(name="Version", value=data["server"]["name"])

            await ctx.send(embed=embed)
        else:
            print(data["online"])
            await ctx.send(f"{ctx.author}, :x: The Jave edition Minecraft server `{server}` is currently not online or cannot be requested")

    #@commands.command()
    #async def status(self, ctx):
    #    """Check the status of all the Mojang services"""

    #    data = get("https://status.mojang.com/check")


    #    embed = discord.Embed(title=f"Minecraft Service Status", color=0x00ff00)
    #    print(data[0][0])

    #    for state in data:
    #        if state[state.keys()[0]] == "red":
    #            embed.add_field(name=state[0], value=state[1])
    #
        #embed.add_field(name=state[0], value=state[1])
        #embed.add_field(name=state[0], value=state[1])
        #embed.add_field(name=state[0], value=state[1])
        #embed.add_field(name=state[0], value=state[1])
        #embed.add_field(name=state[0], value=state[1])
        #embed.add_field(name=state[0], value=state[1])
        #embed.add_field(name=state[0], value=state[1])
        #embed.add_field(name=state[0], value=state[1])

        #for state in data:
            #embed.add_field(name=state[0], value=state[1])

    #    await ctx.send("Still in progress")

    #@commands.command()
    #async def version(self, ctx, version):
    #    """View all of Minecraft Java edition versions or a specific version."""
    #    
    #    await ctx.send("Still in progress")

    #@commands.command(aliases=["latestver", "latestversion"])
    #async def latest(self, ctx, snapshot):
    #    """View the latest version or snapshot within the Minecraft Java launcher."""
    #
     #   await ctx.send("Still in progress")

    #@commands.command(aliases=["latestarticle", "minecraftnews", "latestnews"])
    #async def news(self, ctx):
    #    """See the latest post on Minecraft.net."""
    #
    #    await ctx.send("Still in progress")