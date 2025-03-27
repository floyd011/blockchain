#!/bin/bash

# Proveri da li je korisnik uneo ime sidechain-a
if [ -z "$1" ]; then
    echo "Usage: $0 <Sidechain-Name>"
    exit 1
fi

SIDECHAIN_NAME="$1"

# JSON podaci (može se učitati i iz fajla)
NODES_JSON=`curl -X GET http://192.168.122.11:4000/get_sidechains`

# Pronađi sve nodove koji pripadaju ovom sidechain-u
NODES=$(echo "$NODES_JSON" | jq -c --arg NAME "$SIDECHAIN_NAME" '[.[] | select(.name == $NAME)]')

if [ -z "$NODES" ] || [ "$NODES" == "[]" ]; then
    echo "No nodes found for sidechain: $SIDECHAIN_NAME"
    exit 1
fi

echo "Nodes found for $SIDECHAIN_NAME:"
echo "$NODES" | jq -r '.[].node_url'

for NODE in $(echo "$NODES" | jq -r '.[].node_url'); do
    # Kreiraj listu svih ostalih peer-ova osim trenutnog
    PEERS=$(echo "$NODES" | jq -c --arg NODE "$NODE" '[.[] | select(.node_url != $NODE) | {node_url}]')

    if [ -z "$PEERS" ] || [ "$PEERS" == "[]" ]; then
        echo "No peers to add for $NODE"
        continue
    fi

    echo "Adding peers to $NODE..."

    for PEER in $(echo "$NODES" | jq -r --arg NODE "$NODE" '.[] | select(.node_url != $NODE) | .node_url'); do
        echo "Registering peer $PEER on $NODE..."
        
        curl -X POST "$NODE/register_node" \
             -H "Content-Type: application/json" \
             -d "{\"node_url\": \"$PEER\"}"

        echo -e "\nPeer $PEER added to $NODE successfully!"
    done
done
