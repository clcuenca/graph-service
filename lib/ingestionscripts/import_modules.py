
def set_construct_to(scope, construct, name: str, attributes: dict):
    """
    Sets the construct to the specified scope as an attribute, allowing it to be accessible within
    the specified scope.
    :param scope: The scope to modify
    :param construct: The construct to potentially insert or traverse
    :param name: The name of the construct
    :param attributes: The attributes corresponding to the construct
    """
    if scope is not None and construct is not None:

        # Initialize the alias
        alias = name

        # If valid attributes were specified & they contain an alias specification
        if isinstance(attributes, dict) and 'as' in attributes:

            # Update the alias
            alias = attributes['as']

            # Delete the key-value pair
            del attributes['as']

        # If the value doesn't specify any children, bind the construct with the name within the
        # specified scope
        if attributes is None or len(attributes) == 0: setattr(scope, alias, construct)

        # Otherwise, if the value has content
        elif attributes is not None and len(attributes) > 0:

            # Iterate through the name's constructs
            for child_name, child_attributes in attributes.items():

                # Recur
                set_construct_to(scope, getattr(construct, child_name), child_name, child_attributes)

def import_modules(scope=None, level: int = 0, **modules) -> None:
    """
    Imports the specified modules into the specified scope. If the modules are not present
    in the current system, this function will attempt to install them with pip & attempt
    re-import.
    :param scope: The scope to import the modules or submodules into.
    :param level: Specifies if the import should be flat for each module.
    :param modules: The dictionary containing the modules to import. Any nested submodules should be specified with a
        key corresponding to their name within the containing module.
        Should be in the following format:
        {
            'module_name': {
                'package_name': 'package_name',
                'as': 'alias',
                'submodule1': {
                    'as': 'alias'
                }
            }
        }

        // ----
        // Keys

        module_name     | The name of the module to import                  | Required
        package_name    | The name corresponding to the module's package    | Required
        as              | The alias to import the module or submodule as    | Optional
    """
    # Check the specified modules
    if modules is not None:

        # If a scope was not specified
        if scope is None:

            # Import modules from sys
            from sys import modules as modules_of

            # Initialize it to the top-level execution
            scope = modules_of[__name__]

        # Iterate through each key-value pair
        for name, value in modules.items():

            # Initialize the module
            module = None

            # Attempt
            try:

                # Module import
                module = __import__(name, globals(), locals(), [], level)

            # Except
            except ImportError as import_error:

                from sys import executable
                from subprocess import run

                # Report installation to the user
                print(f'Module \'{name}\' is not installed, installing.')

                # Attempt to install the module
                run([executable, '-m', 'pip', 'install', value['package_name']])

                # Attempt the import again
                module = __import__(name, globals(), locals(), [], level)

            # Delete the package name
            if 'package_name' in value: del value['package_name']

            # Set the corresponding names
            set_construct_to(scope, module, name, value)
