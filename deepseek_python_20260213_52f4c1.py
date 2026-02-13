import asyncio
import random
import logging
import json
import os
import math
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta
import time

# --- Конфигурация ---
BOT_TOKEN = "8447136346:AAGoxtuNONZGIn0fldfzITHSA4y0wANbJq4"
ADMIN_PASSWORD = "1847184"
ADMIN_IDS = []

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Хранилище игр и статистики ---
games = {}
crash_games = {}
twenty_one_games = {}
dice_games = {}
quack_games = {}
hilo_games = {}
tournaments = {}
shop_items = {}
daily_bonus_tracker = {}

STATS_FILE = "player_stats.json"
BANNED_FILE = "banned_users.json"
REFERRAL_FILE = "referrals.json"
TOURNAMENT_FILE = "tournaments.json"
ACHIEVEMENTS_FILE = "achievements.json"
next_game_id = 1

# --- Загрузка и сохранение данных ---
def load_json(filename, default):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_banned(): return load_json(BANNED_FILE, [])
def save_banned(data): save_json(BANNED_FILE, data)
def load_stats(): return load_json(STATS_FILE, {})
def save_stats(data): save_json(STATS_FILE, data)
def load_referrals(): return load_json(REFERRAL_FILE, {})
def save_referrals(data): save_json(REFERRAL_FILE, data)
def load_tournaments(): return load_json(TOURNAMENT_FILE, {})
def save_tournaments(data): save_json(TOURNAMENT_FILE, data)
def load_achievements(): return load_json(ACHIEVEMENTS_FILE, {})
def save_achievements(data): save_json(ACHIEVEMENTS_FILE, data)

# --- Баны ---
def is_banned(user_id):
    banned = load_banned()
    return str(user_id) in banned

def ban_user(user_id, admin_id, reason=""):
    banned = load_banned()
    user_id_str = str(user_id)
    
    if user_id_str not in banned:
        banned.append(user_id_str)
        save_banned(banned)
        log_ban(user_id_str, admin_id, reason)
        return True
    return False

def unban_user(user_id):
    banned = load_banned()
    user_id_str = str(user_id)
    
    if user_id_str in banned:
        banned.remove(user_id_str)
        save_banned(banned)
        return True
    return False

def log_ban(user_id, admin_id, reason=""):
    log_entry = {
        'user_id': user_id,
        'admin_id': admin_id,
        'reason': reason,
        'timestamp': datetime.now().isoformat()
    }
    
    log_file = "ban_log.json"
    logs = load_json(log_file, [])
    logs.append(log_entry)
    save_json(log_file, logs)

# --- Статистика игроков ---
def update_player_stats(user_id, username, first_name, balance_change=0, games_played=0, games_won=0, game_type="mines"):
    stats = load_stats()
    user_id = str(user_id)
    
    if user_id not in stats:
        stats[user_id] = {
            'username': username,
            'first_name': first_name,
            'balance': 1000,
            'games_played': 0,
            'games_won': 0,
            'mines_played': 0,
            'mines_won': 0,
            'crash_played': 0,
            'crash_won': 0,
            'twentyone_played': 0,
            'twentyone_won': 0,
            'dice_played': 0,
            'dice_won': 0,
            'quack_played': 0,
            'quack_won': 0,
            'hilo_played': 0,
            'hilo_won': 0,
            'referrals': 0,
            'referral_earnings': 0,
            'daily_streak': 0,
            'last_daily': None,
            'achievements': [],
            'tournament_points': 0,
            'highest_multiplier': 0,
            'total_bet': 0,
            'total_win': 0,
            'last_played': datetime.now().isoformat()
        }
    
    stats[user_id]['balance'] += balance_change
    stats[user_id]['games_played'] += games_played
    stats[user_id]['games_won'] += games_won
    
    if balance_change > 0:
        stats[user_id]['total_win'] += balance_change
    elif balance_change < 0:
        stats[user_id]['total_bet'] += abs(balance_change)
    
    if game_type == "mines":
        stats[user_id]['mines_played'] += games_played
        stats[user_id]['mines_won'] += games_won
    elif game_type == "crash":
        stats[user_id]['crash_played'] += games_played
        stats[user_id]['crash_won'] += games_won
    elif game_type == "twentyone":
        stats[user_id]['twentyone_played'] += games_played
        stats[user_id]['twentyone_won'] += games_won
    elif game_type == "dice":
        stats[user_id]['dice_played'] += games_played
        stats[user_id]['dice_won'] += games_won
    elif game_type == "quack":
        stats[user_id]['quack_played'] += games_played
        stats[user_id]['quack_won'] += games_won
    elif game_type == "hilo":
        stats[user_id]['hilo_played'] += games_played
        stats[user_id]['hilo_won'] += games_won
    
    stats[user_id]['last_played'] = datetime.now().isoformat()
    stats[user_id]['username'] = username
    
    if stats[user_id]['balance'] < 0:
        stats[user_id]['balance'] = 0
    
    save_stats(stats)
    
    # Проверяем достижения
    check_achievements(user_id)
    
    return stats[user_id]

