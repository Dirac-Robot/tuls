import os
import sys
import traceback
import inspect
from types import ModuleType
from typing import Iterable

from InquirerPy import inquirer
from InquirerPy.base import Choice
from InquirerPy.utils import color_print
from beacon.adict import ADict

from tuls.debug.viewer import open_viewer
from tuls.debug.stack_logger import StackLogger


def replace_iterable_repr(value):
    if isinstance(value, Iterable):
        if hasattr(value, '__len__'):
            return f'{value.__class__.__name__}({len(value)} items)'
        else:
            return f'{value.__class__.__name__}'
    return value


class TraceStatus:
    IN_TRACE = False
    HISTORY_BUFFER = ['']


class KeyBindingRegistry:
    EVENT_KEYS = ADict(
        ESCAPE=ADict(
            key='s-up',
            help='Return to main menu.'
        ),
        HELP=ADict(
            key='c-h',
            help='Print key bindings and their functions.'
        ),
        SOURCE=ADict(
            key='c-s',
            help='Print source code of selected frame or variable it it exists.'
        ),
        SEARCH=ADict(
            key='c-f',
            help='Search text from code of selected frame or variable if its source code exists.'
        ),
        INSPECT=ADict(
            key='c-v',
            help='Inspect variables defined in current frame.'
        ),
        EXEC=ADict(
            key='c-x',
            help='Execute commands on current frame.'
        ),
        OPEN_EDITOR=ADict(
            key='c-e',
            help='Open editor in current frame.'
        ),
        ATTRIBUTES=ADict(
            key='c-t',
            help='Show attributes of selected variable if they exist.'
        ),
        METHODS=ADict(
            key='c-e',
            help='Show methods of selected variable if they exist.'
        ),
        TRACE_FORWARD=ADict(
            key='s-left',
            help='Jump to next frame.'
        ),
        TRACE_BACKWARD=ADict(
            key='s-right',
            help='Jump to previous frame.'
        ),
        PREV_LINE=ADict(
            key='up',
            help='Load previous line from history.'
        ),
        NEXT_LINE=ADict(
            key='down',
            help='Load next line from history.'
        )
    )

    @classmethod
    def to_readable_key(cls, key):
        key_mappings = [
            ADict(
                up='↑',
                down='↓',
                left='←',
                right='→'
            ),
            ADict(
                s='Shift',
                c='Ctrl',
                alt='ALT'
            )
        ]
        return '+'.join(
            reversed([
                f'{sub_key_mappings.get(sub_key, sub_key.upper())}'
                for sub_key, sub_key_mappings in zip(reversed(key.split('-')), key_mappings)
            ])
        )

    @classmethod
    def get_help(cls, event_codes):
        return '\n'.join([
            f'{cls.to_readable_key(cls.EVENT_KEYS[event_code].key)}: {cls.EVENT_KEYS[event_code].help}'
            for event_code in event_codes
        ])

    @classmethod
    def register_kb_from_event_codes(cls, executor, event_codes):
        for event_code in event_codes:
            if event_code in cls.EVENT_KEYS:
                executor.register_kb(cls.EVENT_KEYS[event_code].key)(cls.get_key_binding_fn(event_code))

    @classmethod
    def get_key_binding_fn(cls, event_code):
        def run(event):
            return event.app.exit(event_code)
        return run


def show_main_menu():
    main_choices = [
        Choice(name='Look-up Frames', value='FRAMES'),
        Choice(name='Set Verbosity', value='SET_VERBOSITY'),
        Choice(name='Continue', value='RETURN'),
        Choice(name='Terminate', value='EXIT')
    ]
    main_menu = inquirer.select(message='Select a behavior of debugger:', choices=main_choices)

    @main_menu.register_kb('escape')
    def escape(event):
        event.app.exit('RETURN')

    return main_menu.execute()


