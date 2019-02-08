import pickle
import json
import os
import discord
from collections import defaultdict
import gspread
import asyncio
from oauth2client.service_account import ServiceAccountCredentials
import validators
import datetime
import calendar
import time

warid = 0
wid = ''
cdate = ''

WARDict = defaultdict(list)

client = discord.Client()

GEARdict = defaultdict(list)

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name('SkyNet-cfef4b6afd56.json', scope)

gc = gspread.authorize(credentials)

sh = gc.open_by_url("") #Link to First spreadsheet
wks = sh.worksheet("BOT") #bot tab

sh2 = gc.open_by_url("") #Link to second spreadsheet, if needed
war = sh2.worksheet("Nodewar") #name of spreadsheet page 

cell_name_list = wks.range('A2:A100') #init enough lists to fill the sheet later
cell_family_list = wks.range('B2:B100')
cell_character_list = wks.range('C2:C100')
cell_lvl_list = wks.range('D2:D100')
cell_class_list = wks.range('E2:E100')
cell_ap_list = wks.range('F2:F100')
cell_awaap_list = wks.range('G2:G100')
cell_dp_list = wks.range('H2:H100')
cell_gearpic_list = wks.range('I2:I100')

bdo_classes = ['warrior', 'valkyrie', 'valk', 'wizard', 'wiz', 'witch', 'ranger', 'sorceress', 'sorc', 'berserker', 'tamer', 'musa', 'maehwa', 'lahn', 'ninja', 'kunoichi', 'kuno', 'dk', 'DK', 'striker', 'mystic', 'archer']
#missing check on eof and IOE
def write_war_list():
    global WARDict
    with open('warlist.json','w') as fp:
        json.dump(WARDict,fp)
def read_war_list():
    global WARDict
    try:
        with open('warlist.json','r') as fp:
            WARDict = json.load(fp)
    except IOError:
        fp = open('warlist.json','w+')
        WARDict = defaultdict(list)
    except EOFError: #file empty
        WARDict = defaultdict(list)

def write_gear_list():
    global GEARdict
    with open('gearlist', 'wb') as fp:
        pickle.dump(GEARdict, fp)
def read_gear_list():
    global GEARdict
    try:
        with open('gearlist', 'rb') as fp:
            GEARdict = pickle.load(fp)
    except IOError: #no file
        fp = open('gearlist', 'w+')
        GEARdict = defaultdict(list)
    except EOFError: #file empty
        GEARdict = defaultdict(list)

async def is_officer(message): 
    if "guild master" in [y.name.lower() for y in message.author.roles] or "guild officers" in [y.name.lower() for y in message.author.roles]: # change guild master/officer to roles you would like to have almost full control
        return True

    return False

async def is_member(member): 
    if "members" in [y.name.lower() for y in member.roles]: #normal discord member role, user needs this role for bot to check for gear
        return True

    return False

async def is_limbo(user): 
    if "limbo" in [y.name.lower() for y in user.roles]: # optional limbo role when user joins
        return True

    return False   

#reformat the message removing the bot prefix
def format_input(prefix,message):
    string = message.replace(prefix,'')
    string = string.lstrip()
    return string
#returns the key
def get_key(message):
    key = message.split(" ", 1)
    key = key[0]
    return key

#return the content of the msg 
def get_msg_content(message):
    content = message.split(" ", 1)
    content = content[1]
    return content

def check_day(msg):
    if not isinstance(msg,str):
        try:
            datetime.datetime.strptime(msg.content, '%d-%m-%Y')
            return True
        except ValueError:
            return False
    else:
        try:
            print(msg)
            datetime.datetime.strptime(msg, '%d-%m-%Y')
            print("valid date")
            return True
        except ValueError:
            print("invalid date")
            return False

async def msg_validation(msg_list,message,offset):
    if(len(msg_list) == 8+offset and msg_list[2+offset].isnumeric() and msg_list[3+offset].lower() in bdo_classes and
        msg_list[4+offset].isnumeric() and msg_list[5+offset].isnumeric() and
        msg_list[6+offset].isnumeric()):
        return True
    else:
        await show_help(message)
        return False

async def url_validation(msg_list,message,offset):
    if((msg_list[7+offset].lower().endswith(".png") or msg_list[7+offset].lower().endswith(".jpg")) and validators.url(msg_list[7+offset])):
        return True
    else:
        await client.send_message(message.channel,
                                                    "`Use A Direct Link To The Picture (URL Must End With .jpg/.png) Use ShareX, It's Free`")
        return False

async def show_help(message):
    if message.channel.id == '48000000000000': #change channel id here
        embed = discord.Embed()
        embed.set_author(name="Gear Help",icon_url=client.user.avatar_url)
        embed.set_thumbnail(url=client.user.avatar_url)
        embed.add_field(name="How To Add/Update Gear",value="!gear Family Name | Character Name | Level | Class | AP | AAP | DP | Gear pic",inline=False)
        embed.add_field(name="Classes",value="Abbreviations Work i.e 'wiz' 'valk'\n For Dark Knight Use 'dk'",inline=False)
        embed.add_field(name="Gear Pic Rules",value="Use A Direct Link To The Picture (URL Must End With .jpg/.png) Use ShareX, It's Free",inline=False)
        embed.add_field(name="Update Gear",value="Use !update stats | AP | AAP | DP | Gear Link",inline=False)
        embed.add_field(name="Update Level",value="Use !update level | New Level",inline=False)
        embed.add_field(name="View Gear",value="!gear | @user",inline=False)
        embed.set_footer(text='VendettaBot/Gear | KristiaN', icon_url="https://cdn.discordapp.com/avatars/170960401926848513/9f942640cfc9648d808b2ae9cfae4b7c.png?size=128")
        await client.send_message(message.channel,embed=embed)
        await client.delete_message(message) # change to suit your needs