def update_crash_stats(user_id, username, first_name, balance_change=0, games_played=0, games_won=0, multiplier=0):
    stats = load_stats()
    user_id = str(user_id)
    
    if user_id not in stats:
        stats[user_id] = {
            'username': username,
            'first_name': first_name,
            'balance': 1000,
            'games_played': 0,
            'games_won': 0,
            'crash_played': 0,
            'crash_won': 0,
            'highest_multiplier': 0,
            'last_played': datetime.now().isoformat()
        }
    
    stats[user_id]['balance'] += balance_change
    stats[user_id]['crash_played'] += games_played
    stats[user_id]['crash_won'] += games_won
    
    if multiplier > stats[user_id]['highest_multiplier']:
        stats[user_id]['highest_multiplier'] = multiplier
    
    stats[user_id]['last_played'] = datetime.now().isoformat()
    
    if stats[user_id]['balance'] < 0:
        stats[user_id]['balance'] = 0
    
    save_stats(stats)
    return stats[user_id]

def get_top_players(limit=10):
    stats = load_stats()
    sorted_players = sorted(
        stats.items(), 
        key=lambda x: x[1]['balance'], 
        reverse=True
    )[:limit]
    return sorted_players

def get_player_info(user_id):
    stats = load_stats()
    user_id_str = str(user_id)
    if user_id_str in stats:
        return stats[user_id_str]
    return None

def set_player_balance(user_id, new_balance):
    stats = load_stats()
    user_id_str = str(user_id)
    if user_id_str in stats:
        stats[user_id_str]['balance'] = new_balance
        save_stats(stats)
        return True
    return False

# --- Достижения ---
def check_achievements(user_id):
    stats = load_stats()
    user_id = str(user_id)
    achievements = stats[user_id].get('achievements', [])
    new_achievements = []
    
    achievement_list = [
        {"id": "first_win", "name": "Первая победа", "desc": "Выиграй первую игру", "check": lambda s: s['games_won'] >= 1},
        {"id": "big_winner", "name": "Крупный победитель", "desc": "Выиграй 100 игр", "check": lambda s: s['games_won'] >= 100},
        {"id": "millionaire", "name": "Миллионер", "desc": "Накопи 1,000,000 worlc", "check": lambda s: s['balance'] >= 1000000},
        {"id": "high_roller", "name": "Хайроллер", "desc": "Сделай ставку 10,000 worlc", "check": lambda s: s.get('total_bet', 0) >= 10000},
        {"id": "crash_master", "name": "Мастер краша", "desc": "Поймай множитель x100", "check": lambda s: s.get('highest_multiplier', 0) >= 100},
        {"id": "referral_god", "name": "Бог рефералов", "desc": "Пригласи 10 друзей", "check": lambda s: s.get('referrals', 0) >= 10},
        {"id": "daily_streak_7", "name": "Недельный стрик", "desc": "Забирай ежедневный бонус 7 дней подряд", "check": lambda s: s.get('daily_streak', 0) >= 7},
    ]
    
    for ach in achievement_list:
        if ach["id"] not in achievements and ach["check"](stats[user_id]):
            achievements.append(ach["id"])
            new_achievements.append(ach)
    
    if new_achievements:
        stats[user_id]['achievements'] = achievements
        save_stats(stats)
    
    return new_achievements

