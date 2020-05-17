> Readme. All important projects start with a readme... and hacks... edgy, scary hacks that would make a lawyer or corporate executive nervous... And manifestos... really long and dramatic manifestos...

# Dragonfly Frons

... provides a graphical UI for [Dragonfly](https://github.com/dictation-toolbox/dragonfly), the voice control library.

It lets you see what words were recognized by the underlying voice recognition system, whether your microphone is turned on, etc when using the [Kaldi](https://dragonfly2.readthedocs.io/en/latest/kaldi_engine.html) speech backend of Dragonfly.

![Screensho of Frons in action](https://user-images.githubusercontent.com/931544/82132678-1cf69780-9797-11ea-93f8-bf6116277029.png)

Why? Historically Dragonfly has had minimal (or no) UI because it relied on being hosted inside Dragon NaturallySpeaking (using [natlink](https://qh.antenna.nl/unimacro/index.html)), which would provide visual feedback. But alternate speech engines do not provide a UI, so it's difficult to tell when commands are misrecognized vs not working.

## Status & Usage

As of 2020-05-16, you can use it to replace `kaldi_module_loader.py` (it's based on that), but its API should be considered highly unstable.

Features implemented:

* `kaldi_module_loader.py`'s standard grammar loading and voice commands for going to sleep
* Automatic reloading on changes to `.py` files using [watchdog](https://github.com/gorakhargosh/watchdog)
* Always on top, partially transparent display of microphone status and history of recognized words, time of last speech start detected, and time of last failed recognition
* Ability to render arbitrary additional UI text in the UI
* Voice commands for quitting and restarting

To use, copy `main.py` into the directory that contains your dragonfly grammars.. then read the code to see what voice commands you have, and tweak them to your taste. If you're not comfortable with that then it's best to wait until this is a bit more stable.

NB: this should work on Linux and MacOS, but I haven't tested it on either. Please raise an issue if something seems broken.

## Quirks and next steps

This was originally developed by hacking on `kaldi_module_loader.py` to add UI via Python's TK support (`tkinter`) until it did the bare minimum of what I needed it to do. That has been reached, but there are some limitations of the current quick and dirty design:

* keeping all the code in one file to make an easy drop in replacement is getting a bit unwieldy. It would benefit from being split, but doing so means that the installation will get more complicated.. and if it's a cloned repo or installable python package, then it might warrant a configuration mechanism to avoid people having to dirty their installed packages or local clone of the repo.
* code reloading currently restarts the whole python process. This is a blade that cuts both ways, because on the one hand it's quite reliable due to throwing away in memory state.. but on the other hand, it throws away in memory state, which necessitates users serializing their state to the filesystem and reading it on startup, and it might be a bit slower than necessary.
    * code reloading doesn't actually check for changes to the contents of any loaded files - it just listens for any event in the watched directory, so repeatedly saving a file without changes will cause reloads.
    * additionally, on Windows, code reloading will cause TK to steal focus when its window is created, despite all attempts on my part to not have it do so.
* API for setting visual context is not exposed outside the file

So next step is probably to split this apart and take it from "drop in file with minimal dependencies" to a repo you clone and pip install the dependencies for, which means I can justify using a UI toolkit that is not built in to Python's stdlib and write the more complicated code that's probably necessary to fix those quirks.

There are also a bunch of features I'd like to add:

* hotkey support for exiting/restarting/forcing a grammar reload, etc.
* display of kaldi hypotheses, so you can get feedback as you are speaking
* display of what microphone is in use (and maybe have it be configurable via UI/settings file?)
* separate out the rarely relevant bits from the main overlay (e.g. last speech failure) into a separate window so not too much screen real estate is covered at any given time
* a way to tweak Kaldi settings like voice activity detector aggressiveness
* levels indicator so you can see when you are speaking too softly vs too loudly

## Non-goals

* Replace Dragonfly itself - Dragonfly has its problems but it works well and has a strong community. Frons is intended to make Dragonfly better and perhaps a bit easier to use. Check out [Talon](http://talonvoice.com/) (or it's nascent clone, [Osprey](https://github.com/osprey-voice/osprey/)) if you don't want to write Dragonfly grammars.
* Build a ready to go voice-control/voice-coding solution. Check out [Caster](https://caster.readthedocs.io/en/latest/) for a good alternative.

## What's with the name?

Naming things well is hard. One hypothetical way to deal with that when you're building a front-end for a library called Dragonfly is that you google "dragonfly anatomy" and pick an uncommon but vaguely pronouncible noun on the first returned result. I'm not saying that's what happened here, but I'm also not saying that's not what happened here.

## License

Licensed under the GNU General Public License v3.0 or later; see `LICENSE`.
