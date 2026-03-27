import asyncio
import json
import time
import websockets

from game import Game

# Track state per connection: websocket -> player_state
connected_players: dict[websockets.ServerConnection, Game] = {}

CANVAS_W = 800
CANVAS_H = 400
PLAYER_SPEED = 5
TARGET_TICK_RATE = 64      # ticks per second
TICK_INTERVAL = 1.0 / TARGET_TICK_RATE

def make_game():
    return Game()

def handle_input(game: Game, key, down):
    if down:
        game.held_keys.add(key)
    else:
        game.held_keys.discard(key)

    game.handle_input(key, down)

async def game_loop():
    print(f'Game loop started @ {TARGET_TICK_RATE} Hz')

    last_time = time.perf_counter()

    while True:
        current_time = time.perf_counter()
        delta_time = current_time - last_time
        last_time = current_time

        # === GAME SIMULATION ===
        for websocket, game in list(connected_players.items()):
            try:
                game.update(delta_time)

                await websocket.send(json.dumps([
                    {
                        "x": game.player.x,
                        "y": game.player.y,
                        "width": game.player.width,
                        "height": game.player.height,
                        "color": "#4fc3f7",
                    },
                ]))

            except (websockets.exceptions.ConnectionClosed,
                    websockets.exceptions.ConnectionClosedOK):
                # Client disconnected silently
                if websocket in connected_players:
                    del connected_players[websocket]
            except Exception as e:
                print(f"Error in game loop for a client: {e}")
                if websocket in connected_players:
                    del connected_players[websocket]

        # Compensate for time spent doing work
        work_time = time.perf_counter() - current_time
        sleep_time = max(0.0, TICK_INTERVAL - work_time)
        await asyncio.sleep(sleep_time)


async def handle_connection(websocket: websockets.ServerConnection):
    player_id = id(websocket)
    connected_players[websocket] = make_game()
    print(f"[+] Player {player_id} connected. Total: {len(connected_players)}")

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                key = data.get('key')
                down = data.get('down')

                if key:
                    print(f"[{player_id}] {'pressed' if down else 'released'}: {key}")
                    handle_input(connected_players[websocket], key, down)
            except json.JSONDecodeError:
                print(f"[{player_id}] received invalid JSON")

    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"Error in connection {player_id}: {e}")
    finally:
        # Clean up if still present
        if websocket in connected_players:
            del connected_players[websocket]
        print(f"[-] Player {player_id} disconnected. Total: {len(connected_players)}")


async def main():
    print("Server running on ws://localhost:8765")

    async with websockets.serve(handle_connection, "0.0.0.0", 8765):
        game_task = asyncio.create_task(game_loop())

        try:
            await asyncio.Future()  # run forever
        finally:
            game_task.cancel()
            try:
                await game_task
            except asyncio.CancelledError:
                pass


if __name__ == "__main__":
    asyncio.run(main())