# --- Реферальная система ---
def add_referral(referrer_id, user_id):
    referrals = load_referrals()
    referrer_id = str(referrer_id)
    user_id = str(user_id)
    
    if referrer_id not in referrals:
        referrals[referrer_id] = []
    
    if user_id not in referrals[referrer_id]:
        referrals[referrer_id].append(user_id)
        save_referrals(referrals)
        
        # Начисляем бонус рефереру
        stats = load_stats()
        if referrer_id in stats:
            stats[referrer_id]['referrals'] = len(referrals[referrer_id])
            stats[referrer_id]['balance'] += 100  # Бонус за реферала
            stats[referrer_id]['referral_earnings'] += 100
            save_stats(stats)
        
        return True
    return False

def get_referrals(user_id):
    referrals = load_referrals()
    return referrals.get(str(user_id), [])

# --- Ежедневный бонус ---
def claim_daily_bonus(user_id):
    stats = load_stats()
    user_id = str(user_id)
    
    if user_id not in stats:
        return None
    
    now = datetime.now()
    last_daily = stats[user_id].get('last_daily')
    
    if last_daily:
        last_date = datetime.fromisoformat(last_daily)
        if last_date.date() == now.date():
            return None  # Уже сегодня забирал
        
        # Проверяем стрик
        if (now.date() - last_date.date()).days == 1:
            stats[user_id]['daily_streak'] += 1
        else:
            stats[user_id]['daily_streak'] = 1
    else:
        stats[user_id]['daily_streak'] = 1
    
    # Расчет бонуса
    streak = stats[user_id]['daily_streak']
    bonus = 100 * streak
    
    stats[user_id]['balance'] += bonus
    stats[user_id]['last_daily'] = now.isoformat()
    save_stats(stats)
    
    return bonus, streak

# --- Магазин ---
def init_shop():
    shop = {}
    shop["daily_double"] = {
        "name": "🎰 Daily Double",
        "description": "Удвой свой ежедневный бонус навсегда",
        "price": 5000,
        "type": "upgrade",
        "effect": "daily_double"
    }
    shop["extra_life"] = {
        "name": "❤️ Дополнительная жизнь",
        "description": "Один раз избежишь проигрыша в Mines",
        "price": 2000,
        "type": "consumable",
        "effect": "mines_extra_life"
    }
    return shop

shop_items = init_shop()

# --- Турниры ---
class Tournament:
    def __init__(self, tour_id, name, prize_pool, start_time, end_time, min_bet=0):
        self.tour_id = tour_id
        self.name = name
        self.prize_pool = prize_pool
        self.start_time = start_time
        self.end_time = end_time
        self.min_bet = min_bet
        self.leaderboard = {}
        self.active = True
    
    def add_score(self, user_id, points):
        if not self.active or datetime.now() < self.start_time or datetime.now() > self.end_time:
            return False
        if points < self.min_bet:
            return False
        
        user_id = str(user_id)
        if user_id in self.leaderboard:
            self.leaderboard[user_id] += points
        else:
            self.leaderboard[user_id] = points
        
        return True
    
    def get_leaderboard(self, limit=10):
        sorted_players = sorted(
            self.leaderboard.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        return sorted_players
    
    def end_tournament(self):
        self.active = False
        winners = self.get_leaderboard(3)
        
        prizes = {
            1: int(self.prize_pool * 0.5),
            2: int(self.prize_pool * 0.3),
            3: int(self.prize_pool * 0.2)
        }
        
        stats = load_stats()
        for i, (user_id, points) in enumerate(winners, 1):
            if i <= 3 and user_id in stats:
                stats[user_id]['balance'] += prizes[i]
                stats[user_id]['tournament_points'] = stats[user_id].get('tournament_points', 0) + points
                save_stats(stats)
        
        return winners, prizes

# --- Логика сапера (Mines) ---
def create_mines(rows=5, cols=5, mines_count=5):
    board = [[0 for _ in range(cols)] for _ in range(rows)]
    positions = [(r, c) for r in range(rows) for c in range(cols)]
    mine_positions = random.sample(positions, mines_count)
    
    for r, c in mine_positions:
        board[r][c] = -1
    
    for r, c in mine_positions:
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] != -1:
                    board[nr][nc] += 1
    return board

