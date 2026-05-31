####################################################
# DVrouter.py
# Name:
# HUID:
#####################################################

from router import Router
from packet import Packet
import json
import sys



class DVrouter(Router):
    """Distance vector routing protocol implementation."""

    def __init__(self, addr, heartbeat_time):
        Router.__init__(self, addr)
        self.heartbeat_time = heartbeat_time
        self.last_time = 0

        self.routing_table = {}
        self.routing_table[self.addr] = [0, -1]

        self.ports_info = {}

    def broadcast_routes(self):
        try:
            content = json.dumps(self.routing_table)
            for port in self.ports_info:
                neighbor_addr = self.ports_info[port][0]
                p = Packet(kind=Packet.ROUTING, src_addr=self.addr, dst_addr=neighbor_addr, content=content)
                self.send(port, p)
        except Exception as e:
            print(f"\n[ERROR {self.addr}]: {e}", file=sys.stderr)

    def handle_packet(self, port, packet):
        try:
            if packet.is_traceroute:
                if packet.dst_addr in self.routing_table and self.routing_table[packet.dst_addr][0] < 16:
                    out_port = self.routing_table[packet.dst_addr][1]
                    if out_port != -1:
                        self.send(out_port, packet)
            else:
                if port not in self.ports_info:
                    return

                neighbor_table = json.loads(packet.content)
                cost_to_neighbor = self.ports_info[port][1]
                table_changed = False

                for dest, data in neighbor_table.items():
                    neighbor_cost = data[0]
                    new_cost = cost_to_neighbor + neighbor_cost

                    if new_cost > 16:
                        new_cost = 16

                    if dest not in self.routing_table or self.routing_table[dest][1] == port or new_cost < \
                            self.routing_table[dest][0]:
                        if dest not in self.routing_table or self.routing_table[dest][0] != new_cost or \
                                self.routing_table[dest][1] != port:
                            self.routing_table[dest] = [new_cost, port]
                            table_changed = True

                if table_changed:
                    self.broadcast_routes()
        except Exception as e:
            print(f"\n[ERROR {self.addr}]: {e}", file=sys.stderr)

    def handle_new_link(self, port, endpoint, cost):
        self.ports_info[port] = [endpoint, cost]
        if endpoint not in self.routing_table or cost < self.routing_table[endpoint][0]:
            self.routing_table[endpoint] = [cost, port]
        self.broadcast_routes()

    def handle_remove_link(self, port):
        if port in self.ports_info:
            del self.ports_info[port]

        for dest in self.routing_table:
            if self.routing_table[dest][1] == port:
                self.routing_table[dest][0] = 16

        self.broadcast_routes()

    def handle_time(self, time_ms):
        if time_ms - self.last_time >= self.heartbeat_time:
            self.last_time = time_ms
            self.broadcast_routes()

    def __repr__(self):
        """Representation for debugging in the network visualizer."""
        # TODO
        #   NOTE This method is for your own convenience and will not be graded
        return f"DVrouter(addr={self.addr})"
