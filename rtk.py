from os import path
from string import Template
from glob import glob
import yaml
import sys
import getopt


class Config:
    def __init__(self, glob, name, infiles, outfile, **options):
        self.globals = glob
        self.name = name

        self.infiles = infiles
        self.outfile = outfile
        self.options = options

    def export(self):
        out = {
                'name': self.name,
                'infiles': self.infiles,
                'outfile': self.outfile
        }
        return dict(out, **self.options)

    def add_infile(self, filepath):
        if self.infiles == None:
            self.infiles = []
        if type(self.infiles) == str:
            self.infiles = [self.infiles]
        self.infiles.append(filepath)

    def del_infile(self, filepath):
        try:
            self.infiles.remove(filepath)
        except ValueError:
            print(f'File {filepath} not in infiles')

    # Load infiles, substitute variables and save to outfile
    def reconfigure(self):
        out_str = ""
        infiles = self.infiles

        # Handle glob string
        if infiles == None:
            infiles = []
        elif type(infiles) == str:
            infiles = [infiles]

        for fn in infiles:
            fn = path.abspath(fn)
            if not path.exists(fn):
                # Handle glob inside of list
                infiles.append(sorted(glob(fn)))
            else:
                # Load file
                print(f'Concatenating {fn}')
                with open(fn, 'r') as f:
                    out_str += f.read()

        # Substituting variables
        if self.globals['substitution'].get('default', False) or \
           self.options.get('substitute', False):
            with open(self.globals['substitution']['source'], 'r') as f:
                sub_source = yaml.load(f)
                out_str = Template(out_str).safe_substitute(
                            **sub_source)

        # Saving out_str to outfile
        outfile = self.outfile
        if outfile:
            print(f'Saving to {outfile}')
            with open(outfile, 'w') as f:
                f.write(out_str)


class ConfigsHandler:
    def __init__(self, config_file='config.yaml'):
        self.load_config_file(config_file)

    # Go over all configs
    def reconfigure_configs(self):
        for config in self.configs.values():
            config.reconfigure()

    def get_config(self, name):
        out = None
        try:
            out = self.configs[name]
        except KeyError:
            print(f'Config name {name} not found')
        return out
    
    def new_config(self, name:str, outfile):
        print(outfile)
        self.configs[name] = Config(self.globals, name, None, outfile)

    def load_config_file(self, config_file):
        with open(config_file, 'r') as f:
            self.__config = yaml.load(f.read())

            self.globals = {}
            self.globals['substitution'] = self.__config['substitution']

            self.configs = {}
            for config in self.__config['configs']:
                self.configs[config['name']] = Config(self.globals, **config)

    def dump_config_file(self, out_file):
        out = self.__config.copy()
        out['configs'] = [ c.export() for c in self.configs.values() ]

        with open(out_file, 'w') as f:
            yaml.dump(out, f, default_flow_style=False, indent=4)


if __name__ == '__main__':

    config_file = 'config.yaml'
    opts, args = getopt.getopt(sys.argv[1:], 'c:', ['config='])
    for opt, arg in opts:
        if opt in ('-c', '--config'):
            config_file = arg

    cfgh = ConfigsHandler(config_file=config_file)

    if args[0] in ('new', 'n'):
        cfgh.new_config(args[1], args[2])
    elif args[0] in ('delete', 'del', 'd'):
        print(args[1])
        pass
    elif args[0] in ('add', 'a'):
        config = cfgh.get_config(args[1])
        config.add_infile(args[2])
    elif args[0] in ('list', 'l'):
        for name, config in cfgh.configs.items():
            print(f"""- {name}
\t infiles: {config.infiles}
\t outfile: {config.outfile}""")
    elif args[0]in ('reconfigure', 'reconf', 'r'):
        cfgh.reconfigure_configs()


    cfgh.dump_config_file(config_file)