def generate_keyboard(board, opened, game_id):
    kb_builder = InlineKeyboardBuilder()
    rows = len(board)
    cols = len(board[0])
    
    for i in range(rows):
        row_buttons = []
        for j in range(cols):
            cell_id = f"{game_id}:{i}:{j}"
            if opened[i][j]:
                value = board[i][j]
                if value == -1:
                    text = "💣"
                elif value == 0:
                    text = "⬜"
                else:
                    text = str(value)
                row_buttons.append(InlineKeyboardButton(text=text, callback_data="opened"))
            else:
                row_buttons.append(InlineKeyboardButton(text="⬛", callback_data=cell_id))
        kb_builder.row(*row_buttons)
    return kb_builder.as_markup()

# --- Логика Crash Game ---
def generate_crash_multiplier():
    r = random.random()
    if r < 0.7:
        return round(random.uniform(1.01, 2.0), 2)
    elif r < 0.9:
        return round(random.uniform(2.01, 5.0), 2)
    elif r < 0.97:
        return round(random.uniform(5.01, 20.0), 2)
    elif r < 0.995:
        return round(random.uniform(20.01, 100.0), 2)
    else:
        return round(random.uniform(100.01, 10000.0), 2)

def get_rocket_animation(multiplier, current_multiplier):
    if multiplier == 0:
        return "🚀·····"
    
    progress = min(current_multiplier / multiplier, 1.0)
    
    if progress < 0.2:
        return "🚀·····"
    elif progress < 0.4:
        return "·🚀····"
    elif progress < 0.6:
        return "··🚀···"
    elif progress < 0.8:
        return "···🚀··"
    elif progress < 1.0:
        return "····🚀·"
    else:
        return "·····💥"

