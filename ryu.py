from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet, ethernet, ether_types, ipv4, tcp
from ryu.app.wsgi import WSGIApplication, ControllerBase, route
from webob import Response
import json
import subprocess

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
                self.logger.info("Allowing communication: %s -> %s", src, dst)
                self._delete_isolation_rules(datapath, src, dst)
                self.intents['allow'].append((src, dst))
                self.add_host_communication_rule(datapath, src, dst)

            elif intent_type == 'isolate':
                self.logger.info("Isolating communication: %s <-> %s", src, dst)
                self._delete_allow_rules(datapath, src, dst)
                self.intents['isolate'].append((src, dst))
                self.add_isolation_rule(datapath, src, dst)

            elif intent_type == 'priority_http':
                self.logger.info("Prioritizing HTTP traffic")
                self.intents['priority_http'].append((src, dst))
                self.add_http_priority_rule(datapath)

            elif intent_type == 'limit_bw' and bw:
                self.logger.info("Limiting bandwidth between %s and %s to %s Mbps", src, dst, bw)
                self.intents['limit_bw'].append((src, dst, bw))
                self.add_bandwidth_limit_rule(datapath, src, dst, bw)

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

    def add_http_priority_rule(self, datapath):
        """Prioritize HTTP traffic."""
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(dl_type=0x0800, nw_proto=6, tp_dst=80)  # Match TCP port 80 (HTTP)
        actions = [parser.OFPActionOutput(ofproto_v1_0.OFPP_FLOOD)]
        self.add_flow(datapath, match, actions, priority=5)  # Higher priority for HTTP

    def add_bandwidth_limit_rule(self, datapath, src, dst, bw):
        """
        Add a flow rule to direct traffic between src and dst, leveraging manually pre-configured queues.
        Since OpenFlow v1.0 lacks OFPActionSetQueue, match flows and rely on static queue assignment.
        """
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(dl_src=haddr_to_bin(src), dl_dst=haddr_to_bin(dst))

        # Specify output port (must match port configured with queues, e.g., s1-eth1)
        output_port = 1  # Replace with the correct port ID for s1-eth1 in your topology

        actions = [parser.OFPActionOutput(output_port)]
        self.add_flow(datapath, match, actions, priority=4)

        self.logger.info(f"Added bandwidth limit rule for {src} -> {dst} with pre-configured queue.")



    def _create_queue(self, port_name, max_rate):
        """
        Create a queue with the specified max_rate on the given port using ovs-vsctl.
        :param port_name: The OVS port where the queue is to be created (e.g., "s1-eth1").
        :param max_rate: Bandwidth limit in Mbps (e.g., 10 for 10 Mbps).
        :return: Queue ID (integer) or None if creation fails.
        """
        queue_id = 1  # Assign a default queue ID
        try:
            # Convert max_rate to bits per second for ovs-vsctl
            max_rate_bps = int(max_rate) * 1000000

            # Set QoS on the port and create a queue
            qos_command = [
                "sudo",  # Add sudo for root privileges
                "ovs-vsctl",
                "--",
                "--id=@q{queue_id}".format(queue_id=queue_id),
                "create",
                "Queue",
                f"other-config:max-rate={max_rate_bps}",
                "--",
                "--id=@qos1",
                "create",
                "QoS",
                "type=linux-htb",
                f"other-config:max-rate={max_rate_bps}",
                f"queues:{queue_id}=@q{queue_id}",
                "--",
                "set",
                "Port",
                port_name,
                "qos=@qos1"
            ]

            # Execute the ovs-vsctl command
            subprocess.run(qos_command, check=True)
            self.logger.info(f"Queue {queue_id} created on port {port_name} with max rate {max_rate} Mbps.")
            return queue_id
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create queue on port {port_name}: {e}")
            return None

    def _delete_allow_rules(self, datapath, src, dst):
        """Delete allow rules for the given src and dst."""
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(dl_src=haddr_to_bin(src), dl_dst=haddr_to_bin(dst))
        self.delete_flow(datapath, match)

    def _delete_isolation_rules(self, datapath, src, dst):
        """Delete isolation rules for the given src and dst."""
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(dl_src=haddr_to_bin(src), dl_dst=haddr_to_bin(dst))
        self.delete_flow(datapath, match)

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
            bw = body.get('bw', None)  # Optional bandwidth for limit_bw

            if intent_type in ['allow', 'isolate', 'priority_http', 'limit_bw'] and src and dst:
                self.snowflake_app.add_intent(intent_type, src, dst, bw)
                return Response(status=200, body=json.dumps({'status': 'success'}))
            else:
                return Response(status=400, body=json.dumps({'status': 'invalid input'}))
        except Exception as e:
            return Response(status=500, body=json.dumps({'error': str(e)}))
