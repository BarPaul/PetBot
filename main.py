import disnake
import disnake.state
from constants import *
from disnake.ext import commands
from database import Database, User
from random import randint
from math import e
from datetime import datetime

db = Database()
bot = commands.InteractionBot(
    intents=disnake.Intents.all(), 
    sync_commands_debug=True, 
    activity=disnake.Game(name="Visual Studio Code"), 
    status=disnake.Status.do_not_disturb
)


@bot.slash_command(name="pet", description="Информация о вашем питомце")
async def pet(ctx: disnake.ApplicationCommandInteraction, 
            member: disnake.Member=commands.Param(description="Узнать информацию о питомцах других пользователей", default=None)):    
    if member is not None and not db.is_user(member.id):
        return await ctx.response.send_message(f"У пользователя {member.name} нет питомца")
    elif member is None and not db.is_user(ctx.user.id):
        return await select_menu(ctx, f"У тебя нет питомца\nВыбери одного из них:")
    member = ctx.user if member is None else member
    user = db.get_user(member.id) 
    character = CHARACTERS[user.pet_type]
    embed = disnake.Embed(
        title="Информация о твоем питомце" if member == ctx.user else f"Информация о питомце пользователя {member.global_name.title()}", 
        timestamp=datetime.now(), 
        colour=disnake.Colour.from_rgb(212, 83, 208)
    )
    embed.add_field(name="Питомец", value=f"{character["emoji"]} {character["name"]}")
    embed.add_field(name="Уровень", value=str(user.level))
    embed.add_field(name="Бодрость", value=f"{user.energy}%")
    embed.add_field(name="Опыт", value=f"{user.xp}/{db.get_xp(user)}")
    embed.add_field(name="Баланс", value=f"{user.money} гошек")
    return await ctx.response.send_message(embed=embed, components=get_components(user) if member == ctx.user else [])

@bot.slash_command(name="leaderboard", decription="Посмотреть ТОП-10")
async def leaderboard(ctx: disnake.ApplicationCommandInteraction):
    # print(*db.get_leaderboard('money'), sep='\n')
    # print(*db.get_leaderboard('level'), sep='\n')
    await ctx.response.send_message("Hi", ephemeral=True)


@bot.event
async def on_ready():
    print("Bot online!")


@bot.event
async def on_dropdown(inter: disnake.MessageInteraction):
    match inter.component.custom_id:
        case "choice_pet":
            if db.is_user(inter.user.id):
                return await inter.response.send_message(f"{inter.user.global_name.title()} у тебя уже есть питомец!")
            db.insert_user(User(inter.user.id, inter.resolved_values[0], 1, 0, 100, 0))
            await inter.response.send_message(f"{inter.user.global_name.title()} получил нового питомца!")
        case "choice_pet_reset":
            db.delete_user(inter.user.id)
            db.insert_user(User(inter.user.id, inter.resolved_values[0], 1, 0, 100, 0))
            await inter.response.send_message(f"{inter.user.global_name.title()} поменял питомца")

@bot.event
async def on_button_click(inter: disnake.MessageInteraction):
    if data := list(filter(str.isdigit, inter.component.custom_id.split("_"))):
        if inter.user.id != int(data[-1]):
            return await inter.response.send_message("Не твое - не трогай", ephemeral=True)
    
    match inter.component.custom_id: 
        case exp if exp == f"change_pet_{inter.user.id}":
            await select_menu(inter, f"Выбери на кого заменить\n**НО УЧИТЫВАЙТЕ, ЧТО ДАННЫЕ ПИТОМЦА УДАЛЯТСЯ**", True)
        case exp if exp.startswith("work") or exp.startswith("rest"):
            do, pid, uid = exp.split("_")
            uid = int(uid)
            user = db.get_user(uid)
            await inter.response.defer(with_message=True, ephemeral=True)
            if db.is_calldown(uid, do) and inter.user.id not in ADMIN_IDS:
                return await inter.followup.send(f"Возращайтесь <t:{db.get_timer(uid, do)}:R>")
            elif do == "work":
                if user.energy >= 22:
                    need_energy, get_xp = randint(10, user.energy // 2), randint(1, 10 + int(5 * (user.xp / 1000)))
                    money = int((user.level ** 0.5 + randint(1, 4)) ** e)
                    return await work(inter, db, pid, need_energy, get_xp, money)
                await inter.followup.send("У твоего питомца недостаточно бодрости! Ему нужен отдых...")
            elif do == "rest":
                if user.energy < 90:
                    return await rest(inter, db, pid, randint(int((1.5 * user.energy) ** 0.5), 100 - user.energy))
                await inter.followup.send("Твой питомец уже полон сил", ephemeral=True)
        case "shop":
            await inter.followup.send("Coming soon...", ephemeral=True)



if __name__ == '__main__':
    bot.run(TOKEN)
