import pygame
import random
import sys
import math

pygame.init()
WIDTH, HEIGHT = 600, 400
UI_HEIGHT = 40
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Star")
FONT = pygame.font.SysFont("consolas", 24)

BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
DARK_GREY = (30, 30, 30)
LIGHT_GREY = (150, 150, 150)
YELLOW = (255, 255, 100)
DARK_BLUE = (10, 10, 30)
GROUND_COLOR = (40, 40, 40)
PLAYER_TRAIL_COLOR = (0, 255, 50)

player_base_radius = 15
player_pos = [WIDTH // 2, HEIGHT // 2 + UI_HEIGHT]
player_speed = 5
teleport_cooldown = 5000
last_teleport = -teleport_cooldown
max_collected_stars = 5  
ground_height = 40  
player_trail = []
man_started_walking = False




pygame.mixer.init()


note_sounds = []
try:
    snow_sound = pygame.mixer.Sound("snow.mp3")
    snow_sound.set_volume(0.7)

except:
    print("fail  snow.mp3")
    snow_sound = None

for name in ["do", "re", "mi", "fa"]:
    try:
        sound = pygame.mixer.Sound(f"{name}.mp3")
        sound.set_volume(0.7)
        note_sounds.append(sound)
    except:
        print(f"fail {name}.mp3")
try:
    pygame.mixer.music.load("star.mp3")  

    pygame.mixer.music.set_volume(0.2)
    pygame.mixer.music.play(-1)
except:
    print("fail star.mp3")

stars = [] 

clock = pygame.time.Clock()

teleport_flash_active = False
teleport_flash_start = 0
teleport_flash_duration = 300

dialogues = [
    {"speaker": "player", "text": "I want to run away from here...", "color": WHITE},
    {"speaker": "man", "text": "You can't...", "color": LIGHT_GREY},
    {"speaker": "player", "text": "Who are you?", "color": WHITE},
    {"speaker": "man", "text": "I'm the guardian of this place.", "color": LIGHT_GREY},
    {"speaker": "player", "text": "And who am i?", "color": WHITE},
    {"speaker": "man", "text": "I don't know. And i don't care. bye", "color": LIGHT_GREY},
]

dialogue_index = 0
dialogue_start_time = 0
text_display_speed = 50
displayed_text = ""

COLLECTIBLE_RADIUS = 8
collectibles = [{
    "x": random.randint(20, WIDTH - 20),
    "y": random.randint(UI_HEIGHT + 20, HEIGHT - 20),
    "spawn_time": pygame.time.get_ticks()
}]


man_pos = [-50, HEIGHT // 2 + UI_HEIGHT]  
man_speed = 0.3
man_visible = False
man_reached_center = False
in_dialogue = False

def draw_stars():
    for star in stars:
        pygame.draw.circle(WIN, (star["brightness"],) * 3, (int(star["x"]), int(star["y"])), 1)
        star["y"] += star["speed"]
        if star["y"] > HEIGHT:
            star["y"] = 0
            star["x"] = random.randint(0, WIDTH)
            star["brightness"] = random.randint(100, 255)

def get_ground_color(collected, max_stars):
    ratio = min(collected / max_stars, 1)
    base = 40
    value = int(base + ratio * (255 - base))  
    return (value, value, value)

def draw_trails(now):
    for trail in player_trail:
        elapsed = now - trail["time"]
        if elapsed < 1000:
            alpha = 255 - int((elapsed / 1000) * 255)
            radius = player_base_radius - 5 + int(5 * (1 - elapsed / 1000))
            surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surface, (*WHITE, alpha), (radius, radius), radius)
            WIN.blit(surface, (trail["pos"][0] - radius, trail["pos"][1] - radius))

def draw_teleport_flash(now):
    global teleport_flash_active
    if teleport_flash_active:
        elapsed = now - teleport_flash_start
        if elapsed > teleport_flash_duration:
            teleport_flash_active = False
            return
        alpha = 255 - int((elapsed / teleport_flash_duration) * 255)
        radius = player_base_radius + int(50 * (elapsed / teleport_flash_duration))
        surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surface, (255, 255, 100, alpha), (radius, radius), radius)
        WIN.blit(surface, (player_pos[0] - radius, player_pos[1] - radius))