async def crash_game_loop(game_id):
    game = crash_games.get(game_id)
    if not game:
        return
    
    multiplier = game['crash_point']
    start_time = time.time()
    game_duration = 15
    
    while game['active'] and time.time() - start_time < game_duration:
        elapsed = time.time() - start_time
        progress = elapsed / game_duration
        current_multiplier = round(1.0 + (multiplier - 1.0) * progress, 2)
        
        game['current_multiplier'] = current_multiplier
        rocket = get_rocket_animation(multiplier, current_multiplier)
        
        if current_multiplier >= multiplier:
            game['active'] = False
            game['crashed'] = True
            
            for user_id in list(game['bets'].keys()):
                if not game['bets'][user_id]['cashed_out']:
                    update_crash_stats(
                        int(user_id),
                        game['bets'][user_id]['username'],
                        game['bets'][user_id]['first_name'],
                        balance_change=-game['bets'][user_id]['bet_amount'],
                        games_played=1,
                        games_won=0,
                        multiplier=multiplier
                    )
            
            await game['message'].edit_text(
                f"💥 *КРАШ!*\n\n"
                f"Ракета взорвалась на x{multiplier:.2f}!\n\n"
                f"{rocket}\n\n"
                f"💸 Все кто не успел забрать - проиграли!\n\n"
                f"Начните новую игру: /crash [сумма]",
                parse_mode="Markdown"
            )
            break
        else:
            players_text = ""
            for user_id, bet_info in game['bets'].items():
                status = "✅" if bet_info['cashed_out'] else "⏳"
                if bet_info['cashed_out']:
                    win_amount = int(bet_info['bet_amount'] * bet_info['cashed_multiplier'])
                    players_text += f"{status} {bet_info['first_name']}: {bet_info['bet_amount']} worlc → {win_amount} worlc (x{bet_info['cashed_multiplier']:.2f})\n"
                else:
                    players_text += f"{status} {bet_info['first_name']}: {bet_info['bet_amount']} worlc\n"
            
            # Участие в турнирах
            for user_id in game['bets'].keys():
                for tour_id, tour in tournaments.items():
                    if tour.active:
                        tour.add_score(int(user_id), bet_info['bet_amount'])
            
            await game['message'].edit_text(
                f"🚀 *CRASH GAME*\n\n"
                f"Текущий множитель: *x{current_multiplier:.2f}*\n"
                f"Ракета: {rocket}\n\n"
                f"📊 *Ставки:*\n{players_text}\n"
                f"Нажми /cashout чтобы забрать выигрыш!",
                parse_mode="Markdown"
            )
        
        await asyncio.sleep(0.5)
    
    if game and game['active']:
        game['active'] = False
        game['crashed'] = True
        
        for user_id in list(game['bets'].keys()):
            if not game['bets'][user_id]['cashed_out']:
                update_crash_stats(
                    int(user_id),
                    game['bets'][user_id]['username'],
                    game['bets'][user_id]['first_name'],
                    balance_change=-game['bets'][user_id]['bet_amount'],
                    games_played=1,
                    games_won=0,
                    multiplier=multiplier
                )
        
        await game['message'].edit_text(
            f"💥 *КРАШ! Время вышло!*\n\n"
            f"Ракета взорвалась на x{multiplier:.2f}!",
            parse_mode="Markdown"
        )

# --- Логика игры 21 (Очко) ---
class TwentyOneGame:
    def __init__(self, user_id, bet_amount):
        self.user_id = user_id
        self.bet_amount = bet_amount
        self.player_cards = []
        self.dealer_cards = []
        self.player_score = 0
        self.dealer_score = 0
        self.active = True
        self.player_turn = True
        self.result = None
        
        self.deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4
        random.shuffle(self.deck)
        
        self.player_cards.append(self.deck.pop())
        self.dealer_cards.append(self.deck.pop())
        self.player_cards.append(self.deck.pop())
        self.dealer_cards.append(self.deck.pop())
        
        self.update_scores()
    
    def update_scores(self):
        self.player_score = self.calculate_score(self.player_cards)
        self.dealer_score = self.calculate_score(self.dealer_cards)
    
    def calculate_score(self, cards):
        score = sum(cards)
        while score > 21 and 11 in cards:
            cards[cards.index(11)] = 1
            score = sum(cards)
        return score
    
    def player_hit(self):
        if not self.player_turn or not self.active:
            return False
        self.player_cards.append(self.deck.pop())
        self.update_scores()
        
        if self.player_score > 21:
            self.player_turn = False
            self.active = False
            self.result = "lose"
        return True
    
    def player_stand(self):
        if not self.player_turn or not self.active:
            return False
        self.player_turn = False
        self.dealer_play()
        return True
    
    def dealer_play(self):
        while self.dealer_score < 17:
            self.dealer_cards.append(self.deck.pop())
            self.update_scores()
        
        self.active = False
        if self.dealer_score > 21:
            self.result = "win"
        elif self.player_score > self.dealer_score:
            self.result = "win"
        elif self.player_score < self.dealer_score:
            self.result = "lose"
        else:
            self.result = "push"
    
    def get_result(self):
        if self.result == "win":
            return "win", self.bet_amount * 2
        elif self.result == "lose":
            return "lose", 0
        else:
            return "push", self.bet_amount
    
    def get_cards_text(self):
        player_cards_text = " + ".join([str(c) for c in self.player_cards])
        dealer_cards_text = " + ".join([str(c) for c in self.dealer_cards]) if not self.player_turn else f"{self.dealer_cards[0]} + ?"
        return player_cards_text, dealer_cards_text

