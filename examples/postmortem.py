#!/usr/bin/env python3
import nestedtext as nt
from pathlib import Path
from voluptuous import Schema, Invalid, Extra, REMOVE_EXTRA
from pprint import pprint

# Settings schema
# First define some functions that are used for validation and coercion
def to_str(arg):
    if isinstance(arg, str):
        return arg
    raise Invalid('expected text.')

def to_ident(arg):
    arg = to_str(arg)
    if len(arg.split()) > 1:
        raise Invalid('expected simple identifier.')
    return arg

def to_list(arg):
    if isinstance(arg, str):
        return arg.split()
    if isinstance(arg, dict):
        raise Invalid('expected list.')
    return arg

def to_list_of_paths(arg):
    return [Path(p).expanduser() for p in to_list(arg)]

def to_email(arg):
    user, _, host = arg.partition('@')
    if '.' in host:
        return arg
    raise Invalid('expected email address.')

def to_gpg_id(arg):
    try:
        return to_email(arg)
    except Invalid:
        try:
            int(arg, base=16)
            return arg
        except ValueError:
            raise Invalid('expected GPG id.')

def to_gpg_ids(arg):
    return [to_gpg_id(i) for i in to_list(arg)]

# define the schema for the settings file
schema = Schema(
    {
        'my gpg ids': to_gpg_ids,
        'sign with': to_gpg_id,
        'avendesora gpg passphrase account': to_str,
        'avendesora gpg passphrase field': to_str,
        'name template': to_str,
        'recipients': {
            Extra: {
                'category': to_ident,
                'email': to_email,
                'gpg id': to_gpg_id,
                'attach': to_list_of_paths,
                'networth': to_ident,
            }
        },
    },
    extra = REMOVE_EXTRA
)

# this function implements references
def expand_setting(value):
    # allows macro values to be defined as a top-level setting.
    # allows macro reference to be found anywhere.
    if isinstance(value, str):
        value = value.strip()
        if value[:1] == '@':
            value = settings[value[1:].strip()]
        return value
    if isinstance(value, dict):
        return {k:expand_setting(v) for k, v in value.items()}
    if isinstance(value, list):
        return [expand_setting(v) for v in value]
    raise NotImplementedError(value)

try:
    # Read settings
    config_filepath = Path('postmortem.nt')
    if config_filepath.exists():

        # load from file
        settings = nt.load(config_filepath)

        # expand references
        settings = expand_setting(settings)

        # check settings and transform to desired types
        settings = schema(settings)

        # show the resulting settings
        pprint(settings)

except nt.NestedTextError as e:
    e.report()
except Invalid as e:
    print(f"ERROR: {', '.join(e.path)}: e.msg")