from inspect import isclass

def get_all_subclasses(class_attr) -> list:
    
    all_subclasses = []

    if isclass(class_attr):

        for subclass in class_attr.__bases__:
            
            all_subclasses.append(subclass)
            all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses

def list_child_class_functions(child_class):

    child_functions = set(child_class.__dict__)

    parent_functions = set()

    for subclass in child_class.__bases__:
        parent_functions.update(subclass.__dict__)
    
    # Subtract the parent functions from the child functions
    child_only_functions = child_functions - parent_functions

    # Filter only the callable attributes (functions)
    child_only_functions = [func for func in child_only_functions if callable(getattr(child_class, func))]

    return child_only_functions