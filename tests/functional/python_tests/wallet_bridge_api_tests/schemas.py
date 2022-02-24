find_rc_accounts = {
    'type': 'seq',
    'sequence': [
        {
            'type': 'map',
            'mapping': {
                'account': {'type': 'str'},
                'rc_manabar': {
                    'type': 'map',
                    'mapping': {
                        'current_mana': {'type': 'int'},
                        'last_update_time': {'type': 'int'},
                    }
                },
                'max_rc_creation_adjustment': {
                    'type': 'map',
                    'mapping': {
                        'amount': {'type': 'str'},
                        'precision': {'type': 'int'},
                        'nai': {'type': 'str'},
                    }
                },
                'max_rc': {'type': 'int'},
                'delegated_rc': {'type': 'int'},
                'received_delegated_rc': {'type': 'int'},
            }
        }
    ]
}

list_rc_accounts = {
    'type': 'seq',
    'sequence': [
        {
            'type': 'map',
            'mapping': {
                'account': {'type': 'str'},
                'rc_manabar': {
                    'type': 'map',
                    'mapping': {
                        'current_mana': {'type': 'int'},
                        'last_update_time': {'type': 'int'},
                    }
                },
                'max_rc_creation_adjustment': {
                    'type': 'map',
                    'mapping': {
                        'amount': {'type': 'str'},
                        'precision': {'type': 'int'},
                        'nai': {'type': 'str'},
                    }
                },
                'max_rc': {'type': 'int'},
                'delegated_rc': {'type': 'int'},
                'received_delegated_rc': {'type': 'int'},
            }
        }
    ]
}

list_rc_direct_delegations = {
    'type': 'seq',
    'sequence': [
        {
            'type': 'map',
            'mapping': {
                'from': {'type': 'str'},
                'to': {'type': 'str'},
                'delegated_rc': {'type': 'int'}
            },
        }
    ]
}
