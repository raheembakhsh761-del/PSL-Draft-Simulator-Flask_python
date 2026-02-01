"""
PSL Draft Simulator - Enhanced Flask Web Application with File Handling

"""
#  main laburary use 
from flask import Flask, render_template, request, redirect, url_for, flash
from collections import deque
import secrets
import csv
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# File paths for data storage
PLAYERS_FILE = 'data/players.csv'
TEAMS_FILE = 'data/teams.csv'
TEAM_PLAYERS_FILE = 'data/team_players.csv'
DRAFT_STATE_FILE = 'data/draft_state.csv'

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# ======================
# PLAYER CLASS
# ======================
class Player:
    player_counter = 1001
    
    def __init__(self, name, rating, price, country="Pakistan", player_id=None):
        if player_id:
            self.id = player_id
        else:
            self.id = f"P{Player.player_counter}"
            Player.player_counter += 1
        self.name = name
        self.rating = rating
        self.price = price
        self.country = country
        self.is_picked = False
        self.category = self.get_category()
    
    def get_category(self):
        if self.rating > 90:
            return "Platinum"
        elif self.rating > 80:
            return "Diamond"
        elif self.rating > 60:
            return "Silver"
        elif self.rating > 50:
            return "Bronze"
        else:
            return "Emerging"
    
    def get_category_order(self):
        categories = {"Platinum": 1, "Diamond": 2, "Silver": 3, "Bronze": 4, "Emerging": 5}
        return categories.get(self.category, 6)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'rating': self.rating,
            'price': self.price,
            'country': self.country,
            'category': self.category,
            'is_picked': self.is_picked
        }


# ======================
# TEAM CLASS
# ======================
class Team:
    def __init__(self, name, max_points, max_budget, password):
        self.name = name
        self.max_points = max_points
        self.max_budget = max_budget
        self.password = password
        self.players = []
        self.current_points = 0
        self.current_budget = 0
        self.foreign_players = 0
        self.bought_categories = set()
        self.pre_draft_count = 0
    
    def can_add_player(self, player, is_pre_draft=False):
        if player.is_picked:
            return False, "Player already picked"
        if is_pre_draft and self.pre_draft_count >= 3:
            return False, "Pre-draft limit reached (max 3 players)"
        if self.current_points + player.rating > self.max_points:
            return False, f"Points limit exceeded (Need: {player.rating}, Available: {self.max_points - self.current_points})"
        if self.current_budget + player.price > self.max_budget:
            return False, f"Budget limit exceeded (Need: PKR {player.price:,}, Available: PKR {self.max_budget - self.current_budget:,})"
        if player.country != "Pakistan" and self.foreign_players >= 3:
            return False, "Foreign player limit reached (max 3)"
        if is_pre_draft and player.category in self.bought_categories:
            return False, "Category already taken in pre-draft"
        return True, "OK"
    
    def add_player(self, player, is_pre_draft=False):
        self.players.append(player)
        self.current_points += player.rating
        self.current_budget += player.price
        player.is_picked = True
        if player.country != "Pakistan":
            self.foreign_players += 1
        if is_pre_draft:
            self.bought_categories.add(player.category)
            self.pre_draft_count += 1
    
    def remove_player(self, player):
        self.players.remove(player)
        self.current_points -= player.rating
        self.current_budget -= player.price
        player.is_picked = False
        if player.country != "Pakistan":
            self.foreign_players -= 1
        if player.category in self.bought_categories:
            self.bought_categories.remove(player.category)
            self.pre_draft_count -= 1
    
    def update_budget(self, new_budget):
        if new_budget < self.current_budget:
            return False, f"Cannot set budget lower than current spending (PKR {self.current_budget:,})"
        self.max_budget = new_budget
        return True, "Budget updated successfully"


# ======================
# FILE HANDLING FUNCTIONS
# ======================
def save_players():
    """Save all players to CSV file"""
    with open(PLAYERS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'name', 'rating', 'price', 'country', 'is_picked'])
        for player in players:
            writer.writerow([
                player.id,
                player.name,
                player.rating,
                player.price,
                player.country,
                player.is_picked
            ])