def twentyone_keyboard(game_id):
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(
        InlineKeyboardButton(text="🎯 Ещё", callback_data=f"21_hit:{game_id}"),
        InlineKeyboardButton(text="⏹️ Хватит", callback_data=f"21_stand:{game_id}")
    )
    return kb_builder.as_markup()

# --- Логика игры Кости ---
class DiceGame:
    def __init__(self, user_id, bet_amount):
        self.user_id = user_id
        self.bet_amount = bet_amount
        self.player_roll = 0
        self.bot_roll = 0
        self.result = None
        self.active = True
    
    def roll(self):
        self.player_roll = random.randint(1, 6)
        self.bot_roll = random.randint(1, 6)
        
        if self.player_roll > self.bot_roll:
            self.result = "win"
        elif self.player_roll < self.bot_roll:
            self.result = "lose"
        else:
            self.result = "push"
        
        self.active = False
        return self.player_roll, self.bot_roll
    
    def get_result(self):
        if self.result == "win":
            return "win", self.bet_amount * 2
        elif self.result == "lose":
            return "lose", 0
        else:
            return "push", self.bet_amount

# --- Логика игры Квак ---
class QuackGame:
    def __init__(self, user_id, bet_amount):
        self.user_id = user_id
        self.bet_amount = bet_amount
        self.position = 0
        self.target = random.randint(0, 9)
        self.multiplier = 1.0
        self.active = True
        self.steps = 0
    
    def quack(self):
        if not self.active:
            return False
        
        self.steps += 1
        self.position = random.randint(0, 9)
        self.multiplier = round(1.0 + (self.steps * 0.2), 2)
        
        if self.position == self.target:
            self.active = False
            return "win", self.multiplier
        elif self.steps >= 10:
            self.active = False
            return "lose", self.multiplier
        
        return "continue", self.multiplier

def quack_keyboard(game_id):
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(
        InlineKeyboardButton(text="🦆 КВАК!", callback_data=f"quack_do:{game_id}"),
        InlineKeyboardButton(text="💰 Забрать", callback_data=f"quack_take:{game_id}")
    )
    return kb_builder.as_markup()

def get_quack_animation(position, target):
    line = ["⬜"] * 10
    if position < len(line):
        line[position] = "🦆"
    if target < len(line) and target != position:
        line[target] = "🎯"
    
    return "".join(line)

# --- Логика игры Хило ---
class HiLoGame:
    def __init__(self, user_id, bet_amount):
        self.user_id = user_id
        self.bet_amount = bet_amount
        self.current_card = random.randint(1, 13)
        self.next_card = None
        self.multiplier = 1.0
        self.active = True
        self.rounds = 0
        self.max_rounds = 8
        self.result = None
        
        self.card_names = {
            1: "Туз",
            2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 10: "10",
            11: "Валет",
            12: "Дама",
            13: "Король"
        }
    
    def get_card_name(self, card_value):
        return self.card_names.get(card_value, str(card_value))
    
    def guess(self, choice):
        if not self.active:
            return False
        
        self.next_card = random.randint(1, 13)
        self.rounds += 1
        
        if choice == "higher":
            if self.next_card > self.current_card:
                self.multiplier = round(1.0 + (self.rounds * 0.5), 2)
                self.current_card = self.next_card
                if self.rounds >= self.max_rounds:
                    self.active = False
                    self.result = "win"
                return "win", self.multiplier
            elif self.next_card < self.current_card:
                self.active = False
                self.result = "lose"
                return "lose", self.multiplier
            else:
                self.multiplier = round(1.0 + (self.rounds * 0.5), 2)
                self.active = False
                self.result = "lose"
                return "lose", self.multiplier
        else:
            if self.next_card < self.current_card:
                self.multiplier = round(1.0 + (self.rounds * 0.5), 2)
                self.current_card = self.next_card
                if self.rounds >= self.max_rounds:
                    self.active = False
                    self.result = "win"
                return "win", self.multiplier
            elif self.next_card > self.current_card:
                self.active = False
                self.result = "lose"
                return "lose", self.multiplier
            else:
                self.multiplier = round(1.0 + (self.rounds * 0.5), 2)
                self.active = False
                self.result = "lose"
                return "lose", self.multiplier
    
    def get_result(self):
        if self.result == "win":
            return "win", int(self.bet_amount * self.multiplier)
        else:
            return "lose", 0