def draw_dialogue(now):
    global displayed_text, dialogue_index, dialogue_start_time, in_dialogue

    if dialogue_index >= len(dialogues):
        in_dialogue = False
        return

    dialogue = dialogues[dialogue_index]
    elapsed = now - dialogue_start_time
    total_length = len(dialogue["text"])
    chars_to_show = min(total_length, elapsed // text_display_speed)
    displayed_text = dialogue["text"][:chars_to_show]

    x, y = WIDTH // 2, UI_HEIGHT + 25
    padding = 10
    text_surface = FONT.render(displayed_text, True, dialogue["color"])
    rect = text_surface.get_rect()
    rect.center = (x, y)
    rect.inflate_ip(padding * 2, padding * 2)

    pygame.draw.rect(WIN, DARK_GREY, rect, border_radius=8)
    WIN.blit(text_surface, (rect.x + padding, rect.y + padding))


    if chars_to_show == total_length and elapsed > total_length * text_display_speed + 3000:
        dialogue_index += 1
        dialogue_start_time = now

def draw_collectibles(now):
    for item in collectibles:
        phase = ((now - item["spawn_time"]) % 1000) / 1000
        pulse = 4 * math.sin(phase * 2 * math.pi)
        pygame.draw.circle(WIN, WHITE, (item["x"], item["y"]), int(COLLECTIBLE_RADIUS + pulse))

def draw_man():

    man_rect = pygame.Rect(0, 0, 30, 60)

    ground_height = 40
    man_rect.midbottom = (int(man_pos[0]), HEIGHT - ground_height)
    pygame.draw.rect(WIN, GROUND_COLOR, man_rect, border_radius=5)


def draw_window(score, cooldown_remaining, collected_stars, now):
    WIN.fill(DARK_BLUE)
    ground_height = 40
    ground_color = get_ground_color(collected_stars, max_collected_stars)
    pygame.draw.rect(WIN, ground_color, (0, HEIGHT - ground_height, WIDTH, ground_height))
    draw_stars()


    draw_trails(now)
    draw_teleport_flash(now)

    pulse_period = 1000
    pulse_phase = (now % pulse_period) / pulse_period
    pulse_radius = player_base_radius + 3 * math.sin(pulse_phase * 2 * math.pi)

    radius = pulse_radius + 10 if teleport_flash_active else pulse_radius
    color = YELLOW if teleport_flash_active else WHITE

    size = int(radius * 2)
    player_rect = pygame.Rect(0, 0, size, size)
    player_rect.center = player_pos
    pygame.draw.rect(WIN, color, player_rect, border_radius=6)

    draw_collectibles(now)


    if man_visible:
        draw_man()


    if in_dialogue:
        draw_dialogue(now)

    pygame.display.update()

def handle_teleport(keys, now):
    global last_teleport, teleport_flash_active, teleport_flash_start
    cooldown_remaining = max(0, teleport_cooldown - (now - last_teleport))
    if keys[pygame.K_SPACE] and cooldown_remaining == 0:
        last_teleport = now
        teleport_flash_active = True
        teleport_flash_start = now
        player_pos[0] = random.randint(0, WIDTH)
        player_pos[1] = random.randint(UI_HEIGHT + 20, HEIGHT)
    return cooldown_remaining

def update_trails(now):
    player_trail.append({"pos": player_pos.copy(), "time": now})

def main():
    global dialogue_index, dialogue_start_time, man_pos, man_visible, man_reached_center, in_dialogue, man_started_walking

    run = True
    score = 0
    collected = 0
    dialogue_start_time = pygame.time.get_ticks()

    while run:
        now = pygame.time.get_ticks()
        dt = clock.tick(60)
        score += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        keys = pygame.key.get_pressed()

        if collected >= max_collected_stars and not man_visible:
            man_visible = True
            in_dialogue = False
            dialogue_index = 1
            dialogue_start_time = now

        cooldown_remaining = 0


        if man_visible and not man_reached_center:
            if man_pos[0] < WIDTH // 2:
                man_started_walking = True
                man_pos[0] += man_speed
                if not snow_sound.get_num_channels():
                    snow_sound.play(-1)
            else:
                man_reached_center = True
                snow_sound.stop()
                man_started_walking = False
                in_dialogue = True
                dialogue_start_time = now
        elif man_visible and man_reached_center and not in_dialogue:
            if man_pos[0] < WIDTH+10:
                man_started_walking = True
                man_pos[0] += man_speed
                if not snow_sound.get_num_channels():
                    snow_sound.play(-1)
            else:
                man_started_walking = False
                man_visible = False  
                snow_sound.stop()  


        if man_reached_center:
            player_pos[0] = WIDTH // 2
            player_pos[1] = HEIGHT // 2 + UI_HEIGHT

            cooldown_remaining = teleport_cooldown 
        else:

            cooldown_remaining = handle_teleport(keys, now)
            if not (man_visible and in_dialogue):
                if keys[pygame.K_LEFT]:
                    player_pos[0] -= player_speed
                if keys[pygame.K_RIGHT]:
                    player_pos[0] += player_speed
                if keys[pygame.K_UP]:
                    player_pos[1] -= player_speed
                if keys[pygame.K_DOWN]:
                    player_pos[1] += player_speed

        player_pos[0] = max(0, min(WIDTH, player_pos[0]))
        player_pos[1] = max(UI_HEIGHT, min(HEIGHT - ground_height, player_pos[1]))

        if not (man_visible and man_reached_center and in_dialogue):
            for item in collectibles[:]:
                if math.hypot(player_pos[0] - item["x"], player_pos[1] - item["y"]) < player_base_radius + COLLECTIBLE_RADIUS:
                    collectibles.remove(item)
                    collected += 1
                    if note_sounds:
                        random.choice(note_sounds).play()

                    for _ in range(5):
                        stars.append({
                            "x": random.randint(0, WIDTH),
                            "y": random.randint(0, HEIGHT),
                            "speed": random.uniform(0.2, 0.7),
                            "brightness": random.randint(100, 255)
                        })

                    collectibles.append({
                        "x": random.randint(20, WIDTH - 20),
                        "y": random.randint(UI_HEIGHT + 20, HEIGHT - ground_height - 20),
                        "spawn_time": pygame.time.get_ticks()    
                    })

        update_trails(now)
        draw_window(score, cooldown_remaining, collected, now)

    pygame.quit()
    sys.exit()
    
if __name__ == "__main__":
    main()
