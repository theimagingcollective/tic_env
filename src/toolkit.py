import os
import stat
import collections
from shutil import rmtree

FunctionOutcome = collections.namedtuple('FunctionOutcome', 'fn worked')
FunctionCalled = collections.namedtuple('FunctionCalled', 'fn')
no_print = '\b'
debug_mode = True


def print_exceptions(error='', frontend='', switch: (True, False, None)=False, errors=[]):
    actions = {True: lambda error: (print, error),
               False: lambda frontend: (print, frontend),
               None: lambda error: (errors.append, error)
               }
    actions[switch]
    return errors
               

def fn_worked(fn, worked, notify=False):
    """
    Accepts function name and success status of the nesting function and
    returns namedtuple FunctionOutcome indicating this info.
    Usage, inserted to a condition statement such as if-then, try-catch.
    Inserted at teh end of function.
    :param fn: (str) nesting function's name
    :param worked: (bool) Whether the function's operation worked.
    :param notify: (bool) Allows switching on and off individual calls of this function.
        Default = False
    """
    print(FunctionOutcome(fn=fn, worked=worked)) if notify else None


def fn_called(fn, notify=False):
    """
        Accepts function name of the nesting function and
        returns namedtuple FunctionCalled indicating the begining of a function's execution.
        Usage, Inserted at the begining of a function.
        :param fn: (str) nesting function's name
        :param notify: (bool) Allows switching on and off individual calls of this function.
            Default = False
        """
    print(FunctionCalled(fn=fn)) if notify else None


# def debug_print(*arg):
#     # return
#     if arg[-1] != '00' or True or 'db' or 'debug':
#         print(*arg)
#         return
#     print()
#     if isinstance(arg[0], str) and arg[0].find('--',0, 2):
#         print(arg[0])
#         start_idx = 1
#     else:
#         start_idx = 0
#     on = 1
#     if on and True:
#         for arg_elem in arg[start_idx:]:
#             if arg_elem == 'xxx':
#                 return
#             try:
#                 len(arg_elem)
#             except TypeError:
#                 print(arg[1:], sep='\n')
#             else:
#                 for elem in arg_elem:
#                     print(elem)
#     print()


def cleanup_tree(tree_root, handle_exceptions=True, notify_init=False, notify_outcome=False):
    """
    Accepts path to a directory and removes it and all its content.
    If PermissionError, attempts to change permissions of all the lements in the tree and then remove them.
    :param tree_root (str or path-like obj): Path to the directory to be removed including its contents.
    :param handle_exceptions (bool) True(default): True enables catching exceptions and
    handling them using other functions and/or diplaying front-end friendly messages.
    :param notify_init (bool) False(default): Prints a message when the function is called.
    :param notify_outcome (bool)  False(default): Prints a message of function success or failure
    when the function completes.
    """
    fn_called('cleanup_tree', notify_init)  # Prints when the function is called.
    
    def remove_readonly(fn, problem_path, excinfo):
        """
        Handles next steps when rmtree encounters an error.
        :param fn: Represents rmtree function statement
        :param problem_path: Path of the offending file or directory.
        :param excinfo: Exception info generated when rmtree first encountered an error.
        """
        def core_logic():
            """
            Changes the permissions of the current element (problem_path) and retries rmtree
            """
            if os.name == ' posix':  # Permission model for Unix
                os.chmod(problem_path, 0o600)
            else:  # Permission model for Windows/NT
                os.chmod(problem_path, stat.S_IWRITE)
            fn(problem_path)
        
        if handle_exceptions:
            try:
                core_logic()
            except Exception as exc:
                print("Skipped:", problem_path, "because:\n", exc)
                raise Exception
        else:
            core_logic()
            
    if handle_exceptions:
        try:
            rmtree(tree_root, onerror=remove_readonly)
        except FileNotFoundError as excep:
            print(excep)
        except PermissionError as excep:
            print(excep)
        except Exception as excep:
            print(excep)
    else:
        rmtree(tree_root, onerror=remove_readonly)
    # Prints whether the function succeeded or not.
    fn_worked(fn='cleanup_tree', worked=not os.path.exists(tree_root), notify=notify_outcome)
    
    
def change_permissions(path, nix_perm, tree=False, topdown=True, initial_exception='', handle_exceptions=True, notify_init=False):
    """
    Changes permissions of a directory tree and its elements.
    
    """
    print(fn_called('change_permissions', notify_init))
    perm = stat.S_IWRITE if os.name == 'nt' else nix_perm
    if initial_exception:
        excep_list = [initial_exception]
    else:
        excep_list = []
    try:
        os.chmod(path, perm)
    except Exception as exc:
        print("Skipped:", path, "because:\n", exc)
    finally:
        return excep_list
    
    if tree is False:
        return
    
    for root, dirs, files in os.walk(path, topdown=topdown):
        paths = [os.path.join(root, dir_) for dir_ in dirs]
        paths.extend([os.path.join(root, file_) for file_ in files])
        while paths:
            popped_path = paths.pop()
            try:
                os.chmod(popped_path, perm)
            except Exception as exc:
                print("Skipped:", popped_path, "because:\n", exc)
    

