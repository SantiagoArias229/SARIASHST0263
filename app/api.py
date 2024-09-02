from flask import Flask, jsonify, request
from .chord import ChordNode

app = Flask(__name__)
chord_node = None

def create_chord_node(id, port, ip):
    global chord_node
    chord_node = ChordNode(id, port, ip)
    return chord_node

@app.route('/join', methods=['POST'])
def join_network():
    node_address = request.json.get('node_address')
    node_port = request.json.get('node_port')
    node_ip = request.json.get('node_ip')  # Agregar IP del nodo
    if node_address and node_port and node_ip:
        success = chord_node.join((node_address, node_port, node_ip))  # Pasar IP
        return jsonify({"success": success}), 200
    else:
        return jsonify({"error": "Node address, port, and IP are required"}), 400

@app.route('/leave', methods=['POST'])
def leave_network():
    chord_node.leave()
    return jsonify({"success": True}), 200

@app.route('/show', methods=['GET'])
def show_network():
    network_structure = chord_node.show()
    return jsonify({"success": True, "network": " ---> ".join(network_structure)}), 200

@app.route('/show_finger_table', methods=['GET'])
def show_finger_table():
    finger_table = chord_node.show_finger_table()
    return f"<pre>{finger_table}</pre>", 200

@app.route('/upload', methods=['POST'])
def store_file():
    file_id = request.json.get('file_id')  # Asumiendo que ahora pasas un número directamente
    if file_id is not None:
        chord_node.store_file_via_finger_table(file_id)
        return jsonify({"success": True, "message": f"Archivo '{file_id}' almacenado usando la finger table."}), 200
    else:
        return jsonify({"error": "File ID is required"}), 400

@app.route('/lookup', methods=['GET'])
def lookup():
    key = request.args.get('key')
    if key:
        node = chord_node.lookup(key)
        return jsonify({"node": node}), 200
    else:
        return jsonify({"error": "Key is required"}), 400

@app.route('/find_file', methods=['GET'])
def find_file():
    file_id = request.args.get('file_id')
    if file_id is not None:
        node_id, node_port = chord_node.find_and_store_local_file(int(file_id))
        if node_id is not None:
            return jsonify({"success": True, "message": f"Archivo '{file_id}' encontrado en nodo {node_id} ({node_port})"}), 200
        else:
            return jsonify({"error": "Archivo no encontrado"}), 404
    else:
        return jsonify({"error": "File ID is required"}), 400

@app.route('/check_file', methods=['GET'])
def check_file():
    file_id = int(request.args.get('file_id'))
    exists = file_id in chord_node.files
    return jsonify({"exists": exists}), 200

@app.route('/check_predecessor', methods=['GET'])
def check_predecessor():
    file_id = int(request.args.get('file_id'))
    continue_search = chord_node.predecessor.id > file_id if chord_node.predecessor else False
    return jsonify({
        "continue_search": continue_search,
        "predecessor_id": chord_node.predecessor.id if chord_node.predecessor else None,
        "predecessor_port": chord_node.predecessor.port if chord_node.predecessor else None
    }), 200

@app.route('/update_predecessor', methods=['POST'])
def update_predecessor():
    predecessor_id = request.json.get('predecessor_id')
    predecessor_port = request.json.get('predecessor_port')
    predecessor_ip = request.json.get('predecessor_ip')  # Agregar IP del predecesor
    if predecessor_id and predecessor_port and predecessor_ip:
        chord_node.predecessor = ChordNode(predecessor_id, predecessor_port, predecessor_ip)
        return jsonify({"success": True}), 200
    else:
        return jsonify({"error": "Predecessor ID, port, and IP are required"}), 400

@app.route('/update_successor', methods=['POST'])
def update_successor():
    successor_id = request.json.get('successor_id')
    successor_port = request.json.get('successor_port')
    successor_ip = request.json.get('successor_ip')  # Agregar IP del sucesor
    if successor_id and successor_port and successor_ip:
        chord_node.successor = ChordNode(successor_id, successor_port, successor_ip)
        return jsonify({"success": True}), 200
    else:
        return jsonify({"error": "Successor ID, port, and IP are required"}), 400

@app.route('/update_finger_table', methods=['POST'])
def update_finger_table():
    new_node_id = request.json.get('new_node_id')
    new_node_port = request.json.get('new_node_port')
    new_node_ip = request.json.get('new_node_ip')  # Agregar IP del nuevo nodo
    if new_node_id is not None and new_node_port is not None and new_node_ip is not None:
        chord_node.update_fingers_with_new_node(new_node_id, new_node_port, new_node_ip)
        return jsonify({"success": True}), 200
    else:
        return jsonify({"error": "New node ID, port, and IP are required"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0')
