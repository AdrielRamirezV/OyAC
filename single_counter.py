import pygame
import pymunk
import pymunk.pygame_util
import math

# Configuration
WIDTH, HEIGHT = 800, 600
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
    
    # Marble Tube (Top Center)
    tube_width = 32
    tube_height = 150
    wall_l = pymunk.Segment(space.static_body, (WIDTH//2 - tube_width//2, 0), (WIDTH//2 - tube_width//2, tube_height), 4)
    wall_r = pymunk.Segment(space.static_body, (WIDTH//2 + tube_width//2, 0), (WIDTH//2 + tube_width//2, tube_height), 4)
    for s in [wall_l, wall_r]:
        s.elasticity = 0.5
        s.friction = 0.2
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
    # Shrunk version: 100px wide, 70px tail
    mass = 2.0
    h_bar_pts = [(-50, -3), (50, -3), (50, 3), (-50, 3)]
    v_bar_pts = [(-3, 0), (3, 0), (3, -65), (-3, -65)]
    tip_pts = [(-15, -65), (15, -65), (0, -85)]
    
    moment = pymunk.moment_for_poly(mass, h_bar_pts) + \
             pymunk.moment_for_poly(mass, v_bar_pts) + \
             pymunk.moment_for_poly(mass, tip_pts)
             
    body = pymunk.Body(mass, moment)
    body.position = position
    # Slightly top-heavy for bi-stability
    body.center_of_gravity = (0, -20)
    
    h_bar = pymunk.Poly(body, h_bar_pts)
    v_bar = pymunk.Poly(body, v_bar_pts)
    v_tip = pymunk.Poly(body, tip_pts)
    
    # Anti-jam slopes
    slope_l = pymunk.Poly(body, [(-3, -3), (-20, -3), (-3, -20)])
    slope_r = pymunk.Poly(body, [(3, -3), (20, -3), (3, -20)])
    
    for s in [h_bar, v_bar, v_tip, slope_l, slope_r]:
        s.elasticity = 0.1
        s.friction = 0.3
    
    space.add(body, h_bar, v_bar, v_tip, slope_l, slope_r)
    pivot = pymunk.PivotJoint(space.static_body, body, position)
    space.add(pivot)
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
    pygame.display.set_caption("Single Mechanism Marble Counter")
    clock = pygame.time.Clock()
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    
    space = create_space()
    create_boundaries(space)
    
    gate_closed_pos = (WIDTH // 2, 110)
    gate_open_pos = (WIDTH // 2 + 40, 110)
    gate_body = create_gate(space, gate_closed_pos)
    
    # Mechanism Position
    m_pos = (WIDTH // 2, HEIGHT // 2 + 50)
    counter_body = create_counter_mechanism(space, m_pos)
    counter_body.angle = -math.radians(35) # Initial state
    
    font = pygame.font.SysFont("Arial", 22, bold=False)
    gate_timer = 0
    total_marbles_launched = 0
    
    marbles = []
    # Drop 5 marbles initially
    for i in range(5):
        marbles.append(spawn_marble(space, (WIDTH // 2, 80 - i * 26)))
    
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

        screen.fill((245, 245, 250))
        space.step(1.0 / FPS)
        space.debug_draw(draw_options)
        
        # Logic for state
        angle = math.degrees(counter_body.angle)
        # Even/Par if tilted to the right, Odd/Impar if tilted to the left
        parity = "PAR" if angle > 5 else "IMPAR" if angle < -5 else "..."
        state_color = (180, 50, 50) if parity == "IMPAR" else (50, 150, 50)
        
        text_count = font.render(f"Canicas: {total_marbles_launched}", True, (50, 50, 50))
        text_parity = font.render(f"Estado: {parity}", True, state_color)
        text_instr = font.render("ESPACIO: Lanzar canica", True, (120, 120, 120))
        
        screen.blit(text_count, (20, 20))
        screen.blit(text_parity, (20, 50))
        screen.blit(text_instr, (WIDTH - 220, HEIGHT - 40))
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
