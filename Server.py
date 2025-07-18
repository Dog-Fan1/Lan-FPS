import asyncio
import websockets
import json
import random
import math

class MazeGenerator:
    """
    Generates a maze using a randomized depth-first search (recursive backtracking) algorithm.
    Ensures odd dimensions for proper maze generation and sets a start and end point.
    Supports multiple layers with teleporters between them.
    """
    def __init__(self, width, height, num_layers=1):
        # Ensure odd width and height for proper maze generation
        self.width = width if width % 2 == 1 else width + 1
        self.height = height if height % 2 == 1 else height + 1
        self.num_layers = num_layers
        self.mazes = [] # List to hold maze data for each layer
        self.start_coords = None
        self.end_coords = None
        self.teleporter_coords = {} # Stores {layer: [(r, c, type)]} for L/l blocks
        self.all_open_spots_layer0 = [] # To store open spots on layer 0 for respawn

    def _is_valid(self, r, c):
        """
        Checks if the given row and column are within the maze boundaries.
        """
        return 0 <= r < self.height and 0 <= c < self.width

    def _carve_path(self, r, c, maze):
        """
        Recursively carves paths through the maze using a randomized depth-first search.
        """
        maze[r][c] = ' ' # Mark the current cell as a path

        # Define possible directions (up, down, left, right)
        directions = [(0, 2), (0, -2), (2, 0), (-2, 0)]
        random.shuffle(directions) # Randomize the order of directions

        for dr, dc in directions:
            nr, nc = r + dr, c + dc # New cell to move to
            if self._is_valid(nr, nc) and maze[nr][nc] == '#':
                # If the new cell is valid and a wall, carve a path to it
                maze[r + dr // 2][c + dc // 2] = ' ' # Carve path between current and new cell
                self._carve_path(nr, nc, maze)

    def generate(self):
        """
        Generates a multi-layered maze with start, end, and teleporter points.
        """
        self.mazes = []
        for i in range(self.num_layers):
            # Initialize maze with all walls for the current layer
            maze = [['#' for _ in range(self.width)] for _ in range(self.height)]
            # Start carving from a random odd coordinate to ensure connectivity
            start_r, start_c = random.randrange(1, self.height, 2), random.randrange(1, self.width, 2)
            self._carve_path(start_r, start_c, maze)
            self.mazes.append(maze)

        # Place 'S' (Start) on the first layer (layer 0)
        maze_layer_0 = self.mazes[0]
        # Populate all_open_spots_layer0 for later use (e.g., respawn)
        self.all_open_spots_layer0 = []
        for r in range(self.height):
            for c in range(self.width):
                if maze_layer_0[r][c] == ' ':
                    self.all_open_spots_layer0.append((r, c))

        if self.all_open_spots_layer0:
            sr, sc = random.choice(self.all_open_spots_layer0)
            maze_layer_0[sr][sc] = 'S'
            self.start_coords = (sr, sc)
            print(f"Placed 'S' at grid coordinates: row={sr}, col={sc}")
        else:
            print("Warning: No open spots found for 'S' on layer 0. Falling back to (1,1).")
            self.start_coords = (1, 1) # Fallback

        # Place 'E' (End) on the last layer
        maze_last_layer = self.mazes[self.num_layers - 1]
        all_open_spots_last_layer = []
        for r in range(self.height):
            for c in range(self.width):
                if maze_last_layer[r][c] == ' ':
                    all_open_spots_last_layer.append((r, c))

        if all_open_spots_last_layer:
            er, ec = random.choice(all_open_spots_last_layer)
            maze_last_layer[er][ec] = 'E'
            self.end_coords = (er, ec)
            print(f"Placed 'E' at grid coordinates: row={er}, col={ec} on layer {self.num_layers - 1}")
        else:
            print(f"Warning: No open spots found for 'E' on layer {self.num_layers - 1}. Falling back to (1,1).")
            self.end_coords = (1, 1) # Fallback

        # Place teleporters (L and l) on intermediate layers
        self.teleporter_coords = {}
        for l in range(self.num_layers):
            self.teleporter_coords[l] = []
            if l < self.num_layers - 1: # 'L' teleporter (exit to next layer)
                current_layer_open_spots = []
                for r in range(self.height):
                    for c in range(self.width):
                        if self.mazes[l][r][c] == ' ':
                            current_layer_open_spots.append((r, c))
                if current_layer_open_spots:
                    tr, tc = random.choice(current_layer_open_spots)
                    self.mazes[l][tr][tc] = 'L'
                    self.teleporter_coords[l].append({'r': tr, 'c': tc, 'type': 'L'})
                    print(f"Placed 'L' at layer {l}, coords: ({tr}, {tc})")
                else:
                    print(f"Warning: No open spots for 'L' on layer {l}.")

            if l > 0: # 'l' teleporter (entrance from previous layer)
                current_layer_open_spots = []
                for r in range(self.height):
                    for c in range(self.width):
                        if self.mazes[l][r][c] == ' ':
                            current_layer_open_spots.append((r, c))
                if current_layer_open_spots:
                    tr, tc = random.choice(current_layer_open_spots)
                    self.mazes[l][tr][tc] = 'l'
                    self.teleporter_coords[l].append({'r': tr, 'c': tc, 'type': 'l'})
                    print(f"Placed 'l' at layer {l}, coords: ({tr}, {tc})")
                else:
                    print(f"Warning: No open spots for 'l' on layer {l}.")

        return self.mazes

    def get_maze_data(self):
        """Returns the generated maze data."""
        return self.mazes

    def get_start_coords(self):
        """Returns the grid coordinates of the start point."""
        return self.start_coords

    def get_end_coords(self):
        """Returns the grid coordinates of the end point."""
        return self.end_coords

# Game Constants (MUST MATCH CLIENT'S CONSTANTS FOR CONSISTENCY)
MAZE_WIDTH = 17
MAZE_HEIGHT = 17
NUM_MAZE_LAYERS = 2 # Example: 2 layers
BLOCK_SIZE = 5 # Size of each maze block in world units
WALL_HEIGHT = 6 # Height of maze walls in world units
PLAYER_RADIUS = BLOCK_SIZE * 0.3 # Player collision radius
MAX_HEALTH = 100
BULLET_DAMAGE = 10
INITIAL_START_POSITION = {"x": 0, "y": 0, "z": 0} # Placeholder, will be set by maze generator

# Global game state
PLAYERS = {} # {websocket: {"id": "player_X", "position": {}, "rotation": {}, "layer": 0, "health": 100, "score": 0, "color": "#RRGGBB"}}
BULLETS = [] # [{"id": "bullet_Y", "shooter_id": "player_X", "position": {}, "direction": {}, "layer": 0, "creation_time": time.time()}]
NEXT_PLAYER_ID = 0
NEXT_BULLET_ID = 0
MAZE_GENERATOR = MazeGenerator(MAZE_WIDTH, MAZE_HEIGHT, NUM_MAZE_LAYERS)
GENERATED_MAZE_DATA = MAZE_GENERATOR.generate()
START_GRID_COORDS = MAZE_GENERATOR.get_start_coords()
END_GRID_COORDS = MAZE_GENERATOR.get_end_coords()

# Convert grid coordinates to world coordinates
def grid_to_world_coords(grid_row, grid_col, layer):
    """
    Converts maze grid coordinates to 3D world coordinates.
    The center of the maze (0,0) in world coordinates corresponds to the center of the grid.
    """
    world_x = grid_col * BLOCK_SIZE - (MAZE_WIDTH * BLOCK_SIZE) / 2 + BLOCK_SIZE / 2
    world_z = grid_row * BLOCK_SIZE - (MAZE_HEIGHT * BLOCK_SIZE) / 2 + BLOCK_SIZE / 2
    world_y = layer * WALL_HEIGHT # Y is determined by layer

    return {"x": world_x, "y": world_y, "z": world_z}

# Convert world coordinates to grid coordinates
def world_to_grid_coords(world_x, world_z):
    """
    Converts 3D world coordinates back to maze grid coordinates.
    """
    grid_col = math.floor((world_x + (MAZE_WIDTH * BLOCK_SIZE) / 2 - BLOCK_SIZE / 2) / BLOCK_SIZE)
    grid_row = math.floor((world_z + (MAZE_HEIGHT * BLOCK_SIZE) / 2 - BLOCK_SIZE / 2) / BLOCK_SIZE)
    return {"r": grid_row, "c": grid_col}

def get_random_open_position_on_layer(layer_index):
    """
    Finds a random open spot (' ') on the specified maze layer and returns its world coordinates.
    Returns INITIAL_START_POSITION as a fallback if no open spots are found.
    """
    if layer_index < 0 or layer_index >= NUM_MAZE_LAYERS:
        print(f"Error: Requested layer_index {layer_index} is out of bounds.")
        return INITIAL_START_POSITION.copy()

    target_maze_layer = GENERATED_MAZE_DATA[layer_index]
    open_spots = []
    for r in range(MAZE_HEIGHT):
        for c in range(MAZE_WIDTH):
            if target_maze_layer[r][c] == ' ':
                open_spots.append((r, c))

    if open_spots:
        sr, sc = random.choice(open_spots)
        return grid_to_world_coords(sr, sc, layer_index)
    else:
        print(f"Warning: No open spots found on layer {layer_index} for random respawn. Falling back to initial start position.")
        return INITIAL_START_POSITION.copy()


# Debugging coordinate conversion
def debug_coordinates():
    """Prints debug information about maze dimensions and coordinate conversion."""
    print("\n=== COORDINATE DEBUGGING ===")
    print(f"Maze dimensions: {MAZE_HEIGHT}x{MAZE_WIDTH}")

    # Set initial start position based on the randomly chosen 'S'
    global INITIAL_START_POSITION
    INITIAL_START_POSITION = grid_to_world_coords(START_GRID_COORDS[0], START_GRID_COORDS[1], 0)
    print(f"Start grid coords: row={START_GRID_COORDS[0]}, col={START_GRID_COORDS[1]}")
    print(f"Start world coords: {INITIAL_START_POSITION}")

    # Set end position based on the randomly chosen 'E'
    END_WORLD_POSITION = grid_to_world_coords(END_GRID_COORDS[0], END_GRID_COORDS[1], NUM_MAZE_LAYERS - 1)
    print(f"End grid coords: row={END_GRID_COORDS[0]}, col={END_GRID_COORDS[1]}")
    print(f"End world coords: {END_WORLD_POSITION}")


    # Test conversion back and forth
    test_world_x = INITIAL_START_POSITION["x"]
    test_world_z = INITIAL_START_POSITION["z"]
    converted_grid = world_to_grid_coords(test_world_x, test_world_z)
    print(f"Conversion test - World->Grid: ({test_world_x:.2f}, {test_world_z:.2f}) -> (r={converted_grid['r']}, c={converted_grid['c']})")

    if converted_grid['r'] == START_GRID_COORDS[0] and converted_grid['c'] == START_GRID_COORDS[1]:
        print("✓ Coordinate conversion is working correctly!")
    else:
        print("✗ Coordinate conversion error!")

    # Verify center of the map
    center_grid_r = MAZE_HEIGHT // 2
    center_grid_c = MAZE_WIDTH // 2
    center_world_coords = grid_to_world_coords(center_grid_r, center_grid_c, 0)
    print(f"Center world ({center_world_coords['x']:.0f},{center_world_coords['z']:.0f}) corresponds to grid ({center_grid_r}, {center_grid_c})")
    print(f"Expected center grid: ({MAZE_HEIGHT // 2}, {MAZE_WIDTH // 2})")

    print("=== END COORDINATE DEBUGGING ===\n")

# Call debug function after maze generation
debug_coordinates()

async def broadcast(message):
    """Sends a JSON message to all connected players."""
    disconnected_players = []
    for websocket in PLAYERS:
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosedOK:
            disconnected_players.append(websocket)
        except Exception as e:
            print(f"Error broadcasting message to {PLAYERS[websocket]['id']}: {e}")
            disconnected_players.append(websocket)

    for websocket in disconnected_players:
        await unregister_player(websocket)

async def register_player(websocket):
    """Registers a new player, assigns an ID, and sends initial game state."""
    global NEXT_PLAYER_ID
    player_id = f"player_{NEXT_PLAYER_ID}"
    NEXT_PLAYER_ID += 1

    # Assign a random color to the new player
    color = "#%06x" % random.randint(0, 0xFFFFFF)

    # Get a random respawn position on layer 0 for the new player
    spawn_position = get_random_open_position_on_layer(0)

    # Initialize player data
    player_data = {
        "id": player_id,
        "position": spawn_position.copy(), # Spawn at a random open spot on layer 0
        "rotation": {"x": 0, "y": 0, "z": 0},
        "layer": 0, # Always start on layer 0
        "health": MAX_HEALTH,
        "score": 0,
        "color": color
    }
    PLAYERS[websocket] = player_data
    print(f"Player {player_id} connected at position: {player_data['position']}")
    spawn_grid_coords = world_to_grid_coords(spawn_position["x"], spawn_position["z"])
    print(f"Player {player_id} grid position: row={spawn_grid_coords['r']}, col={spawn_grid_coords['c']}")

    # Prepare list of existing players for the new player
    existing_players = [
        {"id": p["id"], "position": p["position"], "rotation": p["rotation"], "layer": p["layer"], "health": p["health"], "score": p["score"], "color": p["color"]}
        for ws, p in PLAYERS.items() if ws != websocket
    ]

    # Send initial game state to the newly connected player
    init_message = {
        "type": "init",
        "player_id": player_id,
        "players": existing_players,
        "maze_data": GENERATED_MAZE_DATA,
        "start_position": spawn_position, # Send the actual spawn position
        "end_position": grid_to_world_coords(END_GRID_COORDS[0], END_GRID_COORDS[1], NUM_MAZE_LAYERS - 1)
    }
    print(f"Sending init message to {player_id}: {init_message}")
    await websocket.send(json.dumps(init_message))

    # Notify all other players about the new connection
    player_connected_message = {
        "type": "player_connected",
        "player_id": player_id,
        "position": player_data["position"],
        "rotation": player_data["rotation"],
        "layer": player_data["layer"],
        "health": player_data["health"],
        "score": player_data["score"],
        "color": player_data["color"]
    }
    print(f"Broadcasting player_connected message for {player_id}: {player_connected_message}")
    await broadcast(player_connected_message)

async def unregister_player(websocket):
    """Unregisters a player and notifies others."""
    player_id = PLAYERS.get(websocket, {}).get("id")
    if player_id:
        del PLAYERS[websocket]
        print(f"Player {player_id} disconnected.")
        await broadcast({"type": "player_disconnected", "player_id": player_id})

async def respawn_player(websocket, player_id, killer_id=None, reset_score=True):
    """
    Respawns a player to a random open position on layer 0, resets health, and adjusts score.
    """
    player_data = PLAYERS[websocket]

    if killer_id and reset_score:
        player_data["score"] = max(0, player_data["score"] - 100) # Deduct points for being defeated
        print(f"Player {player_id} lost 100 points. New score: {player_data['score']}")

    # Get a NEW random respawn position on layer 0
    new_respawn_position = get_random_open_position_on_layer(0)

    player_data["health"] = MAX_HEALTH
    player_data["position"] = new_respawn_position.copy() # Set to new random position
    player_data["layer"] = 0
    player_data["rotation"] = {"x": 0, "y": 0, "z": 0} # Reset rotation on respawn

    # Notify all clients that the player was defeated
    defeated_message = {
        "type": "player_defeated",
        "player_id": player_id,
        "final_score": player_data["score"],
        "killer_id": killer_id
    }
    print(f"Broadcasting player_defeated message for {player_id}: {defeated_message}")
    await broadcast(defeated_message)

    # Notify all clients that the player has respawned with new state
    respawn_message = {
        "type": "player_respawned",
        "player_id": player_id,
        "position": player_data["position"],
        "layer": player_data["layer"],
        "health": player_data["health"],
        "score": player_data["score"],
        "color": player_data["color"],
        "rotation": player_data["rotation"] # Include rotation for client reset
    }
    print(f"Broadcasting player_respawned message for {player_id}: {respawn_message}")
    await broadcast(respawn_message)

async def handle_player_update(websocket, data):
    """Updates a player's position and rotation based on client input."""
    player_data = PLAYERS.get(websocket)
    if not player_data:
        return

    # Basic validation for position and rotation data
    if "position" in data and isinstance(data["position"], dict):
        player_data["position"]["x"] = float(data["position"].get("x", player_data["position"]["x"]))
        player_data["position"]["y"] = float(data["position"].get("y", player_data["position"]["y"]))
        player_data["position"]["z"] = float(data["position"].get("z", player_data["position"]["z"]))
    if "rotation" in data and isinstance(data["rotation"], dict):
        player_data["rotation"]["x"] = float(data["rotation"].get("x", player_data["rotation"]["x"]))
        player_data["rotation"]["y"] = float(data["rotation"].get("y", player_data["rotation"]["y"]))
        player_data["rotation"]["z"] = float(data["rotation"].get("z", player_data["rotation"]["z"]))
    if "layer" in data:
        player_data["layer"] = int(data["layer"])

    # Broadcast updated position to other players
    await broadcast({
        "type": "player_update",
        "player_id": player_data["id"],
        "position": player_data["position"],
        "rotation": player_data["rotation"],
        "layer": player_data["layer"]
    })

async def handle_bullet_fired(websocket, data):
    """Handles a bullet fired event, adds it to active bullets."""
    player_data = PLAYERS.get(websocket)
    if not player_data:
        return

    global NEXT_BULLET_ID
    bullet_id = f"bullet_{NEXT_BULLET_ID}"
    NEXT_BULLET_ID += 1

    # Basic validation for bullet data
    start_position = {
        "x": float(data["start_position"]["x"]),
        "y": float(data["start_position"]["y"]),
        "z": float(data["start_position"]["z"])
    }
    direction = {
        "x": float(data["direction"]["x"]),
        "y": float(data["direction"]["y"]),
        "z": float(data["direction"]["z"])
    }
    layer = int(data["layer"])

    bullet_data = {
        "id": bullet_id,
        "shooter_id": player_data["id"],
        "position": start_position,
        "direction": direction,
        "layer": layer,
        "creation_time": asyncio.get_event_loop().time() # Server-side timestamp
    }
    BULLETS.append(bullet_data)

    # Broadcast bullet fired event to all clients
    await broadcast({
        "type": "bullet_fired",
        "bullet_id": bullet_id,
        "shooter_id": player_data["id"],
        "start_position": start_position,
        "direction": direction,
        "layer": layer
    })

async def handle_player_hit(websocket, data):
    """Handles a player hit event, applies damage, and checks for defeat."""
    target_id = data.get("target_id")
    shooter_id = PLAYERS.get(websocket, {}).get("id")

    if not target_id or not shooter_id:
        print(f"Invalid player_hit data: {data}")
        return

    target_websocket = None
    for ws, p_data in PLAYERS.items():
        if p_data["id"] == target_id:
            target_websocket = ws
            break

    if not target_websocket:
        print(f"Target player {target_id} not found.")
        return

    target_player_data = PLAYERS[target_websocket]
    target_player_data["health"] -= BULLET_DAMAGE
    print(f"Player {target_id} hit by {shooter_id}. New health: {target_player_data['health']}")

    # Update shooter's score if they hit someone
    shooter_data = PLAYERS[websocket]
    if shooter_data:
        shooter_data["score"] += 10 # Example: 10 points per hit
        print(f"Player {shooter_id} score updated to: {shooter_data['score']}")
        await broadcast({
            "type": "score_update",
            "player_id": shooter_id,
            "new_score": shooter_data["score"]
        })

    # Broadcast health update
    await broadcast({
        "type": "health_update",
        "target_id": target_id,
        "new_health": target_player_data["health"],
        "score": target_player_data["score"] # Send target's score too, in case it changed
    })

    if target_player_data["health"] <= 0:
        print(f"Player {target_id} defeated by {shooter_id}!")
        # Respawn the defeated player
        await respawn_player(target_websocket, target_id, killer_id=shooter_id, reset_score=True)
        # Award points to the killer for defeating the player
        if shooter_data:
            shooter_data["score"] += 500 # Example: 500 points for a defeat
            print(f"Player {shooter_id} awarded 500 points for defeating {target_id}. New score: {shooter_data['score']}")
            await broadcast({
                "type": "score_update",
                "player_id": shooter_id,
                "new_score": shooter_data["score"]
            })

async def handle_teleport_request(websocket, data):
    """Handles a teleport request from a player."""
    player_data = PLAYERS.get(websocket)
    if not player_data:
        return

    target_layer = data.get("target_layer")
    if target_layer is None or not isinstance(target_layer, int):
        print(f"Invalid teleport_request: {data}")
        return

    current_grid_pos = world_to_grid_coords(player_data["position"]["x"], player_data["position"]["z"])
    current_cell_char = GENERATED_MAZE_DATA[player_data["layer"]][current_grid_pos["r"]][current_grid_pos["c"]]

    # Validate if player is on an 'L' block and requesting to go to the next layer
    if current_cell_char == 'L' and target_layer == player_data["layer"] + 1 and target_layer < NUM_MAZE_LAYERS:
        # Find a corresponding 'l' block on the target layer
        target_teleporter_found = False
        for teleporter in MAZE_GENERATOR.teleporter_coords.get(target_layer, []):
            if teleporter['type'] == 'l':
                # Teleport to the found 'l' block
                new_position = grid_to_world_coords(teleporter['r'], teleporter['c'], target_layer)
                player_data["position"] = new_position
                player_data["layer"] = target_layer
                print(f"Player {player_data['id']} teleported to layer {target_layer} at {new_position}")

                # Broadcast player update after teleport
                await broadcast({
                    "type": "player_update",
                    "player_id": player_data["id"],
                    "position": player_data["position"],
                    "rotation": player_data["rotation"],
                    "layer": player_data["layer"]
                })
                target_teleporter_found = True
                break
        if not target_teleporter_found:
            print(f"No 'l' teleporter found on layer {target_layer} for player {player_data['id']}.")
    else:
        print(f"Player {player_data['id']} attempted invalid teleport from layer {player_data['layer']} (on {current_cell_char}) to {target_layer}.")

async def handle_teleport_to_start(websocket):
    """Teleports the player back to the initial start position."""
    player_data = PLAYERS.get(websocket)
    if not player_data:
        return

    player_id = player_data["id"]
    print(f"Player {player_id} requested teleport to start.")

    # Get a NEW random respawn position on layer 0 for teleport to start
    new_respawn_position = get_random_open_position_on_layer(0)

    # Reset player's state to a random open position on layer 0
    player_data["position"] = new_respawn_position.copy()
    player_data["layer"] = 0
    player_data["rotation"] = {"x": 0, "y": 0, "z": 0} # Reset rotation too

    # Broadcast player update after teleport
    await broadcast({
        "type": "player_update",
        "player_id": player_data["id"],
        "position": player_data["position"],
        "rotation": player_data["rotation"],
        "layer": player_data["layer"]
    })
    print(f"Player {player_id} teleported to random start at {player_data['position']} on layer {player_data['layer']}.")

async def handle_player_reached_end(websocket):
    """Handles a player reaching the 'E' (end) block."""
    player_data = PLAYERS.get(websocket)
    if not player_data:
        return

    player_id = player_data["id"]
    current_grid_pos = world_to_grid_coords(player_data["position"]["x"], player_data["position"]["z"])
    
    # Verify player is on the 'E' block on the last layer
    if player_data["layer"] == NUM_MAZE_LAYERS - 1 and \
       current_grid_pos["r"] == END_GRID_COORDS[0] and \
       current_grid_pos["c"] == END_GRID_COORDS[1]:
        
        print(f"Player {player_id} reached the end! Game Over for this player.")
        
        # Broadcast game win message
        await broadcast({
            "type": "game_win",
            "winner_id": player_id
        })

        # Respawn the player after a short delay
        await asyncio.sleep(3) # Give clients time to show win message
        await respawn_player(websocket, player_id, killer_id="maze", reset_score=False) # Respawn without score penalty

    else:
        print(f"Player {player_id} sent 'player_reached_end' but is not at the end block.")


async def handle_client_messages(websocket):
    """Handles incoming messages from a connected client."""
    await register_player(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            # print(f"Received from {PLAYERS[websocket]['id']}: {data['type']}") # Too verbose

            if data["type"] == "player_update":
                await handle_player_update(websocket, data)
            elif data["type"] == "bullet_fired":
                await handle_bullet_fired(websocket, data)
            elif data["type"] == "player_hit":
                await handle_player_hit(websocket, data)
            elif data["type"] == "teleport_request":
                await handle_teleport_request(websocket, data)
            elif data["type"] == "teleport_to_start":
                await handle_teleport_to_start(websocket)
            elif data["type"] == "player_reached_end":
                await handle_player_reached_end(websocket)
            else:
                print(f"Unknown message type: {data['type']}")
    except websockets.exceptions.ConnectionClosedOK:
        print("Client disconnected gracefully.")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Client disconnected with error: {e}")
    except Exception as e:
        print(f"Unexpected error with client {PLAYERS.get(websocket, {}).get('id', 'unknown')}: {e}")
    finally:
        await unregister_player(websocket)

async def game_loop():
    """Main game loop for server-side logic (e.g., bullet physics, NPC updates)."""
    while True:
        # Example: Server-side bullet update (if needed, currently client-authoritative)
        # This section is commented out because bullet physics is handled client-side for now.
        # If you move bullet physics to server, uncomment and implement here.
        # for bullet in BULLETS:
        #     # Update bullet position
        #     bullet["position"]["x"] += bullet["direction"]["x"] * BULLET_SPEED_SERVER
        #     bullet["position"]["y"] += bullet["direction"]["y"] * BULLET_SPEED_SERVER
        #     bullet["position"]["z"] += bullet["direction"]["z"] * BULLET_SPEED_SERVER
        #
        #     # Check for collisions with walls or players (server-side authoritative collision)
        #     # If collision, remove bullet and apply damage
        #
        #     # Remove old bullets
        #     if asyncio.get_event_loop().time() - bullet["creation_time"] > BULLET_LIFETIME_SERVER:
        #         BULLETS.remove(bullet)

        await asyncio.sleep(0.05) # Run game loop every 50ms (20 FPS server-side)

async def main():
    """Starts the WebSocket server and the main game loop."""
    # Print maze data for debugging
    for i, layer_maze in enumerate(GENERATED_MAZE_DATA):
        print(f"\n=== MAZE LAYER {i} ===")
        for r_idx, row in enumerate(layer_maze):
            print(f"Row {r_idx:2}: {' '.join(row)}")

    debug_coordinates() # Print coordinate debugging after maze is fully set up

    server = await websockets.serve(handle_client_messages, "0.0.0.0", 8765)
    print("Multiplayer Maze Server started on ws://0.0.0.0:8765")

    # Run the game loop concurrently with the WebSocket server
    await asyncio.gather(server.wait_closed(), game_loop())

if __name__ == "__main__":
    # Initialize MazeGenerator and generate maze data once at startup
    # This ensures the maze and start/end points are fixed for the server's lifetime
    # To get a new maze/start point, the server process needs to be restarted.
    MAZE_GENERATOR = MazeGenerator(MAZE_WIDTH, MAZE_HEIGHT, NUM_MAZE_LAYERS)
    GENERATED_MAZE_DATA = MAZE_GENERATOR.generate()
    START_GRID_COORDS = MAZE_GENERATOR.get_start_coords()
    END_GRID_COORDS = MAZE_GENERATOR.get_end_coords()
    
    # INITIAL_START_POSITION is now just a fallback if get_random_open_position_on_layer fails
    # It's no longer the fixed spawn point for new connections/respawns.

    asyncio.run(main())
