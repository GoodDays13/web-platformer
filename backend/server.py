import asyncio
import copy
import json
import time
import websockets

from constants import CANVAS_H, TARGET_TICK_RATE, TICK_INTERVAL, HEIGHT_THRESHOLD, FLAG
from game import Game

# Track state per connection: websocket -> player_state
connected_players: dict[websockets.ServerConnection, Game] = {}
saves: dict[websockets.ServerConnection, Game] = {}
timeouts: dict[websockets.ServerConnection, asyncio.Task] = {}

async def close_after_timeout(websocket: websockets.ServerConnection, delay: float):
    await asyncio.sleep(30)
    await websocket.close(code=4000, reason='Idle timeout')

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
                        "x": round(game.player.x, 2),
                        "y": round(game.player.y - game.camera_y, 2),
                        "width": game.player.width,
                        "height": game.player.height,
                        "color": "#4fc3f7",
                    },
                    *[
                        {
                            "x": round(p.x, 2),
                            "y": round(p.y - game.camera_y, 2),
                            "width": p.width,
                            "height": p.height,
                            "color": "#81c784",
                        }
                        for p in game.platforms
                        if -p.height <= (p.y - game.camera_y) <= CANVAS_H
                    ],
                    *([{"flag": FLAG}] if game.player.y > HEIGHT_THRESHOLD else []),
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
    player_id = websocket.request.headers["X-Forwarded-For"] if "X-Forwarded-For" in websocket.request.headers else websocket.remote_address
    connected_players[websocket] = make_game()
    timeouts[websocket] = asyncio.create_task(close_after_timeout(websocket, 30))
    print(f"[+] Player {player_id} connected. Total: {len(connected_players)}")

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                message_type = data.get('type')
                key = data.get('key')
                down = data.get('down')

                if message_type and message_type == 'ping':
                    await websocket.send('{"type":"pong"}')

                elif key:
                    # print(f"[{player_id}] {'pressed' if down else 'released'}: {key}")
                    timeouts[websocket].cancel()
                    timeouts[websocket] = asyncio.create_task(close_after_timeout(websocket, 30))
                    game = connected_players[websocket]
                    if key == 'save':
                        saves[websocket] = copy.deepcopy(game)
                    elif key == 'load' and websocket in saves:
                        connected_players[websocket] = copy.deepcopy(saves[websocket])
                        game = connected_players[websocket]
                    handle_input(game, key, down)
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
    loop = asyncio.get_running_loop()
    stop = loop.create_future()

    # Resolve the future on SIGTERM or SIGINT
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set_result, None)

    async with websockets.serve(handle_connection, "0.0.0.0", 8765):
        game_task = asyncio.create_task(game_loop())

        try:
            await stop  # run until a signal is received
        finally:
            game_task.cancel()
            try:
                await game_task
            except asyncio.CancelledError:
                pass

if __name__ == "__main__":
    import signal
    asyncio.run(main())
