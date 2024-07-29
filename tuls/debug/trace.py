import sys
import traceback
import inspect
from types import ModuleType
from typing import Iterable

from InquirerPy import inquirer
from InquirerPy.base import Choice
from InquirerPy.utils import color_print
from beacon.adict import ADict

from tuls.debug.stack_logger import StackLogger


def replace_iterable_repr(value):
    if isinstance(value, Iterable):
        if hasattr(value, '__len__'):
            return f'<iterable {type(value)}, {len(value)} items>'
        else:
            return f'<iterable {type(value)}>'
    return value


class TraceStatus:
    IN_TRACE = False


def show_main_menu():
    main_choices = [
        Choice(name='Look-up Frames', value='FRAMES'),
        # Choice(name='Look-up Variables', value='VARIABLES'),
        # Choice(name='Execute Code', value='EXEC'),
        Choice(name='Set Verbosity', value='SET_VERBOSITY'),
        Choice(name='Continue', value='RETURN'),
        Choice(name='Terminate', value='EXIT')
    ]
    main_menu = inquirer.select(message='Select a behavior of debugger:', choices=main_choices)

    @main_menu.register_kb('escape')
    def escape(event):
        event.app.exit('RETURN')

    return main_menu.execute()


def get_variables_from_frame(frame):
    if inspect.istraceback(frame):
        frame = frame.tb_frame
    global_vars = {
        name: value for name, value in frame.f_globals.items()
        if not isinstance(value, ModuleType) and not name.startswith('__')
    }
    local_vars = {
        name: value for name, value in frame.f_locals.items()
        if not isinstance(value, ModuleType) and not name.startswith('__')
    }
    variables = dict()
    variables['globals'] = global_vars
    variables['locals'] = local_vars
    return variables


def _get_variable_choices(variables, verbosity):
    choices = dict()
    if verbosity == 3:
        choices.update(variables['globals'])
    choices.update(variables['locals'])
    return choices


def get_variable_info(variable):
    class_members = {
        name: getattr(variable, name) for name in dir(variable)
        if isinstance(name, str) and hasattr(variable, name) and not name.startswith('__')
    }
    attributes = {
        name: replace_iterable_repr(value)
        for name, value in class_members.items()
        if not inspect.ismethod(value)
    }
    methods = {name: value for name, value in class_members.items() if inspect.ismethod(value)}
    return ADict(**attributes), ADict(**methods)


def print_with_split(lines, highlights=None, is_system_log=False):
    print('-'*50)
    if isinstance(lines, str):
        lines = lines.split('\n')
    highlights = highlights or dict()
    for index, line in enumerate(lines):
        if index in highlights:
            colored_line = highlights[index]
            if isinstance(colored_line, str):
                colored_line = [(colored_line, line)]
            color_print(colored_line)
        elif is_system_log:
            print_system_log(line)
        else:
            print(line)
    print('-'*50)


def print_source(obj, highlights=None, query=None):
    lines = inspect.getsource(obj)[:-1].split('\n')
    highlights = highlights or dict()
    for index, line in enumerate(lines):
        if query is not None and query in line:
            sub_lines = line.split(query)
            highlights[index] = []
            for sub_index, sub_line in enumerate(sub_lines):
                if sub_index != 0:
                    highlights[index].append(('#71ADFF', query))
                highlights[index].append(('', sub_line))
    print_with_split(lines, highlights)


def print_system_log(text):
    color_print([('#FAD866', f'[!] {text}')])


