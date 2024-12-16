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
        self.intents = {'allow': [], 'isolate': []}

        # Register WSGI controller
        wsgi = kwargs['wsgi']
        wsgi.register(SnowflakeAPI, {snowflake_instance_name: self})

    def add_flow(self, datapath, match, actions, priority=1):
        """Add a flow entry."""
        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, command=datapath.ofproto.OFPFC_ADD,
            priority=priority, actions=actions)
        datapath.send_msg(mod)

    def delete_flow(self, datapath, src, dst):
        """Delete a flow entry based on src and dst MAC addresses."""
        parser = datapath.ofproto_parser

        # Match and delete flows in both directions
        for direction in [(src, dst), (dst, src)]:
            match = parser.OFPMatch(dl_src=haddr_to_bin(direction[0]), dl_dst=haddr_to_bin(direction[1]))
            mod = parser.OFPFlowMod(
                datapath=datapath, match=match,
                command=datapath.ofproto.OFPFC_DELETE
            )
            datapath.send_msg(mod)

    def apply_intent(self, datapath):
        """Apply all intents (allow and isolate) to the datapath."""
        for src, dst in self.intents['isolate']:
            self.add_isolation_rule(datapath, src, dst)

        for src, dst in self.intents['allow']:
            self.add_host_communication_rule(datapath, src, dst)

    def add_intent(self, intent_type, src=None, dst=None):
        """Handle dynamic addition of intents."""
        for dpid, datapath in self.datapaths.items():
            if intent_type == 'allow':
                self.logger.info("Allowing communication: %s -> %s", src, dst)
                # Remove isolation rules for the same pair
                self.delete_flow(datapath, src, dst)
                self.delete_flow(datapath, dst, src)
                # Remove from isolation intents
                self.intents['isolate'] = [
                    (s, d) for s, d in self.intents['isolate'] if (s, d) != (src, dst) and (s, d) != (dst, src)
                ]
                # Add to allow intents
                if (src, dst) not in self.intents['allow']:
                    self.intents['allow'].append((src, dst))

            elif intent_type == 'isolate':
                self.logger.info("Isolating communication: %s <-> %s", src, dst)
                # Remove from allow intents
                self.intents['allow'] = [
                    (s, d) for s, d in self.intents['allow'] if (s, d) != (src, dst) and (s, d) != (dst, src)
                ]
                # Add to isolate intents
                if (src, dst) not in self.intents['isolate']:
                    self.intents['isolate'].append((src, dst))

            # Reapply all intents for the current datapath
            self.apply_intent(datapath)

    def add_host_communication_rule(self, datapath, src, dst):
        """Allow communication between specific hosts."""
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(dl_src=haddr_to_bin(src), dl_dst=haddr_to_bin(dst))
        actions = [parser.OFPActionOutput(ofproto_v1_0.OFPP_FLOOD)]
        self.add_flow(datapath, match, actions, priority=2)

    def add_isolation_rule(self, datapath, src, dst):
        """Isolate specific hosts by dropping traffic."""
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(dl_src=haddr_to_bin(src), dl_dst=haddr_to_bin(dst))
        self.add_flow(datapath, match, [], priority=3)  # Drop rule with high priority

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
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

        # Forward packet out if no intent matches
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
        self.apply_intent(datapath)  # Reapply intents to the new switch

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
