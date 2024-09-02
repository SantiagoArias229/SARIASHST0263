import requests
from tabulate import tabulate


class ChordNode:
    def __init__(self, id, port, ip, bits=8):
        self.id = id
        self.port = port
        self.ip = ip  # Guardar la IP del nodo
        self.successor = None
        self.predecessor = None
        self.files = []
        self.local_files = []
        self.total_bits = bits
        self.finger_table = self.create_finger_table()
        print(f"[DEBUG] Nodo creado con ID {self.id}, IP {self.ip}, y puerto {self.port}")

    def create_finger_table(self):
        finger_table = []
        for i in range(1, self.total_bits + 1):
            start = (self.id + 2**(i-1)) % 2**self.total_bits
            finger_table.append({
                'start': start,
                'interval': (start, (start + 2**(i-1)) % 2**self.total_bits),
                'successor': None
            })
        print(f"[DEBUG] Finger table creada para nodo {self.id}: {finger_table}")
        return finger_table

    def update_finger_table(self, index, successor):
        if 0 <= index < len(self.finger_table):
            self.finger_table[index]['successor'] = successor
            print(f"[DEBUG] Finger table actualizada en nodo {self.id}, índice {index}, con sucesor {successor['id']}")
        else:
            print(f"[DEBUG] Índice {index} fuera de rango para la tabla de dedos en nodo {self.id}")

    def show_finger_table(self):
        finger_table_data = []
        for i, entry in enumerate(self.finger_table):
            successor = entry['successor']
            successor_id = successor['id'] if successor else None
            finger_table_data.append({
                'Entry': i+1,
                'Start': entry['start'],
                'Interval': f"[{entry['interval'][0]}, {entry['interval'][1]})",
                'Successor': successor_id
            })
        return tabulate(finger_table_data, headers="keys", tablefmt="pretty")


    def update_fingers_with_new_node(self, new_node_id, new_node_port, new_node_ip):
        print(f"[DEBUG] Actualizando finger table en nodo {self.id} con nuevo nodo {new_node_id}")
        for i in range(len(self.finger_table)):
            start = self.finger_table[i]['start']
            current_successor = self.finger_table[i]['successor']['id'] if self.finger_table[i]['successor'] else None
            print(f"[DEBUG] Evaluando entrada {i+1} de la finger table con start {start} y sucesor actual {current_successor}")

            # Condición para manejar el rango circular y evitar sobrescritura incorrecta
            if current_successor is None:
                if start <= new_node_id or (start > new_node_id and start < self.id):
                    print(f"[DEBUG] Nodo {new_node_id} es un mejor sucesor para la finger table del nodo {self.id} en índice {i+1}")
                    self.finger_table[i]['successor'] = {'id': new_node_id, 'port': new_node_port, 'ip': new_node_ip}
            elif (start <= new_node_id < current_successor) or (current_successor < self.id and (start <= new_node_id or new_node_id < current_successor)):
                print(f"[DEBUG] Nodo {new_node_id} es un mejor sucesor para la finger table del nodo {self.id} en índice {i+1}")
                self.finger_table[i]['successor'] = {'id': new_node_id, 'port': new_node_port, 'ip': new_node_ip}
            else:
                print(f"[DEBUG] Nodo {new_node_id} no es un mejor sucesor para la entrada {i+1} en la finger table del nodo {self.id}")

    def get_all_nodes(self):
        nodes = []
        if self.predecessor:
            nodes.extend(self.predecessor.get_all_nodes())
        nodes.append({
            'id': self.id,
            'port': self.port,
            'ip': self.ip  # Añadir la IP del nodo
        })
        if self.successor and self.successor.id != self.id:
            nodes.extend(self.successor.get_all_nodes())
        print(f"[DEBUG] Nodos en la red vistos por nodo {self.id}: {nodes}")
        return nodes


    def notify_all_nodes(self, new_node_id, new_node_port, new_node_ip):
        print(f"[DEBUG] Notificando a todos los nodos desde nodo {self.id} sobre nuevo nodo {new_node_id}")
        all_nodes = self.get_all_nodes()
        for node in all_nodes:
                url = f"http://{node['ip']}:{node['port']}/update_finger_table"  # Usar la IP del nodo
                try:
                    response = requests.post(url, json={"new_node_id": new_node_id, "new_node_port": new_node_port, "new_node_ip": new_node_ip})
                    if response.status_code == 200:
                        print(f"[DEBUG] Finger table en nodo {node['id']} actualizada correctamente.")
                    else:
                        print(f"[DEBUG] Error al actualizar finger table en nodo {node['id']}: {response.text}")
                except requests.exceptions.RequestException as e:
                    print(f"[DEBUG] Error de conexión al intentar actualizar finger table en nodo {node['id']} ({node['port']}): {e}")


    def store_file(self, node, file_id):
        target_node = node
        print(f"[DEBUG] Intentando almacenar archivo '{file_id}' en nodo {target_node.id} ({target_node.ip}:{target_node.port}) desde nodo {self.id}")
        
        if target_node.id != self.id:
            url = f"http://{target_node.ip}:{target_node.port}/upload"  # Usar la IP del nodo
            try:
                response = requests.post(url, json={"file_id": file_id})
                if response.status_code == 200:
                    print(f"[DEBUG] Archivo '{file_id}' almacenado en nodo {target_node.id} ({target_node.ip}:{target_node.port}).")
                else:
                    print(f"[DEBUG] Error al almacenar archivo '{file_id}' en nodo {target_node.id} ({target_node.ip}:{target_node.port}): {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"[DEBUG] Error al intentar conectarse con nodo {target_node.id} ({target_node.ip}:{target_node.port}): {e}")
        else:
            self.files.append(file_id)
            print(f"[DEBUG] Archivo '{file_id}' almacenado localmente en nodo {self.id} ({self.port}).")

    def find_node(self, file_id):
        print(f"[DEBUG] Buscando nodo para almacenar archivo '{file_id}' desde nodo {self.id}")

        # Si el predecesor es None (es el primer nodo) o si el file_id es menor que el id del nodo actual,
        # entonces debe almacenarse en este nodo si no hay un nodo con un id menor.
        if not self.predecessor or (self.predecessor.id > self.id and (file_id > self.predecessor.id or file_id <= self.id)):
            print(f"[DEBUG] Archivo '{file_id}' se almacena en nodo {self.id} porque no hay un predecesor más pequeño.")
            return self

        # Si el file_id es menor que el id del nodo actual pero mayor que el id del predecesor, se almacena aquí.
        if self.predecessor and self.predecessor.id < file_id <= self.id:
            print(f"[DEBUG] Archivo '{file_id}' se almacena en nodo {self.id}")
            return self

        # Si el file_id es mayor que el id del nodo actual pero menor que el id del sucesor, se almacena en el sucesor.
        if self.successor and self.id < file_id <= self.successor.id:
            print(f"[DEBUG] Archivo '{file_id}' se almacena en sucesor {self.successor.id}")
            return self.successor

        # Si no se encuentra un nodo adecuado, continúa la búsqueda en el sucesor.
        if self.successor and self.successor.id != self.id:
            print(f"[DEBUG] Redirigiendo la búsqueda del archivo '{file_id}' al sucesor {self.successor.id}")
            return self.successor.find_node(file_id)

        # Caso por defecto, almacena en el nodo actual.
        print(f"[DEBUG] Archivo '{file_id}' se almacena en nodo {self.id} (caso por defecto)")
        return self

    def find_closest_preceding_node(self, file_id):
        """
        Revisa la finger table, el nodo actual y el predecesor para encontrar el nodo con el ID inmediato mayor al file_id.
        """
        print(f"[DEBUG] Revisando finger table en nodo {self.id} para archivo '{file_id}'")

        # Si el predecesor sigue siendo mayor al file_id, redirigir la búsqueda hacia él
        if self.predecessor and self.predecessor.id > file_id:
            print(f"[DEBUG] Redirigiendo la búsqueda al predecesor {self.predecessor.id} porque es mayor al file_id")
            return self.predecessor.find_closest_preceding_node(file_id)

        # Crear una lista de sucesores que sean mayores o iguales a file_id, incluyendo el nodo actual
        possible_successors = []

        if self.id >= file_id:
            possible_successors.append({'id': self.id, 'port': self.port, 'ip': self.ip})

        for finger in self.finger_table:
            successor_id = finger['successor']['id'] if finger['successor'] else None

            if successor_id is not None and successor_id >= file_id:
                possible_successors.append(finger['successor'])

        if possible_successors:
            # Encontrar el menor de los sucesores mayores o iguales a file_id
            closest_successor = min(possible_successors, key=lambda x: x['id'])
            print(f"[DEBUG] Nodo más cercano encontrado: {closest_successor['id']}")
            return closest_successor

        # Si no se encuentra ningún nodo adecuado, retornar el nodo actual
        print(f"[DEBUG] No se encontraron sucesores adecuados, utilizando el nodo actual {self.id}")
        return {'id': self.id, 'port': self.port, 'ip': self.ip}

    def store_file_via_finger_table(self, file_id):
        """
        Utiliza la finger table para encontrar el nodo más cercano y almacena el archivo allí.
        """
        print(f"[DEBUG] Iniciando proceso para almacenar archivo '{file_id}' utilizando la finger table desde nodo {self.id}")
        
        # Encuentra el nodo más cercano utilizando la finger table
        closest_node_info = self.find_closest_preceding_node(file_id)
        
        # Convertir el diccionario en un objeto ChordNode si es necesario
        if isinstance(closest_node_info, dict):
            closest_node = ChordNode(closest_node_info['id'], closest_node_info['port'], closest_node_info['ip'])
        else:
            closest_node = closest_node_info
        
        # Si el nodo más cercano no es el mismo nodo actual
        if closest_node.id != self.id:
            print(f"[DEBUG] El nodo más cercano para almacenar el archivo '{file_id}' es {closest_node.id} ({closest_node.ip}:{closest_node.port})")
        else:
            print(f"[DEBUG] El nodo actual {self.id} es el mejor candidato para almacenar el archivo '{file_id}'")
        
        # Encuentra el nodo exacto donde se debe almacenar el archivo
        target_node = closest_node.find_node(file_id)
        print(f"[DEBUG] Nodo objetivo para almacenar archivo '{file_id}' es {target_node.id} ({target_node.ip}:{target_node.port})")
        
        # Almacena el archivo en el nodo correcto
        self.store_file(target_node, file_id)

    def find_and_store_local_file(self, file_id):
        """
        Utiliza la finger table para encontrar el nodo que tiene el archivo y lo almacena en local_files si está en el nodo actual.
        """
        print(f"[DEBUG] Iniciando proceso para encontrar archivo '{file_id}' en la red desde nodo {self.id}")
        
        current_node = self
        # Bucle para redirigir la búsqueda al predecesor real si es necesario
        while current_node.predecessor:
            print(f"[DEBUG] Consultando predecesor {current_node.predecessor.id} para archivo '{file_id}'")
            url = f"http://{current_node.predecessor.ip}:{current_node.predecessor.port}/check_predecessor"  # Usar la IP del predecesor
            try:
                response = requests.get(url, params={"file_id": file_id})
                if response.status_code == 200 and response.json().get("continue_search"):
                    print(f"[DEBUG] Redirigiendo la búsqueda al predecesor {current_node.predecessor.id} ({current_node.predecessor.ip}:{current_node.predecessor.port})")
                    current_node = ChordNode(response.json()["predecessor_id"], response.json()["predecessor_port"], response.json()["predecessor_ip"])
                else:
                    print(f"[DEBUG] No se necesita redirigir la búsqueda al predecesor {current_node.predecessor.id}")
                    break
            except requests.exceptions.RequestException as e:
                print(f"[DEBUG] Error al intentar conectarse con predecesor {current_node.predecessor.id} ({current_node.predecessor.port}): {e}")
                break

        # Una vez que se ha determinado el nodo correcto para comenzar la búsqueda,
        # continuar con la lógica existente de encontrar el nodo más cercano en la finger table
        closest_node_info = current_node.find_closest_preceding_node(file_id)
        
        if isinstance(closest_node_info, dict):
            closest_node = ChordNode(closest_node_info['id'], closest_node_info['port'], closest_node_info['ip'])
        else:
            closest_node = closest_node_info
        
        if closest_node.id != self.id:
            print(f"[DEBUG] El nodo más cercano para buscar el archivo '{file_id}' es {closest_node.id} ({closest_node.ip}:{closest_node.port})")
        else:
            print(f"[DEBUG] El nodo actual {self.id} es el mejor candidato para buscar el archivo '{file_id}'")
        
        target_node = closest_node.find_node(file_id)
        print(f"[DEBUG] Nodo objetivo para buscar archivo '{file_id}' es {target_node.id} ({target_node.ip}:{target_node.port})")
        
        try:
            url = f"http://{target_node.ip}:{target_node.port}/check_file"  # Usar la IP del nodo
            response = requests.get(url, params={"file_id": file_id})
            if response.status_code == 200 and response.json().get("exists"):
                print(f"[DEBUG] Archivo '{file_id}' encontrado en nodo {target_node.id} ({target_node.ip}:{target_node.port})")
                self.local_files.append(file_id)
                print(f"[DEBUG] Archivo '{file_id}' añadido a local_files en nodo {self.id}")
                return target_node.id, target_node.port
            else:
                print(f"[DEBUG] Archivo '{file_id}' no encontrado en nodo {target_node.id} ({target_node.ip}:{target_node.port})")
                return None, None
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] Error al intentar conectarse con nodo {target_node.id} ({target_node.ip}:{target_node.port}): {e}")
            return None, None

    def show(self):
            result = []
            if self.predecessor:
                result.extend(self.predecessor.show())
            result.append(f"{self.id} ({self.ip}:{self.port}) - Archivos-red: {self.files} - Archivos-local: {self.local_files}")
            if self.successor:
                result.extend(self.successor.show())
            return result


    def join(self, node_info):
        node_id, node_port, node_ip = node_info

        print(f"[DEBUG] Nodo {self.id} uniéndose a {node_id} ({node_ip}:{node_port})")

        if self.id == node_id or (self.successor and self.successor.id == node_id) or (self.predecessor and self.predecessor.id == node_id):
            print(f"[DEBUG] Nodo {self.id} ya está conectado a {node_id}, evitando recursión")
            return

        if node_id > self.id:
            if self.successor is None or node_id < self.successor.id:
                previous_successor = self.successor
                self.successor = ChordNode(node_id, node_port, node_ip)
                print(f"[DEBUG] Nodo {self.id} ha actualizado su sucesor a {node_id} ({node_ip}:{node_port})")

                url = f"http://{node_ip}:{node_port}/update_predecessor"
                requests.post(url, json={"predecessor_id": self.id, "predecessor_port": self.port, "predecessor_ip": self.ip})

                if previous_successor:
                    url = f"http://{previous_successor.ip}:{previous_successor.port}/update_predecessor"
                    requests.post(url, json={"predecessor_id": node_id, "predecessor_port": node_port, "predecessor_ip": node_ip})

            else:
                self.successor.join(node_info)

        elif node_id < self.id:
            if self.predecessor is None or node_id > self.predecessor.id:
                previous_predecessor = self.predecessor
                self.predecessor = ChordNode(node_id, node_port, node_ip)
                print(f"[DEBUG] Nodo {self.id} ha actualizado su predecesor a {node_id} ({node_ip}:{node_port})")

                url = f"http://{node_ip}:{node_port}/update_successor"
                requests.post(url, json={"successor_id": self.id, "successor_port": self.port, "successor_ip": self.ip})

                if previous_predecessor:
                    url = f"http://{previous_predecessor.ip}:{previous_predecessor.port}/update_successor"
                    requests.post(url, json={"successor_id": node_id, "successor_port": node_port, "successor_ip": node_ip})

            else:
                self.predecessor.join(node_info)

        if self.successor and self.successor.id != node_id:
            url = f"http://{self.successor.ip}:{self.successor.port}/join"
            requests.post(url, json={"node_address": node_id, "node_port": node_port, "node_ip": node_ip})

        if self.predecessor and self.predecessor.id != node_id:
            url = f"http://{self.predecessor.ip}:{self.predecessor.port}/join"
            requests.post(url, json={"node_address": node_id, "node_port": node_port, "node_ip": node_ip})

        self.notify_all_nodes(node_id, node_port, node_ip)