def get_variables_from_frame(frame, include_all=False):
    if inspect.istraceback(frame):
        frame = frame.tb_frame
    global_vars = {
        name: value for name, value in frame.f_globals.items()
        if include_all or (not isinstance(value, ModuleType) and not name.startswith('__'))
    }
    local_vars = {
        name: value for name, value in frame.f_locals.items()
        if include_all or (not isinstance(value, ModuleType) and not name.startswith('__'))
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
        frame_names = list(choices.keys())
        frame_selection = inquirer.fuzzy(
            message='Select frames to jump or press function keys to inspect(Press Ctrl+H to see help.):',
            choices=frame_names
        )
        event_codes = (
            'ESCAPE',
            'HELP',
            'SOURCE',
            'SEARCH',
            'INSPECT',
            'EXEC',
            'OPEN_EDITOR',
            'TRACE_FORWARD',
            'TRACE_BACKWARD'
        )
        KeyBindingRegistry.register_kb_from_event_codes(executor=frame_selection, event_codes=event_codes)
        choice = frame_selection.execute()
        if choice == 'ESCAPE':
            break
        elif choice == 'HELP':
            print_with_split(KeyBindingRegistry.get_help(event_codes), is_system_log=True)
        elif choice == 'SOURCE':
            frame = logger.current_frame()
            frame_info = inspect.getframeinfo(frame)
            print_source(frame, {frame_info.lineno: '#4DEA77'})
        elif choice == 'SEARCH':
            frame = logger.current_frame()
            print_source(frame, query=inquirer.text('Press query to search:').execute())
        elif choice == 'INSPECT':
            search_and_show_variables(logger, verbosity)
        elif choice == 'EXEC':
            frame = logger.current_frame()
            online_execute(frame)
        elif choice == 'OPEN_EDITOR':
            frame = logger.current_frame()
            frame_info = inspect.getframeinfo(frame)
            file_path = os.path.abspath(frame.f_code.co_filename)
            open_viewer(file_path=file_path, start_line=frame_info.lineno)
        elif choice == 'TRACE_FORWARD':
            next_frame = logger.trace()
            if next_frame is None:
                print_system_log('There does not exist next frame, maybe you are already in main code.')
            else:
                frame = next_frame
                frame_info = inspect.getframeinfo(frame)
                print_system_log(f'Jumped to: {frame_info.filename} | Line {frame_info.lineno}')
        elif choice == 'TRACE_BACKWARD':
            prev_frame = logger.traceback()
            if prev_frame is None:
                print('There does not exist previous frame, maybe you are already in last stack.')
            else:
                frame = prev_frame
                frame_info = inspect.getframeinfo(frame)
                print_system_log(f'Jumped to: {frame_info.filename} | Line {frame_info.lineno}')
        else:
            if choice in choices:
                frame_index = choices[choice]
                frame = logger.set_frame_by_index(frame_index)
                frame_info = inspect.getframeinfo(frame)
                print_system_log(f'Jumped to: {frame_info.filename} | Line {frame_info.lineno}')
            else:
                print_system_log(
                    f'There does not exist frame {frame_names[choice]}, maybe your input was wrong.'
                )


def search_and_show_variables(logger, verbosity):
    frame = logger.current_frame()
    frame_info = inspect.getframeinfo(frame)
    print_system_log(f'Currently on: {frame_info.filename} | Line {frame_info.lineno}')
    frame_vars = get_variables_from_frame(frame)
    choices = _get_variable_choices(frame_vars, verbosity)
    var_name = None
    selected_var = None
    attributes = None
    methods = None
    while True:
        var_selection = inquirer.fuzzy(
            message='Select variables to show or press function keys to inspect(Press Ctrl+H to see help.):',
            choices=list(choices.keys())
        )
        event_codes = (
            'ESCAPE',
            'HELP',
            'SOURCE',
            'SEARCH',
            'EXEC',
            'OPEN_EDITOR',
            'ATTRIBUTES',
            'METHODS',
            'TRACE_FORWARD',
            'TRACE_BACKWARD'
        )
        KeyBindingRegistry.register_kb_from_event_codes(executor=var_selection, event_codes=event_codes)
        choice = var_selection.execute()
        if choice == 'ESCAPE':
            break
        elif choice == 'HELP':
            print_with_split(KeyBindingRegistry.get_help(event_codes), is_system_log=True)
        elif choice == 'SOURCE':
            if any(
                [
                    inspect.ismodule(selected_var),
                    inspect.isclass(selected_var),
                    inspect.ismethod(selected_var),
                    inspect.isfunction(selected_var),
                    inspect.istraceback(selected_var),
                    inspect.isframe(selected_var)
                ]
            ):
                print_source(selected_var)
            else:
                print_system_log(f'There does not exist source code of variable "{var_name}".')
        elif choice == 'SEARCH':
            if any(
                [
                    inspect.ismodule(selected_var),
                    inspect.isclass(selected_var),
                    inspect.ismethod(selected_var),
                    inspect.isfunction(selected_var),
                    inspect.istraceback(selected_var),
                    inspect.isframe(selected_var)
                ]
            ):
                print_source(selected_var, query=inquirer.text('Press query to search:').execute())
            else:
                print_system_log(f'There does not exist source code of variable "{var_name}".')
        elif choice == 'EXEC':
            frame = logger.current_frame()
            online_execute(frame)
        elif choice == 'OPEN_EDITOR':
            frame = logger.current_frame()
            file_path = os.path.abspath(frame.f_code.co_filename)
            open_viewer(file_path)
        elif choice == 'ATTRIBUTES':
            if attributes:
                print(attributes.to_xyz())
            else:
                print_system_log(f'There does not exist any attribute in variable "{var_name}".')
        elif choice == 'METHODS':
            if methods:
                print(methods.to_xyz())
            else:
                print_system_log(f'There does not exist any method in variable "{var_name}".')
        elif choice == 'TRACE_FORWARD':
            next_frame = logger.trace()
            if next_frame is None:
                print_system_log('There does not exist next frame, maybe you are already in main code.')
            else:
                frame = next_frame
                frame_info = inspect.getframeinfo(frame)
                print_system_log(f'{frame_info.filename} | Line {frame_info.lineno}')
                selected_var = None
                frame_vars = get_variables_from_frame(frame)
                choices = _get_variable_choices(frame_vars, verbosity)
        elif choice == 'TRACE_BACKWARD':
            prev_frame = logger.traceback()
            if prev_frame is None:
                print('There does not exist previous frame, maybe you are already in last stack.')
            else:
                frame = prev_frame
                frame_info = inspect.getframeinfo(frame)
                print_system_log(f'Jumped to: {frame_info.filename} | Line {frame_info.lineno}')
                selected_var = None
                frame_vars = get_variables_from_frame(frame)
                choices = _get_variable_choices(frame_vars, verbosity)
        else:
            var_name = choice
            if choice not in choices:
                print_system_log(f'There does not exist variable. Please check your input is valid variable name.')
            else:
                selected_var = choices[choice]
                print_with_split(f'{selected_var.__class__.__name__} | {selected_var}')


def online_execute(frame):
    history_index = len(TraceStatus.HISTORY_BUFFER)-1
    value = TraceStatus.HISTORY_BUFFER[history_index]
    variables = get_variables_from_frame(frame, include_all=True)
    global_vars = variables['globals']
    local_vars = variables['locals']
    while True:
        exec_input = inquirer.text('Enter lines to execute:', default=value)
        event_codes = ('ESCAPE', 'HELP', 'PREV_LINE', 'NEXT_LINE')
        KeyBindingRegistry.register_kb_from_event_codes(exec_input, event_codes)
        command = exec_input.execute()
        if command in ('exit', 'ESCAPE'):
            break
        elif command == 'HELP':
            print_with_split(KeyBindingRegistry.get_help(event_codes), is_system_log=True)
        elif command == 'PREV_LINE':
            print("\033[A\033[A")
            history_index = max(0, history_index-1)
            value = TraceStatus.HISTORY_BUFFER[history_index]
        elif command == 'NEXT_LINE':
            print("\033[A\033[A")
            history_index = min(len(TraceStatus.HISTORY_BUFFER)-1, history_index+1)
            value = TraceStatus.HISTORY_BUFFER[history_index]
        else:
            try:
                TraceStatus.HISTORY_BUFFER = TraceStatus.HISTORY_BUFFER[:-1]+[command, '']
                history_index = len(TraceStatus.HISTORY_BUFFER)-1
                exec(compile(command, '<string>', 'exec'), global_vars, local_vars)
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
            if action == 'FRAMES':
                search_and_show_frames(logger, verbosity)
            elif action == 'SET_VERBOSITY':
                verbosity = int(inquirer.select(message='Enter a verbosity:', choices=[0, 1, 2]).execute())
            elif action == 'RETURN':
                confirm = inquirer.confirm(
                    message='Return to execute next parts of main code. Continue?',
                    default=True
                ).execute()
                if confirm:
                    break
            elif action == 'EXIT':
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