async def show_officerhelp(message): # this help embed will only be activated by officers in a seperate channel
    if message.channel.id == '48000000000000': #change channel id here
        embed = discord.Embed()
        embed.set_author(name="Officer Help",icon_url=client.user.avatar_url)
        embed.set_thumbnail(url=client.user.avatar_url)
        embed.add_field(name="!manual",value="!manual @user Family Name | Character Name | Level | Class | AP | AAP | DP | Gear pic",inline=False)
        embed.add_field(name="!fsupdate",value="!fsupdate @user stats **OR** level",inline=False)
        embed.add_field(name="!remove",value="Remove @user **OR** User ID",inline=False)
        embed.add_field(name="!check",value="Replies With Number Of Users On Spreadsheet/Bot",inline=False)
        embed.add_field(name="!dmcheck",value="DM's You A List Of Users Who's Gear Isn't On The Bot",inline=False)
        embed.add_field(name="!slackers",value="@'s All The Slackers In <#488832525389791297>",inline=False)
        embed.add_field(name="!dmslackers",value="DM's Slackers A Whack MSG Threatening Them",inline=False)
        embed.add_field(name="!war",value="Starts WAR Command \n  - Date Format: **01-01-2019**",inline=False)        
        embed.set_footer(text='VendettaBot/Officer Help | KristiaN', icon_url="https://cdn.discordapp.com/avatars/170960401926848513/9f942640cfc9648d808b2ae9cfae4b7c.png?size=128")
        await client.send_message(message.channel,embed=embed)
        await client.delete_message(message) # change to suit your needs

def class_check(class_name):
    if class_name == 'DK':
        bdoclass = 'Dark Knight'
    elif class_name == 'dk':
        bdoclass = 'Dark Knight'
    elif class_name == 'valk':
        bdoclass = 'Valkyrie'
    elif class_name == 'Valk':
        bdoclass = 'Valkyrie'
    elif class_name == 'wiz':
        bdoclass = 'Wizard' 
    elif class_name == 'Wiz':
        bdoclass = 'Wizard' 
    elif class_name == 'sorc':
        bdoclass = 'Sorceress'
    elif class_name == 'Sorc':
        bdoclass = 'Sorceress'
    elif class_name == 'kuno':
        bdoclass = 'Kunoichi' 
    elif class_name == 'Kuno':
        bdoclass = 'Kunoichi' 
    else:
        bdoclass = class_name.title()
    return bdoclass
    
def delete_from_sheet(name):
    gc.login()
    try:
        cell = wks.find(name)
        wks.delete_row(cell.row)
        print("deleted")
    except:
        print("not found on sheet, wrong fam name ?")

def delete_war(name):
    gc.login()
    try:
        print(name)
        cell = war.find(name)
        str_list = list(filter(None, war.col_values(cell.col)))
        for i in range(len(str_list)):
            war.update_cell(i+1,cell.col,"")
        print("deleted")
    except:
        print("something went wrong or not found")

def next_available_row(worksheet):
    str_list = list(filter(None, worksheet.col_values(2)))
    return str(len(str_list)+1)

def next_available_col(worksheet):
    str_list = list(filter(None, worksheet.row_values(1)))
    return str(len(str_list)+1)

async def update_war_sheet(message,date):
    gc.login()
    infos = WARDict[date]
    #user = await client.get_user_info(id)
    try:
        cell = war.find(date)
        column = cell.col
        try:
            for i in range(1,len(infos)+1):
                war.update_cell(i+1,column,infos[i-1])
        except:
            await client.send_message(message.channel,"Error on war.update_cell")
    except:
        print("New war added")
        next_col = next_available_col(war)
        war.update_cell(1,next_col,date)
        try: #write the lists to the sheet
            for i in range(1,len(infos)+1):
                war.update_cell(i+1,next_col,infos[i-1])
                
        except:
            await client.send_message(message.channel,"Error on war.update_cell for new war")

