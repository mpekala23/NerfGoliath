import sys

sys.path.append("..")

import arcade
import socket
from schema import ConnectRequest, ConnectResponse, Machine, wire_decode, Event, Vec2
from connections.consts import WATCHER_IP, WATCHER_PORT
from utils import print_success
from threading import Thread
from queue import Queue
from game import consts as gconsts
import math
import random


class Display(arcade.Window):
    def __init__(self):
        super().__init__(gconsts.SCREEN_WIDTH, gconsts.SCREEN_HEIGHT, "Watcher")
        self.players: dict[str, Vec2] = {}
        self.balls: list[tuple[Vec2, Vec2, str]] = []
        arcade.set_background_color((250, 250, 250))

    def reset_positions(self):
        radius = 200
        middle = Vec2(gconsts.SCREEN_WIDTH / 2, gconsts.SCREEN_HEIGHT / 2)
        for i, player in enumerate(self.players):
            angle = i * 2 * 3.14159 / len(self.players)
            self.players[player] = middle + Vec2(
                radius * math.cos(angle), radius * math.sin(angle)
            )

    def add_player(self, player: str):
        self.players[player] = Vec2(0, 0)
        self.reset_positions()

    def spawn_ball(self, event: Event):
        self.balls.append(
            (self.players[event.source], self.players[event.sink], event.event_type)
        )

    def on_update(self, delta_time: float):
        new_balls = []
        for ball in self.balls:
            start, end, event_type = ball
            dir = end - start
            if dir.x**2 + dir.y**2 < 5:
                continue
            dir.normalize()
            new_balls.append((start + dir * 5, end, event_type))
        self.balls = new_balls

    def get_char(self, event_type):
        if event_type == "input":
            return "i"
        if event_type == "game":
            return "g"
        return "?"

    def on_draw(self):
        self.clear()
        ball_radius = 25
        for ball in self.balls:
            start, end, event_type = ball
            color = (255, 5, 5) if event_type == "input" else (5, 5, 255)
            arcade.draw_circle_outline(start.x, start.y, ball_radius, color)
            arcade.draw_text(
                f"{self.get_char(event_type)}",
                start.x,
                start.y,
                color,
                14,
                font_name="Kenney Pixel Square",
            )

        player_radius = 50
        for player in self.players:
            arcade.draw_circle_filled(
                self.players[player].x,
                self.players[player].y,
                player_radius,
                (50, 50, 50),
            )
            arcade.draw_text(
                f"{player}",
                self.players[player].x,
                self.players[player].y,
                (250, 250, 250),
                14,
                font_name="Kenney Pixel Square",
            )


class Watcher:
    """
    The watcher exists as a central place that players can send information
    so the network can be visualized
    """

    def __init__(self):
        self.socket_map: dict[str, socket.socket] = {}
        self.events: Queue[Event] = Queue()

    def start(self):
        """
        Starts the watcher server
        """
        watch_thread = Thread(target=self.watch)
        watch_thread.start()
        display = Display()
        self.display = display
        arcade.run()

    def watch(self):
        """
        Starts the negotiator server
        """
        # Listen for new player connections
        process_thread = Thread(target=self.process_job)
        process_thread.start()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((WATCHER_IP, WATCHER_PORT))
        sock.listen()
        while True:
            try:
                print("Waiting for connection")
                conn, addr = sock.accept()
                data = conn.recv(1024)
                if not data or len(data) <= 0:
                    continue
                req = wire_decode(data)
                if type(req) != ConnectRequest:
                    continue
                print_success(f"{req.name} being watched")
                self.display.add_player(req.name)
                self.socket_map[req.name] = conn
                job_thread = Thread(target=self.watch_job, args=(req.name,))
                job_thread.start()
                # Let the machine know that it has been connected
                conn.send(ConnectResponse(True).encode())
            except Exception as e:
                sock.close()
                sock.listen()
                break

    def watch_job(self, name: str):
        """
        Watches a machine
        """
        conn = self.socket_map[name]
        while True:
            data = conn.recv(1024)
            if not data or len(data) <= 0:
                break
            jobs = data.split(b"#")
            for job in jobs:
                try:
                    req = wire_decode(job)
                    if type(req) != Event:
                        continue
                    self.events.put(req)
                except:
                    pass

    def process_job(self):
        """
        Spam looks through the queue to handle events
        """
        while True:
            event = self.events.get()
            self.display.spawn_ball(event)


def create_watcher():
    """
    Creates a negotiator and starts it
    """
    watcher = Watcher()
    watcher.start()


if __name__ == "__main__":
    create_watcher()
