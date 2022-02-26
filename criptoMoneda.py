from crypt import methods
from ctypes import resize
import datetime
import hashlib
from itertools import chain
import json
import re
from urllib import response
import uuid
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

# PARTE 1 !!!
#crear la cadena de bloques
class Blockchain:
    # inicio el contructor con __init__
    def __init__(self):
        # esta es la cadena de bloques, dentro de la lista ira la cadena de bloques
        self.chain=[]
        # creo una lista para las transacciones , como una meanPool casera
        self.transactions=[]
        # recordar que el bloque se crea despues del minado
        # tengo que hacer el blocke master (el primero) , el hash previo es 0 porque es el primero
        self.create_block(proof=1,previous_hash='0')
        # creo los nodos , pero los voy a crear como un conjunto (con set()) no como una lista
        self.nodes=set()

    def create_block(self,proof, previous_hash):
        # el bloque que creo
        block= {
            'index':len(self.chain)+1,
            'timestamp':str(datetime.datetime.now()),
            'proof':proof,
            'previous_hash':previous_hash,
            'transactions':self.transactions
        }
        # y ahora obviamente tengo que vaciar la memoria de transacciones
        self.transactions=[]
        self.chain.append(block)
        return block

    def get_previous_blok(self):
        return self.chain[-1]

    # creo la funcion de proof , proof of work 
    def proof_of_work(self,previous_proof):
        # voy a ir haciendo una prueba de fuerza bruta (voy a ir aumentando el 1)
        new_proof=1
        # veo si el proof es correcto, por defoult es False
        check_proof=False
        while check_proof is False:
            # la operacion no puede ser simetrica (2+3 es lo mismo 3+2)
            # hexdigest lo que hace es lo pasa a formato hexadesimal
            hash_operation= hashlib.sha256(str(new_proof**2-previous_proof**2).encode()).hexdigest()
            # pruebo que los 4 primras pociciones sean 0000
            if hash_operation[:4]=='0000':
                check_proof=True
            else:
                new_proof+=1
        return new_proof

    # crear el hash del bloque
    def hash(self,block):
        # paso el diccionario a string primero
        encode_block=json.dumps(block,sort_keys=True).encode()
        return hashlib.sha256(encode_block).hexdigest()

    # tengo que probar que todos los hasprevios son iguales al anterior
    def is_chain_valid(self,chain):
        previous_block=chain[0]
        block_index=1
        while block_index < len(chain):
            # es igual al hash del anterior?
            block=chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            # para cada uno de los bloques compruebo el proof
            # tomo el valor de la prueba previa
            previous_proof=previous_block['proof']
            # tomo el valor de la prueba actual
            proof=block['proof']
            hash_operation= hashlib.sha256(str(proof**2-previous_proof**2).encode()).hexdigest()
            if hash_operation[:4]!='0000':
                return False
            previous_block=block
            block_index+=1
        return True

    # voy a anadir la transaccion, necesito 3 variables , emisor , receptor y monto
    def add_transaction(self,sender , receiver, amount):
        self.transactions.append({
            'sender':sender,
            'receiver':receiver,
            'amount':amount
        })
        # voy con el ultimo blocke
        previous_block=self.previous_block()
        return previous_block['index']+1

    # voy a anadir el nuevo nodo
    def add_node(self,address):
        parsed_url= urlparse(address)
        self.nodes.add(parsed_url.netloc) #el netloc es la url '127.0.0.0:500'


    
    # tengo que armar la funcion de consenso ... la mas grande gana
    def replace_chain(self):
        network= self.nodes
        # busco la cadena mas larga
        longest_chain=None
        max_length= len(self.chain)
        # busco la cadena mas larga
        for node in network:
            response= requests.get(url=f'http://{node}/get_chain')
            if response.status_code == 200:
                # agarro la longitud
                length= response.json()['length']
                # agarro la cadena de bloques
                chain= response.json()['chain']
                # ahora compruebo si esta cadena es mas larga que max_length y ademas tiene que ser valida
                if length > max_length and self.is_chain_valid(chain):
                    # entonces remplazo por la mas larga
                    max_length= length
                    longest_chain=chain
        # si longest_chain es dif a none, osea si se cambio arriba
        if longest_chain:
            self.chain=longest_chain
            return True
        # sino retorno falso
        return False





# parte dos MINADO
app=Flask(__name__)

# crear una Blockchain
blockchain=Blockchain()

# creo la direccion (el primero) de los nodos en el puerto 5000
node_address=str(uuid4()).replace('-','')

# PARTE 2 !!
# minar bloque
@app.route('/mine_block',methods=['GET'])
def mine_block():
    # tomo el block anterior
    previous_block= blockchain.get_previous_blok()
    # tomo la proof
    previous_proof=previous_block['proof']
    proof=blockchain.proof_of_work(previous_proof)
    previous_hash=blockchain.hash(previous_block)
    blockchain.add_transaction(sender=node_address,receiver="Emanuel Lemos",amount=10)
    block=blockchain.create_block(proof,previous_hash)
    response = {
        'mensaage':'Muy bien, haz minado un nuevo bloque',
        'index':block['index'],
        'timestamp':block['timestamp'],
        'proof':block['proof'],
        'previous_hash':block['previous_hash'],
        'transactions':block['transactions']
        }
    return jsonify(response),200

@app.route('/get_chain',methods=['GET'])
def get_chain():
    response= {
        'chain':blockchain.chain,
        'length':len(blockchain.chain) 
    }
    return jsonify(response),200

# Comprobar si la cadena de bloques es válida
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message' : 'Todo correcto. La cadena de bloques es válida.'}
    else:
        response = {'message' : 'Houston, tenemos un problema. La cadena de bloques no es válida.'}
    return jsonify(response), 200  


# agrego una nueva transaccion a la cadena de bloques
@app.route('/add_transaction',methods=['POST'])
def add_transaction():
    # este json va a tener un objeto nodos con lista
    # ejemplo json= {'nodes':['127.0.0.1:5000','127.0.0.1:5001','127.0.0.1:5002']}
    json = request.get_json()
    transactions_keys=['sender','receiver','amount']
    if not all(key in json for key in transactions_keys):
        return 'Faltan algunos argumentos de la transaccion'
    index= blockchain.add_transaction(json['sender'],json['receiver'],json['amount'])
    response={
        'message':f'la transaccion sera anadida al bloque{index}'
    }
    return jsonify(response), 201


# PARTE 3 !!!
# Desentralizar cadena de bloques
# conectar nuevo nodos
@app.route('/connect_node',methods=['POST'])
def connect_node():
    # este json va a tener un objeto nodos con lista
    # ejemplo json= {'nodes':['127.0.0.1:5000','127.0.0.1:5001','127.0.0.1:5002']}
    json= request.get_json()
    nodes=json.get('nodes')
    if nodes is None:
        return 'No hay ningun nodo para anadir',400
    for node in nodes:
        blockchain.add_node(node)
    response={
        'message':'Todos los nodos ha sido conectados',
        'total_nodes':list(blockchain.nodes)
    }
    return jsonify(response),201 

# remplazar la cadena por la mas larga si es necesario
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {
            'message' : 'Los nodos tenian diferentes cadenas, que han sido remplazada por la mas larga',
            'new_chain':blockchain.chain
            }
    else:
        response = {
            'message' : 'todo correcto. La cadena en todos los nodos ya es la mas larga',
            'actual_chain':blockchain.chain
            }
    return jsonify(response), 200  

app.run(host='0.0.0.0',port=5000)