def search_and_show_frames(logger, verbosity):
    frames_info = [inspect.getframeinfo(frame) for frame in logger]
    while True:
        choices = ADict(**{
            f'[>] {frame_info.filename} | Line {frame_info.lineno}'
            if index == logger.index else f'{frame_info.filename} | Line {frame_info.lineno}': index
            for index, frame_info in enumerate(frames_info)
        })
        frame_input = inquirer.fuzzy(
            message='Select frames to jump or press function keys to inspect(Press Ctrl+H to see help.):',
            choices=list(choices.keys())
        )

        @frame_input.register_kb('s-up')
        def return_to_main_menu(event):
            event.app.exit('RETURN')

        @frame_input.register_kb('c-h')
        def print_help(event):
            event.app.exit('HELP')

        @frame_input.register_kb('c-s')
        def print_frame(event):
            event.app.exit('PRINT')

        @frame_input.register_kb('c-f')
        def print_frame_with_query(event):
            event.app.exit('SEARCH')

        @frame_input.register_kb('c-v')
        def run_inspect(event):
            event.app.exit('VARIABLES')

        @frame_input.register_kb('c-x')
        def run_exec(event):
            event.app.exit('EXEC')

        @frame_input.register_kb('s-right')
        def run_trace(event):
            event.app.exit('TRACE')

        @frame_input.register_kb('s-left')
        def run_traceback(event):
            event.app.exit('TRACEBACK')

        choice = frame_input.execute()
        match choice:
            case 'RETURN':
                break
            case 'HELP':
                print_with_split(
                    'Shift+↑: Return to main menu.\n'
                    'Ctrl+S: Print source code of current frame.\n'
                    'Ctrl+F: Search text from code of current frame.\n'
                    'Ctrl+V: Inspect variables defined in current frame.\n'
                    'Ctrl+X: Execute commands on current frame.\n'
                    'Shift+→: Jump to next frame.\n'
                    'Shift+←: Jump to previous frame.',
                    is_system_log=True
                )
            case 'PRINT':
                frame = logger.current_frame()
                frame_info = inspect.getframeinfo(frame)
                print_source(frame, {frame_info.lineno: '#4DEA77'})
            case 'SEARCH':
                frame = logger.current_frame()
                print_source(frame, query=inquirer.text('Press query to search:').execute())
            case 'TRACE':
                next_frame = logger.trace()
                if next_frame is None:
                    print_system_log('There does not exist next frame, maybe you are already in main code.')
                else:
                    frame = next_frame
                    frame_info = inspect.getframeinfo(frame)
                    print_system_log(f'Jumped to: {frame_info.filename} | Line {frame_info.lineno}')
            case 'TRACEBACK':
                prev_frame = logger.traceback()
                if prev_frame is None:
                    print('There does not exist previous frame, maybe you are already in last stack.')
                else:
                    frame = prev_frame
                    frame_info = inspect.getframeinfo(frame)
                    print_system_log(f'Jumped to: {frame_info.filename} | Line {frame_info.lineno}')
            case 'VARIABLES':
                search_and_show_variables(logger, verbosity)
            case 'EXEC':
                frame = logger.current_frame()
                online_execute(frame)
            case _:
                frame_index = choices[choice]
                frame = logger.set_frame_by_index(frame_index)
                frame_info = inspect.getframeinfo(frame)
                print_system_log(f'Jumped to: {frame_info.filename} | Line {frame_info.lineno}')