def check_remove(path, notify=False):
    try:
        assert(os.path.exists(path) is False)
    except:
        try:
            assert(os.path.isfile(path))
        except:
            cleanup_tree(path, notify_init=notify, notify_outcome=notify)
            assert (os.path.exists(path) is False)
        else:
            os.remove(path)
            assert (os.path.exists(path) is False)


def check_make(path, notify=False):
    try:
        assert(os.path.exists(path) is True)
    except:
        if os.path.isdir(path):
            os.mkdir(path)
        elif os.path.isfile(path):
            with open(path, 'w') as temp_obj:
                pass
        assert(os.path.exists(path) is True)
        
        
def increment(start=0, step=1):
        while True:
            yield start
            start += step


def path_nt2nix(abspath):
    drive_letter, rest_of_path = os.path.splitdrive(abspath)
    path_with_posix_drive = os.sep.join(['mnt', drive_letter[0].lower(), rest_of_path])
    almost_posix = ''.join([os.sep, os.path.normpath(path_with_posix_drive)])
    return almost_posix.replace('\\', '/')


def get_file_permission_via_shell(filepath, in_form='namedtuple'):
    global debug_mode
    
    from subprocess import check_output
    try:
        assert(os.path.isfile(filepath))
    except AssertionError:
        path = filepath
    else:
        path, file = os.path.split(filepath)
    try:
        ls_call = str(check_output(['ls', '-l', path]))
    except FileNotFoundError as excep:
        debug_mode = False
        if debug_mode:
            raise excep
        elif os.name != 'posix':
            print("Not a Unix based OS. NT methods not implemented yet.")
        else:
            print("The file  \n{}\n was not found. \nCan't show permissions for a file "
                  "that can't be found. \nMoving on...".format(path))
        debug_mode = True
    else:
        ls_call = ls_call.lstrip('b')
        ls_call = ls_call.split('\\n')
        file_entry = [entry for entry in ls_call if file in entry][0]
        permissions_string = file_entry[0:file_entry.find(' ')]
        permissions_key_alpha2num = {'r': 4, 'w': 2, 'x': 1, '-': 0, 'd':0}
        permission_nums = ([permissions_key_alpha2num[p] for p in permissions_string])
        user_categs = ('user', 'group', 'other')
        permits_dict = {gp: (str(sum(permission_nums[start:stop])), *(permissions_string[start:stop].replace('-', '')))
                   for (gp, start, stop) in zip(user_categs, range(1, 10, 3), range(4, 13, 3))}
        perm_code = ''.join(['0o', permits_dict['user'][0], permits_dict['group'][0], permits_dict['other'][0]])
        
        return_options = {'dict': permits_dict, 'groups': permits_dict, 'code': perm_code, 'str': permissions_string}
        is_dict = True if permissions_string[0] == 'd' else False
        try:
            return return_options[in_form]
        except KeyError:
            Permissions = collections.namedtuple('Permissions', 'code user group other string is_dict')
            return Permissions(code=perm_code, user=permits_dict['user'], group=permits_dict['group'],
                               other=permits_dict['other'], string=permissions_string, is_dict=is_dict)


def reattempt(max_attempts:(1|2|3),quit_at_last=False):
    
    if max_attempts == 0:
        print("Too many attempts with incorrect paths."
              "Please ascertain the file paths and run install again.")
        if quit_at_last:
            quit()
    if max_attempts not in (1, 2, 3):
        print("max_attempt can be 1, 2 or 3.")
        print("Using default.")
        max_attempts = 1
    max_attempts -= 1
    yield max_attempts


def recalculate_final_permission(current_perm, new_perm, action='add'):
    perm_num_sets = {'x': {1, 3, 5, 7}, 'w': {2, 3, 6, 7}, 'r': {4, 5, 6, 7}}
    current_perm = str(current_perm)
    for perm in current_perm[-3:]:
        pass
    
    final_perm = {'add': int(str(current_perm)[-3:]) + int(str(new_perm)[-3:])}
        # ,'remove': int(str(current_perm)[-3:]) - int(str(new_perm)[-3:])}
    
    
def excep_handle_frontend(handle=False, excep=None, erring_entity=None, user_corrects=False,
    raise_error=True, friendly_msg=False):
    if not handle:
        raise excep
    print(excep, erring_entity, sep='/n')
    

    

if __name__ == '__main__':
    path_arg = "/mnt/c/Users/kshit/bin_test/direnv/direnv.linux-amd64"