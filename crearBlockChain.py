from ctypes import resize
import datetime
import hashlib
import json
from flask import Flask, jsonify


#crear la cadena de bloques
class Blockchain:
    # inicio el contructor con __init__
    def __init__(self):
        # esta es la cadena de bloques, dentro de la lista ira la cadena de bloques
        self.chain=[]
        # recordar que el bloque se crea despues del minado
        # tengo que hacer el blocke master (el primero) , el hash previo es 0 porque es el primero
        self.create_block(proof=1,previous_hash='0')

    def create_block(self,proof, previous_hash):
        # el bloque que creo
        block= {
            'index':len(self.chain)+1,
            'timestamp':str(datetime.datetime.now()),
            'proof':proof,
            'previous_hash':previous_hash
        }
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



# parte dos MINADO
app=Flask(__name__)

# crear una Blockchain
blockchain=Blockchain()

# minar bloque
@app.route('/mine_block',methods=['GET'])
def mine_block():
    # tomo el block anterior
    previous_block= blockchain.get_previous_blok()
    # tomo la proof
    previous_proof=previous_block['proof']
    proof=blockchain.proof_of_work(previous_proof)
    previous_hash=blockchain.hash(previous_block)
    block=blockchain.create_block(proof,previous_hash)
    response = {
        'mensaage':'Muy bien, haz minado un nuevo bloque',
        'index':block['index'],
        'timestamp':block['timestamp'],
        'proof':block['proof'],
        'previous_hash':block['previous_hash']
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


app.run(host='0.0.0.0',port=5000)