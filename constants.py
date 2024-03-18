from dotenv import load_dotenv, find_dotenv
from random import choice, choices
from disnake import ui, ButtonStyle, Embed, Color
from json import load
from os import getenv

load_dotenv(find_dotenv())
with open("characters.json", encoding="utf-8") as f:
    CHARACTERS, TOKEN = load(f), getenv("TOKEN")
with open("works.json", encoding="utf-8") as f:
    WORKS = load(f)
ADMIN_IDS = [1084900263611088948]


async def select_menu(ctx, reason, reset=False):
    select = ui.StringSelect(placeholder="Выберите питомца", max_values=1, custom_id="choice_pet_reset" if reset else "choice_pet")
    for pid, data in CHARACTERS.items():
        select.add_option(label=data["name"], emoji=data["emoji"], value=pid)
    return await ctx.response.send_message(reason, view=ui.View().add_item(select), ephemeral=True)   


get_components = lambda user: [
    [ui.Button(label="Работа", emoji="🧑‍🏭", style=ButtonStyle.success, custom_id=f"work_{user.pet_type}_{user.id}"),
    ui.Button(label="Отдых", emoji="😴", style=ButtonStyle.blurple, custom_id=f"rest_{user.pet_type}_{user.id}")],
    [ui.Button(label="Сменить", emoji="🔁", style=ButtonStyle.danger, custom_id=f"change_pet_{user.id}"),
    ui.Button(label="Магазин", emoji="🛍️", style=ButtonStyle.grey, custom_id="shop")]
]

async def work(inter, db, pid: str, energy: int, xp: int, money: int):
    emotion = choices(["good", "bad"], weights=[40, 60])[0]
    user = db.get_user(inter.user.id)
    user.energy -= energy
    user.xp += xp
    user.money += money
    data = choice(WORKS[pid][emotion])
    part_2 = f"\n⚡ Бодрость: -{energy}%\n🧪 Опыт: +{xp}\n🏦 Баланс: +{money} гошек" 
    work = Embed(
        title=data["title"],
        description=data["description"] + part_2, 
        color=Color.from_rgb(97, 193, 1)
    )
    if emotion == "bad":
        user.xp -= xp
        user.money -= money
        work.color = Color.from_rgb(193, 1, 1)
        work.description = '\n'.join(work.description.splitlines()[:-2] + ["❌ Опыт: не начислен", "❌ Баланс: не начислен"])
    work.set_footer(text="Возращайтесь через полчаса")
    await inter.followup.send(embed=work)
    db.add_timer(inter.user.id, 1800, "work")
    db.level_up(user)

async def rest(inter, db, pid: str, energy: int):
    user = db.get_user(inter.user.id)
    user.energy += energy
    db.update_user(user)
    rest = Embed(
        title="Время отдыха",
        description=f"{CHARACTERS[pid]["emoji"]} {CHARACTERS[pid]["name"]} хорошенько отдохнул и получил {energy}% бодрости",
        color=Color.from_rgb(97, 193, 1)
    )
    rest.set_footer(text="Возращайтесь через 2 часа")
    await inter.followup.send(embed=rest)
    db.add_timer(inter.user.id, 7200, "rest")
