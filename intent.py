import requests
import json

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

    if (intent_type in ['allow', 'isolate', 'limit_bw']) and (not src_mac or not dst_mac):
        print(f"Error: Invalid host name(s). Please check your input ({src_host}, {dst_host}).")
        return

    payload = {
        "type": intent_type,
        "src": src_mac,
        "dst": dst_mac,
    }

    # Add bandwidth if specified for limit_bw intent
    if intent_type == 'limit_bw' and bw:
        payload["bw"] = bw

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


def main():
    print("#########################################")
    print("##                                     ##")
    print("##   Welcome to the IBN Demonstrator!  ##")
    print("##                                     ##")
    print("#########################################")
    print("Created by: Antonio Lopes & Pedro Duarte")
    print("Type 'exit' anytime to quit.\n")

    while True:
        print("Available Intent Types:")
        print("1. Allow Communication")
        print("2. Isolate Hosts")
        print("3. Prioritize HTTP Traffic")
        print("4. Limit Bandwidth")
        intent_choice = input("Enter choice (1, 2, 3, or 4): ").strip()

        if intent_choice.lower() == 'exit':
            print("Exiting...")
            break

        if intent_choice == '1':
            intent_type = 'allow'
        elif intent_choice == '2':
            intent_type = 'isolate'
        elif intent_choice == '3':
            intent_type = 'priority_http'
        elif intent_choice == '4':
            intent_type = 'limit_bw'
        else:
            print("Invalid choice. Try again.")
            continue

        src_host, dst_host, bw = None, None, None

        if intent_type in ['allow', 'isolate', 'limit_bw']:
            src_host = input("Enter Source Host (e.g., h1): ").strip()
            if src_host.lower() == 'exit':
                break

            dst_host = input("Enter Destination Host (e.g., h5): ").strip()
            if dst_host.lower() == 'exit':
                break

        if intent_type == 'limit_bw':
            bw = input("Enter Bandwidth Limit (e.g., 1Mbps): ").strip()
            if bw.lower() == 'exit':
                break

        # Send intent
        if intent_type in ['allow', 'isolate', 'limit_bw']:
            print(f"\nSending '{intent_type}' intent from {src_host} to {dst_host}...")
            send_intent(intent_type, src_host, dst_host, bw)
        elif intent_type == 'priority_http':
            print("\nSending 'priority_http' intent...")
            send_intent(intent_type)

        print("\n" + "-" * 50 + "\n")


if __name__ == "__main__":
    main()