async def find_and_update(message,user):
    gc.login()
    id = user.id
    infos = GEARdict[id]
    #user = await client.get_user_info(id)
    name = user.display_name
    bdoclass = class_check(infos[3])
    try:
        cell = wks.find(infos[0]) #find fam name in sheet which is at col 2
        column = cell.col
        if (column == 2): #fam name same as discord name ?
            column = column+1
            print("same discord name as fam name")
        print("user found in sheet")
        try: #write the lists to the sheet
            wks.update_cell(cell.row,column-1,name)
            wks.update_cell(cell.row,column,infos[0])
            wks.update_cell(cell.row,column+1,infos[1])
            wks.update_cell(cell.row,column+2,infos[2])
            wks.update_cell(cell.row,column+3,bdoclass)
            wks.update_cell(cell.row,column+4,infos[4])
            wks.update_cell(cell.row,column+5,infos[5])
            wks.update_cell(cell.row,column+6,infos[6])
            wks.update_cell(cell.row,column+8,infos[7])
        except:
            await client.send_message(message.channel,"Something went wrong while updating the sheet, please inform my cute master")
            return
    except:
        next_row = next_available_row(wks)
        print("add new user")
        try: #write the lists to the sheet
            wks.update_cell(next_row,2,name)
            wks.update_cell(next_row,3,infos[0])
            wks.update_cell(next_row,4,infos[1])
            wks.update_cell(next_row,5,infos[2])
            wks.update_cell(next_row,6,bdoclass)
            wks.update_cell(next_row,7,infos[4])
            wks.update_cell(next_row,8,infos[5])
            wks.update_cell(next_row,9,infos[6])
            wks.update_cell(next_row,11,infos[7])
        except Exception as e:
            print(e)
            await client.send_message(message.channel,"Something went wrong while updating the sheet, please inform my cute master")

async def send_timed_msg(message,embed,timer):
    await client.wait_until_ready()
    msg = await client.send_message(message.channel,embed=embed )
    await asyncio.sleep(timer) 
    await client.delete_message(msg)

async def show_gear_embed(message,picurl,classgs,userID):
    embed = discord.Embed()
    embed.set_author(name=userID,icon_url=message.mentions[0].avatar_url)
    embed.set_thumbnail(url=message.mentions[0].avatar_url)
    embed.add_field(name=message.mentions[0].display_name,value=classgs,inline=False)
    embed.set_image(url=picurl)
    #await send_timed_msg(message,embed,15) #timed message example
    await client.send_message(message.channel,embed=embed)

@client.event
async def on_ready():
    timey = (time.strftime("%H:%M:%S"))
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    print(timey)
    # read_gear_list()     #this will fail if gearlist file is empty or not there at all, uncomment once you have sumbitted gear to the bot, then restart
    read_war_list()
    logchannel = client.get_channel("48000000000000") #Log channel ID
    channel = client.get_channel("48000000000001") #limbo channel ID
    embed = discord.Embed()
    embed.set_author(name="Choose Your Destiny!!",icon_url=client.user.avatar_url)
    embed.set_thumbnail(url=client.user.avatar_url)
    embed.add_field(name="You **Must** Choose A Side! Or Remain In Limbo **Forever!**",value="For Help Msg <@&499373094012715015>",inline=False)
    embed.add_field(name="Recruit",value="If You Are A Potential Recruit, Click \U0001F4D5",inline=False)
    embed.add_field(name="Other Guild",value="If You Are A Member Of Another Guild, Click \U0001F4D9",inline=False)
    embed.add_field(name="Friend",value="If You Are A Friend Of The Guild Or It's Members, Click \U0001F4D8",inline=False)
    embed.set_footer(text='Welcome To Limbo!!', icon_url="https://cdn.discordapp.com/avatars/170960401926848513/9f942640cfc9648d808b2ae9cfae4b7c.png?size=128") #change to suit your needs
    await chat_del(channel)
    wmsg = await client.send_message(channel,embed=embed)
    await client.send_message(logchannel,"```Logged in as:\n" + client.user.name + "\n" + client.user.id + "\n------\n" + timey + "```" )
    await client.add_reaction(wmsg,'\U0001F4D5')
    await client.add_reaction(wmsg,'\U0001F4D9')
    await client.add_reaction(wmsg,'\U0001F4D8')


