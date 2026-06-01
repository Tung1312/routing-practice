####################################################
# LSrouter.py
# Name:
# HUID:
#####################################################

import json

from packet import Packet
from router import Router


class LSrouter(Router):
    """Link state routing protocol implementation.

    Add your own class fields and initialization code (e.g. to create forwarding table
    data structures). See the `Router` base class for docstrings of the methods to
    override.
    """

    def __init__(self, addr, heartbeat_time):
        Router.__init__(self, addr)  # Initialize base class - DO NOT REMOVE
        self.heartbeat_time = heartbeat_time
        self.last_time = 0
        self.routing_table = {self.addr: -1}
        self.ports_info = {}
        self.graph = {}
        self.lsa_seq_tracker = {}
        self.my_seq = 0

    def broadcast_lsa(self):
        self.my_seq += 1
        my_neighbors = {}
        for port, info in self.ports_info.items():
            my_neighbors[info[0]] = info[1]

        lsa_data = {"source": self.addr, "seq": self.my_seq, "neighbors": my_neighbors}
        content = json.dumps(lsa_data)

        self.graph[self.addr] = my_neighbors

        for port in self.ports_info:
            p = Packet(Packet.ROUTING, self.addr, self.ports_info[port][0], content)
            self.send(port, p)

    def run_dijkstra(self):
        costs = {}
        first_hops = {}

        all_nodes = set(self.graph.keys())
        for u in self.graph:
            all_nodes.update(self.graph[u].keys())

        for node in all_nodes:
            costs[node] = 16

        costs[self.addr] = 0
        first_hops[self.addr] = -1

        for port, info in self.ports_info.items():
            neighbor, link_cost = info[0], info[1]
            costs[neighbor] = link_cost
            first_hops[neighbor] = port

        unvisited = set(all_nodes)

        while unvisited:
            u = min(unvisited, key=lambda node: costs[node])

            if costs[u] >= 16:
                break
            unvisited.remove(u)
            if u in self.graph:
                for v, edge_cost in self.graph[u].items():
                    if v in unvisited:
                        new_cost = costs[u] + edge_cost
                        if new_cost > 16:
                            new_cost = 16

                        if new_cost < costs[v]:
                            costs[v] = new_cost
                            first_hops[v] = first_hops[u]

        new_routing_table = {}
        for node in all_nodes:
            if costs[node] < 16:
                new_routing_table[node] = first_hops[node]

        self.routing_table = new_routing_table

    def handle_packet(self, port, packet):
        """Process incoming packet."""

        if packet.is_traceroute:
            if packet.dst_addr in self.routing_table:
                out_port = self.routing_table[packet.dst_addr]
                if out_port != -1:
                    self.send(out_port, packet)
        else:
            lsa_data = json.loads(packet.content)
            source = lsa_data["source"]
            seq = lsa_data["seq"]
            neighbors = lsa_data["neighbors"]
            if source in self.lsa_seq_tracker and seq <= self.lsa_seq_tracker[source]:
                return
            self.lsa_seq_tracker[source] = seq
            self.graph[source] = neighbors

            for p_idx in self.ports_info:
                if p_idx != port:
                    forward_packet = Packet(
                        Packet.ROUTING,
                        packet.src_addr,
                        self.ports_info[p_idx][0],
                        packet.content,
                    )
                    self.send(p_idx, forward_packet)
            self.run_dijkstra()

    def handle_new_link(self, port, endpoint, cost):
        """Handle new link."""
        self.ports_info[port] = [endpoint, cost]
        self.broadcast_lsa()
        self.run_dijkstra()

    def handle_remove_link(self, port):
        """Handle removed link."""
        if port in self.ports_info:
            del self.ports_info[port]
        my_neighbors = {}
        for p, info in self.ports_info.items():
            my_neighbors[info[0]] = info[1]
        self.graph[self.addr] = my_neighbors

        self.broadcast_lsa()
        self.run_dijkstra()

    def handle_time(self, time_ms):
        """Handle current time."""
        if time_ms - self.last_time >= self.heartbeat_time:
            self.last_time = time_ms
            # TODO
            #   broadcast the link state of this router to all neighbors
            pass

    def __repr__(self):
        """Representation for debugging in the network visualizer."""
        # TODO
        #   NOTE This method is for your own convenience and will not be graded
        return f"LSrouter(addr={self.addr})"
