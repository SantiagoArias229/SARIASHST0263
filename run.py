import sys
from app.api import create_chord_node, app

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    node_id = int(sys.argv[2]) if len(sys.argv) > 2 else port
    node_ip = sys.argv[3] if len(sys.argv) > 3 else '127.0.0.1'  # Agregar parámetro para la IP

    chord_node = create_chord_node(node_id, port, node_ip)  # Pasar la IP al crear el nodo

    app.run(host='0.0.0.0', port=port)