@client.event
async def on_message(message):
    if message.content.startswith('!gear'):
        if message.channel.id == '48000000000000': #Gear channel id here
            msg = format_input("!gear", message.content) #cleanup the message
            if msg: #empty message
                if message.mentions == []: #if there's no mentions it means you want to add/update gears otherwise pull the mentioned gear out
                    msg_list = msg.split(" ",8) #split the msg in multiple args
                    if await msg_validation(msg_list,message,0) and await url_validation(msg_list,message,0):
                            if message.author.id in GEARdict.keys(): #if key is already there update it
                                del GEARdict[message.author.id]
                                for i in range(8):
                                    GEARdict[message.author.id].append(msg_list[i])
                                    #0 fam n 1 char n 2 lvl 3 class 4 ap 5  awap 6 dp 7 pic
                                await find_and_update(message,message.author)
                                write_gear_list()
                                await client.send_message(message.channel,
                                                      "Gear updated, remember that you can use !update to update your gear instead")
                                await client.delete_message(message)
                            else: #else add it anew
                                for j in range(8):
                                    GEARdict[message.author.id].append(msg_list[j])
                                await find_and_update(message,message.author)
                                write_gear_list()
                                await client.send_message(message.channel,
                                                    "Gear submitted!")
                else:
                    if msg: #show gear
                        id = message.mentions[0].id
                        for key in GEARdict:
                            if key == id:
                                userID = await client.get_user_info(key)
                                list = GEARdict[key]
                                bdoclass = class_check(list[3])                            
                                picurl = list[7].strip()
                                gs = int(((int(list[4]) + int(list[5])) / 2) + int(list[6]))
                                stringfix = list[1] + " " + list[0] + "**\nClass: **" + bdoclass + "**\nLvl: **"+ list[2] + "**\nGS: **" + str(gs)
                                classgs = stringfix.strip()
                                await show_gear_embed(message,picurl,classgs,userID)
                                break
                        else:
                            await client.send_message(message.channel,"Gear not found!")
            else:
                await show_help(message)


    elif message.content.startswith('!remove'):
        eval = await is_officer(message)
        if message.channel.id == '48000000000000' or '480000000000001': #change channel id here, 1st id=gear channel, 2nd=admin command channel
            if eval:
                if not message.mentions:
                    id = format_input("!remove", message.content)
                    if id in GEARdict.keys():
                        member = await client.get_user_info(id)
                        discord_name = member.display_name
                        list = GEARdict[id]
                        name = list[0]
                        delete_from_sheet(name)
                        del GEARdict[id]
                        write_gear_list()
                        await client.send_message(message.channel, "{} gear has been moved to Bless Online!".format(discord_name))
                        await client.delete_message
                    else:
                        await client.send_message(message.channel, "Use !remove @someone or ID to remove his gear")
                        await client.delete_message
                else:    
                    if message.mentions[0].id in GEARdict.keys():
                        list = GEARdict[message.mentions[0].id]
                        name = list[0]
                        delete_from_sheet(name)
                        del GEARdict[message.mentions[0].id]
                        write_gear_list()
                        await client.send_message(message.channel, "{} gear has been moved to Bless Online!".format(message.mentions[0].display_name))
                        await client.delete_message
                    else:
                        await client.send_message(message.channel, "Gear not found!")
            else:
                await client.send_message(message.channel,
                                        "I don't think so!")
        await client.delete_message(message)

    elif message.content.startswith('!update'):
        if message.channel.id == '48000000000000': #change channel id here:
            msg = format_input("!update", message.content)
            msg_list = msg.split(" ",1)
            msg_list[0] = msg_list[0].lower()
            print("msg_list: ",msg_list)
            if message.author.id in GEARdict.keys():
                if msg_list[0] == 'stats':
                    stats_list = msg_list[1].split(" ",4)
                    print("stats_list: ",stats_list)
                    if (len(stats_list) == 4 and stats_list[0].isnumeric() and 
                        stats_list[1].isnumeric() and stats_list[2].isnumeric() and validators.url(stats_list[3])):
                        if(stats_list[3].lower().endswith(".png") or stats_list[3].lower().endswith(".jpg") ):
                            GEARdict[message.author.id].pop(4)
                            GEARdict[message.author.id].insert(4,stats_list[0]) #ap
                            GEARdict[message.author.id].pop(5)
                            GEARdict[message.author.id].insert(5,stats_list[1]) #awaap
                            GEARdict[message.author.id].pop(6)
                            GEARdict[message.author.id].insert(6,stats_list[2]) #dp
                            GEARdict[message.author.id].pop(7)
                            GEARdict[message.author.id].insert(7,stats_list[3]) #link
                            await find_and_update(message,message.author)
                            write_gear_list()
                            await client.send_message(message.channel,
                                                        "Gear updated!")
                        else:
                            await client.send_message(message.channel,
                                                    "`Use A Direct Link To The Picture (URL Must End With .jpg/.png) Use ShareX, It's Free`")
                    else:
                        await show_help(message)
                elif msg_list[0] == 'level':
                    level_list = msg_list[1].split(" ",2)
                    print("level: ",level_list)
                    if(level_list[0].isnumeric()):
                        GEARdict[message.author.id].pop(2)
                        GEARdict[message.author.id].insert(2,level_list[0])
                        await find_and_update(message,message.author)
                        write_gear_list()
                        await client.send_message(message.channel,
                                                    "How to waste your life 101 by {}".format(message.author.display_name))  
                else:
                    await show_help(message)
            else:
                       await client.send_message(message.channel,"You should submit your gear first!")


    elif message.content.startswith('!check'): #self explanatory just counts how many entries we have got so far
        if message.channel.id == '48000000000000' or '48000000000001': #change channel id here, 1st id=gear channel, 2nd=admin command channel
            eval = await is_officer(message)
            if eval:
                i = 0
                for key in GEARdict.fromkeys(GEARdict):
                    i += 1
                else:
                    await client.send_message(message.channel, "Number of slaves that submitted to me thus far: " + str(i))
            else:  
                await client.send_message(message.channel,
                                        "What are you trying to do ? Time to take out the whip")
        await client.delete_message(message)

    elif message.content.startswith('!help'): 
        try:
            await show_help(message)
            #await show_officerhelp(message) #uncomment if you want a seperate admin help list
        except:
            pass

    elif message.content.startswith('!slackers'): #dm's slcares names in the channel
        eval = await is_officer(message)
        if message.channel.id == '48000000000000' and eval: #change channel id here
            m_list = message.server.members
            await client.send_message(message.channel,"What is this trash")
            for members in m_list:
                check = await is_member(members)
                if check:
                    if members.id not in GEARdict.keys():
                        await client.send_message(message.channel,"" + members.mention)
                        await client.delete_message
        else:
            await client.send_message(message.channel,
                                      "Listen here you little shit")
        await client.delete_message(message)

    elif message.content.startswith('!sheets'): #embeds links to spreadsheets for admins
        eval = await is_officer(message)
        if message.channel.id == '48000000000000'and eval: #admin channel channel id here
            channel = client.get_channel("48000000000000") #admin channel channel id here
            embed = discord.Embed()
            embed.set_author(name="Sheets!!",icon_url=client.user.avatar_url)
            embed.set_thumbnail(url=client.user.avatar_url)
            embed.add_field(name="Main Sheet",value="[*LINK*](URL)",inline=False)
            embed.add_field(name="Management",value="[*LINK*](URL)",inline=False)
            embed.add_field(name="Payouts",value="[*LINK*](URL)",inline=False)
            embed.add_field(name="Daily Pay",value="[*LINK*](URL)",inline=False)
            embed.set_footer(text='USE THIS POWER WISELY!!', icon_url="https://cdn.discordapp.com/avatars/170960401926848513/9f942640cfc9648d808b2ae9cfae4b7c.png?size=128")
            await client.send_message(channel,embed=embed)
        await client.delete_message(message)

    elif message.content.startswith('!fsupdate'):
        if message.channel.id == '48000000000000': #change channel id here
            eval = await is_officer(message)
            if eval:
                if message.mentions:
                    id = message.mentions[0].id
                    print(id)
                    msg = format_input("!fsupdate", message.content)
                    print("msg1: {}".format(msg))
                    try:
                        msg_list = msg.split(" ",2)
                        msg_list[1] = msg_list[1].lower()
                        print("msg_list: ",msg_list)
                        if id in GEARdict.keys():
                            #user = await client.get_user_info(id)
                            if msg_list[1] == 'stats':
                                stats_list = msg_list[2].split(" ",4)
                                print("stats_list: ",stats_list)
                                if (len(stats_list) == 4 and stats_list[0].isnumeric() and 
                                    stats_list[1].isnumeric() and stats_list[2].isnumeric() and validators.url(stats_list[3])):
                                    if(stats_list[3].lower().endswith(".png") or stats_list[3].lower().endswith(".jpg") ):
                                        GEARdict[id].pop(4)
                                        GEARdict[id].insert(4,stats_list[0]) #ap
                                        GEARdict[id].pop(5)
                                        GEARdict[id].insert(5,stats_list[1]) #awaap
                                        GEARdict[id].pop(6)
                                        GEARdict[id].insert(6,stats_list[2]) #dp
                                        GEARdict[id].pop(7)
                                        GEARdict[id].insert(7,stats_list[3]) #link
                                        await find_and_update(message,message.mentions[0])
                                        write_gear_list()
                                        await client.send_message(message.channel,
                                                                    "Forcefully updated his gear!")
                                    else:
                                        await client.send_message(message.channel,
                                                                "`Not A Direct Link Or Invalid URL! \nURL Must End With .jpg/.png`")
                                else:
                                    await show_help(message)
                            elif msg_list[1] == 'level':
                                level = msg_list[2]
                                print("level: ",level)
                                if(level.isnumeric()):
                                    GEARdict[id].pop(2)
                                    GEARdict[id].insert(2,level)
                                    await find_and_update(message,message.mentions[0])
                                    write_gear_list()
                                    await client.send_message(message.channel,
                                                                "Level forcefully updated")  
                            else:
                                await client.send_message(message.channel,"Wrong sintax, !fsupdate @someone stats/level")
                        else:
                            await client.send_message(message.channel,"Gear not found!")
                    except:
                        await client.send_message(message.channel,"Wrong sintax, !fsupdate @someone stats/level")
                else:
                    await client.send_message(message.channel,"You are not mentioning anyone are you drunk again or just stupid?") 

    elif message.content.startswith('!dmcheck'):
        eval = await is_officer(message)
        if message.channel.id == '48000000000000' or '48000000000001' and eval: #change channel id here, 1st id=gear channel, 2nd=admin command channel
            m_list = message.server.members 
            await client.send_message(message.author,"**Faggot's who haven't submitted their gear yet:**")
            for members in m_list:
                check = await is_member(members)
                if check:
                    if members.id not in GEARdict.keys():
                        await client.send_message(message.author,"{}".format(members.display_name))
        else:
            await client.send_message(message.channel,
                                      "Are you THAT stupid ?")
        await client.delete_message(message)

    elif message.content.startswith('!dmslackers'): 
        eval = await is_officer(message)
        if message.channel.id == '48000000000000' or '48000000000001' and eval: #change channel id here, 1st id=gear channel, 2nd=admin command channel
            m_list = message.server.members
            await client.send_message(message.channel,"On it Boss! Check your dms for the list!") 
            await client.send_message(message.author,"**Sent a threat to:**")
            for members in m_list:
                check = await is_member(members)
                if check:
                    if members.id not in GEARdict.keys():
                        try:
                            await client.send_message(members,"Kind reminder to submit your <#gearchannelID>, or weird action will be taken! https://b.catgirlsare.sexy/hRvs.gif") #change ID here
                            await client.send_message(message.author,"{}".format(members.display_name))
                        except:
                            await client.send_message(message.author,"*error* sending **{}** a message".format(members.display_name))
                            channel = client.get_channel("48000000000002") #log channel ID
                            await client.send_message(channel,"**error* sending **{}** a threat".format(members.display_name))
                            pass
        else:
            await client.send_message(message.channel,
                                        "Are you THAT stupid ?")
        await client.delete_message(message)

    elif message.content.startswith('!limbo'): #manual limbo embed if startup doesn't work for some reason
        eval = await is_officer(message)
        if message.channel.id == '48000000000003' and eval: #limbo channel ID
            channel = client.get_channel("48000000000003")#limbo channel ID
            embed = discord.Embed()
            embed.set_author(name="Choose Your Destiny!!",icon_url=client.user.avatar_url)
            embed.set_thumbnail(url=client.user.avatar_url)
            embed.add_field(name="You **Must** Choose A Side! Or Remain In Limbo **Forever!**",value="For Help Msg <@&USER1>",inline=False)#change user ID
            embed.add_field(name="Recruit",value="If You Are A Potential Recruit, Click \U0001F4D5",inline=False)
            embed.add_field(name="Other Guild",value="If You Are A Member Of Another Guild, Click \U0001F4D9",inline=False)
            embed.add_field(name="Friend",value="If You Are A Friend Of The Guild Or It's Members, Click \U0001F4D8",inline=False)
            embed.set_footer(text='Welcome To Limbo!!', icon_url="https://cdn.discordapp.com/avatars/170960401926848513/9f942640cfc9648d808b2ae9cfae4b7c.png?size=128")
            await chat_del(channel)
            wmsg = await client.send_message(channel,embed=embed)
            await client.add_reaction(wmsg,'\U0001F4D5')
            await client.add_reaction(wmsg,'\U0001F4D9')
            await client.add_reaction(wmsg,'\U0001F4D8')
            await client.delete_message(message)

    elif message.content.startswith('!manual'):
        eval = await is_officer(message)
        if message.channel.id == '48000000000000' and eval: #change channel id here
            msg = format_input("!manual", message.content) #cleanup the message
            if msg: #check for empty msg
                if message.mentions: #if there's no mentions it means you want to add/update gears otherwise pull the mentioned gear out
                    msg_list = msg.split(" ",9) #split the msg in multiple args
                    if await msg_validation(msg_list,message,1) and await url_validation(msg_list,message,1):
                        if message.mentions[0].id in GEARdict.keys(): #if key is already there update it
                            del GEARdict[message.mentions[0].id]
                            for i in range(1,9):
                                GEARdict[message.mentions[0].id].append(msg_list[i])
                                #0 fam n 1 char n 2 lvl 3 class 4 ap 5  awap 6 dp 7 pic
                            await find_and_update(message,message.mentions[0])
                            write_gear_list()
                            await client.send_message(message.channel,
                                                    "Why are you doing this, are you aware that you can use !fsupdate ? Whatever I'll let this pass")
                        else: #else add it anew
                            for j in range(1,9):
                                GEARdict[message.mentions[0].id].append(msg_list[j])
                            await find_and_update(message,message.mentions[0])
                            write_gear_list()
                            await client.send_message(message.channel,
                                                "Added a new slave to the pack")
                    else:
                        print("message validation failed")
                else:
                    print("mention not found")
            else:
                print("empty msg")

    elif message.content.startswith('!war'):
        global warid
        global cdate
        #WARDict.setdefault('culo',[]).append('culo2')
        eval = await is_officer(message)
        if message.channel.id == '48000000000003' and eval: #war/admin channel ID
            nwchannel = message.author.server.get_channel("48000000000001") #channel where announcement will be
            channel = message.author.server.get_channel("48000000000002") #admin channel ID
            await client.send_message(message.channel,"Insert the date of the nodewar in the day-month-year format")
            date = await client.wait_for_message(author=message.author,channel=channel,check=check_day,timeout=60)
            if date is None:
                await client.send_message(message.channel, "Nodewar announcement exited successfully")
                return
            await client.send_message(message.channel, "Now insert the place of the nw")
            place = await client.wait_for_message(author=message.author,channel=channel,timeout=60)
            if place is None or place.content == '$exit':
                await client.send_message(message.channel, "Nodewar announcement exited successfully")
                return
            await client.send_message(message.channel, "Now insert the server")
            server = await client.wait_for_message(author=message.author,channel=channel,timeout=60)
            if server is None or server.content == '$exit':
                await client.send_message(message.channel, "Nodewar announcement exited successfully")
                return
            await client.send_message(message.channel, "A nodewar message will be sent to the nodewar channel!")
            if date.content not in WARDict.keys():
                cdate = date.content 
                WARDict.setdefault(date.content,[]).append(place.content)
                WARDict.setdefault(date.content,[]).append(server.content)
                write_war_list()
                print(WARDict)
                embed = discord.Embed()
                embed.set_author(name="Node War Sign-Up",icon_url=client.user.avatar_url)
                embed.set_thumbnail(url=client.user.avatar_url)
                embed.add_field(name="(^=˃ᆺ˂)",value="@everyone Signup by reacting here for **{}** Nodewar that will be fought at **{}** on **{}**\n ̷̧̟̭̺͕̜̦̔̏̊̍ͧ͊́̚̕͞".format(datetime.datetime.strptime(date.content, '%d-%m-%Y').strftime("%A"),place.content,server.content),inline=False)
                embed.add_field(name="PLEASE BRING :",value="-what you want them to bring",inline=False)
                embed.set_footer(text='VendettaBot/NW', icon_url="https://cdn.discordapp.com/avatars/170960401926848513/9f942640cfc9648d808b2ae9cfae4b7c.png?size=128")
                cwar = await client.send_message(nwchannel,embed=embed)
                await client.add_reaction(cwar,'\U0001F1FE')
                await update_war_sheet(message,cdate)
                warid = cwar.id
            else:
                await client.send_message(message.channel,"Nodewar already added, please remove the old one or kys")
    
    elif message.content.startswith('!list'):
        if message.channel.id == '48000000000004' and await is_officer(message): #war/admin channel ID
            await client.send_message(message.channel,json.dumps(WARDict, indent=2)
                                  .replace("[","").replace("'","").replace("]","").strip('}').strip('{')
                                  .replace(",","").replace('"',""))
    
    elif message.content.startswith('!attendance'):
        if message.channel.id == '48000000000004' and await is_officer(message): #war/admin channel ID
            msg = format_input("!attendance", message.content)
            if msg and check_day(msg) and msg in WARDict.keys():
                list = WARDict[msg][2:]
                await show_war_embed(message.channel,list,msg)
    
    elif message.content.startswith('!rmwar'):
        if message.channel.id == '48000000000004' and await is_officer(message): #war/admin channel ID
            msg = format_input("!rmwar", message.content)
            if msg and check_day(msg) and msg in WARDict.keys():
                del WARDict[msg]
                delete_war(msg)
                write_war_list()
                await client.send_message(message.channel,"{} nodewar removed".format(msg))

   

