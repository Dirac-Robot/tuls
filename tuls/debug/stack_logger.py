import inspect


class StackLogger:
    def __init__(self):
        self.frames = []
        self.index = 0

    def set_stacks(self, source):
        if inspect.istraceback(source):
            while True:
                self.frames.append(source.tb_frame)
                source = source.tb_next
                if source is None:
                    break
        else:
            while True:
                self.frames.append(source)
                source = source.f_back
                if source is None:
                    break
            self.frames.reverse()

    def __iter__(self):
        for stack in self.frames:
            yield stack

    def __len__(self):
        return len(self.frames)

    def __next__(self):
        if self.index < len(self.frames):
            stack = self.frames[self.index]
            self.index += 1
            return stack
        else:
            self.index = 0
            raise StopIteration

    def __getitem__(self, index):
        return self.frames[index]

    def current_frame(self):
        return self.frames[self.index]

    def trace(self):
        if self.index >= 1:
            self.index -= 1
            return self.current_frame()

    def traceback(self):
        if self.index <= len(self.frames)-2:
            self.index += 1
            return self.current_frame()

    def set_frame_by_index(self, index):
        if not isinstance(index, int):
            raise TypeError(f'index should be an integer, but {index} is not.')
        elif 0 <= index <= len(self.frames)-1:
            self.index = index
        else:
            raise IndexError(f'index should be 0 <= index <= {len(self.frames)-1}, but {index} is not.')
        return self.current_frame()