def search_and_show_variables(logger, verbosity):
    frame = logger.current_frame()
    frame_info = inspect.getframeinfo(frame)
    print_system_log(f'Currently on: {frame_info.filename} | Line {frame_info.lineno}')
    variables = get_variables_from_frame(frame)
    choices = _get_variable_choices(variables, verbosity)
    variable_name = None
    selected_variable = None
    attributes = None
    methods = None
    while True:
        variable_input = inquirer.fuzzy(
            message='Select variables to show or press function keys to inspect(Press Ctrl+H to see help.):',
            choices=list(choices.keys())
        )

        @variable_input.register_kb('s-up')
        def return_to_main_menu(event):
            event.app.exit('RETURN')

        @variable_input.register_kb('c-h')
        def print_help(event):
            event.app.exit('HELP')

        @variable_input.register_kb('c-s')
        def print_frame(event):
            event.app.exit('PRINT')

        @variable_input.register_kb('c-f')
        def print_frame_with_query(event):
            event.app.exit('SEARCH')

        @variable_input.register_kb('c-t')
        def print_attributes(event):
            event.app.exit('PRINT-ATTRS')

        @variable_input.register_kb('c-e')
        def print_methods(event):
            event.app.exit('PRINT-METHODS')

        @variable_input.register_kb('c-x')
        def run_exec(event):
            event.app.exit('EXEC')

        @variable_input.register_kb('s-right')
        def run_trace(event):
            event.app.exit('TRACE')

        @variable_input.register_kb('s-left')
        def run_traceback(event):
            event.app.exit('TRACEBACK')

        choice = variable_input.execute()
        match choice:
            case 'RETURN':
                break
            case 'HELP':
                print_with_split(
                    'Shift+↑: Return to previous menu.\n'
                    'Ctrl+S: Print source code of current frame.\n'
                    'Ctrl+F: Search text from code of current frame.\n'
                    'Ctrl+T: Print attribute list of selected variable.\n'
                    'Ctrl+E: Print method list of selected object.\n'
                    'Ctrl+X: Execute commands on current frame.\n\n'
                    'Shift+→: Jump to next frame.\n'
                    'Shift+←: Jump to previous frame.',
                    is_system_log=True
                )
            case 'PRINT':
                if any(
                    [
                        inspect.ismodule(selected_variable),
                        inspect.isclass(selected_variable),
                        inspect.ismethod(selected_variable),
                        inspect.isfunction(selected_variable),
                        inspect.istraceback(selected_variable),
                        inspect.isframe(selected_variable)
                    ]
                ):
                    print_source(selected_variable)
                else:
                    print_system_log(f'There does not exist source code of variable "{variable_name}".')
            case 'SEARCH':
                if any(
                    [
                        inspect.ismodule(selected_variable),
                        inspect.isclass(selected_variable),
                        inspect.ismethod(selected_variable),
                        inspect.isfunction(selected_variable),
                        inspect.istraceback(selected_variable),
                        inspect.isframe(selected_variable)
                    ]
                ):
                    print_source(selected_variable, query=inquirer.text('Press query to search:').execute())
                else:
                    print_system_log(f'There does not exist source code of variable "{variable_name}".')
            case 'PRINT-ATTRS':
                if attributes:
                    print(attributes.to_xyz())
                else:
                    print_system_log(f'There does not exist any attributes in variable "{variable_name}".')
            case 'PRINT-METHODS':
                if methods:
                    print(methods.to_xyz())
                else:
                    print_system_log(f'There does not exist any method in variable "{variable_name}".')
            case 'TRACE':
                next_frame = logger.trace()
                if next_frame is None:
                    print_system_log('There does not exist next frame, maybe you are already in main code.')
                else:
                    frame = next_frame
                    frame_info = inspect.getframeinfo(frame)
                    print_system_log(f'{frame_info.filename} | Line {frame_info.lineno}')
                    selected_variable = None
                    variables = get_variables_from_frame(frame)
                    choices = _get_variable_choices(variables, verbosity)
            case 'TRACEBACK':
                prev_frame = logger.traceback()
                if prev_frame is None:
                    print('There does not exist previous frame, maybe you are already in last stack.')
                else:
                    frame = prev_frame
                    frame_info = inspect.getframeinfo(frame)
                    print_system_log(f'Jumped to: {frame_info.filename} | Line {frame_info.lineno}')
                    selected_variable = None
                    variables = get_variables_from_frame(frame)
                    choices = _get_variable_choices(variables, verbosity)
            case _:
                variable_name = choice
                if choice not in choices:
                    print_system_log(f'There does not exist variable: {choice}')
                else:
                    selected_variable = choices[choice]
                    print_with_split(f'{selected_variable.__class__.__name__} | {selected_variable}')


def online_execute(frame):
    variables = get_variables_from_frame(frame)
    global_vars = variables['globals']
    local_vars = variables['locals']
    while True:
        line_input = inquirer.text('Enter a line to execute:')

        @line_input.register_kb('up')
        def return_to_main_menu(event):
            event.app.exit('RETURN')

        line = line_input.execute()

        if line in ('exit', 'RETURN'):
            break
        try:
            exec(compile(line, '<string>', 'single'), global_vars, local_vars)
        except Exception:
            print(traceback.format_exc())


def trace(frame=None, enabled=True):
    if enabled and not TraceStatus.IN_TRACE:
        TraceStatus.IN_TRACE = True
        frame = frame or inspect.currentframe().f_back
        logger = StackLogger()
        logger.set_stacks(frame)
        verbosity = 1
        while True:
            action = show_main_menu()
            match action:
                case 'FRAMES':
                    search_and_show_frames(logger, verbosity)
                # case 'VARIABLES':
                #     search_and_show_variables(logger, verbosity=verbosity)
                # case 'EXEC':
                #     online_execute(logger.current_frame())
                case 'SET_VERBOSITY':
                    verbosity = int(inquirer.select(message='Enter a verbosity:', choices=[0, 1, 2]).execute())
                case 'RETURN':
                    confirm = inquirer.confirm(
                        message='Return to execute next parts of main code. Continue?',
                        default=True
                    ).execute()
                    if confirm:
                        break
                case 'EXIT':
                    confirm = inquirer.confirm(
                        message='Terminate main code. It cannot be undone. Continue?',
                        default=False
                    ).execute()
                    if confirm:
                        sys.exit(0)
        TraceStatus.IN_TRACE = False


if __name__ == '__main__':
    a = 1
    b = 2
    c = 3
    trace()