@client.event
async def on_reaction_add(reaction, user):
    global WARDict
    global warid
    global cdate
    global wid
    #print(warid)
    #print(reaction.message.id)
    channelid = '48000000000003' #limbo channel ID
    logchannelid = '48000000000002' # log channel iD
    logchannel = user.server.get_channel(logchannelid)
    mention = user.mention    

    if reaction.message.channel.id != channelid:
        return
    elif user.id == 'BOTID': #botid
        return
    elif reaction.message.id == warid and str(reaction.emoji) == "\U0001F1FE":
        print(user.display_name)
        WARDict.setdefault(cdate,[]).append(user.display_name)
        write_war_list()
        await update_war_sheet(reaction.message,cdate)
        print(WARDict)
        return
    elif str(reaction.emoji) == "\U0001F4D5":
        role1 = discord.utils.get(user.server.roles, name="Recruit")
        mentionr1 = role1.mention
        erole1 = discord.Embed()
        erole1.set_author(name="Welcome To Vendetta",icon_url=client.user.avatar_url)
        erole1.set_thumbnail(url=client.user.avatar_url)
        erole1.add_field(name="Member/Recruit",value="Hey **" + mention + "**, Welcome to **Vendetta** \uD83E\uDD17\uD83C\uDF89 !\n\nPlease wait in <#488381580390301708> while <@170960401926848513> or a <@&499373094012715015> come and talk to you \uD83E\uDD17\n\nCan you please change your **Nickname** to reflect your family name as it helps us out.",inline=False)
        erole1.add_field(name="Contact Guild Master",value="<@>",inline=False)
        erole1.add_field(name="Contact Officers",value="<@&>",inline=False)
        erole1.add_field(name="BOT HELP",value="Type !help in <#GEAR CHANNEL ID>",inline=False) #insert channel ID here
        erole1.set_footer(text='Congrats, You Are No Longer In Limbo', icon_url=client.user.avatar_url)
        lrole1 = discord.Embed()
        lrole1.set_author(name="Role Update!!",icon_url=client.user.avatar_url)
        lrole1.set_thumbnail(url=client.user.avatar_url)
        lrole1.add_field(name="(^=˃ᆺ˂)",value="\nHey <@USER1> | <@&Role1> \n\n**" + mention + "** has joined **Vendetta** As A Recruit/Member\nThey have been given the role " + mentionr1 + ", told to wait in the <#488381580390301708> and change their nickname",inline=False)
        lrole1.set_footer(text='VendettaBot/Limbo', icon_url=client.user.avatar_url)
        await client.replace_roles(user, role1)
        await client.send_message(user,embed=erole1)
        await client.send_message(logchannel,embed=lrole1)
    elif str(reaction.emoji) == "\U0001F4D9":
        role2 = discord.utils.get(user.server.roles, name="Other Guilds")
        mentionr2 = role2.mention
        erole2 = discord.Embed()
        erole2.set_author(name="Welcome To Vendetta",icon_url=client.user.avatar_url)
        erole2.set_thumbnail(url=client.user.avatar_url)
        erole2.add_field(name="Other Guild",value="Hey **" + mention + "**, Welcome to **Vendetta** \uD83E\uDD17\uD83C\uDF89 !\n\nCan you please change your **Nickname** to reflect your family name as it helps us out.",inline=False)
        erole2.add_field(name="Contact Guild Master",value="<@>",inline=False)
        erole2.add_field(name="Contact Officers",value="<@&>",inline=False)
        erole2.add_field(name="BOT HELP",value="Type !help in <#GEAR CHANNEL ID>",inline=False) #insert channel ID here
        erole2.set_footer(text='Congrats, You Are No Longer In Limbo', icon_url=client.user.avatar_url)
        lrole2 = discord.Embed()
        lrole2.set_author(name="Role Update!!",icon_url=client.user.avatar_url)
        lrole2.set_thumbnail(url=client.user.avatar_url)
        lrole2.add_field(name="(^=˃ᆺ˂)",value="\nHey <@USER1> | <@&Role1> \n\n**" + mention + "** Has Joined **Vendetta** From Another Guild\nThey They Have Been Given The Role " + mentionr2 + " And Told To Change Their Nickname",inline=False)
        lrole2.set_footer(text='VendettaBot/Limbo', icon_url=client.user.avatar_url)
        await client.replace_roles(user, role2)
        await client.send_message(user,embed=erole2)
        await client.send_message(logchannel,embed=lrole2)
    elif str(reaction.emoji) == "\U0001F4D8":
        role3 = discord.utils.get(user.server.roles, name="Friends")
        mentionr3 = role3.mention
        erole3 = discord.Embed()
        erole3.set_author(name="Welcome To Vendetta",icon_url=client.user.avatar_url)
        erole3.set_thumbnail(url=client.user.avatar_url)
        erole3.add_field(name="Friend",value="Hey **" + mention + "**, Welcome to **Vendetta** \uD83E\uDD17\uD83C\uDF89 !",inline=False)
        erole3.add_field(name="Contact Guild Master",value="<@>",inline=False)
        erole3.add_field(name="Contact Officers",value="<@&>",inline=False)
        erole3.add_field(name="BOT HELP",value="Type !help in <#GEAR CHANNEL ID>",inline=False) #insert channel ID here
        erole3.set_footer(text='Congrats, You Are No Longer In Limbo', icon_url=client.user.avatar_url)
        lrole3 = discord.Embed()
        lrole3.set_author(name="Role Update!!",icon_url=client.user.avatar_url)
        lrole3.set_thumbnail(url=client.user.avatar_url)
        lrole3.add_field(name="(^=˃ᆺ˂)",value="\nHey <@USER1> | <@&Role1> \n\n**" + mention + " ** Has Joined **Vendetta** As " + mentionr3 ,inline=False)
        lrole3.set_footer(text='VendettaBot/Limbo', icon_url=client.user.avatar_url)
        await client.replace_roles(user, role3)
        await client.send_message(user,embed=erole3)
        await client.send_message(logchannel,embed=lrole3)


        #help embed

   # elif str(reaction.emoji) == "\U0001F4D5":
      #  rules = discord.Embed()
       # rules.set_author(name="**RULES:**",icon_url=client.user.avatar_url)
       # rules.set_thumbnail(url=client.user.avatar_url)
      #  rules.add_field(name="**1)** Morals -",value="Have Courage, Discipline, Respect, Integrity, Loyalty, Selfless Commitment and above all take Pride in being a Member of Vendetta!",inline=False)
      #  rules.add_field(name="**2)** Honesty -",value="Be Honest in all situations and do not ever Lie to another member of Vendetta!",inline=False)
       # rules.add_field(name="**3)** Discord -",value="Please use the correct channels for whatever it may be.",inline=False)
       # rules.add_field(name="**4)** Strength - ",value="The guild is only as Strong as it's members, support those around you and help strengthen our ranks!",inline=False)
       # rules.add_field(name="**5)** Toxicicity -",value="There is no tolerance for Toxic Members.",inline=False)
      #  rules.set_footer(text='BOT HELP', icon_url=client.user.avatar_url)
     #   await client.send_message(user,embed=rules)

