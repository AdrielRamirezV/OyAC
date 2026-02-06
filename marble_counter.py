import pygame
import pymunk
import pymunk.pygame_util
import math

# Configuration
WIDTH, HEIGHT = 1000, 1000
FPS = 60
GRAVITY = 900.0

def create_space():
    space = pymunk.Space()
    space.gravity = (0, GRAVITY)
    return space

def create_boundaries(space):
    # Floor
    floor = pymunk.Segment(space.static_body, (0, HEIGHT - 10), (WIDTH, HEIGHT - 10), 10)
    floor.elasticity = 0.5
    floor.friction = 0.5
    space.add(floor)
    
    # Marble Tube (Top Right)
    tube_x = WIDTH - 200
    tube_width = 32
    tube_height = 100
    wall_l = pymunk.Segment(space.static_body, (tube_x - tube_width//2, 0), (tube_x - tube_width//2, tube_height), 4)
    wall_r = pymunk.Segment(space.static_body, (tube_x + tube_width//2, 0), (tube_x + tube_width//2, tube_height), 4)
    for s in [wall_l, wall_r]:
        s.elasticity = 0.5
        s.friction = 0.2
        space.add(s)
    return tube_x

def create_catch_funnel(space, x, y):
    # Wide funnel to catch the "Carry" from the right
    # Funnel must be wide enough to catch marbles flying out from the level above
    w = 195
    h = 50
    gap = 40
    # Left wall
    l_slope = pymunk.Segment(space.static_body, (x - w//2, y), (x - gap//2, y + h), 4)
    # Right wall - extremely long/wide to catch carry from x + 250
    r_slope = pymunk.Segment(space.static_body, (x + w//2 + 100, y - 60), (x + gap//2, y + h), 4)
    for s in [l_slope, r_slope]:
        s.elasticity = 0.2
        s.friction = 0.1
        space.add(s)

def create_gate(space, position):
    mass = 1
    moment = pymunk.moment_for_segment(mass, (-18, 0), (18, 0), 5)
    body = pymunk.Body(mass, moment, body_type=pymunk.Body.KINEMATIC)
    body.position = position
    gate_shape = pymunk.Segment(body, (-18, 0), (18, 0), 5)
    gate_shape.elasticity = 0.5
    gate_shape.friction = 0.5
    space.add(body, gate_shape)
    return body

def create_counter_mechanism(space, position):
    # Small and robust: 100px wide, 70px tail
    mass = 2.0
    h_bar_pts = [(-50, -3), (50, -3), (50, 3), (-50, 3)]
    v_bar_pts = [(-3, 0), (3, 0), (3, -65), (-3, -65)]
    tip_pts = [(-15, -65), (15, -65), (0, -85)]
    
    moment = pymunk.moment_for_poly(mass, h_bar_pts) + \
             pymunk.moment_for_poly(mass, v_bar_pts) + \
             pymunk.moment_for_poly(mass, tip_pts)
             
    body = pymunk.Body(mass, moment)
    body.position = position
    body.center_of_gravity = (0, -20)
    
    h_bar = pymunk.Poly(body, h_bar_pts)
    v_bar = pymunk.Poly(body, v_bar_pts)
    v_tip = pymunk.Poly(body, tip_pts)
    
    # Slopes to prevent jam
    slope_l = pymunk.Poly(body, [(-3, -3), (-20, -3), (-3, -20)])
    slope_r = pymunk.Poly(body, [(3, -3), (20, -3), (3, -20)])
    
    for s in [h_bar, v_bar, v_tip, slope_l, slope_r]:
        s.elasticity = 0.1
        s.friction = 0.3
    
    space.add(body, h_bar, v_bar, v_tip, slope_l, slope_r)
    pivot = pymunk.PivotJoint(space.static_body, body, position)
    space.add(pivot)
    # Limits for bi-stability
    limit = pymunk.RotaryLimitJoint(space.static_body, body, -math.radians(35), math.radians(35))
    space.add(limit)
    
    return body

def spawn_marble(space, position):
    mass = 12.0
    radius = 12
    moment = pymunk.moment_for_circle(mass, 0, radius)
    body = pymunk.Body(mass, moment)
    body.position = position
    shape = pymunk.Circle(body, radius)
    shape.elasticity = 0.1
    shape.friction = 0.5
    space.add(body, shape)
    return body

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Contador Binario Mecánico Diagonal")
    clock = pygame.time.Clock()
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    
    space = create_space()
    tube_x = create_boundaries(space)
    
    gate_closed_pos = (tube_x, 103)
    gate_open_pos = (tube_x + 40, 103)
    gate_body = create_gate(space, gate_closed_pos)
    
    # Diagonal Cascade
    mechanisms = []
    # Generous distance: 250px horizontal, 230px vertical
    bits_pos = [
        (WIDTH - 180, 220), # Bit 0
        (WIDTH - 430, 450), # Bit 1
        (WIDTH - 680, 680), # Bit 2
        (WIDTH - 930, 910)  # Bit 3
    ]
    
    for i, pos in enumerate(bits_pos):
        body = create_counter_mechanism(space, pos)
        # 0 = Tilted Left (falls Right/Down)
        body.angle = -math.radians(35)
        mechanisms.append(body)
        
        # Funnel for carry (catch from right-above)
        if i > 0:
            # Position funnel 140px above pivot. Exit at -90. Tail top at -85. 
            # Safe 5px clearance but very close for precision.
            create_catch_funnel(space, pos[0], pos[1] - 140)

    font = pygame.font.SysFont("Arial", 20, bold=True)
    gate_timer = 0
    total_marbles_launched = 0
    
    marbles = []
    # Drop 10 marbles
    for i in range(10):
        marbles.append(spawn_marble(space, (tube_x, 80 - i * 26)))
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    gate_body.position = gate_open_pos
                    gate_timer = 15
                    total_marbles_launched += 1

        if gate_timer > 0:
            gate_timer -= 1
            if gate_timer == 0:
                gate_body.position = gate_closed_pos

        screen.fill((240, 240, 245))
        space.step(1.0 / FPS)
        space.debug_draw(draw_options)
        
        binary_val = 0
        for i, m in enumerate(mechanisms):
            angle = math.degrees(m.angle)
            val = 1 if angle > 5 else 0
            binary_val += val * (2**i)
            color = (0, 150, 0) if val == 1 else (150, 0, 0)
            txt = font.render(f"Bit {i}: {val}", True, color)
            screen.blit(txt, (20, 180 + i * 30))
            
        text_count = font.render(f"Canicas lanzadas: {total_marbles_launched}", True, (50, 50, 50))
        text_total = font.render(f"Contador: {binary_val}", True, (0, 0, 150))
        text_instr = font.render("ESPACIO: Lanzar '+1' (Canica)", True, (100, 100, 100))
        
        screen.blit(text_count, (20, 20))
        screen.blit(text_total, (20, 50))
        screen.blit(text_instr, (20, HEIGHT - 40))
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
