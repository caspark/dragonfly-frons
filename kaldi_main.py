"""
Command-module loader for Kaldi.

This script is based on 'dfly-loader-wsr.py' written by Christo Butcher and
has been adapted to work with the Kaldi engine instead.

This script can be used to look for Dragonfly command-modules for use with
the Kaldi engine. It scans the directory it's in and loads any ``_*.py`` it
finds.
"""

import logging
import os.path
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from dragonfly import (Dictation, FuncContext, Function, Grammar, MappingRule,
                       get_engine)
from dragonfly.loader import CommandModuleDirectory
from dragonfly.log import setup_log


class App(threading.Thread):

    def __init__(self, shutdown_engine):
        threading.Thread.__init__(self)
        self.shutdown_engine = shutdown_engine
        self.start()
        self.should_close = False

    def quit(self):
        """ Quit the UI. Intended to be called from outside the UI - i.e. is safe to call from another thread. """
        self._do_shutdown()

    def set_last_heard(self, s):
        if len(s):
            self.last_heard.set(f"Last heard: {s}")

    def _on_window_close(self):
        do_quit = messagebox.askyesno(message='Are you sure you want to quit KaldiUI?', icon='question', title='Quit?')
        if do_quit:
            print("UI window closed - shutting down")
            self._do_shutdown()

    def _do_shutdown(self):
        self.shutdown_engine()
        self.should_close = True

    def _check_for_quit(self):
        """ Periodically checks whether we should quit.

        Checking on a timer is more resilient to being asked to quit from another thread;
        without this, tk won't quit on a ctrl-c interrupt until the mouse is moved or it gets
        some other event. This approach supports ctrl-c, quitting via the window manager, and
        quitting via voice command."""
        if self.should_close:
            self.root.quit()
        else:
            self.root.after(1000, self._check_for_quit)

    def run(self):
        self.root = tk.Tk()
        self.root.title("KaldiUI")
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

        self.last_heard = tk.StringVar()
        label = tk.Label(self.root, textvariable=self.last_heard)
        label.grid()

        self.root.after(1000, self._check_for_quit)

        self.root.mainloop()


# --------------------------------------------------------------------------
# Set up basic logging.

if False:
    # Debugging logging for reporting trouble
    logging.basicConfig(level=10)
    logging.getLogger('grammar.decode').setLevel(20)
    logging.getLogger('grammar.begin').setLevel(20)
    logging.getLogger('compound').setLevel(20)
    logging.getLogger('kaldi.compiler').setLevel(10)
else:
    setup_log()


# --------------------------------------------------------------------------
# User notification / rudimentary UI. MODIFY AS DESIRED

# For message in ('sleep', 'wake')
def notify(message):
    if message == 'sleep':
        print("Sleeping...")
        # get_engine().speak("Sleeping")
    elif message == 'wake':
        print("Awake...")
        # get_engine().speak("Awake")


# --------------------------------------------------------------------------
# Sleep/wake grammar. (This can be unused or removed if you don't want it.)

sleeping = False

def load_sleep_wake_grammar(initial_awake):
    sleep_grammar = Grammar("sleep")

    def sleep(force=False):
        global sleeping
        if not sleeping or force:
            sleeping = True
            sleep_grammar.set_exclusiveness(True)
        notify('sleep')

    def wake(force=False):
        global sleeping
        if sleeping or force:
            sleeping = False
            sleep_grammar.set_exclusiveness(False)
        notify('wake')

    class SleepRule(MappingRule):
        mapping = {
            "start listening":  Function(wake) + Function(lambda: get_engine().start_saving_adaptation_state()),
            "stop listening":   Function(lambda: get_engine().stop_saving_adaptation_state()) + Function(sleep),
            "halt listening":   Function(lambda: get_engine().stop_saving_adaptation_state()) + Function(sleep),
        }
    sleep_grammar.add_rule(SleepRule())

    sleep_noise_rule = MappingRule(
        name = "sleep_noise_rule",
        mapping = { "<text>": Function(lambda text: False and print(text)) },
        extras = [ Dictation("text") ],
        context = FuncContext(lambda: sleeping),
    )
    sleep_grammar.add_rule(sleep_noise_rule)

    sleep_grammar.load()

    if initial_awake:
        wake(force=True)
    else:
        sleep(force=True)

def load_ui_grammar(do_quit):
    ui_grammar = Grammar("KaldiUI")

    class ControlRule(MappingRule):
        mapping = {
            "please quit the kaldi UI":  Function(do_quit),
        }
    ui_grammar.add_rule(ControlRule())

    ui_grammar.load()

# --------------------------------------------------------------------------
# Main event driving loop.

def main():
    logging.basicConfig(level=logging.INFO)

    try:
        path = os.path.dirname(__file__)
    except NameError:
        # The "__file__" name is not always available, for example
        # when this module is run from PythonWin.  In this case we
        # simply use the current working directory.
        path = os.getcwd()
        __file__ = os.path.join(path, "kaldi_module_loader_plus.py")

    # Set any configuration options here as keyword arguments.
    # See Kaldi engine documentation for all available options and more info.
    engine = get_engine('kaldi',
        model_dir='models/daanzu_20200328_1ep-mediumlm',  # default model directory
        vad_aggressiveness=1,  # default aggressiveness of VAD
        vad_padding_start_ms=10,  # default ms of required silence before VAD
        vad_padding_end_ms=10,  # default ms of required silence after VAD
        vad_complex_padding_end_ms=10,  # default ms of required silence after VAD for complex utterances
        # input_device_index=None,  # set to an int to choose a non-default microphone
        lazy_compilation=True,  # set to True to parallelize & speed up loading
        # retain_dir=None,  # set to a writable directory path to retain recognition metadata and/or audio data
        # retain_audio=None,  # set to True to retain speech data wave files in the retain_dir (if set)
    )

    ui = App(shutdown_engine=engine.disconnect)

    # Call connect() now that the engine configuration is set.
    engine.connect()

    # Load grammars.
    load_sleep_wake_grammar(True)
    load_ui_grammar(do_quit=ui.quit)
    directory = CommandModuleDirectory(path, excludes=[__file__])
    directory.load()

    # Define recognition callback functions.
    def on_begin():
        print("Speech start detected.")

    def on_recognition(words):
        ui.set_last_heard(" ".join(words))
        print("Recognized: %s" % " ".join(words))

    def on_failure():
        print("Sorry, what was that?")

    # Start the engine's main recognition loop
    engine.prepare_for_recognition()
    try:
        print("Listening...")
        engine.do_recognition(begin_callback=on_begin, recognition_callback=on_recognition,
                       failure_callback=on_failure, end_callback=None,
                       post_recognition_callback=None)
    except KeyboardInterrupt:
        print(f"Received keyboard interrupt so quitting...")
        ui.quit()


if __name__ == "__main__":
    main()