def load_players():
    """Load players from CSV file"""
    global players, player_dict
    players = []
    player_dict = {}
    
    if not os.path.exists(PLAYERS_FILE):
        # Create default players if file doesn't exist
        players = create_demo_players()
        player_dict = {p.id: p for p in players}
        save_players()
        return
    
    with open(PLAYERS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        max_id = 1000
        for row in reader:
            player = Player(
                name=row['name'],
                rating=int(row['rating']),
                price=int(row['price']),
                country=row['country'],
                player_id=row['id']
            )
            player.is_picked = row['is_picked'] == 'True'
            players.append(player)
            player_dict[player.id] = player
            
            # Update counter
            id_num = int(row['id'][1:])
            if id_num > max_id:
                max_id = id_num
        
        Player.player_counter = max_id + 1


def save_teams():
    """Save team configurations to CSV file"""
    with open(TEAMS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'max_points', 'max_budget', 'password', 'current_points', 'current_budget', 'foreign_players', 'pre_draft_count'])
        for team in teams:
            writer.writerow([
                team.name,
                team.max_points,
                team.max_budget,
                team.password,
                team.current_points,
                team.current_budget,
                team.foreign_players,
                team.pre_draft_count
            ])


def load_teams():
    """Load teams from CSV file"""
    global teams
    
    if not os.path.exists(TEAMS_FILE):
        # Create default teams if file doesn't exist
        teams = [
            Team("Lahore Qalandars", 1000, 5000000, "lahore123"),
            Team("Karachi Kings", 1000, 5000000, "karachi123"),
            Team("Multan Sultans", 1000, 5000000, "multan123"),
            Team("Peshawar Zalmi", 1000, 5000000, "peshawar123"),
        ]
        save_teams()
        return
    
    teams = []
    with open(TEAMS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            team = Team(
                name=row['name'],
                max_points=int(row['max_points']),
                max_budget=int(row['max_budget']),
                password=row['password']
            )
            team.current_points = int(row['current_points'])
            team.current_budget = int(row['current_budget'])
            team.foreign_players = int(row['foreign_players'])
            team.pre_draft_count = int(row['pre_draft_count'])
            teams.append(team)


def save_team_players():
    """Save team-player assignments to CSV file"""
    with open(TEAM_PLAYERS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['team_name', 'player_id', 'category'])
        for team in teams:
            for player in team.players:
                writer.writerow([
                    team.name,
                    player.id,
                    player.category
                ])
                if player.category in ['Platinum', 'Diamond', 'Silver', 'Bronze', 'Emerging']:
                    team.bought_categories.add(player.category)


def load_team_players():
    """Load team-player assignments from CSV file"""
    if not os.path.exists(TEAM_PLAYERS_FILE):
        return
    
    # Clear existing players from teams
    for team in teams:
        team.players = []
        team.bought_categories = set()
    
    with open(TEAM_PLAYERS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Find team and player
            team = next((t for t in teams if t.name == row['team_name']), None)
            player = player_dict.get(row['player_id'])
            
            if team and player:
                team.players.append(player)
                player.is_picked = True
                team.bought_categories.add(row['category'])


def save_draft_state():
    """Save draft state to CSV file"""
    with open(DRAFT_STATE_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['draft_started', 'undo_stack'])
        writer.writerow([
            draft_started,
            '|'.join([f"{t},{p},{r}" for t, p, r in undo_stack])
        ])


def load_draft_state():
    """Load draft state from CSV file"""
    global draft_started, undo_stack
    
    if not os.path.exists(DRAFT_STATE_FILE):
        draft_started = False
        undo_stack = []
        return
    
    with open(DRAFT_STATE_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            draft_started = row['draft_started'] == 'True'
            if row['undo_stack']:
                undo_stack = []
                for item in row['undo_stack'].split('|'):
                    if item:
                        parts = item.split(',')
                        undo_stack.append((int(parts[0]), parts[1], int(parts[2])))
            else:
                undo_stack = []


# ======================
# INITIALIZE DATA
# ======================
def create_demo_players():
    return [
        Player("Babar Azam", 95, 500000),
        Player("Shaheen Afridi", 93, 480000),
        Player("Mohammad Rizwan", 92, 470000),
        Player("Naseem Shah", 88, 420000),
        Player("Haris Rauf", 87, 410000),
        Player("Shadab Khan", 85, 390000),
        Player("Fakhar Zaman", 82, 370000),
        Player("Saim Ayub", 78, 340000),
        Player("Imad Wasim", 75, 320000),
        Player("Usama Mir", 70, 280000),
    ]

# Global data - Load from files
players = []
player_dict = {}
teams = []
undo_stack = []
draft_queue = deque()
draft_started = False

# Load all data on startup
load_players()
load_teams()
load_team_players()
load_draft_state()

ADMIN_PASSWORD = "admin123"


# ======================
# HELPER FUNCTIONS
# ======================
def create_draft_queue(total_rounds=5):
    global draft_queue
    draft_queue.clear()
    num_teams = len(teams)
    for round_num in range(1, total_rounds + 1):
        if round_num % 2 == 1:
            for team_idx in range(num_teams):
                draft_queue.append((round_num, team_idx))
        else:
            for team_idx in range(num_teams - 1, -1, -1):
                draft_queue.append((round_num, team_idx))


def get_available_players():
    available = [p for p in players if not p.is_picked]
    return sorted(available, key=lambda p: (p.get_category_order(), -p.rating))


def get_all_players_sorted():
    return sorted(players, key=lambda p: (p.get_category_order(), -p.rating))


def get_category_color(category):
    colors = {
        'Platinum': '#E5E4E2',
        'Diamond': '#B9F2FF',
        'Silver': '#C0C0C0',
        'Bronze': '#CD7F32',
        'Emerging': '#90EE90'
    }
    return colors.get(category, '#FFFFFF')


def format_currency(amount):
    return f"PKR {amount:,}"


# ======================
# ROUTES
# ======================

@app.route('/')
def index():
    return render_template('index.html', teams=teams, draft_started=draft_started, format_currency=format_currency)


@app.route('/budget_allocation')
def budget_allocation():
    return render_template('budget_allocation.html', teams=teams, format_currency=format_currency, ADMIN_PASSWORD=ADMIN_PASSWORD)


@app.route('/update_team_budget', methods=['POST'])
def update_team_budget():
    admin_password = request.form.get('admin_password')
    team_idx = int(request.form.get('team_idx'))
    new_budget = request.form.get('new_budget')
    
    if admin_password != ADMIN_PASSWORD:
        flash('❌ Incorrect admin password', 'error')
        return redirect(url_for('budget_allocation'))
    
    try:
        new_budget = int(new_budget)
        if new_budget < 0:
            flash('❌ Budget cannot be negative', 'error')
            return redirect(url_for('budget_allocation'))
        
        team = teams[team_idx]
        success, message = team.update_budget(new_budget)
        
        if success:
            save_teams()  # Save after budget update
            flash(f'✅ {team.name} budget updated to {format_currency(new_budget)}', 'success')
        else:
            flash(f'❌ {message}', 'error')
    except ValueError:
        flash('❌ Invalid budget value', 'error')
    
    return redirect(url_for('budget_allocation'))


@app.route('/update_all_budgets', methods=['POST'])
def update_all_budgets():
    admin_password = request.form.get('admin_password')
    
    if admin_password != ADMIN_PASSWORD:
        flash('❌ Incorrect admin password', 'error')
        return redirect(url_for('budget_allocation'))
    
    try:
        updated_count = 0
        for idx, team in enumerate(teams):
            budget_value = request.form.get(f'budget_{idx}')
            if budget_value:
                new_budget = int(budget_value)
                if new_budget >= team.current_budget:
                    team.max_budget = new_budget
                    updated_count += 1
        
        save_teams()  # Save after updating all budgets
        flash(f'✅ Updated budgets for {updated_count} team(s)', 'success')
    except ValueError:
        flash('❌ Invalid budget value(s)', 'error')
    
    return redirect(url_for('budget_allocation'))


@app.route('/players')
def view_players():
    sorted_players = get_all_players_sorted()
    return render_template('players.html', players=sorted_players, get_category_color=get_category_color, format_currency=format_currency)


@app.route('/register_player', methods=['POST'])
def register_player():
    name = request.form.get('name')
    rating = request.form.get('rating')
    price = request.form.get('price')
    country = request.form.get('country', 'Pakistan')
    
    try:
        rating = int(rating)
        price = int(price)
        new_player = Player(name, rating, price, country)
        players.append(new_player)
        player_dict[new_player.id] = new_player
        save_players()  # Save after registering player
        flash(f'✅ Player {name} registered successfully! (Category: {new_player.category})', 'success')
    except ValueError:
        flash('❌ Invalid rating or price value', 'error')
    
    return redirect(url_for('view_players'))


@app.route('/teams')
def view_teams():
    return render_template('teams.html', teams=teams, get_category_color=get_category_color, format_currency=format_currency)


@app.route('/pre_draft')
def pre_draft():
    available = get_available_players()
    return render_template('pre_draft.html', teams=teams, players=available, get_category_color=get_category_color, format_currency=format_currency)


@app.route('/pre_draft_buy', methods=['POST'])
def pre_draft_buy():
    team_idx = int(request.form.get('team_idx'))
    password = request.form.get('password')
    player_id = request.form.get('player_id')
    
    team = teams[team_idx]
    
    if password != team.password:
        flash('❌ Incorrect password', 'error')
        return redirect(url_for('pre_draft'))
    
    if player_id not in player_dict:
        flash('❌ Invalid player', 'error')
        return redirect(url_for('pre_draft'))
    
    player = player_dict[player_id]
    can_add, message = team.can_add_player(player, is_pre_draft=True)
    
    if not can_add:
        flash(f'❌ {message}', 'error')
        return redirect(url_for('pre_draft'))
    
    team.add_player(player, is_pre_draft=True)
    undo_stack.append((team_idx, player_id, 0))
    
    # Save changes
    save_players()
    save_teams()
    save_team_players()
    save_draft_state()
    
    flash(f'✅ {team.name} bought {player.name} for {format_currency(player.price)}!', 'success')
    
    return redirect(url_for('pre_draft'))


@app.route('/start_draft', methods=['POST'])
def start_draft():
    global draft_started
    
    password = request.form.get('admin_password')
    
    if password != ADMIN_PASSWORD:
        flash('❌ Incorrect admin password', 'error')
        return redirect(url_for('index'))
    
    create_draft_queue()
    draft_started = True
    save_draft_state()  # Save draft state
    flash('🎯 Draft started successfully!', 'success')
    return redirect(url_for('draft'))


@app.route('/draft')
def draft():
    if not draft_started:
        flash('❌ Draft not started yet', 'error')
        return redirect(url_for('index'))
    
    if not draft_queue:
        return redirect(url_for('draft_finished'))
    
    current_round, current_team_idx = draft_queue[0]
    current_team = teams[current_team_idx]
    available = get_available_players()
    
    return render_template('draft.html',
                         current_team=current_team,
                         current_round=current_round,
                         available_players=available,
                         teams=teams,
                         get_category_color=get_category_color,
                         format_currency=format_currency,
                         total_picks=len(draft_queue))


@app.route('/draft_pick', methods=['POST'])
def draft_pick():
    player_id = request.form.get('player_id')
    
    if not draft_queue:
        flash('❌ Draft already finished', 'error')
        return redirect(url_for('draft_finished'))
    
    current_round, current_team_idx = draft_queue[0]
    team = teams[current_team_idx]
    
    if player_id not in player_dict:
        flash('❌ Invalid player', 'error')
        return redirect(url_for('draft'))
    
    player = player_dict[player_id]
    can_add, message = team.can_add_player(player)
    
    if not can_add:
        flash(f'❌ {message}', 'error')
        return redirect(url_for('draft'))
    
    team.add_player(player)
    undo_stack.append((current_team_idx, player_id, current_round))
    draft_queue.popleft()
    
    # Save changes
    save_players()
    save_teams()
    save_team_players()
    save_draft_state()
    
    flash(f'✅ {team.name} picked {player.name} for {format_currency(player.price)}!', 'success')
    
    if draft_queue:
        return redirect(url_for('draft'))
    else:
        return redirect(url_for('draft_finished'))


@app.route('/draft_skip', methods=['POST'])
def draft_skip():
    if draft_queue:
        draft_queue.popleft()
        flash('⏭️ Turn skipped', 'info')
    
    if draft_queue:
        return redirect(url_for('draft'))
    else:
        return redirect(url_for('draft_finished'))


@app.route('/draft_undo', methods=['POST'])
def draft_undo():
    if not undo_stack:
        flash('❌ Nothing to undo', 'error')
        return redirect(url_for('draft'))
    
    team_idx, player_id, round_num = undo_stack.pop()
    team = teams[team_idx]
    player = player_dict[player_id]
    
    team.remove_player(player)
    
    # Save changes
    save_players()
    save_teams()
    save_team_players()
    save_draft_state()
    
    flash(f'↩️ Undone: {player.name} removed from {team.name}', 'info')
    
    return redirect(url_for('draft'))


@app.route('/draft_finished')
def draft_finished():
    return render_template('draft_finished.html', teams=teams, get_category_color=get_category_color, format_currency=format_currency)


@app.route('/reset', methods=['POST'])
def reset():
    global draft_started, players, player_dict, teams, undo_stack, draft_queue
    
    # Reset data
    Player.player_counter = 1001
    players = create_demo_players()
    player_dict = {p.id: p for p in players}
    
    teams = [
        Team("Lahore Qalandars", 1000, 5000000, "lahore123"),
        Team("Karachi Kings", 1000, 5000000, "karachi123"),
        Team("Multan Sultans", 1000, 5000000, "multan123"),
        Team("Peshawar Zalmi", 1000, 5000000, "peshawar123"),
    ]
    
    undo_stack.clear()
    draft_queue.clear()
    draft_started = False
    
    # Save reset data to files
    save_players()
    save_teams()
    save_team_players()
    save_draft_state()
    
    flash('🔄 Application reset successfully!', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':

    app.run(debug=True)
