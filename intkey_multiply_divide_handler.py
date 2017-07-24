# A processor for a transaction family which will allow users to `set, multiply and divide
# the value of entries stored in the state dictionary.
import logging
import hashlib
import cbor

from sawtooth_sdk.processor.state import StateEntry
from sawtooth_Sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError

LOGGER = logging.getLogger(_name_)

valid_verbs = 'set', 'multiply', 'divide'

min_value = 0
max_value = 4294967295
max_namelength = 20

FAMILY_NAME = 'intkey_multiply_divide'

INTKEY_ADDRESS_PREFIX = hashlib.sha512(FAMILY_NAME.encode('utf-8')).hexdigest()[0:6]

def make_intkey_address(name):
	return INTKEY_ADDRESS_PREFIX + hashlib.sha512(name.encode('utf-8')).hexdigest()[-64:]
	
class TransactionHandler:
	@property
	def family_name(self):
		return FAMILY_NAME
		
	@property
	def family_versions(self):
		return ['1.0']
		
	@property
	def encodings(self):
		return [INTKEY_ADDRESS_PREFIX]
		
	def apply(self, transaction, state_store):
		verb, name, value = _unpack_transaction(transaction)
		state = _get_state_data(name, state_store)
		updated_state = _do_intkey(verb, name, value, state)
		_set_state_data(name, updated_state, state_store)
	
	def _unpack_transaction(transaction):
		verb, name, value = _decode_transaction(transaction)
		_validate_verb(verb)
		_validate_name(name)
		_validate_value(value)
		return verb, name, value
		
	def _decode_transaction(transaction):
		try:
			content = cbor.loads(transaction.payload)
		except:
			raise InvalidTransaction('Invalid Payload Serialization.')
			
		try:
			verb = content['Verb']
		except AttributeError:
				raise InvalidTransaction('Verb is required.')
		
		try:
			name = content['Name']
		except AttributeError:
        	raise InvalidTransaction('Name is required.')	
        	
        try:
        value = content['Value']
    	except AttributeError:
        	raise InvalidTransaction('Value is required.')
        	
        return verb, name, value
        
    def _validate_verb(verb):
    if verb not in valid_verbs:
        raise InvalidTransaction('Verb must be "set", "multiply", or "divide"')
            
    def _validate_name(name):
    if not isinstance(name, str) or len(name) > max_namelength:
        raise InvalidTransaction('Name must be a string less than {} characters'.format(max_namelength))
	
	def _validate_value(value):
    if not isinstance(value, int) or value < 0 or value > max_value:
        raise InvalidTransaction('Value must be an integer '
                                 'Ranging between {i} and {a}'.format(i=min_value,a=max_value))
                                
    def _get_state_data(name, state_store):
    	address = make_intkey_address(name)
		state_entries = state_store.get([address])
		
		try:
        	return cbor.loads(state_entries[0].data)
    	except IndexError:
        	return {}
    	except:
        	raise InternalError('Failed to load state data')
        	
    def _set_state_data(name, state, state_store):
    	address = make_intkey_address(name)
    	encoded = cbor.dumps(state)
    	addresses = state_store.set([StateEntry(address=address,data=encoded)])
    	if not addresses:
    		raise InternalError('State Error')
    		
    def _do_intkey(verb, name, value, state):
    	verbs =  { 
    		'set': _do_set,
    		'multiply': _do_multiply,
    		'divide': _do_divide,
    		}
    try:
        return verbs[verb](name, value, state)
    except KeyError:
        raise InternalError('Unhandled verb: {}'.format(verb))
    
    #set verb    
    def _do_set(name, value, state):
    msg = 'Setting "{n}" to "{v}"'.format(n=name, v=value)
    LOGGER.debug(msg)
    if name in state:
        raise InvalidTransaction('Verb is "set", but already exists: Name: {n}, Value {v}'.format(n=name,v=state[name]))
	updated = {k: v for k, v in state.items()}
    updated[name] = value
	return updated
	
	#multiply verb
	def _do_multiply(name, value, state):
    msg = 'Multiplying "{n}" by {v}'.format(n=name, v=value)
    LOGGER.debug(msg)
	if name not in state:
        raise InvalidTransaction('Verb is "multiply" but name "{}" not in state'.format(name))
	curr = state[name]
    multiplied = curr * value
	if multiplied > max_value:
        raise InvalidTransaction('Verb is "multiply", but result would be greater than {}'.format(max_value))
	updated = {k: v for k, v in state.items()}
    updated[name] = multiplied
	return updated
	
	#divide verb
	def _do_divide(name, value, state):
    msg = 'Dividing "{n}" by {v}'.format(n=name, v=value)
    LOGGER.debug(msg)
	if name not in state:
        raise InvalidTransaction('Verb is "divide" but name "{}" not in state'.format(name))
	curr = state[name]
    divided = curr/value
	if divided < min_value:
        raise InvalidTransaction('Verb is "divide", but result would be less than {}'.format(min_value))
	updated = {k: v for k, v in state.items()}
    updated[name] = divided
	return updated
        	
        	
        	
        	
        	
        	
        	
        	
        	
        	
        	
        	
        	
        	
        	
        	
        	


