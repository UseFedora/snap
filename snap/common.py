#!/usr/bin/env python


import yaml
import os
import jinja2
from os.path import expanduser
import json


class UnregisteredServiceObjectException(Exception):
      def __init__(self, alias):
            Exception.__init__(self, 'No ServiceObject registered under the alias "%s".' % alias)


class MissingEnvironmentVarException(Exception):
      def __init__(self, env_var):
            Exception.__init__(self, 'The environment variable %s has not been set.' % env_var)


            
class Enum(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError
            

def read_config_file(filename):
    '''Load a YAML initfile by name, returning a dictionary of its contents

    '''
    config = None
    with open(filename, 'r') as f:
        config = yaml.load(f)
    return config  



def full_path(filename):
    if filename.startswith(os.sep):
        return filename
    return os.path.join(os.getcwd(), filename)



def load_config_var(value):
      var = None
      if not value:
          pass
      elif value.__class__.__name__ == 'list':
          var = value
      elif isinstance(value, basestring):
            if value.startswith('$'):
                  var = os.environ.get(value[1:])            
                  if not var:
                        raise MissingEnvironmentVarException(value[1:])
            elif value.startswith('~%s' % os.path.sep):
                  home_dir = expanduser(value[0])
                  path_stub = value[2:]
                  var = os.path.join(home_dir, path_stub)
            else:
                  var = value            
      else:
          var = value
      return var

      

def load_class(class_name, module_name):
    module = __import__(module_name)    
    return getattr(module, class_name)


def jsonpretty(dict):
    return json.dumps(dict, indent=4, sort_keys=True)


class JinjaTemplateManager:
    def __init__(self, j2_environment):
        self.environment = j2_environment
        
    def get_template(self, filename):
        return self.environment.get_template(filename)
        


def get_template_mgr_for_location(directory):
      j2env = jinja2.Environment(loader = jinja2.FileSystemLoader(directory))
      return JinjaTemplateManager(j2env)
      




class ServiceObjectRegistry():
      def __init__(self, service_object_dictionary):
        self.services = service_object_dictionary


      def lookup(self, service_object_name):
            sobj = self.services.get(service_object_name)
            if not sobj:
                  raise UnregisteredServiceObjectException(service_object_name)
            return sobj
