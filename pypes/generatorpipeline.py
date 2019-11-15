# Copyright (C) 2019 Stephan Kuschel



import functools
import types
from multiprocessing import Pool
import os

__all__  = ['pipeline']

class pipeline():

    def __init__(self, workers=0, verbose=False):
        self.workers = workers
        self.verbose = verbose

    def __call__(self, func):
        '''
        Decorate the function `func` to be used as a pipeline.

        kwargs will be forwarded to every call of f.
        '''
        if not callable(func):
            raise TypeError("must be a callable")
        return self._build_pipeline(func)


    def _build_pipeline(self, f):

        def return_generator_serial(arg, **kwargs):
            if self.verbose:
                print(f'serial execution of "{f.__name__}"')
            for el in arg:
                yield wrapper(el, **kwargs)  # f(el)

        def return_generator_parallel(arg, **kwargs):
            if self.verbose:
                print(f'parallel execution of "{f.__name__}" with {self.workers} workers.')
            pool = Pool(self.workers)
            readidx = 0
            writeidx = 0
            clen = self.workers + 1
            cache = [None] * clen
            for el in arg:
                cache[writeidx] = pool.apply_async(wrapper, (el,), kwargs)
                writeidx = (writeidx + 1) % clen
                if writeidx != readidx:
                    # fill cache
                    continue
                yield cache[readidx].get()
                readidx = (readidx + 1) % clen
            # flush cache
            while True:
                yield cache[readidx].get()
                readidx = (readidx + 1) % clen
                if readidx == writeidx:
                    pool.close()
                    return

        @functools.wraps(f)
        def wrapper(arg, **kwargs):
            if isinstance(arg, types.GeneratorType):
                if self.workers == 0:
                    return return_generator_serial(arg, **kwargs)
                else:
                    return return_generator_parallel(arg, **kwargs)
                return ret
            else:
                if self.verbose:
                    print(f'executing wrapped function "{f.__name__}" (PID: {os.getpid()}).')
                return f(arg, **kwargs)
        wrapper.workers = self.workers
        return wrapper