async def show_war_embed(channel,list,date):
    embed = discord.Embed()
    embed.set_thumbnail(url=client.user.avatar_url)
    embed.set_author(name="{} Nodewar Attendance".format(date),icon_url=client.user.avatar_url)
    for i in range(len(list)):
        embed.add_field(name="{}".format(list[i]),value='\u200b',inline=False)
    embed.set_footer(text="OwO Bot", icon_url=client.user.avatar_url)
    await client.send_message(channel,embed=embed)

async def chat_del(channel): #cleares limbo channel everytime bot is launched 
    async for msg in client.logs_from(channel):
      await client.delete_message(msg)

@client.event
async def on_member_join(member):
    mention = member.mention
    membed = discord.Embed()
    membed.set_author(name="Choose Your Destiny!!",icon_url=client.user.avatar_url)
    membed.set_thumbnail(url=client.user.avatar_url)
    membed.add_field(name="You **Must** Choose A Side! Or Remain In Limbo **Forever!**",value=mention,inline=False)
    membed.add_field(name="Where To Go!",value="<#LimboID>",inline=False) # ID to limbo channel
    membed.set_footer(text='Welcome To Limbo!!', icon_url="https://cdn.discordapp.com/avatars/170960401926848513/9f942640cfc9648d808b2ae9cfae4b7c.png?size=128")
    await client.send_message(member,embed=membed)


client.run('') #insert token ID here
