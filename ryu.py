from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet, ethernet, ether_types
from ryu.app.wsgi import WSGIApplication, ControllerBase, route
from webob import Response
import json

# WSGI Controller Name
snowflake_instance_name = 'snowflake_api_app'


class SnowflakeIntentBasedSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]
    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(SnowflakeIntentBasedSwitch, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = {}  # Map of dpid -> datapath objects
        self.intents = {'allow': [], 'isolate': [], 'priority_http': [], 'limit_bw': []}

        # Register WSGI controller
        wsgi = kwargs['wsgi']
        wsgi.register(SnowflakeAPI, {snowflake_instance_name: self})

    def add_flow(self, datapath, match, actions, priority=1):
        """Add a flow entry."""
        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, command=datapath.ofproto.OFPFC_ADD,
            priority=priority, actions=actions)
        datapath.send_msg(mod)

    def delete_flow(self, datapath, match):
        """Delete flow entries matching the given match."""
        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, command=datapath.ofproto.OFPFC_DELETE)
        datapath.send_msg(mod)

    def add_intent(self, intent_type, src=None, dst=None, bw=None):
        """Handle dynamic addition of intents."""
        for dpid, datapath in self.datapaths.items():
            if intent_type == 'allow':
                self.logger.info("Restoring normal communication: %s <-> %s", src, dst)
                self.remove_isolation_rule(datapath, src, dst)
                self.add_host_communication_rule(datapath, src, dst)

            elif intent_type == 'isolate':
                self.logger.info("Isolating hosts: Only %s <-> %s allowed", src, dst)
                self.add_isolation_rule(datapath, src, dst)

            elif intent_type == 'priority_http':
                self.logger.info("Prioritizing HTTP traffic")
                self.add_http_priority_rule(datapath)

    def add_isolation_rule(self, datapath, src, dst):
        """Isolate specific hosts while allowing them to communicate only with each other."""
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        # Drop all other traffic from src to others
        match = parser.OFPMatch(dl_src=haddr_to_bin(src))
        self.add_flow(datapath, match, [], priority=9)

        # Drop all other traffic to src from others
        match = parser.OFPMatch(dl_dst=haddr_to_bin(src))
        self.add_flow(datapath, match, [], priority=9)

        # Drop all other traffic from dst to others
        match = parser.OFPMatch(dl_src=haddr_to_bin(dst))
        self.add_flow(datapath, match, [], priority=9)

        # Drop all other traffic to dst from others
        match = parser.OFPMatch(dl_dst=haddr_to_bin(dst))
        self.add_flow(datapath, match, [], priority=9)

        # Allow communication between src -> dst
        match = parser.OFPMatch(dl_src=haddr_to_bin(src), dl_dst=haddr_to_bin(dst))
        actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]
        self.add_flow(datapath, match, actions, priority=10)

        # Allow communication between dst -> src
        match = parser.OFPMatch(dl_src=haddr_to_bin(dst), dl_dst=haddr_to_bin(src))
        actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]
        self.add_flow(datapath, match, actions, priority=10)

        self.logger.info("Isolation applied: Hosts %s and %s can only communicate with each other.", src, dst)

    def remove_isolation_rule(self, datapath, src, dst):
        """Remove isolation rules and restore normal communication for specific hosts."""
        parser = datapath.ofproto_parser

        # Remove all drop rules involving src and dst
        match = parser.OFPMatch(dl_src=haddr_to_bin(src))
        self.delete_flow(datapath, match)

        match = parser.OFPMatch(dl_dst=haddr_to_bin(src))
        self.delete_flow(datapath, match)

        match = parser.OFPMatch(dl_src=haddr_to_bin(dst))
        self.delete_flow(datapath, match)

        match = parser.OFPMatch(dl_dst=haddr_to_bin(dst))
        self.delete_flow(datapath, match)

        self.logger.info("Isolation removed: Restored communication for %s and %s.", src, dst)

    def add_host_communication_rule(self, datapath, src, dst):
        """Allow communication between specific hosts."""
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        # Allow src -> dst
        match = parser.OFPMatch(dl_src=haddr_to_bin(src), dl_dst=haddr_to_bin(dst))
        actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]
        self.add_flow(datapath, match, actions, priority=1)

        # Allow dst -> src
        match = parser.OFPMatch(dl_src=haddr_to_bin(dst), dl_dst=haddr_to_bin(src))
        actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]
        self.add_flow(datapath, match, actions, priority=1)

        self.logger.info("Normal communication allowed between %s and %s.", src, dst)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """Handle packet-in events for MAC learning and forwarding."""
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return  # Ignore LLDP packets

        dst = eth.dst
        src = eth.src
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = msg.in_port

        out_port = self.mac_to_port[dpid].get(dst, ofproto.OFPP_FLOOD)
        actions = [parser.OFPActionOutput(out_port)]
        data = msg.data if msg.buffer_id == ofproto.OFP_NO_BUFFER else None
        out = parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id,
            in_port=msg.in_port, actions=actions, data=data)
        datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, MAIN_DISPATCHER)
    def switch_features_handler(self, ev):
        """Handle new switch connection."""
        datapath = ev.msg.datapath
        self.datapaths[datapath.id] = datapath
        self.logger.info("Switch connected: %s", datapath.id)

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def state_change_handler(self, ev):
        """Handle switch state changes."""
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            self.datapaths.pop(datapath.id, None)


# WSGI REST API Controller
class SnowflakeAPI(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(SnowflakeAPI, self).__init__(req, link, data, **config)
        self.snowflake_app = data[snowflake_instance_name]

    @route('add_intent', '/intent/add', methods=['POST'])
    def add_intent(self, req, **kwargs):
        try:
            body = json.loads(req.body)
            intent_type = body.get('type')
            src = body.get('src')
            dst = body.get('dst')

            if intent_type in ['allow', 'isolate'] and src and dst:
                self.snowflake_app.add_intent(intent_type, src, dst)
                return Response(status=200, body=json.dumps({'status': 'success'}))
            else:
                return Response(status=400, body=json.dumps({'status': 'invalid input'}))
        except Exception as e:
            return Response(status=500, body=json.dumps({'error': str(e)}))