def hilo_keyboard(game_id):
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(
        InlineKeyboardButton(text="⬆️ Выше", callback_data=f"hilo_higher:{game_id}"),
        InlineKeyboardButton(text="⬇️ Ниже", callback_data=f"hilo_lower:{game_id}")
    )
    kb_builder.row(
        InlineKeyboardButton(text="💰 Забрать", callback_data=f"hilo_take:{game_id}")
    )
    return kb_builder.as_markup()

# --- Админ-панель ---
def admin_keyboard():
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(
        InlineKeyboardButton(text="💰 Выдать worlc", callback_data="admin_give_money"),
        InlineKeyboardButton(text="🔨 Забанить", callback_data="admin_ban")
    )
    kb_builder.row(
        InlineKeyboardButton(text="✅ Разбанить", callback_data="admin_unban"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
    )
    kb_builder.row(
        InlineKeyboardButton(text="👥 Список игроков", callback_data="admin_players"),
        InlineKeyboardButton(text="📝 Логи банов", callback_data="admin_ban_logs")
    )
    kb_builder.row(
        InlineKeyboardButton(text="🎮 Создать турнир", callback_data="admin_create_tournament"),
        InlineKeyboardButton(text="🔙 Выйти", callback_data="admin_exit")
    )
    return kb_builder.as_markup()

# --- Основные команды ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if is_banned(message.from_user.id):
        await message.answer("❌ Вы забанены в этом боте!")
        return
    
    user = message.from_user
    args = message.text.split()
    
    # Реферальная система
    if len(args) > 1 and args[1].isdigit():
        referrer_id = args[1]
        if str(referrer_id) != str(user.id):
            add_referral(referrer_id, user.id)
    
    update_player_stats(
        user.id, 
        user.username or "NoUsername", 
        user.first_name,
        balance_change=0
    )
    
    await message.answer(
        "🦆 *Добро пожаловать в Worlc Casino!*\n\n"
        "💰 *Система богатства:*\n"
        "• Каждый игрок начинает с 1000 worlc\n"
        "• Приглашай друзей и получай бонусы\n"
        "• Ежедневные бонусы за стрик\n\n"
        "🎮 *ИГРЫ:*\n\n"
        "💣 *MINES (Сапер):*\n"
        "• /newgame - Начать игру (5×5, 5 мин)\n"
        "• Победа: +100 worlc, Поражение: -50 worlc\n\n"
        "🚀 *CRASH (Ракета):*\n"
        "• /crash [сумма] - Сделать ставку\n"
        "• /cashout - Забрать выигрыш\n"
        "• Множитель растет до 10000x!\n\n"
        "🃏 *21 (Очко):*\n"
        "• /21 [сумма] - Игра против дилера\n\n"
        "🎲 *КОСТИ:*\n"
        "• /dice [сумма] - Кто выбросит больше?\n\n"
        "🦆 *КВАК:*\n"
        "• /quack [сумма] - Найди утку!\n\n"
        "⬆️ *ХИЛО:*\n"
        "• /hilo [сумма] - Угадай выше или ниже\n\n"
        "💰 *ДОПОЛНИТЕЛЬНО:*\n"
        "• /daily - Ежедневный бонус\n"
        "• /shop - Магазин\n"
        "• /tournaments - Турниры\n"
        "• /profile - Мой профиль\n"
        "• /referrals - Мои рефералы\n"
        "• /top - Топ богачей\n"
       