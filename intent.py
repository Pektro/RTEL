import requests
import json
import os

# Define a mapping of host names to MAC addresses
HOST_MAC_MAPPING = {
    "h1": "00:00:00:00:00:01",
    "h2": "00:00:00:00:00:02",
    "h3": "00:00:00:00:00:03",
    "h4": "00:00:00:00:00:04",
    "h5": "00:00:00:00:00:05",
    "h6": "00:00:00:00:00:06",
    "h7": "00:00:00:00:00:07",
    "h8": "00:00:00:00:00:08",
    "h9": "00:00:00:00:00:09",
    "h10": "00:00:00:00:00:10",
    "h11": "00:00:00:00:00:11",
    "h12": "00:00:00:00:00:12"
}

def send_intent(intent_type, src_host=None, dst_host=None, bw=None):
    """
    Function to send intent to Ryu controller via REST API.
    :param intent_type: Type of intent ('allow', 'isolate', 'priority_http', 'limit_bw')
    :param src_host: Source host (e.g., 'h1'), optional for 'priority_http'
    :param dst_host: Destination host (e.g., 'h5'), optional for 'priority_http'
    :param bw: Bandwidth limit (e.g., '1Mbps') for 'limit_bw' intent
    """
    url = "http://localhost:8080/intent/add"
    headers = {"Content-Type": "application/json"}

    # Resolve MAC addresses from host names, if needed
    src_mac = HOST_MAC_MAPPING.get(src_host) if src_host else None
    dst_mac = HOST_MAC_MAPPING.get(dst_host) if dst_host else None

    if (intent_type in ['allow', 'isolate']) and (not src_mac or not dst_mac):
        print(f"Error: Invalid host name(s). Please check your input ({src_host}, {dst_host}).")
        return

    payload = {
        "type": intent_type,
        "src": src_mac,
        "dst": dst_mac,
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            print("Success:", response.json())
        elif response.status_code == 400:
            print("Invalid Input:", response.json())
        else:
            print("Error:", response.status_code, response.json())
    except Exception as e:
        print("Failed to send intent:", str(e))

def process_prompt(prompt):
    if "snowflake topology" in prompt.lower():
        print("Creating a Snowflake topology with 7 switches and 12 hosts...")
        try:
            os.system("gnome-terminal -- bash -c 'sudo mn --custom snowflake.py --topo mytopo --controller=remote,ip=127.0.0.1 --switch=ovsk; exec bash' > /tmp/snowflake_terminal.log")
            print("Topology created successfully.")
        except Exception as e:
            print(f"Failed to create topology: {e}")
    elif "isolate" in prompt.lower():
        print("Isolating hosts from the rest of the network...")
        send_intent("isolate", "h10", "h11")
    elif "reconnect" in prompt.lower() and "hosts 10 and 11" in prompt.lower():
        print("Reconnecting hosts and allowing them to communicate the other hosts...")
        send_intent("allow", "h10", "h11")
    else:
        print("Unrecognized command. Please try again.")

def main():
    print("#########################################")
    print("##                                     ##")
    print("##   Welcome to the IBN Demonstrator!  ##")
    print("##                                     ##")
    print("#########################################")
    print("Created by: Antonio Lopes & Pedro Duarte")
    print("Type 'exit' anytime to quit.\n")

    while True:
        prompt = input("Enter a command: ").strip()
        if prompt.lower() == 'exit':
            print("Exiting...")
            break
        process_prompt(prompt)

if __name__ == "__main__":
    main()
