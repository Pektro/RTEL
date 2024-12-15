from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

class SnowflakeIntentBasedSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SnowflakeIntentBasedSwitch, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    def add_flow(self, datapath, match, actions, priority=1):
        ofproto = datapath.ofproto
        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, cookie=0,
            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=priority, actions=actions)
        datapath.send_msg(mod)

    def add_host_communication_rule(self, datapath, src, dst, out_port):
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(dl_src=haddr_to_bin(src), dl_dst=haddr_to_bin(dst))
        actions = [parser.OFPActionOutput(out_port)]
        self.add_flow(datapath, match, actions, priority=2)

    def add_isolation_rule(self, datapath, src, dst):
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(dl_src=haddr_to_bin(src), dl_dst=haddr_to_bin(dst))
        self.add_flow(datapath, match, [], priority=3)  # No actions = drop traffic

    def add_http_priority_rule(self, datapath, in_port, out_port):
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(
            in_port=in_port,
            dl_type=ether_types.ETH_TYPE_IP,
            nw_proto=6,  # TCP protocol
            tp_dst=80    # HTTP traffic
        )
        actions = [parser.OFPActionOutput(out_port)]
        self.add_flow(datapath, match, actions, priority=4)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, msg.in_port)

        # Learn MAC address to avoid FLOOD next time
        self.mac_to_port[dpid][src] = msg.in_port

        # Define output port
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

        # Install flow rules
        if out_port != ofproto.OFPP_FLOOD:
            # Example intents for your topology
            if src == '00:00:00:00:00:01' and dst == '00:00:00:00:00:03':
                self.add_host_communication_rule(datapath, src, dst, out_port)
            elif src == '00:00:00:00:00:05' or dst == '00:00:00:00:00:05':
                self.add_isolation_rule(datapath, src, dst)
            elif eth.ethertype == ether_types.ETH_TYPE_IP:
                self.add_http_priority_rule(datapath, msg.in_port, out_port)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port,
            actions=actions, data=data)
        datapath.send_msg(out)
