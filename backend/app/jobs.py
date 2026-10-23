"""One ephemeral isolated process per analysis. No stored jobs or external queue."""
import multiprocessing as mp
from .engine import detect
from .custom_rules import RuleExecutionError

mp.set_forkserver_preload(["app.preload"])

def worker(connection,text,language,rules):
    try:
        def progress(percent,phase):connection.send({'type':'progress','percent':percent,'phase':phase})
        language_info={}
        hits=detect(text,language,progress=progress,custom_rules=rules,language_info=language_info)
        connection.send({'type':'result','detections':hits,'language_info':language_info})
    except RuleExecutionError as error:
        connection.send({'type':'error','detail':str(error)})
    except Exception:
        connection.send({'type':'error','detail':'Analyse interrompue. Aucun résultat validé.'})
    finally:connection.close()

def start(text,language,rules=()):
    # Fork from a dedicated server, never from the threaded ASGI process.
    context=mp.get_context('forkserver')
    reader,writer=context.Pipe(duplex=False)
    process=context.Process(target=worker,args=(writer,text,language,rules),daemon=True)
    process.start();writer.close()
    return process,reader

def stop(process,reader):
    if process.is_alive():process.terminate()
    process.join(timeout=1)
    if process.is_alive():process.kill();process.join(timeout=1)
    reader.close()

def _ready():
    pass

def warmup():
    process=mp.get_context('forkserver').Process(target=_ready)
    process.start();process.join(timeout=60)
    if process.is_alive():
        process.terminate();process.join()
        raise RuntimeError('Worker startup timeout')
    if process.exitcode!=0:raise RuntimeError('Worker startup failed')
